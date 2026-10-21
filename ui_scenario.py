"""Guided learning workspace shared by the full scenario catalog."""
from datetime import datetime, timezone
from uuid import uuid4
import streamlit as st
from learning import (ANALYSIS, STRATEGY, QUESTIONS, MASTER_THRESHOLD, question,
                      score_attempt, record_attempt, summary, strategy_brief)
from ui_components import GLOSSARY, go

STAGES = ['Brief'] + [k.title() for k in ANALYSIS + STRATEGY] + ['Concept check', 'Explain', 'Debrief']


def start_case(sid):
    current = st.session_state.draft
    if current and current['scenario_id'] != sid:
        st.session_state.replace_case = sid
        return
    _new_case(sid)


def _new_case(sid):
    st.session_state.draft = {'id': str(uuid4()), 'scenario_id': sid, 'content_version': 2, 'step': 0,
        'answers': {}, 'checked': {}, 'notes': {}, 'hints': [], 'revealed': [],
        'revised': [], 'explanation': '', 'transfer': ''}
    st.session_state.replace_case = None
    go('Case workspace')


def case_card(s):
    status = summary(st.session_state.progress, s['scenario_id'])
    with st.container(border=True):
        st.subheader(s['title'])
        st.caption(f"{s['scenario_type']} · {['Beginner', 'Intermediate', 'Advanced'][s['difficulty_tier'] - 1]}")
        st.write(s['objective'])
        if status['latest']:
            st.caption(f"Latest {status['latest']['points']}/100 · Best {status['best']}/100 · {status['count']} attempts")
        if st.button('Open case', type='primary', key=f"start_{s['scenario_id']}"):
            draft = st.session_state.draft
            if draft and draft['scenario_id'] == s['scenario_id']:
                go('Case workspace')
            else:
                start_case(s['scenario_id'])
                st.rerun()


def replacement_prompt():
    sid = st.session_state.get('replace_case')
    if sid:
        st.warning('You have an unfinished case. Download a backup in Settings before replacing it if you want to keep that draft.')
        a, b = st.columns(2)
        if a.button('Replace active draft'):
            _new_case(sid)
        if b.button('Keep current case'):
            st.session_state.replace_case = None
            st.rerun()
        return True
    return False


def render_home():
    st.title('Your next marketing decision')
    st.write('Build a strategy you can explain. Investigate the evidence, choose a direction, and defend your recommendation.')
    if replacement_prompt():
        return
    if st.session_state.draft:
        with st.container(border=True):
            d = st.session_state.draft
            s = next(s for s in st.session_state.scenarios if s['scenario_id'] == d['scenario_id'])
            st.subheader('Continue where you left off')
            st.write(s['title'])
            st.caption(f"Next: {STAGES[d['step']]}")
            if st.button('Continue my case', type='primary'):
                go('Case workspace')
    completed = st.session_state.progress['attempts']
    recommended = next((s for s in st.session_state.scenarios if not completed.get(str(s['scenario_id']))), st.session_state.scenarios[0])
    st.subheader('Recommended next case')
    case_card(recommended)
    st.caption('Start with a familiar business, then explore more complex trade-offs. All difficulty levels are open.')
    if st.button('Practice a concept'):
        go('Review')


def render_catalog():
    st.title('Explore the cases')
    st.write('Follow the recommended order or choose a business problem that interests you.')
    if replacement_prompt():
        return
    query = st.text_input('Find a case', placeholder='Try coffee, pricing, or platform')
    tier = st.selectbox('Difficulty', ['All', 'Beginner', 'Intermediate', 'Advanced'])
    matches = [s for s in st.session_state.scenarios if query.lower() in (s['title'] + s['scenario_type']).lower()
               and (tier == 'All' or s['difficulty_tier'] == ['All', 'Beginner', 'Intermediate', 'Advanced'].index(tier))]
    for s in matches:
        case_card(s)
    if not matches:
        st.info('No matching cases. Try a broader search.')


def _answer_changed(key, widget):
    d = st.session_state.draft
    idx = st.session_state[widget]
    if key in d['checked'] and d['checked'][key] != idx:
        if key not in d['revised']:
            d['revised'].append(key)
        d['checked'].pop(key, None)
    if idx is not None:
        d['answers'][key] = idx


def _note_changed(key, field, widget):
    st.session_state.draft['notes'].setdefault(key, {})[field] = st.session_state[widget]


def _text_changed(field, widget):
    st.session_state.draft[field] = st.session_state[widget]


def _set_step(step):
    st.session_state.draft['step'] = step


def _evidence(s, key):
    data = s['situation_analysis'][key]
    if data.get('summary'):
        st.write(data['summary'])
    fields = [(k, v) for k, v in data.items() if k != 'summary']
    # Facts remain available; longer source lists are folded below the summary.
    with st.expander('Read the supporting evidence', expanded=not bool(data.get('summary'))):
        for field, value in fields:
            st.markdown(f"**{field.replace('_', ' ').title()}**")
            if isinstance(value, list):
                for item in value:
                    st.write('• ' + item)
            else:
                st.write(value)


