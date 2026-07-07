import streamlit as st
from data import TIER_NAMES, STEPS_ORDERED, ANALYSIS_STEPS_ORDERED, get_default_progress, save_progress
from ui_components import h


def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">📋 CMO Desk</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-subtitle">STP Learning Suite</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        render_progress_dashboard()
        render_how_to_use()
        render_reset_button()


def render_progress_dashboard():
    progress = st.session_state.progress
    scenarios = st.session_state.scenarios
    total_scenarios = len(scenarios)
    mastered_count = len(progress.get("mastered_scenarios", []))
    completion_pct = mastered_count / total_scenarios if total_scenarios > 0 else 0

    st.markdown(
        '<div class="sidebar-section">📊 Progress Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.progress(completion_pct, text=f"{mastered_count}/{total_scenarios} mastered")

    total_points = progress.get("total_points", 0)
    st.markdown(
        f'<div style="font-size:0.9rem;color:#EAE0D0;margin-bottom:0.8rem;">'
        f'⭐ <strong>Total Points:</strong> {total_points}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section">🎯 Mastery</div>',
        unsafe_allow_html=True,
    )
    score = progress.get("total_score", {})

    # Analysis mastery
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:600;color:#D4A843;margin-top:0.5rem;">Situation Analysis (5C)</div>',
        unsafe_allow_html=True,
    )
    for step in ANALYSIS_STEPS_ORDERED:
        key = f"analysis_{step}"
        data = score.get(key, {"correct": 0, "total": 0})
        if data["total"] > 0:
            pct = int(data["correct"] / data["total"] * 100)
            st.markdown(
                f'<div class="mastery-row">'
                f'  <span class="mastery-label">{step.title()}</span>'
                f'  <span>{data["correct"]}/{data["total"]} ({pct}%)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="mastery-row">'
                f'  <span class="mastery-label">{step.title()}</span>'
                f'  <span>—</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # STP mastery
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:600;color:#D4A843;margin-top:0.5rem;">STP Decisions</div>',
        unsafe_allow_html=True,
    )
    for step in STEPS_ORDERED:
        data = score.get(step, {"correct": 0, "total": 0})
        if data["total"] > 0:
            pct = int(data["correct"] / data["total"] * 100)
            st.markdown(
                f'<div class="mastery-row">'
                f'  <span class="mastery-label">{step.title()}</span>'
                f'  <span>{data["correct"]}/{data["total"]} ({pct}%)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="mastery-row">'
                f'  <span class="mastery-label">{step.title()}</span>'
                f'  <span>—</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Concept check
    cc_data = score.get("concept_check", {"correct": 0, "total": 0})
    if cc_data["total"] > 0:
        pct = int(cc_data["correct"] / cc_data["total"] * 100)
        st.markdown(
            f'<div class="mastery-row">'
            f'  <span class="mastery-label">Concept Check</span>'
            f'  <span>{cc_data["correct"]}/{cc_data["total"]} ({pct}%)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(
        '<div class="sidebar-section">🏆 Tiers</div>',
        unsafe_allow_html=True,
    )

    unlocked = progress.get("unlocked_tiers", [1])
    mastered = progress.get("mastered_scenarios", [])

    for tier_num in [1, 2, 3]:
        tier_scenarios = [s for s in scenarios if s["difficulty_tier"] == tier_num]
        if not tier_scenarios:
            continue
        tier_all_mastered = all(s["scenario_id"] in mastered for s in tier_scenarios)

        if tier_num in unlocked:
            icon = "✅" if tier_all_mastered else "🔓"
        else:
            icon = "🔒"

        tier_count = sum(1 for s in tier_scenarios if s["scenario_id"] in mastered)
        tier_total = len(tier_scenarios)

        st.markdown(
            f'<div class="tier-status">'
            f'{icon} <strong>Tier {tier_num}:</strong> {TIER_NAMES[tier_num]}'
            f' ({tier_count}/{tier_total})'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("Master all scenarios (≥75 pts) in a tier to unlock the next.")


def render_how_to_use():
    with st.expander("❓ How to use"):
        st.markdown(
            "<div style='font-size:0.85rem;line-height:1.5;color:#EAE0D0;'>"
            "<strong>1. Situation Analysis</strong> — Examine the 5C environment "
            "(Company, Competitors, Customers, Collaborators, Climate). "
            "Answer the analysis questions; the model answer is shown if you're wrong.<br><br>"
            "<strong>2. Strategy</strong> — Make Segmentation, Targeting, and Positioning "
            "decisions. The relevant 5C context is embedded above each question.<br><br>"
            "<strong>3. Concept Check</strong> — Connect theory to practice.<br><br>"
            "<strong>4. Results</strong> — Review your analytical decision trace.<br><br>"
            "<strong>Scoring:</strong> 9 questions, 100 pts total. Mastery ≥ 75 pts. "
            "Replay a failed scenario to master it; your score history is not inflated."
            "</div>",
            unsafe_allow_html=True,
        )


def render_reset_button():
    st.divider()
    if not st.session_state.get("reset_confirm", False):
        if st.button("🗑️ Reset progress", type="secondary", use_container_width=True, key="reset_init"):
            st.session_state.reset_confirm = True
            st.rerun()
    else:
        st.markdown(
            '<div style="font-size:0.8rem;color:#F39C12;margin-bottom:0.4rem;">'
            '⚠️ This will erase all progress. Are you sure?</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Yes, reset", type="primary", use_container_width=True, key="reset_confirm"):
                default = get_default_progress()
                save_progress(default)
                st.session_state.progress = default
                st.session_state.user_answers = {}
                st.session_state.current_scenario = None
                st.session_state.phase = "selection"
                st.session_state.welcome_dismissed = False
                st.session_state.reset_confirm = False
                st.rerun()
        with col_b:
            if st.button("Cancel", use_container_width=True, key="reset_cancel"):
                st.session_state.reset_confirm = False
                st.rerun()
