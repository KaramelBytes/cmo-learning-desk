"""Client-side persistence helpers for mid-scenario resume.

The app's primary state lives in st.session_state, which is in-memory and lost
on browser refresh. We mirror user_answers to browser localStorage so a learner
can refresh mid-scenario without losing their work.

This module uses `streamlit-js-eval` to read/write localStorage from Python.
`streamlit_js_eval.st_javascript` runs JS in the parent frame and returns the
result. We use a small stateful approach: the first read on init uses
`getItem`; subsequent writes use `setItem` and return None (no result needed).
"""
import json
from streamlit_js_eval import get_local_storage, set_local_storage, remove_local_storage

STORAGE_KEY = "cmo_desk_resume"


def load_resume_payload():
    """Read the resume payload from localStorage. Returns the dict or None."""
    try:
        raw = get_local_storage(STORAGE_KEY, key="cmo_desk_resume_read")
    except Exception:
        return None
    if not raw or not isinstance(raw, str):
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if "scenario_id" not in data or "answers" not in data:
        return None
    return data


def save_resume_payload(answers, scenario_id):
    """Write the resume payload to localStorage. Best-effort; silently no-ops on error."""
    if scenario_id is None:
        return
    payload = json.dumps({"scenario_id": scenario_id, "answers": answers or {}})
    try:
        set_local_storage(STORAGE_KEY, payload, key=f"cmo_desk_resume_write_{scenario_id}")
    except Exception:
        pass


def clear_resume_payload():
    """Remove the localStorage entry. Call when a scenario is fully completed
    or the user returns to scenario selection."""
    try:
        remove_local_storage(STORAGE_KEY, key=f"cmo_desk_resume_clear")
    except Exception:
        pass
