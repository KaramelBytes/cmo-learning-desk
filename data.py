"""Read-only scenario catalog. Learner data is never written to this directory."""
import json
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / 'data'
SCENARIOS_PATHS = [DATA_DIR / f'scenarios_tier{i}.json' for i in (1, 2, 3)]
TIER_NAMES = {1: 'Beginner', 2: 'Intermediate', 3: 'Advanced'}


@st.cache_data
def load_scenarios():
    scenarios = []
    metadata = json.loads((DATA_DIR / 'learning_guides.json').read_text(encoding='utf-8'))
    for path in SCENARIOS_PATHS:
        scenarios.extend(json.loads(path.read_text(encoding='utf-8')))
    for scenario in scenarios:
        scenario.update(metadata[str(scenario['scenario_id'])])
    return scenarios
