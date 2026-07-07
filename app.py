import streamlit as st
from data import load_scenarios, load_progress
from ui_components import CUSTOM_CSS
from ui_sidebar import render_sidebar
from ui_scenario import render_scenario_mode
from utils.persistence import load_resume_payload, clear_resume_payload

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="CMO Desk",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# STATE INITIALIZATION
# =============================================================================


def init_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_page = "scenario_mode"
        st.session_state.current_scenario = None
        st.session_state.phase = "selection"
        st.session_state.user_answers = {}
        st.session_state.progress = load_progress()
        st.session_state.scenarios = load_scenarios()
        st.session_state.resume_offer_shown = False

        # Try to restore a previously in-progress scenario from localStorage
        payload = load_resume_payload()
        if payload:
            sid = payload.get("scenario_id")
            answers = payload.get("answers") or {}
            scenarios = st.session_state.scenarios
            scenario = next((s for s in scenarios if s.get("scenario_id") == sid), None)
            if scenario and answers:
                st.session_state.pending_resume = {"scenario": scenario, "answers": answers}
                st.session_state.resume_offer_shown = True

# =============================================================================
# MAIN
# =============================================================================


def main():
    init_state()

    # If we have a pending resume from localStorage, ask the user before applying it
    if st.session_state.get("pending_resume") and st.session_state.get("phase") == "selection":
        offer_resume()

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    render_sidebar()
    render_scenario_mode()

    # Footer
    st.markdown("<div style='margin:3rem 0 0.5rem 0;'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.75rem;color:#7F8C8D;text-align:center;border-top:1px solid #E0DCD3;padding-top:1rem;">'
        'Built by an MBA student · '
        '<a href="https://github.com/KaramelBytes/CMO-learning-desk" style="color:#7F8C8D;text-decoration:underline;" target="_blank">View source on GitHub</a> · '
        'MIT Licensed'
        '</div>',
        unsafe_allow_html=True,
    )


def offer_resume():
    payload = st.session_state.get("pending_resume")
    if not payload:
        return
    scenario = payload.get("scenario")
    answers = payload.get("answers") or {}
    n_answered = sum(1 for v in answers.values() if v is not None)
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:1rem;font-weight:700;color:#1B2A4A;margin-bottom:0.4rem;">'
            f'↩️ Resume previous scenario?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.9rem;color:#2C3E50;line-height:1.5;">'
            f'You have <strong>{n_answered}</strong> in-progress answer'
            f'{"s" if n_answered != 1 else ""} for <em>{scenario["title"]}</em> '
            f'(Tier {scenario["difficulty_tier"]}). Continue from where you left off?</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Resume", type="primary", use_container_width=True, key="resume_yes"):
                st.session_state.current_scenario = scenario
                st.session_state.user_answers = answers
                # Jump to the most advanced answered phase
                if any(answers.get(k) is not None for k in ["segmentation", "targeting", "positioning"]):
                    st.session_state.phase = "strategy"
                else:
                    st.session_state.phase = "situation_analysis"
                st.session_state.pending_resume = None
                clear_resume_payload()
                st.rerun()
        with col_b:
            if st.button("Discard", use_container_width=True, key="resume_no"):
                st.session_state.pending_resume = None
                clear_resume_payload()
                st.rerun()
    st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
