"""Notebook, practice review, progress, and learner-controlled data tools."""
import json
from datetime import datetime, timezone
import streamlit as st
from learning import QUESTIONS, default_progress, question, summary, review_due, strategy_brief
from ui_components import go
from ui_scenario import render_notebook_content
from utils.persistence import MAX_BYTES, make_payload, validate_payload

PRIVACY = ('No account is required. The app does not intentionally save your answers or notes '
           'to server files or a database. Answers and notes are processed on Streamlit Community Cloud. '
           'If you enable “Remember my progress,” learning data is saved in this browser. '
           'You can clear it here. Downloads are saved wherever you choose on your device.')


def render_notebook():
    st.title('Your evidence notebook')
    st.write('Keep the connection between facts, interpretation, and decisions.')
    d = st.session_state.draft
    if d:
        s = next(s for s in st.session_state.scenarios if s['scenario_id'] == d['scenario_id'])
        st.subheader('Active case · ' + s['title'])
        render_notebook_content(s, d['notes'])
        if st.button('Continue this case', type='primary'):
            go('Case workspace')
    for s in st.session_state.scenarios:
        history = st.session_state.progress['attempts'].get(str(s['scenario_id']), [])
        if history:
            with st.expander(s['title'] + ' · completed briefs'):
                labels = list(range(len(history)))
                idx = st.selectbox('Attempt', labels, format_func=lambda i: f"Attempt {i+1} · {history[i]['points']}/100", key=f"brief_attempt_{s['scenario_id']}")
                a = history[idx]
                st.text(a.get('explanation') or 'No reflection added.')
                render_notebook_content(s, a['notes'])
                st.download_button('Download strategy brief', strategy_brief(s, a), file_name=f"cmo-strategy-{s['scenario_id']}.md", key=f"brief_{s['scenario_id']}")
    if not d and not st.session_state.progress['attempts']:
        st.info('Your notebook will grow as you investigate a case.')


def render_progress():
    st.title('Your learning progress')
    st.write('See improvement across attempts. Scores describe performance on these cases; later review provides another check on understanding.')
    progress = st.session_state.progress
    completed = sum(bool(v) for v in progress['attempts'].values())
    st.progress(completed / len(st.session_state.scenarios), text=f'{completed} of 15 cases completed')
    if not completed:
        st.info('Complete a case to see your learning history here.')
        return
    rows = []
    for s in st.session_state.scenarios:
        stats = summary(progress, s['scenario_id'])
        if stats['count']:
            rows.append({'Case': s['title'], 'Attempts': stats['count'], 'First': stats['first']['points'],
                         'Latest': stats['latest']['points'], 'Best': stats['best'],
                         '75+ independently': 'Yes' if stats['independent'] else 'Not yet'})
    st.dataframe(rows, hide_index=True, width='stretch')
    st.subheader('Skills in your latest attempts')
    for key in QUESTIONS:
        attempts = [v[-1] for v in progress['attempts'].values() if v]
        correct = sum(a['results'][key]['correct'] for a in attempts)
        st.write(f"**{key.replace('_', ' ').title()}:** {correct}/{len(attempts)} supported choices")
    st.caption('Latest-case accuracy includes practice with assistance. It is not a mastery estimate.')
    if st.button('Review a concept', type='primary'):
        go('Review')


