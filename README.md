# CMO Desk

A free, open-source Streamlit learning app for evidence-based marketing decisions. Fifteen authored business cases teach Segmentation, Targeting, and Positioning (STP) through the 5C framework: Company, Competitors, Customers, Collaborators, and Climate.

[Open the app](https://karamelbytes-cmo-learning-desk.streamlit.app)

## Run locally

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py
```

Streamlit is pinned to the version used for validation. Community Cloud should use Python 3.11 or 3.12 and `app.py` as the entry point. No database, credentials, accounts, or external API services are required.

## Learning experience

Each case follows a guided sequence:

1. **Brief:** read the business situation, trigger, assignment, and learning objective.
2. **Investigate:** examine one 5C lens at a time, interpret evidence, and save optional notes about strategic implications.
3. **Decide:** choose segmentation, targeting, and positioning with your notebook at hand.
4. **Explain:** answer a concept question, defend your recommendation, and consider a changed condition.
5. **Debrief:** review feedback and download a personal strategy brief.

Questions start unanswered. Checking an answer is explicit. Incorrect answers can be revised; hints and model reasoning are available without blocking progression. Learner-written reflections are self-reviewed, not automatically graded. The coffee shop exemplar includes additional worked-example and option-specific feedback. All cases include objectives and authored changed-condition discussions.

All tiers are open. Beginners receive an optional worked example; more advanced cases emphasize trade-offs with less scaffolding. Home recommends the next unfinished case. Cases can be searched by title or topic and filtered by difficulty.

The notebook retains completed briefs. Progress displays first/latest/best attempts rather than hiding replay improvement. Review prioritizes missed questions and revisits other questions after two days. Review is recall practice using existing questions, not an independent transfer assessment.

### Scoring

Five analysis questions are worth 4 points each; three STP decisions and one concept question are worth 20 points each. The practice target is 75/100. Hints, model answers, and revised checked answers are recorded as support. An independently reached practice target is shown separately. Scores measure performance on a case, not lasting mastery. Submitting an attempt is idempotent across reruns.

## Privacy and storage

The app is designed for Streamlit Community Cloud:

- No account, learner database, application-added analytics, or intentional server-file storage of answers and notes.
- Active state lives in the learner's Streamlit session.
- **Remember my progress on this device** is optional and off for new visitors. It saves progress and the active draft in that browser's localStorage.
- A returning browser with saved learning restores its history and offers the active case on Home.
- Settings provides explicit backup download/import and deletion. Import replaces current learning after confirmation and validates its schema, size, answers, and dates. Scores are recalculated from imported answers.
- Browser saving is best effort. Browser settings, private mode, storage limits, or clearing site data can remove progress. Download backups for important work.
- Turning remembering off removes the app's saved browser data while retaining the active session. Clearing learning data also clears the session. Downloaded files must be deleted separately.

Streamlit processes entered answers and notes on its server. This is not a browser-only application. Community Cloud's hosting practices and platform analytics are separate from the app: [Streamlit privacy notice](https://streamlit.io/privacy-policy), [platform analytics](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-analytics). Library usage telemetry is disabled in `.streamlit/config.toml`; this does not disable Community Cloud platform analytics.

The browser storage component is bundled locally with no external scripts or network dependencies. It uses Streamlit's component message protocol and reports storage failures. Keep one active tab per browser to avoid competing draft writes. No cross-device synchronization is provided; use backup export/import.

### Upgrading from the earlier app

The app deliberately does not import the old server-side `data/progress.json`: that file was shared across visitors and cannot be reliably attributed to an individual. The previous browser resume format is also not automatically imported. New backups use schema version 2. Clearing learning data removes the old browser resume key as well.

## Architecture

| File | Responsibility |
|---|---|
| `app.py` | Session bootstrap, browser persistence lifecycle, native navigation |
| `data.py` | Read-only cached scenario catalog |
| `learning.py` | Pure scoring, attempt history, summaries, review timing, Markdown export |
| `ui_scenario.py` | Home, case catalog, guided workspace and debrief |
| `ui_learning.py` | Notebook, practice review, progress, settings |
| `ui_components.py` | Small theme, concept guide, navigation helper |
| `ui_sidebar.py` | Contextual active-case progress |
| `utils/persistence.py` | Browser component declaration and bounded backup validation |
| `components/browser_store/index.html` | Local browser-storage bridge without third-party JavaScript |
| `data/scenarios_tier*.json` | Original business cases and questions |
| `data/learning_guides.json` | Versioned learning objectives, transfer discussions, exemplar feedback |

Canonical answers live in the draft, separate from widget keys. Widget keys include a unique attempt ID so replays start fresh. Callbacks update the draft before rendering and saving. Only static scenario content is cached. Attempts record content version, timestamps, reasoning, evidence notes, and support use.

## Validation

```bash
python -m pytest tests -q
```

Tests cover content validity, scoring, replay history, support tracking, import validation, unanswered defaults, explicit checks, and notes across step navigation. Browser checks additionally exercise opt-in localStorage, refresh/resume, independent visitors, backup import/export, deletion, and narrow-screen layout. The browser smoke script is `tests/browser_smoke.py`; install Playwright and Chromium separately to run it against a local server:

```bash
pip install playwright
python -m playwright install chromium
python tests/browser_smoke.py
```

Usability testing with representative learners remains valuable for evaluating explanation quality, navigation clarity, and delayed application. The app does not collect production learning analytics.

## License

MIT. See [LICENSE](LICENSE).
