"""Data loading and progress management for CMO Desk."""
import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

# =============================================================================
# CONSTANTS
# =============================================================================

DATA_DIR = Path("data")
SCENARIOS_PATHS: List[Path] = [
    DATA_DIR / "scenarios_tier1.json",
    DATA_DIR / "scenarios_tier2.json",
    DATA_DIR / "scenarios_tier3.json",
]
PROGRESS_PATH: Path = DATA_DIR / "progress.json"

TIER_NAMES: Dict[int, str] = {1: "Beginner", 2: "Intermediate", 3: "Advanced"}
TIER_ICONS: Dict[int, str] = {1: "🟢", 2: "🟡", 3: "🔴"}

SCENARIO_EMOJIS: Dict[int, str] = {
    1: "☕", 2: "🏋️", 3: "🎓", 4: "🐾", 5: "🚗",
    6: "🚚", 7: "🏨", 8: "☕", 9: "🛴", 10: "📱",
    11: "🏥", 12: "⚡", 13: "💰", 14: "⚙️", 15: "🧹",
}

STEPS_ORDERED: List[str] = ["segmentation", "targeting", "positioning"]
ANALYSIS_STEPS_ORDERED: List[str] = ["company", "competitors", "customers", "collaborators", "climate"]
STP_POINTS: int = 20
ANALYSIS_POINTS: int = 4
CC_POINTS: int = 20
MASTER_THRESHOLD: int = 75


# =============================================================================
# DATA FUNCTIONS
# =============================================================================

def load_scenarios() -> List[Dict[str, Any]]:
    @st.cache_data
    def _load() -> List[Dict[str, Any]]:
        all_scenarios: List[Dict[str, Any]] = []
        for path in SCENARIOS_PATHS:
            if not path.exists():
                st.error(f"Scenarios file not found at {path}. Ensure data migration is complete.")
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        st.error(f"Scenarios file {path} must contain a JSON array.")
                        continue
                    all_scenarios.extend(data)
            except json.JSONDecodeError as e:
                st.error(f"Scenarios file {path} is corrupted: {e}")
            except Exception as e:
                st.error(f"Could not load scenarios from {path}: {e}")
        return all_scenarios

    return _load()


def load_progress() -> Dict[str, Any]:
    if not PROGRESS_PATH.exists():
        default = get_default_progress()
        save_progress(default)
        return default
    try:
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Progress file is not a JSON object")
            return _migrate_progress(data)
    except (json.JSONDecodeError, ValueError) as e:
        st.warning(f"Progress file corrupted ({e}). Resetting to default.")
        default = get_default_progress()
        save_progress(default)
        return default
    except Exception as e:
        st.warning(f"Could not load progress ({e}). Resetting to default.")
        default = get_default_progress()
        save_progress(default)
        return default


def _migrate_progress(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure older progress files have all required keys and no obsolete keys."""
    default = get_default_progress()
    obsolete_keys = {"flashcard_progress"}
    for key in obsolete_keys:
        data.pop(key, None)
    for key in default:
        if key not in data:
            data[key] = default[key]
    return data


def save_progress(progress: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = PROGRESS_PATH.with_suffix(".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
        temp_path.replace(PROGRESS_PATH)
    except Exception as e:
        st.error(f"Failed to save progress: {e}")


def get_default_progress() -> Dict[str, Any]:
    return {
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
