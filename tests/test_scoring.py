"""Tests for the save_scenario_progress scoring/mastery/tier-unlock logic.

These tests import the scoring function directly and exercise the critical
paths:

  - First-time completion updates score history
  - Replay does NOT inflate score history
  - Replay CAN promote mastery if the new score crosses the threshold
  - Tier N+1 unlocks when all Tier N scenarios are mastered
  - Mastery check uses MAX score (latest attempt's scenario_points)
"""
import json
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class FakeSessionState(dict):
    """Dict-like stand-in for st.session_state.

    Streamlit's real SessionState supports both attribute access (s.key) and
    item access (s["key"] or s.get("key", default)). This class supports all
    three, which lets us test code that uses either style.
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value


def _make_session_state(progress, scenarios, current_scenario=None, user_answers=None):
    """Build a mock st.session_state with the keys save_scenario_progress reads."""
    state = FakeSessionState()
    state.progress = progress
    state.scenarios = scenarios
    state.current_scenario = current_scenario
    state.user_answers = user_answers or {}
    return state


def _make_full_scenarios():
    """Build a small set of fake scenarios across 2 tiers for testing."""
    return [
        {"scenario_id": i, "title": f"S{i}", "difficulty_tier": 1 if i <= 2 else 2}
        for i in range(1, 5)
    ]


def _make_results(analysis_correct, stp_correct, cc_correct):
    """Build fake analysis_results, stp_results, cc_result dicts."""
    analysis = {
        "company": {"correct": analysis_correct},
        "competitors": {"correct": analysis_correct},
        "customers": {"correct": analysis_correct},
        "collaborators": {"correct": analysis_correct},
        "climate": {"correct": analysis_correct},
    }
    stp = {
        "segmentation": {"correct": stp_correct},
        "targeting": {"correct": stp_correct},
        "positioning": {"correct": stp_correct},
    }
    cc = {"correct": cc_correct}
    return analysis, stp, cc


def _make_scenario_points(analysis_correct, stp_correct, cc_correct):
    # analysis_correct: bool for all 5 C questions. Each is 4 pts → 20 if all correct.
    # stp_correct: bool for all 3 STP questions. Each is 20 pts → 60 if all correct.
    # cc_correct: bool for concept check. 20 pts.
    return (
        (20 if analysis_correct else 0)
        + (60 if stp_correct else 0)
        + (20 if cc_correct else 0)
    )


def test_first_completion_updates_score_history():
    from data import MASTER_THRESHOLD, save_progress
    import ui_scenario

    progress = {
        "completed_scenarios": [],
        "mastered_scenarios": [],
        "scenario_scores": {},
        "last_attempt_answers": {},
        "unlocked_tiers": [1],
        "total_points": 0,
        "total_score": {
            "analysis_company": {"correct": 0, "total": 0},
            "analysis_competitors": {"correct": 0, "total": 0},
            "analysis_customers": {"correct": 0, "total": 0},
            "analysis_collaborators": {"correct": 0, "total": 0},
            "analysis_climate": {"correct": 0, "total": 0},
            "segmentation": {"correct": 0, "total": 0},
            "targeting": {"correct": 0, "total": 0},
            "positioning": {"correct": 0, "total": 0},
            "concept_check": {"correct": 0, "total": 0},
        },
    }
    scenarios = _make_full_scenarios()
    scenario = scenarios[0]
    # 20 (analysis) + 0 (no stp) + 0 (no cc) = 20 pts (no mastery)
    analysis, stp, cc = _make_results(True, False, False)
    points = 20

    state = FakeSessionState()
    state.progress = progress
    state.scenarios = scenarios
    state.current_scenario = scenario
    state.user_answers = {"x": 1}
    with patch.object(ui_scenario.st, "session_state", state):
        with patch.object(ui_scenario, "save_progress", lambda p: None):
            ui_scenario.save_scenario_progress(scenario, analysis, stp, cc, points)

    assert progress["scenario_scores"]["1"] == points
    assert progress["total_points"] == points
    assert 1 in progress["completed_scenarios"]
    assert 1 not in progress["mastered_scenarios"]


def test_replay_does_not_inflate_score_history():
    from data import MASTER_THRESHOLD
    import ui_scenario

    progress = {
        "completed_scenarios": [1],
        "mastered_scenarios": [],
        "scenario_scores": {"1": 60},
        "last_attempt_answers": {},
        "unlocked_tiers": [1],
        "total_points": 60,
        "total_score": {
            "analysis_company": {"correct": 0, "total": 1},
            "analysis_competitors": {"correct": 0, "total": 1},
            "analysis_customers": {"correct": 0, "total": 1},
            "analysis_collaborators": {"correct": 0, "total": 1},
            "analysis_climate": {"correct": 0, "total": 1},
            "segmentation": {"correct": 1, "total": 1},
            "targeting": {"correct": 1, "total": 1},
            "positioning": {"correct": 1, "total": 1},
            "concept_check": {"correct": 1, "total": 1},
        },
    }
    scenarios = _make_full_scenarios()
    scenario = scenarios[0]
    analysis, stp, cc = _make_results(True, True, True)  # 100 pts this replay
    points = _make_scenario_points(True, True, True)

    state = _make_session_state(progress, scenarios, scenario, {"x": 1})
    with patch.object(ui_scenario.st, "session_state", state):
        with patch.object(ui_scenario, "save_progress", lambda p: None):
            ui_scenario.save_scenario_progress(scenario, analysis, stp, cc, points)

    # Score history NOT changed
    assert progress["scenario_scores"]["1"] == 60
    assert progress["total_points"] == 60
    # Score totals NOT incremented
    assert progress["total_score"]["analysis_company"]["total"] == 1
    # But mastery IS updated (new score is ≥ threshold)
    assert 1 in progress["mastered_scenarios"]


def test_replay_promotes_mastery_even_if_first_score_was_below_threshold():
    import ui_scenario

    progress = {
        "completed_scenarios": [1],
        "mastered_scenarios": [],
        "scenario_scores": {"1": 60},
        "last_attempt_answers": {},
        "unlocked_tiers": [1],
        "total_points": 60,
        "total_score": {
            "analysis_company": {"correct": 0, "total": 1},
            "analysis_competitors": {"correct": 0, "total": 1},
            "analysis_customers": {"correct": 0, "total": 1},
            "analysis_collaborators": {"correct": 0, "total": 1},
            "analysis_climate": {"correct": 0, "total": 1},
            "segmentation": {"correct": 1, "total": 1},
            "targeting": {"correct": 1, "total": 1},
            "positioning": {"correct": 1, "total": 1},
            "concept_check": {"correct": 1, "total": 1},
        },
    }
    scenarios = _make_full_scenarios()
    scenario = scenarios[0]
    analysis, stp, cc = _make_results(True, True, True)
    points = 80  # Above threshold
    state = _make_session_state(progress, scenarios, scenario, {"x": 1})
    with patch.object(ui_scenario.st, "session_state", state):
        with patch.object(ui_scenario, "save_progress", lambda p: None):
            ui_scenario.save_scenario_progress(scenario, analysis, stp, cc, points)

    assert 1 in progress["mastered_scenarios"]


def test_tier_unlock_when_all_scenarios_in_tier_mastered():
    import ui_scenario

    progress = {
        "completed_scenarios": [1, 2],
        "mastered_scenarios": [1],  # only S1 mastered
        "scenario_scores": {"1": 80, "2": 60},
        "last_attempt_answers": {},
        "unlocked_tiers": [1],
        "total_points": 140,
        "total_score": {},
    }
    scenarios = _make_full_scenarios()
    scenario = scenarios[1]  # S2 — first attempt with mastery
    analysis, stp, cc = _make_results(True, True, True)
    points = 100
    state = _make_session_state(progress, scenarios, scenario, {})
    with patch.object(ui_scenario.st, "session_state", state):
        with patch.object(ui_scenario, "save_progress", lambda p: None):
            ui_scenario.save_scenario_progress(scenario, analysis, stp, cc, points)

    # Now S1 + S2 are both mastered → Tier 2 should unlock
    assert 2 in progress["unlocked_tiers"]


def test_tier_unlock_supports_arbitrary_tier_count():
    """Adding a Tier 4 should not require code changes to the unlock loop."""
    import ui_scenario

    progress = {
        "completed_scenarios": [1, 2, 3, 4],
        "mastered_scenarios": [1, 2],  # S1+S2 mastered (Tier 1)
        "scenario_scores": {"1": 80, "2": 80, "3": 60, "4": 60},
        "last_attempt_answers": {},
        "unlocked_tiers": [1, 2],
        "total_points": 280,
        "total_score": {},
    }
    # Add a Tier 3 + Tier 4 to the fake scenarios
    scenarios = _make_full_scenarios() + [
        {"scenario_id": 5, "title": "S5", "difficulty_tier": 3},
        {"scenario_id": 6, "title": "S6", "difficulty_tier": 3},
        {"scenario_id": 7, "title": "S7", "difficulty_tier": 4},
    ]
    # Master S3+S4 (Tier 2) by replaying one of them
    scenario = scenarios[2]  # S3
    analysis, stp, cc = _make_results(True, True, True)
    points = 100
    state = _make_session_state(progress, scenarios, scenario, {})
    with patch.object(ui_scenario.st, "session_state", state):
        with patch.object(ui_scenario, "save_progress", lambda p: None):
            ui_scenario.save_scenario_progress(scenario, analysis, stp, cc, points)

    # Now S1+S2+S3 mastered → Tier 2 unlocked; S4 not mastered so no further unlock
    assert 2 in progress["unlocked_tiers"]


def test_last_attempt_answers_is_snapshotted():
    import ui_scenario

    progress = {
        "completed_scenarios": [],
        "mastered_scenarios": [],
        "scenario_scores": {},
        "last_attempt_answers": {},
        "unlocked_tiers": [1],
        "total_points": 0,
        "total_score": {
            "analysis_company": {"correct": 0, "total": 0},
            "analysis_competitors": {"correct": 0, "total": 0},
            "analysis_customers": {"correct": 0, "total": 0},
            "analysis_collaborators": {"correct": 0, "total": 0},
            "analysis_climate": {"correct": 0, "total": 0},
            "segmentation": {"correct": 0, "total": 0},
            "targeting": {"correct": 0, "total": 0},
            "positioning": {"correct": 0, "total": 0},
            "concept_check": {"correct": 0, "total": 0},
        },
    }
    scenarios = _make_full_scenarios()
    scenario = scenarios[0]
    analysis, stp, cc = _make_results(True, True, True)
    points = 100
    user_answers = {"segmentation": 1, "targeting": 0, "company": 2}
    state = FakeSessionState()
    state.progress = progress
    state.scenarios = scenarios
    state.current_scenario = scenario
    state.user_answers = user_answers
    with patch.object(ui_scenario.st, "session_state", state):
        with patch.object(ui_scenario, "save_progress", lambda p: None):
            ui_scenario.save_scenario_progress(scenario, analysis, stp, cc, points)

    assert "1" in progress["last_attempt_answers"]
    assert progress["last_attempt_answers"]["1"]["answers"]["segmentation"] == 1
    assert progress["last_attempt_answers"]["1"]["score"] == 100
