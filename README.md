# CMO Desk — STP Learning Suite

> ⚠️ **Cloud deployment note:** When deployed on Streamlit Community Cloud, user progress is stored in a local file and in browser localStorage (via `streamlit-js-eval`). Progress persists within a browser session across page refreshes, but **will be lost if the app restarts** (Cloud idles apps after inactivity and periodically restarts). This is acceptable for a learning tool; if you need persistent progress across Cloud restarts, you would need a backend database.

An MBA-level interactive learning app that teaches **Segmentation, Targeting, and Positioning (STP)** within the context of a full marketing **situation analysis** using the 5C framework. Conduct structured market analysis across 15 pre-authored business scenarios before making strategic STP decisions.

**Stack:** Python / Streamlit | **Data:** Static JSON (no LLM) | **State:** `st.session_state` + `localStorage` for mid-scenario resume

---

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

---

## Try It Live

The app is deployed on Streamlit Community Cloud:

**[Open the CMO Learning Desk](https://karamelbytes-cmo-learning-desk.streamlit.app)**

---

## How It Works

### Learning Flow

```
Scenario Selection → Situation Analysis (5C) → Strategy (STP) → Concept Check → Results
```

1. **Situation Analysis** — Interactive 5C dashboard (Company, Competitors, Customers, Collaborators, Climate) with graded analysis questions. Examine market data before making any STP decisions.
2. **Strategy** — Make segmentation, targeting, and positioning decisions informed by the analysis. Relevant 5C context is embedded above each question.
3. **Concept Check** — Theory question reinforcing the *why* behind the decisions.
4. **Results** — Score breakdown (analysis + STP + concept), expandable rubrics with rationale, and an analytical decision trace.

### Scoring

| Phase | Questions | Points |
|---|---|---|
| Situation Analysis (5C) | 5 | 20 |
| Segmentation | 1 | 20 |
| Targeting | 1 | 20 |
| Positioning | 1 | 20 |
| Concept Check | 1 | 20 |
| **Total** | **9** | **100** |

Mastery threshold: ≥75 points. Mastering all scenarios in a tier unlocks the next.

---

## Architecture

```
CMO-desk-app/
├── app.py                  # Entry point: page config, init_state, main dispatch
├── data.py                 # Constants, JSON load/save, progress management
├── ui_components.py        # Shared: CSS theme, back button, step pipeline
├── ui_sidebar.py           # Sidebar: progress dashboard, how-to-use, reset
├── ui_scenario.py          # Scenario mode: all phases and scoring logic
├── utils/
│   ├── __init__.py
│   └── persistence.py      # localStorage helpers for mid-scenario resume
├── data/
│   ├── scenarios_tier1.json  # Tier 1 (Beginner): scenarios 1-5
│   ├── scenarios_tier2.json  # Tier 2 (Intermediate): scenarios 6-10
│   └── scenarios_tier3.json  # Tier 3 (Advanced): scenarios 11-15
├── tests/
│   ├── test_scenario_validity.py  # JSON schema validation
│   ├── test_data.py                # Loader + migration tests
│   └── test_scoring.py             # Mastery + tier unlock tests
├── .streamlit/config.toml  # Streamlit theme / server config
├── .github/workflows/      # CI: pytest on push/PR
├── requirements.txt
├── requirements-dev.txt    # Includes pytest
├── runtime.txt             # Python 3.11 for Cloud
└── LICENSE                 # MIT
```

---

## Scenario Catalog

| Tier | IDs | Difficulty |
|---|---|---|
| 🟢 Tier 1 | 1-5 | Beginner — Core STP concepts |
| 🟡 Tier 2 | 6-10 | Intermediate — Multi-stage, channel, and behavioral segmentation |
| 🔴 Tier 3 | 11-15 | Advanced — Ethical, platform, and cannibalization scenarios |

Each scenario contains: company background, trigger event, full 5C situation analysis, 5 graded analysis questions, 3 STP questions, and 1 concept check.

---

## Key Design Decisions

- **Situation analysis before STP** — Students analyze the market environment (5C) before making segmentation, targeting, and positioning decisions. Mirrors the real marketing planning process.
- **Context-embedded strategy tabs** — Each STP tab opens with the relevant 5C analysis above the question.
- **Formative feedback during practice** — Analysis answers reveal correctness inline with model answer expanders on incorrect answers.
- **No LLM** — All scenarios, analysis data, and rubrics are pre-authored JSON.
- **Progressive unlocking** — Tier N+1 unlocks when all Tier N scenarios are mastered (≥75 pts).
- **Mastery on replay** — Replays can upgrade a scenario to mastered without inflating score history.
- **Mid-scenario resume** — User answers mirrored to `localStorage` for refresh safety within a browser session.
- **Atomic progress writes** — `progress.json` uses temp-file-and-rename to prevent corruption.

## Requirements

- Python 3.8+
- Streamlit ≥ 1.28

See `requirements.txt`.

## License

MIT — see `LICENSE`.