def render_notebook_content(s, notes):
    if not notes:
        st.caption('Save evidence and implications during the investigation to build your notebook.')
    for key in ANALYSIS:
        if key in notes:
            with st.expander(key.title()):
                st.write('**Evidence**')
                st.text(notes[key].get('evidence') or 'No evidence saved yet.')
                st.write('**Strategic implication**')
                st.text(notes[key].get('implication') or 'No implication saved yet.')


def _question_panel(s, key):
    d = st.session_state.draft
    q = question(s, key)
    widget = f"answer_{d['id']}_{key}"
    if widget not in st.session_state:
        st.session_state[widget] = d['answers'].get(key)
    st.radio(q['question'], range(len(q['options'])), format_func=lambda i: q['options'][i],
             index=None, key=widget, on_change=_answer_changed, args=(key, widget))
    a, b = st.columns(2)
    if a.button('Check my reasoning', type='primary', disabled=key not in d['answers'], key=f'check_{key}'):
        d['checked'][key] = d['answers'][key]
        st.rerun()
    if b.button('Give me a hint', key=f'hint_{key}'):
        if key not in d['hints']:
            d['hints'].append(key)
        st.rerun()
    if key in d['hints']:
        hint_lenses = {'segmentation': 'Customers', 'targeting': 'Company', 'positioning': 'Competitors', 'concept_check': 'Positioning'}
        lens = key.title() if key in ANALYSIS else hint_lenses[key]
        st.info(GLOSSARY[lens] + ' Identify one fact that supports your choice and one that challenges it.')
    if key in d['checked']:
        idx = d['checked'][key]
        correct = idx == q['correct_idx']
        feedback = s.get('option_feedback', {}).get(key, [])
        if correct:
            st.success('Your choice is supported by the case evidence.')
            st.write(feedback[idx] if feedback else q.get('rationale', q.get('rubric_rationale')))
        else:
            st.warning('There is a stronger fit with the evidence. You can revise your choice.')
            if feedback:
                st.write(feedback[idx])
            else:
                st.write('Compare the needs in the question with the company’s capabilities and constraints. Which fact would make you reconsider this choice?')
            if st.button('Show the model reasoning', key=f'model_{key}'):
                if key not in d['revealed']:
                    d['revealed'].append(key)
                st.rerun()
        if key in d['revealed']:
            st.write('**Model answer:** ' + q['options'][q['correct_idx']])
            st.write(q.get('rationale', q.get('rubric_rationale')))
    return key in d['checked']


