import html
import streamlit as st
from utils.persistence import clear_resume_payload

# =============================================================================
# HELPERS
# =============================================================================

def h(text):
    """Escape text for safe insertion into HTML blocks."""
    return html.escape(str(text))


# =============================================================================
# CUSTOM CSS — Full Theme
# =============================================================================

CUSTOM_CSS = """
<style>
    /* ===== Base ===== */
    .stApp {
        background-color: #F5F3EE;
    }

    * {
        -webkit-font-smoothing: antialiased;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #1B2A4A;
        font-family: 'Georgia', serif;
    }

    p, li, .stMarkdown {
        color: #2C3E50;
    }

    .main-title {
        color: #1B2A4A !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .section-title {
        color: #1B2A4A !important;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #D4A843;
        padding-bottom: 0.4rem;
    }
    .subtitle {
        color: #5A6C7D !important;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background-color: #1B2A4A !important;
        color: #EAE0D0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: inherit;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #EAE0D0;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6 {
        color: #D4A843 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(212, 168, 67, 0.3);
        margin: 1rem 0;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] div:not([data-testid]),
    section[data-testid="stSidebar"] .st-cb {
        color: #EAE0D0 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #EAE0D0 !important;
    }
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        background-color: transparent;
    }
    section[data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        color: #EAE0D0 !important;
    }
    section[data-testid="stSidebar"] .stProgress > div > div {
        background-color: #D4A843;
    }
    section[data-testid="stSidebar"] .stProgress {
        margin-bottom: 1.2rem;
    }
    section[data-testid="stSidebar"] .stProgress label,
    section[data-testid="stSidebar"] .stProgress p,
    section[data-testid="stSidebar"] .stProgress span {
        color: #EAE0D0 !important;
    }
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] caption,
    section[data-testid="stSidebar"] .caption {
        color: #C8C0B0 !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background-color: #D4A843;
        color: #1B2A4A;
        border: none;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #E8C96A;
    }

    /* ===== Sidebar Title ===== */
    .sidebar-title {
        font-size: 1.8rem !important;
        font-weight: 700;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    .sidebar-subtitle {
        font-size: 0.9rem;
        color: #C8C0B0 !important;
        margin-top: -0.3rem;
        margin-bottom: 0.5rem;
    }
    .sidebar-section {
        font-size: 0.95rem;
        font-weight: 600;
        color: #D4A843 !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .tier-status {
        padding: 0.3rem 0;
        font-size: 0.9rem;
        color: #EAE0D0;
    }
    .mastery-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        padding: 0.15rem 0;
        color: #EAE0D0;
    }
    .mastery-label {
        color: #C8C0B0;
    }

    /* ===== Tier Headers ===== */
    .tier-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .tier-icon {
        font-size: 1.3rem;
    }
    .tier-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1B2A4A;
    }
    .tier-divider {
        border: none;
        border-top: 1px solid #E0DCD3;
        margin: 1.2rem 0;
    }

    /* ===== Scenario Cards ===== */
    .scenario-card {
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        text-align: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        position: relative;
    }
    .scenario-card.unlocked {
        background: #FFFFFF;
        border: 1px solid #E0DCD3;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .scenario-card.unlocked:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(27, 42, 74, 0.12);
        border-color: #D4A843;
    }
    .scenario-card.completed {
        background: #F0F9F0;
        border: 1px solid #A3D9A5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .scenario-card.locked {
        background: #F0F0ED;
        border: 1px solid #D5D0C5;
        box-shadow: none;
        opacity: 0.7;
    }
    .card-icon {
        font-size: 2rem;
        margin-bottom: 0.4rem;
    }
    .card-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: #1B2A4A;
        margin-bottom: 0.3rem;
    }
    .card-type {
        font-size: 0.78rem;
        color: #5A6C7D;
        font-style: italic;
    }
    .card-locked-text {
        font-size: 0.75rem;
        color: #7F8C8D;
        margin-top: 0.4rem;
    }

    /* ===== Phase-specific container styling via markers ===== */
    /* Strategy step containers */
    #strategy-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF;
        border: 1px solid #E0DCD3;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
    }
    #strategy-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] .stRadio label {
        font-size: 0.95rem;
    }
    #strategy-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] .stRadio div[data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem;
        color: #1B2A4A !important;
    }
    #strategy-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] .stRadio div[role="radiogroup"] label {
        color: #2C3E50 !important;
    }

    /* Concept check container */
    #concept-check-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFBF0;
        border: 2px solid #D4A843;
        border-radius: 10px;
        padding: 1.8rem 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 20px rgba(212, 168, 67, 0.15);
    }
    #concept-check-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] .stRadio label {
        font-size: 0.95rem;
    }
    #concept-check-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] .stRadio div[data-testid="stMarkdownContainer"] p {
        color: #1B2A4A !important;
    }
    #concept-check-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] .stRadio div[role="radiogroup"] label {
        color: #2C3E50 !important;
    }

    /* ===== Situation Analysis phase ===== */
    #situation-analysis-phase-marker ~ [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF;
        border: 1px solid #E0DCD3;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
    }
    .analysis-intro {
        background: #F8F7F4;
        border-left: 4px solid #1B2A4A;
        border-radius: 6px;
        padding: 1rem 1.5rem;
        margin: 1rem 0 1.5rem 0;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #2C3E50;
    }
    .analysis-5c-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1B2A4A;
        margin-bottom: 0.8rem;
    }
    .analysis-summary {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #2C3E50;
        margin-bottom: 0.8rem;
    }
    .analysis-q-label {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #D4A843;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .analysis-progress {
        text-align: center;
        font-size: 0.9rem;
        color: #5A6C7D;
        margin: 1rem 0;
        padding: 0.5rem;
        background: #F8F7F4;
        border-radius: 6px;
    }
    .analysis-model-answer {
        background: #FBF6E8;
        border-left: 4px solid #D4A843;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin-top: 0.5rem;
    }
    .analysis-model-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        color: #D4A843;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .analysis-model-option {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1B2A4A;
        margin-bottom: 0.4rem;
        line-height: 1.4;
    }
    .analysis-model-rationale {
        font-size: 0.88rem;
        color: #2C3E50;
        line-height: 1.55;
    }
    .analysis-prompt-callout {
        background: linear-gradient(180deg, #FFFBF0 0%, #FDF7E2 100%);
        border: 1px solid #D4A843;
        border-left: 5px solid #D4A843;
        border-radius: 8px;
        padding: 1rem 1.4rem;
        margin: 0.8rem 0 1.5rem 0;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #2C3E50;
        box-shadow: 0 2px 8px rgba(212, 168, 67, 0.10);
    }
    .analysis-prompt-callout strong {
        color: #1B2A4A;
    }

    /* ===== Step Pipeline Indicator ===== */
    .step-pipeline {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin: 0.5rem 0 1.5rem 0;
        font-size: 0.82rem;
    }
    .step-pill {
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        color: #7F8C8D;
        background: #F0EDE5;
    }
    .step-pill.active {
        color: #FFFFFF;
        background: #1B2A4A;
    }
    .step-pill.done {
        color: #1B2A4A;
        background: #E8E4D8;
    }
    .step-arrow {
        margin: 0 0.3rem;
        color: #C8C0B0;
        font-weight: 400;
    }

    /* ===== Memo internal styling ===== */
    .memo-header {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #D4A843 !important;
        margin-bottom: 1rem;
    }
    .memo-body h3 {
        font-size: 1rem;
        color: #1B2A4A !important;
        margin-top: 1rem;
        margin-bottom: 0.3rem;
    }
    .memo-body p {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #2C3E50;
    }

    /* ===== Score Banner ===== */
    .score-banner {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1.2rem 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        color: #2C3E50;
    }
    .score-banner * {
        color: #2C3E50;
    }
    .score-banner h2 {
        margin: 0 0 0.3rem 0;
        font-size: 1.8rem;
        color: #1B2A4A !important;
    }
    .score-banner p {
        margin: 0;
        color: #2C3E50 !important;
        font-size: 0.95rem;
    }

    /* ===== Scenario Meta ===== */
    .scenario-meta {
        color: #5A6C7D;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    /* ===== Buttons ===== */
    .stButton button[kind="primary"] {
        background-color: #1B2A4A;
        color: #FFFFFF;
        border: none;
        font-weight: 600;
        padding: 0.5rem 2rem;
        border-radius: 6px;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #2C3E6B;
    }
    .stButton button[kind="secondary"] {
        background-color: #FFFFFF;
        color: #1B2A4A;
        border: 1px solid #1B2A4A;
    }
    .stButton button[kind="secondary"]:hover {
        background-color: #F0EDE5;
    }
    .stButton button[kind="primary"] * {
        color: #FFFFFF !important;
    }
    .stButton button[kind="secondary"] * {
        color: #1B2A4A !important;
    }

    /* ===== Expanders ===== */
    .st-expander {
        border: 1px solid #E0DCD3;
        border-radius: 8px;
        background: #FFFFFF;
        margin-bottom: 0.75rem;
    }
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.95rem;
        background-color: #FFFFFF;
        border-radius: 6px;
        color: #1B2A4A !important;
    }
    .streamlit-expanderContent {
        background-color: #FFFFFF;
        border-radius: 0 0 6px 6px;
        border-top: 1px solid #E0DCD3;
        padding: 1rem 1.5rem;
        color: #2C3E50;
    }
    .streamlit-expanderContent p,
    .streamlit-expanderContent li,
    .streamlit-expanderContent span,
    .streamlit-expanderContent strong,
    .streamlit-expanderContent div {
        color: #2C3E50 !important;
    }
</style>
"""


