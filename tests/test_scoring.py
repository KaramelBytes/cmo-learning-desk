from copy import deepcopy
from datetime import datetime, timedelta, timezone
from data import load_scenarios
from learning import (QUESTIONS, question, default_progress, score_attempt, record_attempt,
                      summary, review_due, strategy_brief)
from test_data import sample_draft


def test_weighted_scoring_and_idempotent_submission():
    s = load_scenarios()[0]
    d = sample_draft(s)
    d['answers']['company'] = (question(s, 'company')['correct_idx'] + 1) % len(question(s, 'company')['options'])
    a = score_attempt(s, d)
    assert a['points'] == 96
    p = default_progress()
    record_attempt(p, 1, a)
    record_attempt(p, 1, a)
    assert summary(p, 1)['count'] == 1


def test_replay_exposes_improvement_without_losing_first_attempt():
    s = load_scenarios()[0]
    d = sample_draft(s)
    p = default_progress()
    first = score_attempt(s, d)
    first['points'] = 20
    record_attempt(p, 1, first)
    d.update(id='second', hints=[], revised=[], revealed=[])
    record_attempt(p, 1, score_attempt(s, d))
    stats = summary(p, 1)
    assert stats['first']['points'] == 20
    assert stats['latest']['points'] == stats['best'] == 100
    assert stats['independent']


def test_assisted_success_is_distinct_from_independent_success():
    s = load_scenarios()[0]
    p = default_progress()
    record_attempt(p, 1, score_attempt(s, sample_draft(s)))
    assert summary(p, 1)['best'] == 100
    assert not summary(p, 1)['independent']


def test_notes_are_snapshots_and_export_includes_learner_reasoning():
    s = load_scenarios()[0]
    d = sample_draft(s)
    a = score_attempt(s, d)
    d['notes']['company']['evidence'] = 'Changed'
    assert a['notes']['company']['evidence'] == 'Limited capital'
    brief = strategy_brief(s, a)
    assert a['explanation'] in brief
    assert a['transfer'] in brief


def test_review_uses_elapsed_time():
    now = datetime.now(timezone.utc)
    assert review_due({'at': (now - timedelta(days=3)).isoformat()}, now)
    assert not review_due({'at': now.isoformat()}, now)
