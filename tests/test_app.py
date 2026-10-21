"""Native interaction tests; browser storage is exercised separately in Playwright."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from data import load_scenarios
from learning import default_progress, QUESTIONS, question
from test_data import sample_draft

ROOT = Path(__file__).resolve().parents[1]


def workspace(step=0):
    at = AppTest.from_string('from ui_scenario import render_workspace\nrender_workspace()')
    s = load_scenarios()[0]
    d = sample_draft(s)
    d.update(step=step, answers={}, checked={}, notes={}, hints=[], revised=[])
    at.session_state['draft'] = d
    at.session_state['scenarios'] = load_scenarios()
    at.session_state['progress'] = default_progress()
    return at.run()


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_home_starts_without_account_or_saved_progress():
    at = AppTest.from_file(str(ROOT / 'app.py'))
    at.session_state['storage_ready'] = True
    at.run()
    assert not at.exception
    assert at.title[0].value == 'Your next marketing decision'
    assert not at.session_state['remember']


def test_brief_exposes_business_trigger_and_learning_objective():
    at = workspace()
    assert not at.exception
    assert any('20%' in info.value for info in at.info)
    button(at, 'Continue').click().run()
    assert at.session_state['draft']['step'] == 1


def test_unvisited_questions_are_unanswered_and_check_is_explicit():
    at = workspace(1)
    assert at.radio[0].value is None
    assert at.session_state['draft']['answers'] == {}
    assert button(at, 'Continue').disabled
    correct = question(load_scenarios()[0], 'company')['correct_idx']
    at.radio[0].set_value(correct).run()
    assert not at.session_state['draft']['checked']
    button(at, 'Check my reasoning').click().run()
    assert not button(at, 'Continue').disabled
    assert at.success


def test_revising_answer_requires_new_check_and_tracks_support():
    at = workspace(1)
    at.radio[0].set_value(0).run()
    button(at, 'Check my reasoning').click().run()
    at.radio[0].set_value(1).run()
    assert button(at, 'Continue').disabled
    assert 'company' in at.session_state['draft']['revised']


def test_notes_survive_navigation():
    at = workspace(1)
    at.text_area[0].set_value('Limited capital').run()
    at.radio[0].set_value(0).run()
    button(at, 'Check my reasoning').click().run()
    button(at, 'Continue').click().run()
    button(at, 'Back').click().run()
    assert not at.exception
    assert at.text_area[0].value == 'Limited capital'
    assert at.session_state['draft']['notes']['company']['evidence'] == 'Limited capital'


import pytest


@pytest.mark.parametrize('sid', range(1, 16))
def test_every_case_can_complete_and_save_consistent_score(sid):
    at = workspace(1)
    s = next(s for s in load_scenarios() if s['scenario_id'] == sid)
    d = dict(at.session_state['draft'])
    d.update(id=f'case-{sid}', scenario_id=sid)
    at.session_state['draft'] = d
    at.run()
    for key in QUESTIONS:
        at.radio[0].set_value(question(s, key)['correct_idx']).run()
        button(at, 'Check my reasoning').click().run()
        button(at, 'Continue').click().run()
        assert not at.exception
    at.text_area[0].set_value('The target fits the company capabilities.').run()
    button(at, 'Finish case').click().run()
    assert not at.exception
    history = at.session_state['progress']['attempts'][str(sid)]
    assert len(history) == 1
    assert history[0]['points'] == 100
    assert not history[0]['supported']
    at.run()
    assert len(at.session_state['progress']['attempts'][str(sid)]) == 1


def test_settings_delete_resets_session_and_requests_browser_removal():
    at = AppTest.from_string('from ui_learning import render_settings\nrender_settings()')
    at.session_state['progress'] = default_progress()
    at.session_state['draft'] = sample_draft(load_scenarios()[0])
    at.session_state['remember'] = True
    at.session_state['scenarios'] = load_scenarios()
    at.run()
    at.checkbox[0].check().run()
    button(at, 'Clear my learning data').click().run()
    assert not at.exception
    assert not at.session_state['remember']
    assert at.session_state['draft'] is None
    assert at.session_state['progress'] == default_progress()
    assert at.session_state['storage_clear_pending']


def test_turning_off_remembering_keeps_draft_but_removes_browser_copy():
    at = AppTest.from_string('from ui_learning import render_settings\nrender_settings()')
    at.session_state['progress'] = default_progress()
    at.session_state['draft'] = sample_draft(load_scenarios()[0])
    at.session_state['remember'] = True
    at.session_state['scenarios'] = load_scenarios()
    at.run()
    at.toggle[0].set_value(False).run()
    assert not at.exception
    assert at.session_state['draft']['id'] == 'attempt-1'
    assert at.session_state['storage_clear_pending']


def test_browser_saving_preference_survives_widget_cleanup_between_pages():
    at = AppTest.from_string('''
import streamlit as st
from app import init_state
from ui_learning import render_settings
init_state()
if st.session_state.get('show_settings', True):
    render_settings()
else:
    st.write('Another learning page')
''')
    at.run()
    at.toggle[0].set_value(True).run()
    assert at.session_state['remember']
    at.session_state['show_settings'] = False
    at.run()
    at.run()
    assert not at.exception
    assert at.session_state['remember']
