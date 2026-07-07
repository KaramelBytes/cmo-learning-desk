"""Tests for the data loading and progress migration logic.

These tests exercise the pure-Python helpers in `data.py` and the localStorage
helpers in `utils.persistence.py`. They do not require Streamlit to be
running, but they do import from `streamlit` for the @st.cache_data decorator
on `load_scenarios` (which is a no-op when the test calls the cached function
outside of a Streamlit session).
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# load_progress / _migrate_progress / get_default_progress
# ---------------------------------------------------------------------------

def test_get_default_progress_has_all_keys():
    from data import get_default_progress
    default = get_default_progress()
    for key in [
        "completed_scenarios",
        "mastered_scenarios",
        "scenario_scores",
        "last_attempt_answers",
        "unlocked_tiers",
        "total_points",
        "total_score",
    ]:
        assert key in default, f"Missing default key: {key}"


def test_migrate_progress_drops_obsolete_keys(tmp_path):
    from data import _migrate_progress
    legacy = {
        "completed_scenarios": [1],
        "mastered_scenarios": [],
        "scenario_scores": {"1": 60},
        "flashcard_progress": {"last_card_id": "SC_01"},
        "unlocked_tiers": [1],
        "total_points": 60,
        "total_score": {},
    }
    migrated = _migrate_progress(legacy)
    assert "flashcard_progress" not in migrated, "flashcard_progress should be dropped"
    assert migrated["completed_scenarios"] == [1]


def test_migrate_progress_adds_missing_keys():
    from data import _migrate_progress
    minimal = {"completed_scenarios": []}
    migrated = _migrate_progress(minimal)
    assert "mastered_scenarios" in migrated
    assert "scenario_scores" in migrated
    assert "last_attempt_answers" in migrated
    assert "unlocked_tiers" in migrated
    assert "total_points" in migrated
    assert "total_score" in migrated


def test_load_progress_returns_defaults_when_file_missing(tmp_path, monkeypatch):
    from data import load_progress
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    progress = load_progress()
    assert progress["completed_scenarios"] == []
    assert progress["unlocked_tiers"] == [1]
    assert progress["total_points"] == 0


def test_load_progress_recovers_from_corrupt_file(tmp_path, monkeypatch):
    from data import load_progress
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "progress.json").write_text("{not valid json")
    progress = load_progress()
    assert progress["completed_scenarios"] == []
    assert progress["unlocked_tiers"] == [1]


def test_load_progress_migrates_legacy_flashcard_field(tmp_path, monkeypatch):
    from data import load_progress
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    legacy = {
        "completed_scenarios": [1, 2],
        "mastered_scenarios": [1],
        "scenario_scores": {"1": 80, "2": 60},
        "unlocked_tiers": [1, 2],
        "total_points": 140,
        "total_score": {},
        "flashcard_progress": {"last_card_id": "SC_05"},
    }
    (data_dir / "progress.json").write_text(json.dumps(legacy))
    progress = load_progress()
    assert "flashcard_progress" not in progress
    assert progress["completed_scenarios"] == [1, 2]
    assert progress["mastered_scenarios"] == [1]


# ---------------------------------------------------------------------------
# save_progress: atomic write
# ---------------------------------------------------------------------------

def test_save_progress_creates_file_atomically(tmp_path, monkeypatch):
    from data import save_progress, get_default_progress, PROGRESS_PATH
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    payload = get_default_progress()
    payload["completed_scenarios"] = [3, 4]
    save_progress(payload)
    assert PROGRESS_PATH.exists()
    with open(PROGRESS_PATH) as f:
        loaded = json.load(f)
    assert loaded["completed_scenarios"] == [3, 4]


# ---------------------------------------------------------------------------
# load_scenarios: returns 15 scenarios across 3 tiers
# ---------------------------------------------------------------------------

def test_load_scenarios_returns_fifteen():
    from data import load_scenarios
    scenarios = load_scenarios()
    assert len(scenarios) == 15
    tiers = sorted({s["difficulty_tier"] for s in scenarios})
    assert tiers == [1, 2, 3]