def render_review():
    st.title('A little practice, a stronger connection')
    st.write('Revisit a question without replaying a whole case. Priority goes to missed decisions, then questions ready for review after two days.')
    candidates = []
    progress = st.session_state.progress
    for s in st.session_state.scenarios:
        history = progress['attempts'].get(str(s['scenario_id']), [])
        if not history:
            continue
        latest = history[-1]
        for key in QUESTIONS:
            prior = progress['reviews'].get(f"{s['scenario_id']}:{key}")
            due = review_due(prior or latest)
            wrong = not latest['results'][key]['correct'] if not prior else prior['answer'] != question(s, key)['correct_idx']
            candidates.append((0 if wrong else 1 if due else 2, s, key))
    if not candidates:
        st.info('Complete a case first. Your decisions will become a personal practice collection.')
        return
    candidates.sort(key=lambda item: item[0])
    current = st.session_state.get('review_current')
    index = next((i for i, (_, case, key) in enumerate(candidates) if current == (case['scenario_id'], key)), 0)
    priority, s, key = candidates[index]
    st.session_state.review_current = (s['scenario_id'], key)
    st.caption(('Focus area' if priority == 0 else 'Ready for spaced review' if priority == 1 else 'Optional extra practice') + ' · ' + s['title'])
    with st.expander('Case context'):
        st.write(s['background'])
        st.write(s['trigger_event'])
    q = question(s, key)
    widget = f"review_{s['scenario_id']}_{key}_{st.session_state.get('review_round', 0)}"
    idx = st.radio(q['question'], range(len(q['options'])), format_func=lambda i: q['options'][i], index=None, key=widget)
    if st.button('Check recall', type='primary', disabled=idx is None):
        progress['reviews'][f"{s['scenario_id']}:{key}"] = {'answer': idx, 'at': datetime.now(timezone.utc).isoformat()}
        st.session_state.review_feedback = {'widget': widget, 'answer': idx}
    feedback = st.session_state.get('review_feedback', {})
    if feedback.get('widget') == widget:
        correct = feedback['answer'] == q['correct_idx']
        (st.success if correct else st.info)('You recalled the supported choice.' if correct else 'Use the model reasoning to reconnect the idea with the evidence.')
        st.write('**Model answer:** ' + q['options'][q['correct_idx']])
        st.write(q.get('rationale', q.get('rubric_rationale')))
    if st.button('Try another question'):
        _, next_case, next_key = candidates[(index + 1) % len(candidates)]
        st.session_state.review_current = (next_case['scenario_id'], next_key)
        st.session_state.review_round = st.session_state.get('review_round', 0) + 1
        st.rerun()
    st.caption('Repeated questions check recall of these cases. The changed-condition reflections in each case ask you to apply the idea more broadly.')


def _remember_changed():
    st.session_state.remember = st.session_state['_remember_widget']
    if not st.session_state.remember:
        st.session_state.storage_clear_pending = True


def render_settings():
    st.title('Your data, your choice')
    st.write(PRIVACY)
    st.markdown('[Streamlit privacy notice](https://streamlit.io/privacy-policy) · [Community Cloud platform analytics](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-analytics)')
    if '_remember_widget' not in st.session_state:
        st.session_state['_remember_widget'] = st.session_state.remember
    st.toggle('Remember my progress on this device', key='_remember_widget', on_change=_remember_changed,
              help='Save case progress, reflections, and notebook entries in this browser. Leave this off on a shared device.')
    if st.session_state.remember:
        st.caption('Browser storage can be cleared by your browser. Download a backup for work you want to keep.')
    else:
        st.caption('Session only: refreshing or disconnecting can lose your work. You can still download a backup.')
    st.subheader('Back up or move your learning')
    payload = make_payload(st.session_state.progress, st.session_state.draft)
    st.download_button('Download learning backup', json.dumps(payload, indent=2), file_name='cmo-learning-backup.json', mime='application/json')
    uploaded = st.file_uploader('Restore a learning backup', type=['json'], key=f"import_{st.session_state.get('import_round', 0)}", help='Replaces current progress after you choose Restore. Maximum 2 MB.')
    if uploaded:
        try:
            if uploaded.size > MAX_BYTES:
                raise ValueError('Backup is too large (maximum 2 MB).')
            restored = validate_payload(uploaded.getvalue(), st.session_state.scenarios)
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError):
            st.error('This backup could not be restored. Choose an unmodified CMO Desk version 2 backup, up to 2 MB.')
        else:
            st.caption(f"Contains {sum(len(v) for v in restored['progress']['attempts'].values())} completed attempts" + (' and an active draft.' if restored['draft'] else '.'))
            if st.button('Replace current learning with this backup'):
                st.session_state.progress = restored['progress']
                st.session_state.draft = restored['draft']
                for key in list(st.session_state):
                    if key.startswith(('answer_', 'note_', 'reflection_', 'brief_attempt_', 'review_')):
                        del st.session_state[key]
                st.session_state.import_round = st.session_state.get('import_round', 0) + 1
                st.session_state.import_success = True
                st.rerun()
    if st.session_state.pop('import_success', False):
        st.success('Backup restored. Continue from Home or explore your notebook.')
    st.divider()
    st.subheader('Clear learning data')
    confirmed = st.checkbox('I want to erase my session and browser-saved learning data.')
    st.button('Clear my learning data', disabled=not confirmed, on_click=_clear_data)
    if st.session_state.pop('cleared', False):
        st.success('Session learning data cleared. Browser removal status appears below.')
    st.caption('Clearing here does not delete backup files you previously downloaded.')


def _clear_data():
    st.session_state.progress = default_progress()
    st.session_state.draft = None
    st.session_state.remember = False
    st.session_state['_remember_widget'] = False
    st.session_state.storage_clear_pending = True
    for key in list(st.session_state):
        if key.startswith(('answer_', 'note_', 'reflection_', 'review_', 'brief_attempt_', 'import_')):
            del st.session_state[key]
    st.session_state.cleared = True
