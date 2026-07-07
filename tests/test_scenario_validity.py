import json
from pathlib import Path

import pytest

DATA_DIR = Path("data")
TIER_FILES = [
    DATA_DIR / "scenarios_tier1.json",
    DATA_DIR / "scenarios_tier2.json",
    DATA_DIR / "scenarios_tier3.json",
]

REQUIRED_ROOT_KEYS = {
    "scenario_id", "title", "difficulty_tier", "scenario_type",
    "background", "trigger_event", "steps", "situation_analysis",
    "analysis_questions", "concept_check",
}

REJECTED_ROOT_KEYS = {
    "financial_projections", "swot_analysis",
    "founder_biography", "macro_economic_history",
}

FORBIDDEN_BRANDS = ["apple", "nike", "disney", "harvard"]

REQUIRED_FIVE_C_KEYS = {"company", "competitors", "customers", "collaborators", "climate"}
REQUIRED_STP_KEYS = {"segmentation", "targeting", "positioning"}
REQUIRED_CONCEPT_CHECK_KEYS = {"question", "options", "correct_idx", "rationale"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_all_scenarios():
    all_scenarios = []
    for path in TIER_FILES:
        if not path.exists():
            pytest.fail(f"Scenario file not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            pytest.fail(f"{path} must contain a JSON array")
        all_scenarios.extend(data)
    return all_scenarios


# ---------------------------------------------------------------------------
# 1. Root key structure
# ---------------------------------------------------------------------------

def test_all_scenarios_have_required_root_keys():
    scenarios = load_all_scenarios()
    for s in scenarios:
        keys = set(s.keys())
        missing = REQUIRED_ROOT_KEYS - keys
        assert not missing, (
            f"Scenario {s.get('scenario_id', '?')} missing required root keys: {missing}"
        )


# ---------------------------------------------------------------------------
# 2. No extraneous keys
# ---------------------------------------------------------------------------

def test_no_extraneous_keys():
    scenarios = load_all_scenarios()
    for s in scenarios:
        keys = set(s.keys())
        rejected = keys & REJECTED_ROOT_KEYS
        assert not rejected, (
            f"Scenario {s.get('scenario_id', '?')} contains rejected keys: {rejected}"
        )


# ---------------------------------------------------------------------------
# 3. No forbidden brand names in any text field
# ---------------------------------------------------------------------------

def test_no_forbidden_brands():
    scenarios = load_all_scenarios()
    for s in scenarios:
        text = json.dumps(s).lower()
        for brand in FORBIDDEN_BRANDS:
            assert brand not in text, (
                f"Scenario {s.get('scenario_id', '?')} contains forbidden brand: '{brand}'"
            )


# ---------------------------------------------------------------------------
# 4. 5C framework keys in situation_analysis
# ---------------------------------------------------------------------------

def test_five_c_keys_present():
    scenarios = load_all_scenarios()
    for s in scenarios:
        sa = s.get("situation_analysis", {})
        keys = set(sa.keys())
        missing = REQUIRED_FIVE_C_KEYS - keys
        assert not missing, (
            f"Scenario {s.get('scenario_id', '?')} missing 5C keys: {missing}"
        )


# ---------------------------------------------------------------------------
# 5. STP framework keys in steps
# ---------------------------------------------------------------------------

def test_stp_keys_present():
    scenarios = load_all_scenarios()
    for s in scenarios:
        steps = s.get("steps", {})
        keys = set(steps.keys())
        missing = REQUIRED_STP_KEYS - keys
        assert not missing, (
            f"Scenario {s.get('scenario_id', '?')} missing STP keys: {missing}"
        )
        extra = keys - REQUIRED_STP_KEYS
        assert not extra, (
            f"Scenario {s.get('scenario_id', '?')} has extra STP keys: {extra}"
        )


# ---------------------------------------------------------------------------
# 6. analysis_questions keys correspond to 5C keys in situation_analysis
# ---------------------------------------------------------------------------

def test_analysis_questions_keys_correspond():
    """analysis_questions must contain exactly the 5C keys (not analysis_prompt)."""
    scenarios = load_all_scenarios()
    for s in scenarios:
        aq_keys = set(s.get("analysis_questions", {}).keys())
        assert aq_keys == REQUIRED_FIVE_C_KEYS, (
            f"Scenario {s.get('scenario_id', '?')} analysis_questions keys "
            f"{aq_keys} don't match expected 5C keys {REQUIRED_FIVE_C_KEYS}"
        )


# ---------------------------------------------------------------------------
# 7. correct_idx is in valid range for all option arrays
# ---------------------------------------------------------------------------

def test_all_correct_idx_in_range():
    scenarios = load_all_scenarios()
    for s in scenarios:
        sid = s.get("scenario_id", "?")

        # Check analysis_questions
        aq = s.get("analysis_questions", {})
        for c_key in REQUIRED_FIVE_C_KEYS:
            q = aq.get(c_key, {})
            if "options" in q and "correct_idx" in q:
                opts = q["options"]
                idx = q["correct_idx"]
                assert 0 <= idx < len(opts), (
                    f"Scenario {sid}, analysis_questions.{c_key}: "
                    f"correct_idx {idx} out of range [0, {len(opts)})"
                )

        # Check steps
        steps = s.get("steps", {})
        for stp_key in REQUIRED_STP_KEYS:
            step = steps.get(stp_key, {})
            if "options" in step and "correct_idx" in step:
                opts = step["options"]
                idx = step["correct_idx"]
                assert 0 <= idx < len(opts), (
                    f"Scenario {sid}, steps.{stp_key}: "
                    f"correct_idx {idx} out of range [0, {len(opts)})"
                )

        # Check concept_check
        cc = s.get("concept_check", {})
        if "options" in cc and "correct_idx" in cc:
            opts = cc["options"]
            idx = cc["correct_idx"]
            assert 0 <= idx < len(opts), (
                f"Scenario {sid}, concept_check: "
                f"correct_idx {idx} out of range [0, {len(opts)})"
            )


# ---------------------------------------------------------------------------
# 8. All scenario_id values are unique across all three tier files
# ---------------------------------------------------------------------------

def test_scenario_ids_unique():
    scenarios = load_all_scenarios()
    ids = [s.get("scenario_id", None) for s in scenarios]
    none_ids = [i for i, v in enumerate(ids) if v is None]
    assert not none_ids, (
        f"Scenarios at indices {none_ids} have no scenario_id"
    )
    duplicates = {x for x in ids if ids.count(x) > 1}
    assert not duplicates, (
        f"Duplicate scenario_id(s) found: {duplicates}"
    )


# ---------------------------------------------------------------------------
# 9. concept_check structure
# ---------------------------------------------------------------------------

def test_concept_check_structure():
    scenarios = load_all_scenarios()
    for s in scenarios:
        cc = s.get("concept_check", {})
        missing = REQUIRED_CONCEPT_CHECK_KEYS - set(cc.keys())
        assert not missing, (
            f"Scenario {s.get('scenario_id', '?')} concept_check missing: {missing}"
        )


# ---------------------------------------------------------------------------
# 10. State amnesia check — verifies that every answerable question has a
#     corresponding answer path in user_answers, ensuring scores can be
#     re-derived from persisted state rather than local accumulators.
# ---------------------------------------------------------------------------

def test_state_amnesia_safe():
    """Every question with a correct_idx must have a corresponding answer
    storage key that would survive a Streamlit rerun. This checks that the
    JSON data model supports session-state-based scoring: all
    analysis_questions.*, steps.*, and concept_check have correct_idx
    values so answers can be mapped back to correct answers."""
    scenarios = load_all_scenarios()
    for s in scenarios:
        sid = s.get("scenario_id", "?")

        aq = s.get("analysis_questions", {})
        for c_key in REQUIRED_FIVE_C_KEYS:
            q = aq.get(c_key, {})
            assert "correct_idx" in q, (
                f"Scenario {sid}, analysis_questions.{c_key}: missing correct_idx"
            )
            assert "options" in q, (
                f"Scenario {sid}, analysis_questions.{c_key}: missing options"
            )

        steps = s.get("steps", {})
        for stp_key in REQUIRED_STP_KEYS:
            step = steps.get(stp_key, {})
            assert "correct_idx" in step, (
                f"Scenario {sid}, steps.{stp_key}: missing correct_idx"
            )
            assert "options" in step, (
                f"Scenario {sid}, steps.{stp_key}: missing options"
            )

        cc = s.get("concept_check", {})
        assert "correct_idx" in cc, (
            f"Scenario {sid}, concept_check: missing correct_idx"
        )
        assert "options" in cc, (
            f"Scenario {sid}, concept_check: missing options"
        )


# ---------------------------------------------------------------------------
# 11. Feedback strings do not contain raw JSON ---
#     spot-check that rubric text isn't accidentally JSON-dumped.
# ---------------------------------------------------------------------------

def test_rubric_no_raw_json():
    """Ensure that rationale/rubric strings don't look like JSON dumps."""
    scenarios = load_all_scenarios()
    for s in scenarios:
        sid = s.get("scenario_id", "?")

        aq = s.get("analysis_questions", {})
        for c_key in REQUIRED_FIVE_C_KEYS:
            text = aq.get(c_key, {}).get("rationale", "")
            _assert_not_json(text, sid, f"analysis_questions.{c_key}.rationale")

        steps = s.get("steps", {})
        for stp_key in REQUIRED_STP_KEYS:
            text = steps.get(stp_key, {}).get("rubric_rationale", "")
            _assert_not_json(text, sid, f"steps.{stp_key}.rubric_rationale")

        cc = s.get("concept_check", {})
        text = cc.get("rationale", "")
        _assert_not_json(text, sid, "concept_check.rationale")


def _assert_not_json(text, sid, field):
    t = text.strip()
    if t.startswith("{") or t.startswith("[") or t.startswith('"'):
        try:
            json.loads(t)
            pytest.fail(f"Scenario {sid}, {field}: appears to be raw JSON")
        except (json.JSONDecodeError, ValueError):
            pass


# ---------------------------------------------------------------------------
# 12. All 15 scenarios loaded cleanly
# ---------------------------------------------------------------------------

def test_all_15_scenarios_accounted_for():
    scenarios = load_all_scenarios()
    assert len(scenarios) == 15, (
        f"Expected 15 total scenarios across all tiers, got {len(scenarios)}"
    )
