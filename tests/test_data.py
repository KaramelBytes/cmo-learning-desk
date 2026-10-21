"""Privacy boundaries, content loading, and portable state validation."""
import json
from copy import deepcopy
from pathlib import Path
import pytest
from data import load_scenarios
from learning import default_progress, score_attempt, QUESTIONS, question
from utils.persistence import make_payload, validate_payload


def sample_draft(scenario):
    return {'id': 'attempt-1', 'scenario_id': scenario['scenario_id'], 'step': 10,
            'answers': {k: question(scenario, k)['correct_idx'] for k in QUESTIONS},
            'checked': {}, 'notes': {'company': {'evidence': 'Limited capital', 'implication': 'Focus'}},
            'hints': ['company'], 'revealed': [], 'revised': ['company'],
            'explanation': 'Customer needs fit capabilities.', 'transfer': 'Recheck the promise.'}


def test_catalog_is_complete_and_has_learning_guides():
    scenarios = load_scenarios()
    assert len(scenarios) == 15
    assert {s['difficulty_tier'] for s in scenarios} == {1, 2, 3}
    assert all(s['objective'] and s['transfer_prompt'] and s['transfer_discussion'] for s in scenarios)


def test_load_catalog_never_creates_progress_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(load_scenarios()) == 15
    assert not list(tmp_path.iterdir())


def test_backup_round_trip_recalculates_scores_and_preserves_support():
    scenarios = load_scenarios()
    draft = sample_draft(scenarios[0])
    attempt = score_attempt(scenarios[0], draft)
    progress = default_progress()
    progress['attempts']['1'] = [attempt]
    raw = make_payload(progress, draft)
    raw['progress']['attempts']['1'][0]['points'] = -100
    restored = validate_payload(json.dumps(raw), scenarios)
    a = restored['progress']['attempts']['1'][0]
    assert a['points'] == 100
    assert a['supported']
    assert a['revised'] == ['company']
    assert restored['draft']['notes'] == draft['notes']


@pytest.mark.parametrize('mutate', [
    lambda p: p.update(version=999),
    lambda p: p['draft']['answers'].update(company=-1),
    lambda p: p['draft']['answers'].update(company=True),
    lambda p: p['draft'].update(step=99),
    lambda p: p['draft'].update(scenario_id=1000),
    lambda p: p['draft'].update(explanation='x' * 4001),
    lambda p: p['draft']['checked'].update(company=99),
])
def test_reject_malformed_backups(mutate):
    scenarios = load_scenarios()
    raw = make_payload(default_progress(), sample_draft(scenarios[0]))
    mutate(raw)
    with pytest.raises((ValueError, KeyError)):
        validate_payload(raw, scenarios)


def test_no_learner_files_or_analytics_in_app():
    root = Path(__file__).resolve().parents[1]
    sources = '\n'.join((root / name).read_text() for name in ('app.py', 'data.py', 'learning.py', 'ui_learning.py', 'utils/persistence.py'))
    assert 'progress.json' not in sources
    assert 'set_local_storage' not in sources
    assert 'gatherUsageStats = false' in (root / '.streamlit/config.toml').read_text()


def test_reject_backup_from_changed_case_content():
    scenarios = load_scenarios()
    d = sample_draft(scenarios[0])
    d['content_version'] = 999
    with pytest.raises(ValueError, match='content version'):
        validate_payload(make_payload(default_progress(), d), scenarios)