def render_workspace():
    d = st.session_state.draft
    st.title('Case workspace')
    if not d:
        st.info('Choose a case to begin.')
        if st.button('Explore cases', type='primary'):
            go('Cases')
        return
    s = next(s for s in st.session_state.scenarios if s['scenario_id'] == d['scenario_id'])
    step = d['step']
    st.caption(s['title'])
    phase = 'Brief' if step == 0 else 'Investigate' if step <= 5 else 'Decide' if step <= 8 else 'Explain' if step <= 10 else 'Debrief'
    st.progress(step / 11, text=f'{phase} · Task {step + 1} of 12')
    st.header(STAGES[step])
    can_continue = True
    if step == 0:
        st.write(s['background'])
        st.info(s['trigger_event'])
        st.subheader('Your assignment')
        st.write('Recommend how this business should segment its market, which customers it should prioritize, and how it should position its offer. Defend your recommendation with evidence.')
        st.write('**You will learn to:** ' + s['objective'])
        st.caption('Practice is low stakes. You can revise answers, ask for hints, and save your work. Support use is shown separately from your score.')
        if s['difficulty_tier'] == 1:
            with st.expander('See how to connect evidence to a decision'):
                st.write(s.get('worked_example', 'Evidence describes what is happening. Interpretation explains why it matters. A strategic implication connects it to a decision: “Because this segment needs X and we can deliver Y, we should consider Z.”'))
    elif step <= 5:
        key = ANALYSIS[step - 1]
        st.caption(GLOSSARY[key.title()])
        _evidence(s, key)
        st.subheader('What does this mean?')
        can_continue = _question_panel(s, key)
        with st.expander('Save an insight to your notebook', expanded=True):
            note = d['notes'].get(key, {})
            for field, label in [('evidence', 'Which fact matters most?'), ('implication', 'What might this mean for the strategy?')]:
                widget = f"note_{d['id']}_{key}_{field}"
                st.text_area(label, value=note.get(field, ''), key=widget, max_chars=4000,
                             on_change=_note_changed, args=(key, field, widget),
                             placeholder='Optional: explain it in your own words.')
    elif step <= 8:
        key = STRATEGY[step - 6]
        st.caption(GLOSSARY[key.title()])
        st.subheader('Your evidence notebook')
        render_notebook_content(s, d['notes'])
        with st.expander('Revisit the source evidence'):
            context = {'segmentation': ['customers'], 'targeting': ['company', 'competitors', 'collaborators'], 'positioning': ['company', 'customers', 'climate']}
            for lens in context[key]:
                st.markdown('**' + lens.title() + '**')
                _evidence(s, lens)
        st.subheader('Make your decision')
        can_continue = _question_panel(s, key)
    elif step == 9:
        st.write('Apply the underlying idea before reviewing the complete strategy.')
        can_continue = _question_panel(s, 'concept_check')
    elif step == 10:
        st.write('Connect one important fact to your recommendation. These reflections are for you; they are not automatically graded.')
        for field, label in [('explanation', 'Why is your strategy a good fit for this business?'), ('transfer', s['transfer_prompt'])]:
            widget = f"reflection_{d['id']}_{field}"
            st.text_area(label, value=d.get(field, ''), max_chars=4000, key=widget,
                         on_change=_text_changed, args=(field, widget))
        with st.expander('Self-review checklist and discussion'):
            st.write('• Did I cite a specific fact?\n\n• Did I connect customer needs with capabilities?\n\n• Did I explain a trade-off or assumption?')
            st.write('**Changed conditions:** ' + s['transfer_discussion'])
        st.caption('Writing even one sentence helps make your reasoning explicit. You may also continue without a reflection.')
    else:
        render_debrief(s, d)
        return
    st.divider()
    back, forward = st.columns(2)
    if back.button('Back', disabled=step == 0):
        _set_step(step - 1)
        st.rerun()
    if forward.button('Finish case' if step == 10 else 'Continue', disabled=not can_continue, width='stretch'):
        if step == 10:
            if set(d['checked']) != set(QUESTIONS):
                st.error('Check each decision before completing the case.')
                return
            attempt = score_attempt(s, d)
            record_attempt(st.session_state.progress, s['scenario_id'], attempt)
        _set_step(step + 1)
        st.rerun()
    if not can_continue:
        st.caption('Choose an answer and check your reasoning to continue. A checked answer can be revised, whether correct or incorrect.')
    if st.button('Pause and return to desk'):
        go('Home')
    st.caption('You can leave this page and continue from Home. Enable browser saving in Settings to resume after refreshing.')


def render_debrief(s, d):
    history = st.session_state.progress['attempts'].get(str(s['scenario_id']), [])
    attempt = next((a for a in history if a['id'] == d['id']), None)
    if not attempt:
        # An imported draft at the final step is not itself a submitted attempt.
        st.info('Review your explanation and finish the case to save this attempt.')
        if st.button('Return to explanation'):
            d['step'] = 10
            st.rerun()
        return
    pts = attempt['points']
    if pts >= MASTER_THRESHOLD:
        st.success('Practice target reached' if attempt['supported'] else 'Practice target reached independently')
    else:
        st.info('Case completed. Use the feedback below to choose what to practice next.')
    st.metric('Case score', f'{pts}/100')
    st.caption('Practice target: 75/100. This score measures this case, not lasting mastery. ' + ('Hints, model answers, or revisions were used.' if attempt['supported'] else 'No hints, model answers, or answer revisions were used.'))
    correct = [k for k in QUESTIONS if attempt['results'][k]['correct']]
    weak = [k for k in QUESTIONS if not attempt['results'][k]['correct']]
    st.write('**What went well:** ' + (', '.join(k.replace('_', ' ').title() for k in correct) or 'You completed a full evidence-to-strategy cycle.'))
    if weak:
        st.write('**Next practice:** ' + weak[0].replace('_', ' ').title())
    st.subheader('Your evidence-to-decision chain')
    render_notebook_content(s, attempt['notes'])
    for key in QUESTIONS:
        q = question(s, key)
        result = attempt['results'][key]
        with st.expander(('✓ ' if result['correct'] else 'Revisit · ') + key.replace('_', ' ').title()):
            st.write('**Your choice:** ' + q['options'][result['selected']])
            st.write('**Model choice:** ' + q['options'][q['correct_idx']])
            st.write(q.get('rationale', q.get('rubric_rationale')))
    st.write('**Your explanation**')
    st.text(attempt['explanation'] or 'No reflection added.')
    st.download_button('Download my strategy brief', strategy_brief(s, attempt), file_name=f"cmo-strategy-{s['scenario_id']}.md", mime='text/markdown')
    st.caption('Your attempt has been recorded in this session. Browser saving is optional in Settings.')
    if st.button('Return to my desk', type='primary'):
        st.session_state.draft = None
        go('Home')
    if st.button('Start a fresh attempt'):
        _new_case(s['scenario_id'])