# =============================================================================
# SHARED UI COMPONENTS
# =============================================================================

def render_back_button(target_phase=None, label=None):
    """Render a secondary back button.

    Args:
        target_phase: Phase to navigate to. If None, goes to scenario selection.
        label: Button label. If None, uses default based on target_phase.
    """
    if label is None:
        if target_phase == "situation_analysis":
            label = "← Back to Analysis"
        elif target_phase == "strategy":
            label = "← Back to Strategy"
        else:
            label = "← Back to Scenarios"

    if st.button(label, type="secondary"):
        if target_phase:
            st.session_state.phase = target_phase
        else:
            st.session_state.phase = "selection"
            st.session_state.current_scenario = None
            clear_resume_payload()
        st.rerun()


def render_step_pipeline(current_step):
    """Render a visual step pipeline indicator.
    current_step: 0=Situation Analysis, 1=Strategy, 2=Concept Check, 3=Results
    """
    steps_labels = ["Situation Analysis", "Strategy", "Concept Check", "Results"]
    st.markdown(
        '<div class="step-pipeline">'
        + "".join(
            f'<span class="step-pill{" active" if i == current_step else " done" if i < current_step else ""}">'
            f'{label}</span>'
            f'{"<span class=step-arrow>→</span>" if i < len(steps_labels) - 1 else ""}'
            for i, label in enumerate(steps_labels)
        )
        + '</div>',
        unsafe_allow_html=True,
    )
