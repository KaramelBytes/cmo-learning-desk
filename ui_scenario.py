import streamlit as st
from data import (
    SCENARIO_EMOJIS,
    STEPS_ORDERED,
    ANALYSIS_STEPS_ORDERED,
    STP_POINTS,
    ANALYSIS_POINTS,
    CC_POINTS,
    MASTER_THRESHOLD,
    TIER_ICONS,
    TIER_NAMES,
    save_progress,
)
from ui_components import h, render_back_button, render_step_pipeline
from utils.persistence import save_resume_payload, clear_resume_payload


def _persist_current():
    """Mirror current user_answers to localStorage for refresh-resume."""
    scenario = st.session_state.get("current_scenario")
    if scenario and "scenario_id" in scenario:
        save_resume_payload(
            st.session_state.get("user_answers", {}),
            scenario["scenario_id"],
        )


def _generate_takeaway_options(key, sa_data):
    """Generate key takeaway options from 5C data for the active learning worksheet."""
    options = []
    if key == "company":
        strengths = sa_data.get("strengths", [])
        weaknesses = sa_data.get("weaknesses", [])
        if strengths:
            options.append(f"Strength: {strengths[0]}")
        if weaknesses:
            options.append(f"Weakness: {weaknesses[0]}")
        if len(strengths) > 1:
            options.append(f"Strength: {strengths[1]}")
        if len(weaknesses) > 1:
            options.append(f"Weakness: {weaknesses[1]}")
    elif key == "competitors":
        direct = sa_data.get("direct", [])
        indirect = sa_data.get("indirect", [])
        if direct:
            options.append(f"Direct competitor: {direct[0]}")
        if indirect:
            options.append(f"Indirect competitor: {indirect[0]}")
        if len(direct) > 1:
            options.append(f"Direct competitor: {direct[1]}")
    elif key == "customers":
        segments = sa_data.get("segments_observed", [])
        insight = sa_data.get("key_insight", "")
        if segments:
            options.append(f"Segment: {segments[0]}")
        if len(segments) > 1:
            options.append(f"Segment: {segments[1]}")
        if insight:
            options.append(f"Insight: {insight[:80]}...")
    elif key == "collaborators":
        suppliers = sa_data.get("suppliers", [])
        channels = sa_data.get("channels", [])
        if suppliers:
            options.append(f"Supplier: {suppliers[0]}")
        if channels:
            options.append(f"Channel: {channels[0]}")
    elif key == "climate":
        trends = sa_data.get("trends", [])
        threats = sa_data.get("threats", [])
        if trends:
            options.append(f"Trend: {trends[0]}")
        if threats:
            options.append(f"Threat: {threats[0]}")
        if len(trends) > 1:
            options.append(f"Trend: {trends[1]}")
    return options[:4]


def _tab_status_icon(key, q_data, scenario_id=None):
    """Return status icon for a 5C section reflecting answer state and correctness.
    - ⭕: unanswered
    - ✅: answered correctly (or correctness cannot be determined)
    - ❌: answered incorrectly

    Reads the radio's value directly from Streamlit's widget state via its key,
    which is always in sync with the user's current selection. This is more
    reliable than mirroring the value in user_answers, which has ordering issues
    when widgets are recreated on each rerun.
    """
    if scenario_id is None:
        scenario = st.session_state.get("current_scenario")
        scenario_id = scenario.get("scenario_id") if scenario else None
    if scenario_id is None:
        return "⭕"
    radio_key = f"radio_analysis_{key}_{scenario_id}"
    answer = st.session_state.get(radio_key)
    if answer is None:
        return "⭕"
    correct_idx = q_data.get("correct_idx") if q_data else None
    if correct_idx is None:
        return "✅"
    return "✅" if answer == correct_idx else "❌"


def render_scenario_mode():
    phase = st.session_state.phase

    if phase == "selection":
        render_scenario_selection()
    elif phase == "situation_analysis":
        render_situation_analysis()
    elif phase == "strategy":
        render_strategy()
    elif phase == "concept_check":
        render_concept_check()
    elif phase == "results":
        render_results()
    elif phase == "next_steps":
        render_next_steps()
    elif phase == "review":
        render_review()


def render_scenario_selection():
    st.markdown('<div class="main-title">📋 Scenario Mode</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Select a scenario. You will conduct a 5C situation analysis before making STP decisions.</div>',
        unsafe_allow_html=True,
    )

    scenarios = st.session_state.scenarios
    progress = st.session_state.progress
    completed = progress.get("completed_scenarios", [])

    # First-visit welcome
    if not completed and not st.session_state.get("welcome_dismissed"):
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;margin-bottom:0.8rem;">'
                '👋 Welcome to CMO Desk</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.95rem;color:#2C3E50;line-height:1.6;'>"
                "This app teaches you to make <strong>STP (Segmentation, Targeting, Positioning)</strong> "
                "decisions grounded in a full marketing <strong>situation analysis</strong>.<br><br>"
                "<strong>How it works:</strong><br>"
                "1. <strong>Situation Analysis</strong> — Examine the 5C environment (Company, Competitors, Customers, Collaborators, Climate)<br>"
                "2. <strong>Strategy</strong> — Make Segmentation, Targeting, and Positioning decisions based on your analysis<br>"
                "3. <strong>Concept Check</strong> — Connect theory to practice with a framework question<br>"
                "4. <strong>Results</strong> — Review your analytical decision trace and learn from the rubric<br><br>"
                "<strong>Scoring:</strong> 9 questions, 100 points total. Master a scenario with ≥75 points.<br>"
                "Master all scenarios in a tier to unlock the next difficulty level."
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button("Get Started →", type="primary"):
                st.session_state.welcome_dismissed = True
                st.rerun()
        st.markdown("<div style='margin:1.5rem 0;'></div>", unsafe_allow_html=True)
        return

    unlocked = progress.get("unlocked_tiers", [1])
    mastered = progress.get("mastered_scenarios", [])

    if not scenarios:
        st.warning("No scenarios available. Check that data/scenarios_tier{1,2,3}.json exist.")
        return

    for tier_num in [1, 2, 3]:
        tier_scenarios = [s for s in scenarios if s["difficulty_tier"] == tier_num]
        if not tier_scenarios:
            continue

        is_unlocked = tier_num in unlocked

        st.markdown(
            f'<div class="tier-header">'
            f'<span class="tier-icon">{TIER_ICONS[tier_num]}</span>'
            f'<span class="tier-title">Tier {tier_num}: {TIER_NAMES[tier_num]} '
            f'({sum(1 for s in tier_scenarios if s["scenario_id"] in mastered)}/{len(tier_scenarios)})</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        n_cols = min(3, len(tier_scenarios))
        for row_start in range(0, len(tier_scenarios), n_cols):
            row = tier_scenarios[row_start:row_start + n_cols]
            cols = st.columns(n_cols)
            for i, scenario in enumerate(row):
                sid = scenario["scenario_id"]
                is_completed = sid in completed
                is_mastered = sid in mastered
                is_locked = not is_unlocked

                with cols[i]:
                    if is_locked:
                        st.markdown(
                            f'<div class="scenario-card locked">'
                            f'<div class="card-icon">🔒</div>'
                            f'<div class="card-title">Locked</div>'
                            f'<div class="card-type">Complete Tier {tier_num - 1}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    elif is_mastered:
                        score = progress.get("scenario_scores", {}).get(str(sid), 0)
                        st.markdown(
                            f'<div class="scenario-card completed">'
                            f'<div class="card-icon">✅</div>'
                            f'<div class="card-title">{h(scenario["title"])}</div>'
                            f'<div class="card-type">{h(scenario["scenario_type"])}</div>'
                            f'<div class="card-locked-text" style="color:#27AE60;font-weight:600;">'
                            f'{score} pts — Mastered</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.button("📖 Review", key=f"review_{sid}", use_container_width=True):
                                start_review(sid)
                        with col_y:
                            if st.button("🔄 Replay", key=f"replay_{sid}", use_container_width=True):
                                start_scenario(sid)
                    elif is_completed:
                        score = progress.get("scenario_scores", {}).get(str(sid), 0)
                        st.markdown(
                            f'<div class="scenario-card unlocked">'
                            f'<div class="card-icon">☑️</div>'
                            f'<div class="card-title">{h(scenario["title"])}</div>'
                            f'<div class="card-type">{h(scenario["scenario_type"])}</div>'
                            f'<div class="card-locked-text" style="color:#F39C12;font-weight:600;">'
                            f'{score} pts — Revisit</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.button("📖 Review", key=f"review_{sid}", use_container_width=True):
                                start_review(sid)
                        with col_y:
                            if st.button("🔄 Replay", key=f"replay_{sid}", use_container_width=True):
                                start_scenario(sid)
                    else:
                        emoji = SCENARIO_EMOJIS.get(sid, "📋")
                        st.markdown(
                            f'<div class="scenario-card unlocked">'
                            f'<div class="card-icon">{emoji}</div>'
                            f'<div class="card-title">{h(scenario["title"])}</div>'
                            f'<div class="card-type">{h(scenario["scenario_type"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("▶️ Start", key=f"start_{sid}", use_container_width=True):
                            start_scenario(sid)

        if tier_num < 3:
            st.markdown('<hr class="tier-divider">', unsafe_allow_html=True)


def start_scenario(scenario_id):
    scenarios = st.session_state.scenarios
    scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
    if not scenario:
        return
    if "scenario_id" not in scenario or "difficulty_tier" not in scenario:
        st.error("Scenario is missing required identifiers. Check the JSON schema.")
        return
    progress = st.session_state.progress
    unlocked = progress.get("unlocked_tiers", [1])
    if scenario["difficulty_tier"] not in unlocked:
        st.warning("Complete previous tiers to unlock this scenario.")
        return
    st.session_state.current_scenario = scenario
    st.session_state.phase = "situation_analysis"
    st.session_state.user_answers = {}
    st.rerun()


def start_review(scenario_id):
    """Enter Review mode for a completed scenario without resetting answers."""
    scenarios = st.session_state.scenarios
    scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
    if not scenario:
        return
    progress = st.session_state.progress
    attempts = progress.get("last_attempt_answers", {})
    last = attempts.get(str(scenario_id))
    if not last or not last.get("answers"):
        st.warning("No saved answers for this scenario yet. Replay it once first.")
        return
    st.session_state.current_scenario = scenario
    st.session_state.user_answers = dict(last["answers"])
    st.session_state.phase = "review"
    st.rerun()


def render_review():
    """Re-display a completed scenario's answers + rubrics without re-attempting."""
    scenario = st.session_state.current_scenario
    if not scenario:
        st.session_state.phase = "selection"
        st.rerun()
        return

    saved = st.session_state.progress.get("last_attempt_answers", {}).get(
        str(scenario["scenario_id"]), {}
    )
    if not saved:
        st.info("No saved answers for this scenario. Replay it to populate the review.")
        if st.button("← Back to Scenarios", type="secondary"):
            st.session_state.phase = "selection"
            st.session_state.current_scenario = None
            st.rerun()
        return

    saved_score = saved.get("score", 0)

    st.markdown(
        f'<div class="main-title">📖 Review: {h(scenario["title"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="subtitle">Read-only re-display of your previous attempt. '
        f'Last score: <strong>{saved_score} pts</strong>.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Your previous answers")
    aq = scenario.get("analysis_questions", {})
    for step in ANALYSIS_STEPS_ORDERED:
        q_data = aq.get(step, {})
        options = q_data.get("options", [])
        user_idx = saved["answers"].get(step)
        correct_idx = q_data.get("correct_idx")
        if user_idx is not None and 0 <= user_idx < len(options):
            user_text = options[user_idx]
            icon = "✅" if user_idx == correct_idx else "❌"
            correct_text = options[correct_idx] if correct_idx is not None and 0 <= correct_idx < len(options) else "—"
            with st.expander(f"{icon} Analysis: {step.title()}"):
                st.markdown(f"**Your choice:** {h(user_text)}")
                st.markdown(f"**Correct answer:** {h(correct_text)}")
                if q_data.get("rationale"):
                    st.markdown(f"**Rationale:** {h(q_data['rationale'])}")
        else:
            with st.expander(f"⭕ Analysis: {step.title()} — not answered"):
                st.caption("You did not answer this question in the last attempt.")

    st.markdown("#### STP Decisions")
    steps = scenario.get("steps", {})
    for step in STEPS_ORDERED:
        step_data = steps.get(step, {})
        options = step_data.get("options", [])
        user_idx = saved["answers"].get(step)
        correct_idx = step_data.get("correct_idx")
        if user_idx is not None and 0 <= user_idx < len(options):
            icon = "✅" if user_idx == correct_idx else "❌"
            with st.expander(f"{icon} {step.title()}"):
                st.markdown(f"**Your choice:** {h(options[user_idx])}")
                st.markdown(f"**Correct answer:** {h(options[correct_idx])}")
                st.markdown(f"**Rationale:** {h(step_data.get('rubric_rationale', ''))}")
        else:
            with st.expander(f"⭕ {step.title()} — not answered"):
                st.caption("You did not answer this question in the last attempt.")

    cc = scenario.get("concept_check", {})
    cc_idx = saved["answers"].get("concept_check")
    if cc and cc_idx is not None and 0 <= cc_idx < len(cc.get("options", [])):
        icon = "✅" if cc_idx == cc.get("correct_idx") else "❌"
        with st.expander(f"{icon} Concept Check"):
            st.markdown(f"**Your choice:** {h(cc['options'][cc_idx])}")
            st.markdown(f"**Correct answer:** {h(cc['options'][cc['correct_idx']])}")
            st.markdown(f"**Rationale:** {h(cc.get('rationale', ''))}")
    else:
        with st.expander("⭕ Concept Check — not answered"):
            st.caption("You did not answer this question in the last attempt.")

    st.markdown("<div style='margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Scenarios", type="secondary", use_container_width=True):
            st.session_state.phase = "selection"
            st.session_state.current_scenario = None
            st.rerun()
    with col2:
        if st.button("🔄 Replay this scenario", type="primary", use_container_width=True):
            start_scenario(scenario["scenario_id"])


def render_situation_analysis():
    scenario = st.session_state.current_scenario
    if not scenario:
        st.session_state.phase = "selection"
        st.rerun()
        return

    sa = scenario.get("situation_analysis", {})
    aq = scenario.get("analysis_questions", {})

    if not sa or not aq:
        st.session_state.phase = "strategy"
        st.rerun()
        return

    _persist_current()

    # Hidden marker for CSS phase targeting
    st.markdown('<div id="situation-analysis-phase-marker" style="display:none;"></div>', unsafe_allow_html=True)

    emoji = SCENARIO_EMOJIS.get(scenario["scenario_id"], "📋")
    st.markdown(f'<div class="main-title">{emoji} {h(scenario["title"])}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="scenario-meta">Type: {h(scenario["scenario_type"])} | '
        f'Tier {scenario["difficulty_tier"]}: {TIER_NAMES.get(scenario["difficulty_tier"], "")} | '
        f'Scenario {scenario["scenario_id"]} of {len(st.session_state.scenarios)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">🔍 Situation Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="analysis-intro">Before making STP decisions, examine the market environment using the '
        '<strong>5C Framework</strong>: Company, Competitors, Customers, Collaborators, and Climate. '
        'Each tab below contains market intelligence and one analysis question. '
        'Answer all five to unlock the strategy phase.<br>'
        '<span style="font-size:0.8rem;color:#7F8C8D;">⌨️ Tip: Use <kbd>Tab</kbd> to move between questions, '
        '<kbd>←</kbd>/<kbd>→</kbd> to switch between the 5C tabs.</span></div>',
        unsafe_allow_html=True,
    )

    # Phase step indicator
    render_step_pipeline(0)

    # Build tab content
    tab_config = [
        ("🏢 Company", "company", "bg_company"),
        ("⚔️ Competitors", "competitors", "bg_competitors"),
        ("👥 Customers", "customers", "bg_customers"),
        ("🤝 Collaborators", "collaborators", "bg_collaborators"),
        ("🌍 Climate", "climate", "bg_climate"),
    ]

    # Static tab labels: keeping labels constant across reruns prevents
    # Streamlit from rebuilding the tab structure (which would reset child
    # widget state, including the radio button selections).
    # The status icon is shown inside each tab's content instead.
    tab_labels = [t[0] for t in tab_config]
    tabs = st.tabs(tab_labels)

    for tab_idx, (label, key, bg_class) in enumerate(tab_config):
        with tabs[tab_idx]:
            sa_data = sa.get(key, {})
            q_data = aq.get(key, {})

            if not sa_data or not q_data:
                st.info("No analysis data available for this section.")
                continue

            # Status indicator at the top of the tab content
            # (⭕ unanswered | ✅ correct | ❌ incorrect)
            status_icon = _tab_status_icon(key, q_data, scenario["scenario_id"])
            aria = {
                "⭕": "unanswered",
                "✅": "correct",
                "❌": "incorrect",
            }.get(status_icon, "unanswered")
            st.markdown(
                f'<div style="font-size:1.4rem;font-weight:700;color:#1B2A4A;'
                f'margin-bottom:0.8rem;display:flex;align-items:center;gap:0.5rem;" '
                f'role="status" aria-label="{aria}">'
                f'<span style="font-size:1.6rem;" aria-hidden="true">{status_icon}</span>'
                f'<span>{h(label)}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                st.markdown(
                    f'<div class="analysis-5c-header">{label}</div>',
                    unsafe_allow_html=True,
                )

                # Render summary
                if sa_data.get("summary"):
                    st.markdown(f'<div class="analysis-summary">{h(sa_data["summary"])}</div>', unsafe_allow_html=True)

                # Render key data points
                for field_label, field_key in [
                    ("Strengths", "strengths"),
                    ("Weaknesses", "weaknesses"),
                    ("Direct Competitors", "direct"),
                    ("Indirect Competitors", "indirect"),
                    ("Segments Observed", "segments_observed"),
                    ("Key Insight", "key_insight"),
                    ("Suppliers", "suppliers"),
                    ("Channels", "channels"),
                    ("Trends", "trends"),
                    ("Threats", "threats"),
                ]:
                    items = sa_data.get(field_key, [])
                    if items:
                        if isinstance(items, str):
                            st.markdown(f"**{field_label}:** {h(items)}")
                        elif isinstance(items, list) and items:
                            st.markdown(f"**{field_label}:**")
                            for item in items:
                                st.markdown(f"- {h(item)}")

            # Analysis question
            if q_data.get("question"):
                with st.container(border=True):
                    st.markdown(
                        f'<div class="analysis-q-label">📝 Analysis Question '
                        f'<span style="font-size:0.75rem;color:#7F8C8D;font-weight:400;letter-spacing:0;">'
                        f'({ANALYSIS_POINTS} pts)</span></div>',
                        unsafe_allow_html=True,
                    )

                    # Key Takeaway worksheet (active learning)
                    takeaway_key = f"takeaway_{key}"
                    takeaway_options = _generate_takeaway_options(key, sa_data)
                    if takeaway_options:
                        st.markdown(
                            '<div style="font-size:0.85rem;color:#5A6C7D;margin-bottom:0.3rem;">'
                            '<strong>Step 1:</strong> What is the most important insight from this analysis?</div>',
                            unsafe_allow_html=True,
                        )
                        ta_value = st.selectbox(
                            "Select your key takeaway",
                            options=["— Select one —"] + takeaway_options,
                            key=f"select_takeaway_{key}_{scenario['scenario_id']}",
                        )
                        if ta_value != "— Select one —":
                            st.session_state.user_answers[takeaway_key] = ta_value
                            st.caption("✅ Selected — this is your key insight to carry into Step 2.")
                        else:
                            st.caption("💡 Pick the insight you'd defend in a client conversation.")
                        st.markdown(
                            '<div style="margin:0.8rem 0;border-top:1px dashed #E0DCD3;"></div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            '<div style="font-size:0.85rem;color:#5A6C7D;margin-bottom:0.3rem;">'
                            '<strong>Step 2:</strong> Now answer the graded question:</div>',
                            unsafe_allow_html=True,
                        )

                    options = q_data["options"]

                    idx = st.radio(
                        q_data["question"],
                        options=list(range(len(options))),
                        format_func=lambda i, opts=options: opts[i],
                        key=f"radio_analysis_{key}_{scenario['scenario_id']}",
                    )
                    if idx is not None:
                        st.session_state.user_answers[key] = idx
                        st.caption("✅ Answered")
                        correct_idx = q_data.get("correct_idx")
                        if correct_idx is not None:
                            if idx == correct_idx:
                                st.markdown(
                                    '<div style="background:#F0F9F0;border-left:4px solid #27AE60;'
                                    'padding:0.6rem 1rem;margin-top:0.5rem;border-radius:6px;'
                                    'font-size:0.85rem;color:#2C3E50;">'
                                    '✅ <strong>Correct</strong> — Strong analytical reasoning.</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div style="background:#FFF8F0;border-left:4px solid #F39C12;'
                                    'padding:0.6rem 1rem;margin-top:0.5rem;border-radius:6px;'
                                    'font-size:0.85rem;color:#2C3E50;">'
                                    '⚠️ <strong>Review your reasoning</strong> — '
                                    'Consider the analysis data more carefully before proceeding.</div>',
                                    unsafe_allow_html=True,
                                )
                                with st.expander("Show model answer", expanded=False):
                                    model_option = options[correct_idx] if 0 <= correct_idx < len(options) else ""
                                    rationale = q_data.get("rationale", "")
                                    st.markdown(
                                        f'<div class="analysis-model-answer">'
                                        f'<div class="analysis-model-label">Model answer</div>'
                                        f'<div class="analysis-model-option">{h(model_option)}</div>'
                                        f'<div class="analysis-model-rationale">{h(rationale)}</div>'
                                        f'</div>',
                                        unsafe_allow_html=True,
                                    )
            else:
                st.warning(f"Missing analysis question data for {label}.")

    # Compute all_answered across all 5 sections using each radio's widget state.
    # Reading directly from st.session_state[widget_key] is authoritative — Streamlit
    # keeps it in sync with the user's current selection across reruns.
    sid = scenario["scenario_id"]
    all_answered = True
    for k in ANALYSIS_STEPS_ORDERED:
        if not aq.get(k, {}).get("question"):
            all_answered = False
            break
        if st.session_state.get(f"radio_analysis_{k}_{sid}") is None:
            all_answered = False
            break

    if sa.get("analysis_prompt"):
        st.markdown(
            '<div class="analysis-prompt-callout">'
            '<strong>💡 Analysis Prompt</strong> — Read before proceeding:<br>'
            f'{h(sa["analysis_prompt"])}'
            '</div>',
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([1, 3])
    with col1:
        render_back_button()
    with col2:
        if st.button(
            "Submit Analysis & Continue to Strategy →",
            type="primary",
            use_container_width=True,
            disabled=not all_answered,
        ):
            st.session_state.phase = "strategy"
            st.rerun()
        if not all_answered:
            sid = scenario["scenario_id"]
            missing = []
            answered_keys = []
            for k in ANALYSIS_STEPS_ORDERED:
                radio_key = f"radio_analysis_{k}_{sid}"
                answer = st.session_state.get(radio_key)
                if answer is None:
                    missing.append(k.title())
                else:
                    answered_keys.append(k)
                    if answer != aq.get(k, {}).get("correct_idx"):
                        pass  # counted as incorrect below
            correct_so_far = sum(
                1 for k in answered_keys
                if st.session_state.get(f"radio_analysis_{k}_{sid}") == aq.get(k, {}).get("correct_idx")
            )
            st.caption(
                f"⏳ {correct_so_far}/{len(answered_keys)} correct so far &nbsp;•&nbsp; "
                f"Answer {len(missing)} more to continue: {', '.join(missing)}"
            )


def _get_stp_hint(step_name, scenario, answers):
    """Generate a contextual hint linking the STP step to the relevant 5C analysis."""
    aq = scenario.get("analysis_questions", {})
    sa = scenario.get("situation_analysis", {})

    if step_name == "segmentation":
        user_idx = answers.get("customers")
        q_data = aq.get("customers", {})
        options = q_data.get("options", [])
        insight = options[user_idx] if user_idx is not None and user_idx < len(options) else None
        if insight:
            return (
                f'<div style="background:#F8F7F4;border-left:4px solid #D4A843;'
                f'padding:0.8rem 1rem;margin-bottom:0.8rem;border-radius:6px;'
                f'font-size:0.9rem;color:#2C3E50;line-height:1.5;">'
                f'💡 <strong>Customer analysis informs segmentation.</strong><br>'
                f'Your insight: <em>{h(insight)}</em></div>'
            )
        return None

    elif step_name == "targeting":
        comp_idx = answers.get("competitors")
        comp_q = aq.get("competitors", {})
        comp_opts = comp_q.get("options", [])
        comp_insight = comp_opts[comp_idx] if comp_idx is not None and comp_idx < len(comp_opts) else None

        collab_idx = answers.get("collaborators")
        collab_q = aq.get("collaborators", {})
        collab_opts = collab_q.get("options", [])
        collab_insight = collab_opts[collab_idx] if collab_idx is not None and collab_idx < len(collab_opts) else None

        collab_data = sa.get("collaborators", {})
        channels = collab_data.get("channels", [])
        channel_note = ""
        if channels:
            channel_note = (
                f'<br>🤝 <strong>Channel constraint:</strong> '
                f'{h(channels[0])}'
            )

        parts = []
        if comp_insight:
            parts.append(f'Competitor: <em>{h(comp_insight)}</em>')
        if collab_insight:
            parts.append(f'Collaborator: <em>{h(collab_insight)}</em>')
        if parts or channel_note:
            inner = "<br>".join(parts) if parts else ""
            return (
                f'<div style="background:#F8F7F4;border-left:4px solid #D4A843;'
                f'padding:0.8rem 1rem;margin-bottom:0.8rem;border-radius:6px;'
                f'font-size:0.9rem;color:#2C3E50;line-height:1.5;">'
                f'💡 <strong>Competitor landscape & channel constraints inform targeting.</strong><br>'
                f'Your insights: {inner or "—"}'
                f'{channel_note}'
                f'</div>'
            )
        return None

    elif step_name == "positioning":
        company_idx = answers.get("company")
        climate_idx = answers.get("climate")
        company_q = aq.get("company", {})
        climate_q = aq.get("climate", {})
        company_opts = company_q.get("options", [])
        climate_opts = climate_q.get("options", [])
        company_insight = company_opts[company_idx] if company_idx is not None and company_idx < len(company_opts) else None
        climate_insight = climate_opts[climate_idx] if climate_idx is not None and climate_idx < len(climate_opts) else None
        parts = []
        if company_insight:
            parts.append(f'Company: <em>{h(company_insight)}</em>')
        if climate_insight:
            parts.append(f'Climate: <em>{h(climate_insight)}</em>')
        if parts:
            return (
                f'<div style="background:#F8F7F4;border-left:4px solid #D4A843;'
                f'padding:0.8rem 1rem;margin-bottom:0.8rem;border-radius:6px;'
                f'font-size:0.9rem;color:#2C3E50;line-height:1.5;">'
                f'💡 <strong>Company capabilities & climate trends inform positioning.</strong><br>'
                f'Your insights: {" | ".join(parts)}</div>'
            )
        return None

    return None


def _render_5c_context(tab_key, scenario, answers):
    """Render the relevant 5C analysis context for a given STP tab."""
    sa = scenario.get("situation_analysis", {})
    aq = scenario.get("analysis_questions", {})
    sa_data = sa.get(tab_key, {})
    q_data = aq.get(tab_key, {})

    if not sa_data:
        return

    # Summary
    if sa_data.get("summary"):
        st.markdown(
            f'<div style="font-size:0.9rem;line-height:1.6;color:#2C3E50;'
            f'margin-bottom:0.8rem;">{h(sa_data["summary"])}</div>',
            unsafe_allow_html=True,
        )

    # Key fields
    field_map = {
        "company": [
            ("Strengths", "strengths"),
            ("Weaknesses", "weaknesses"),
        ],
        "competitors": [
            ("Direct", "direct"),
            ("Indirect", "indirect"),
        ],
        "customers": [
            ("Segments", "segments_observed"),
            ("Key Insight", "key_insight"),
        ],
        "climate": [
            ("Trends", "trends"),
            ("Threats", "threats"),
        ],
    }
    for label, key in field_map.get(tab_key, []):
        items = sa_data.get(key, [])
        if items:
            if isinstance(items, str):
                st.markdown(f"**{label}:** {h(items)}")
            elif isinstance(items, list) and items:
                st.markdown(f"**{label}:**")
                for item in items:
                    st.markdown(f"- {h(item)}")

    # Student's analysis answer
    user_idx = answers.get(tab_key)
    options = q_data.get("options", [])
    if user_idx is not None and user_idx < len(options):
        st.markdown(
            f'<div style="background:#F8F7F4;border-left:4px solid #1B2A4A;'
            f'padding:0.6rem 1rem;margin-top:0.8rem;border-radius:6px;'
            f'font-size:0.9rem;color:#2C3E50;">'
            f'<strong>Your analysis:</strong> {h(options[user_idx])}</div>',
            unsafe_allow_html=True,
        )


def render_strategy():
    scenario = st.session_state.current_scenario
    if not scenario:
        st.session_state.phase = "selection"
        st.rerun()
        return

    _persist_current()

    # Hidden marker for CSS phase targeting
    st.markdown('<div id="strategy-phase-marker" style="display:none;"></div>', unsafe_allow_html=True)

    # Step pipeline
    render_step_pipeline(1)

    st.markdown('<div class="section-title">🧠 The Strategy</div>', unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.95rem;color:#5A6C7D;margin-bottom:1rem;'>"
        "Each tab below shows the relevant situation analysis for that STP decision, "
        "followed by the question. Review the context before selecting your answer.</div>",
        unsafe_allow_html=True,
    )

    steps = scenario["steps"]
    answers = st.session_state.user_answers

    tab_labels = [
        "👥 Segmentation",
        "⚔️ Targeting",
        "🏢 Positioning",
    ]
    tabs = st.tabs(tab_labels)

    all_answered = True
    for i, step_name in enumerate(STEPS_ORDERED):
        step_data = steps[step_name]
        options = step_data["options"]
        current_answer = answers.get(step_name)

        with tabs[i]:
            # 5C context section
            context_keys = {
                "segmentation": "customers",
                "targeting": "competitors",
                "positioning": "company",
            }
            context_key = context_keys.get(step_name)
            if context_key:
                st.markdown(
                    f'<div style="font-size:0.85rem;font-weight:700;letter-spacing:1px;'
                    f'color:#D4A843;text-transform:uppercase;margin-bottom:0.5rem;">'
                    f'Relevant Analysis: {context_key.title()}</div>',
                    unsafe_allow_html=True,
                )
                _render_5c_context(context_key, scenario, answers)

            # Positioning also shows climate
            if step_name == "positioning":
                st.markdown(
                    f'<div style="font-size:0.85rem;font-weight:700;letter-spacing:1px;'
                    f'color:#D4A843;text-transform:uppercase;margin:1rem 0 0.5rem 0;">'
                    f'Relevant Analysis: Climate</div>',
                    unsafe_allow_html=True,
                )
                _render_5c_context("climate", scenario, answers)

            st.markdown("<div style='margin:1.2rem 0;border-top:1px solid #E0DCD3;'></div>", unsafe_allow_html=True)

            # STP question
            with st.container(border=True):
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#7F8C8D;margin-bottom:0.5rem;">'
                    f'{step_name.title()} — {STP_POINTS} pts</div>',
                    unsafe_allow_html=True,
                )
                hint = _get_stp_hint(step_name, scenario, answers)
                if hint:
                    st.markdown(hint, unsafe_allow_html=True)
                idx = st.radio(
                    step_data["question"],
                    options=list(range(len(options))),
                    format_func=lambda i, opts=options: opts[i],
                    index=current_answer if current_answer is not None else None,
                    key=f"radio_{step_name}_{scenario['scenario_id']}",
                )
                st.session_state.user_answers[step_name] = idx

        if idx is None:
            all_answered = False

    col1, col2 = st.columns([1, 3])
    with col1:
        render_back_button(target_phase="situation_analysis")
    with col2:
        if st.button(
            "Submit Strategy",
            type="primary",
            use_container_width=True,
            disabled=not all_answered,
        ):
            st.session_state.phase = "concept_check"
            st.rerun()


def render_concept_check():
    scenario = st.session_state.current_scenario
    if not scenario:
        st.session_state.phase = "selection"
        st.rerun()
        return

    _persist_current()

    # Hidden marker for CSS phase targeting
    st.markdown('<div id="concept-check-phase-marker" style="display:none;"></div>', unsafe_allow_html=True)

    # Step pipeline
    render_step_pipeline(2)

    cc = scenario["concept_check"]
    current_cc = st.session_state.user_answers.get("concept_check")

    st.markdown('<div class="section-title">📝 Concept Check</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.75rem;color:#7F8C8D;margin-bottom:0.5rem;">'
        f'Theory — {CC_POINTS} pts</div>',
        unsafe_allow_html=True,
    )
    st.markdown("Before reviewing your results, answer this theory question:")

    with st.container(border=True):
        idx = st.radio(
            cc["question"],
            options=list(range(len(cc["options"]))),
            format_func=lambda i: cc["options"][i],
            index=current_cc if current_cc is not None else None,
            key=f"radio_cc_{scenario['scenario_id']}",
        )
        st.session_state.user_answers["concept_check"] = idx

    col1, col2 = st.columns([1, 3])
    with col1:
        render_back_button(target_phase="strategy")
    with col2:
        if st.button(
            "Submit Answer & See Results →",
            type="primary",
            use_container_width=True,
            disabled=idx is None,
        ):
            st.session_state.phase = "results"
            st.rerun()


def render_results():
    scenario = st.session_state.current_scenario
    if not scenario:
        st.session_state.phase = "selection"
        st.rerun()
        return

    steps = scenario["steps"]
    cc = scenario["concept_check"]
    aq = scenario.get("analysis_questions", {})
    answers = st.session_state.user_answers

    # --- Analysis results ---
    analysis_results = {}
    for step_name in ANALYSIS_STEPS_ORDERED:
        q_data = aq.get(step_name, {})
        user_idx = answers.get(step_name)
        correct_idx = q_data.get("correct_idx")
        if correct_idx is not None and user_idx is not None:
            is_correct = user_idx == correct_idx
            analysis_results[step_name] = {
                "correct": is_correct,
                "user_option": q_data["options"][user_idx] if "options" in q_data else None,
                "correct_option": q_data["options"][correct_idx] if "options" in q_data else None,
                "rubric": q_data.get("rationale", ""),
            }
        elif correct_idx is not None:
            analysis_results[step_name] = {
                "correct": False,
                "user_option": None,
                "correct_option": q_data.get("options", [""])[correct_idx] if "options" in q_data else None,
                "rubric": q_data.get("rationale", ""),
            }

    # --- STP results ---
    stp_results = {}
    for step_name in STEPS_ORDERED:
        step_data = steps[step_name]
        user_idx = answers.get(step_name)
        correct_idx = step_data["correct_idx"]
        is_correct = user_idx == correct_idx
        stp_results[step_name] = {
            "correct": is_correct,
            "user_option": step_data["options"][user_idx] if user_idx is not None else None,
            "correct_option": step_data["options"][correct_idx],
            "rubric": step_data["rubric_rationale"],
        }

    # --- Concept check results ---
    cc_user_idx = answers.get("concept_check")
    cc_correct_idx = cc["correct_idx"]
    cc_correct = cc_user_idx == cc_correct_idx
    cc_result = {
        "correct": cc_correct,
        "user_option": cc["options"][cc_user_idx] if cc_user_idx is not None else None,
        "correct_option": cc["options"][cc_correct_idx],
        "rubric": cc["rationale"],
    }

    # --- Compute scores ---
    analysis_correct_count = sum(1 for r in analysis_results.values() if r.get("correct", False))
    analysis_total = len(analysis_results)
    stp_correct_count = sum(1 for r in stp_results.values() if r["correct"])
    cc_correct_count = 1 if cc_correct else 0

    analysis_points = analysis_correct_count * ANALYSIS_POINTS if analysis_total > 0 else 0
    stp_points = stp_correct_count * STP_POINTS
    cc_points = cc_correct_count * CC_POINTS
    scenario_points = analysis_points + stp_points + cc_points
    total_questions = analysis_total + len(STEPS_ORDERED) + 1
    total_correct = analysis_correct_count + stp_correct_count + cc_correct_count

    # --- Render ---
    st.markdown(
        f'<div class="main-title">{h(scenario["title"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### 📊 Board Review")

    # Overall score
    if total_correct == total_questions:
        border_color = "#27AE60"
        score_label = "Mastered"
    elif total_correct >= total_questions // 2:
        border_color = "#F39C12"
        score_label = "Passing"
    else:
        border_color = "#C0392B"
        score_label = "Needs Work"

    st.markdown(
        f'<div class="score-banner" style="border-left: 5px solid {border_color};">'
        f'  <h2>{score_label}: {total_correct}/{total_questions} ({scenario_points} pts)</h2>'
        f'  <p>Analysis: {analysis_correct_count}/{analysis_total} ({analysis_points} pts) &nbsp;|&nbsp; '
        f'STP: {stp_correct_count}/3 ({stp_points} pts) &nbsp;|&nbsp; '
        f'Concept: {"✅" if cc_correct else "❌"} ({cc_points} pts)</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Visual score breakdown
    st.markdown("#### Score Breakdown")
    total_possible = analysis_total * ANALYSIS_POINTS + len(STEPS_ORDERED) * STP_POINTS + CC_POINTS
    analysis_pct = (analysis_points / (analysis_total * ANALYSIS_POINTS if analysis_total > 0 else 1)) * 100 if analysis_total > 0 else 0
    stp_pct = (stp_points / (len(STEPS_ORDERED) * STP_POINTS)) * 100
    cc_pct = (cc_points / CC_POINTS) * 100

    col_a, col_s, col_c = st.columns(3)
    with col_a:
        st.markdown(
            f'<div style="text-align:center;padding:0.8rem;background:#FFFFFF;'
            f'border-radius:8px;border:1px solid #E0DCD3;">'
            f'<div style="font-size:0.75rem;color:#5A6C7D;">Situation Analysis</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:#1B2A4A;">'
            f'{analysis_correct_count}/{analysis_total}</div>'
            f'<div style="font-size:0.8rem;color:#7F8C8D;">{analysis_points} pts</div></div>',
            unsafe_allow_html=True,
        )
    with col_s:
        st.markdown(
            f'<div style="text-align:center;padding:0.8rem;background:#FFFFFF;'
            f'border-radius:8px;border:1px solid #E0DCD3;">'
            f'<div style="font-size:0.75rem;color:#5A6C7D;">STP Strategy</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:#1B2A4A;">'
            f'{stp_correct_count}/3</div>'
            f'<div style="font-size:0.8rem;color:#7F8C8D;">{stp_points} pts</div></div>',
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            f'<div style="text-align:center;padding:0.8rem;background:#FFFFFF;'
            f'border-radius:8px;border:1px solid #E0DCD3;">'
            f'<div style="font-size:0.75rem;color:#5A6C7D;">Concept Check</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:#1B2A4A;">'
            f'{"✅" if cc_correct else "❌"}</div>'
            f'<div style="font-size:0.8rem;color:#7F8C8D;">{cc_points} pts</div></div>',
            unsafe_allow_html=True,
        )

    # What to focus on next
    if scenario_points < MASTER_THRESHOLD:
        st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)
        weak_areas = []
        if analysis_correct_count < analysis_total:
            weak_areas.append("situation analysis")
        if stp_correct_count < 3:
            weak_stp = [name for name in STEPS_ORDERED if not stp_results[name]["correct"]]
            weak_areas.append(f"STP decisions ({', '.join(weak_stp)})")
        if not cc_correct:
            weak_areas.append("concept check (theory)")
        if weak_areas:
            st.markdown(
                f'<div style="background:#FFF8F0;border-left:4px solid #F39C12;'
                f'padding:1rem 1.5rem;border-radius:8px;font-size:0.95rem;'
                f'color:#2C3E50;line-height:1.5;">'
                f'<strong>🎯 Focus area:</strong> Your {weak_areas[0]} need attention. '
                f'Review the rationale for each question in the detailed results below before your next attempt.</div>',
                unsafe_allow_html=True,
            )

    # Detailed results expanders
    st.markdown("<div style='margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("#### Detailed Results")

    # Analysis expanders
    if analysis_results:
        for step_name in ANALYSIS_STEPS_ORDERED:
            r = analysis_results.get(step_name)
            if not r:
                continue
            icon = "✅" if r.get("correct") else "❌"
            label = f"{icon} Analysis: {step_name.title()}"
            with st.expander(label):
                st.markdown(f"**Your choice:** {r.get('user_option', 'Not answered')}")
                st.markdown(f"**Correct answer:** {r.get('correct_option', 'N/A')}")
                if r.get("rubric"):
                    st.markdown(f"**Rationale:** {r['rubric']}")

    # STP expanders
    for step_name in STEPS_ORDERED:
        r = stp_results[step_name]
        icon = "✅" if r["correct"] else "❌"
        label = f"{icon} {step_name.title()}"
        with st.expander(label):
            st.markdown(f"**Your choice:** {r['user_option']}")
            st.markdown(f"**Correct answer:** {r['correct_option']}")
            st.markdown(f"**Rationale:** {r['rubric']}")

    # Concept check expander
    cc_icon = "✅" if cc_correct else "❌"
    with st.expander(f"{cc_icon} Concept Check"):
        st.markdown(f"**Your choice:** {cc_result['user_option']}")
        st.markdown(f"**Correct answer:** {cc_result['correct_option']}")
        st.markdown(f"**Rationale:** {cc_result['rubric']}")

    # Decision trace — analytical chain from 5C to STP
    st.markdown('<div style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)
    st.markdown("### 🔗 Analytical Decision Trace")
    st.markdown(
        "<div style='font-size:0.9rem;color:#5A6C7D;margin-bottom:1rem;'>"
        "The connection between your situation analysis and your STP decisions:</div>",
        unsafe_allow_html=True,
    )

    trace_items = []

    # Customers → Segmentation
    customer_r = analysis_results.get("customers")
    seg_r = stp_results.get("segmentation")
    if customer_r and seg_r:
        cust_icon = "✅" if customer_r.get("correct") else "❌"
        seg_icon = "✅" if seg_r["correct"] else "❌"
        trace_items.append(
            f"<div style='background:#FFFFFF;border:1px solid #E0DCD3;border-radius:8px;padding:1rem;margin-bottom:0.8rem;'>"
            f"<div style='font-size:0.85rem;font-weight:700;color:#D4A843;margin-bottom:0.5rem;'>"
            f"👥 Customers → Segmentation</div>"
            f"<div style='font-size:0.9rem;color:#2C3E50;line-height:1.5;'>"
            f"<strong>Your analysis:</strong> {cust_icon} {h(customer_r.get('user_option', '—'))}<br>"
            f"<strong>Your strategy:</strong> {seg_icon} {h(seg_r['user_option'])}<br>"
            f"<strong>Correct strategy:</strong> {h(seg_r['correct_option'])}<br>"
            f"<span style='color:#5A6C7D;'>💡 {h(seg_r['rubric'])}</span>"
            f"</div></div>"
        )

    # Competitors → Targeting
    comp_r = analysis_results.get("competitors")
    tgt_r = stp_results.get("targeting")
    if comp_r and tgt_r:
        comp_icon = "✅" if comp_r.get("correct") else "❌"
        tgt_icon = "✅" if tgt_r["correct"] else "❌"
        trace_items.append(
            f"<div style='background:#FFFFFF;border:1px solid #E0DCD3;border-radius:8px;padding:1rem;margin-bottom:0.8rem;'>"
            f"<div style='font-size:0.85rem;font-weight:700;color:#D4A843;margin-bottom:0.5rem;'>"
            f"⚔️ Competitors → Targeting</div>"
            f"<div style='font-size:0.9rem;color:#2C3E50;line-height:1.5;'>"
            f"<strong>Your analysis:</strong> {comp_icon} {h(comp_r.get('user_option', '—'))}<br>"
            f"<strong>Your strategy:</strong> {tgt_icon} {h(tgt_r['user_option'])}<br>"
            f"<strong>Correct strategy:</strong> {h(tgt_r['correct_option'])}<br>"
            f"<span style='color:#5A6C7D;'>💡 {h(tgt_r['rubric'])}</span>"
            f"</div></div>"
        )

    # Company + Climate → Positioning
    company_r = analysis_results.get("company")
    climate_r = analysis_results.get("climate")
    pos_r = stp_results.get("positioning")
    if pos_r:
        company_str = ""
        if company_r:
            company_icon = "✅" if company_r.get("correct") else "❌"
            company_str = f"{company_icon} {h(company_r.get('user_option', '—'))}"
        climate_str = ""
        if climate_r:
            climate_icon = "✅" if climate_r.get("correct") else "❌"
            climate_str = f"{climate_icon} {h(climate_r.get('user_option', '—'))}"
        pos_icon = "✅" if pos_r["correct"] else "❌"
        analysis_parts = []
        if company_str:
            analysis_parts.append(f"<strong>Company:</strong> {company_str}")
        if climate_str:
            analysis_parts.append(f"<strong>Climate:</strong> {climate_str}")
        analysis_line = "<br>".join(analysis_parts) if analysis_parts else "—"
        trace_items.append(
            f"<div style='background:#FFFFFF;border:1px solid #E0DCD3;border-radius:8px;padding:1rem;margin-bottom:0.8rem;'>"
            f"<div style='font-size:0.85rem;font-weight:700;color:#D4A843;margin-bottom:0.5rem;'>"
            f"🏢 Company + 🌍 Climate → Positioning</div>"
            f"<div style='font-size:0.9rem;color:#2C3E50;line-height:1.5;'>"
            f"<strong>Your analysis:</strong><br>{analysis_line}<br>"
            f"<strong>Your strategy:</strong> {pos_icon} {h(pos_r['user_option'])}<br>"
            f"<strong>Correct strategy:</strong> {h(pos_r['correct_option'])}<br>"
            f"<span style='color:#5A6C7D;'>💡 {h(pos_r['rubric'])}</span>"
            f"</div></div>"
        )

    if trace_items:
        st.markdown("\n".join(trace_items), unsafe_allow_html=True)
    else:
        st.info("No analysis data available to build the decision trace.")

    # Mark complete button
    is_new = scenario["scenario_id"] not in st.session_state.progress.get("completed_scenarios", [])
    button_text = "✅ Mark Complete & Return to Desk" if is_new else "🔄 Update Progress & Return to Desk"

    if st.button(button_text, type="primary", use_container_width=True):
        save_scenario_progress(scenario, analysis_results, stp_results, cc_result, scenario_points)
        clear_resume_payload()
        st.session_state.phase = "next_steps"
        st.rerun()


def save_scenario_progress(scenario, analysis_results, stp_results, cc_result, scenario_points):
    progress = st.session_state.progress
    sid = scenario["scenario_id"]

    if sid not in progress["completed_scenarios"]:
        progress["completed_scenarios"].append(sid)

    # Snapshot the answers the user just submitted so the Review mode can
    # re-show them later without re-attempting.
    last_attempts = progress.setdefault("last_attempt_answers", {})
    last_attempts[str(sid)] = {
        "answers": dict(st.session_state.get("user_answers", {})),
        "score": scenario_points,
    }

    is_first_completion = str(sid) not in progress.get("scenario_scores", {})

    if is_first_completion:
        progress["scenario_scores"][str(sid)] = scenario_points
        progress["total_points"] = progress.get("total_points", 0) + scenario_points

        score = progress.get("total_score", {})

        for step in ANALYSIS_STEPS_ORDERED:
            key = f"analysis_{step}"
            if key not in score:
                score[key] = {"correct": 0, "total": 0}
            score[key]["total"] += 1
            if analysis_results.get(step, {}).get("correct", False):
                score[key]["correct"] += 1

        for step in STEPS_ORDERED:
            if step not in score:
                score[step] = {"correct": 0, "total": 0}
            score[step]["total"] += 1
            if stp_results[step]["correct"]:
                score[step]["correct"] += 1

        if "concept_check" not in score:
            score["concept_check"] = {"correct": 0, "total": 0}
        score["concept_check"]["total"] += 1
        if cc_result["correct"]:
            score["concept_check"]["correct"] += 1

        progress["total_score"] = score

    if scenario_points >= MASTER_THRESHOLD:
        if sid not in progress.get("mastered_scenarios", []):
            progress["mastered_scenarios"].append(sid)

    scenarios = st.session_state.scenarios
    max_tier = max(s["difficulty_tier"] for s in scenarios)
    for tier_num in range(1, max_tier + 1):
        if tier_num in progress["unlocked_tiers"]:
            tier_scenarios = [s for s in scenarios if s["difficulty_tier"] == tier_num]
            if tier_scenarios:
                tier_all_mastered = all(
                    s["scenario_id"] in progress.get("mastered_scenarios", [])
                    for s in tier_scenarios
                )
                if tier_all_mastered and (tier_num + 1) not in progress["unlocked_tiers"]:
                    progress["unlocked_tiers"].append(tier_num + 1)

    save_progress(progress)
    st.session_state.progress = progress


def render_next_steps():
    """Show scenario progression guidance after completing a scenario."""
    scenario = st.session_state.current_scenario
    if not scenario:
        st.session_state.phase = "selection"
        st.session_state.current_scenario = None
        st.rerun()
        return

    progress = st.session_state.progress
    sid = scenario["scenario_id"]
    scenario_points = progress.get("scenario_scores", {}).get(str(sid), 0)
    is_mastered = sid in progress.get("mastered_scenarios", [])
    scenarios = st.session_state.scenarios

    st.markdown('<div class="main-title">📋 Next Steps</div>', unsafe_allow_html=True)

    # Tier unlock check
    tier_num = scenario["difficulty_tier"]
    tier_scenarios = [s for s in scenarios if s["difficulty_tier"] == tier_num]
    tier_all_mastered = all(s["scenario_id"] in progress.get("mastered_scenarios", []) for s in tier_scenarios)
    next_tier_unlocked = (tier_num + 1) in progress.get("unlocked_tiers", [])

    if tier_all_mastered and not next_tier_unlocked and tier_num < 3:
        # This was the scenario that unlocked the next tier
        st.markdown(
            f'<div style="background:#F0F9F0;border:2px solid #27AE60;border-radius:10px;'
            f'padding:1.5rem;margin-bottom:1.5rem;text-align:center;">'
            f'<div style="font-size:1.5rem;margin-bottom:0.5rem;">🎉</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#27AE60;">'
            f'Tier {tier_num} Complete!</div>'
            f'<div style="font-size:0.95rem;color:#2C3E50;margin-top:0.5rem;">'
            f'You have unlocked <strong>Tier {tier_num + 1}</strong> — '
            f'{TIER_NAMES.get(tier_num + 1, "Advanced")} scenarios are now available.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Main guidance card
    with st.container(border=True):
        if is_mastered:
            st.markdown(
                '<div style="font-size:1.1rem;font-weight:700;color:#27AE60;margin-bottom:0.5rem;">'
                '✅ Scenario Mastered</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:0.95rem;color:#2C3E50;line-height:1.5;">'
                f'You scored <strong>{scenario_points} points</strong> on this scenario. '
                f'Great analytical work!</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:1.1rem;font-weight:700;color:#F39C12;margin-bottom:0.5rem;">'
                '⚠️ Keep Practicing</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:0.95rem;color:#2C3E50;line-height:1.5;">'
                f'You scored <strong>{scenario_points} points</strong>. '
                f'You need <strong>{MASTER_THRESHOLD} points</strong> to master this scenario. '
                f'Review the detailed results and try again.</div>',
                unsafe_allow_html=True,
            )

        # Recommend next scenario
        st.markdown("<div style='margin:1rem 0;border-top:1px solid #E0DCD3;'></div>", unsafe_allow_html=True)
        st.markdown("**Recommended next scenario:**")

        # Find next unmastered scenario in same tier
        unmastered_same_tier = [
            s for s in tier_scenarios
            if s["scenario_id"] not in progress.get("mastered_scenarios", [])
            and s["scenario_id"] != sid
        ]
        if unmastered_same_tier:
            next_scenario = unmastered_same_tier[0]
            st.markdown(
                f'<div style="background:#F8F7F4;border-radius:8px;padding:1rem;margin:0.5rem 0;">'
                f'<div style="font-weight:600;color:#1B2A4A;">{h(next_scenario["title"])}</div>'
                f'<div style="font-size:0.85rem;color:#5A6C7D;">'
                f'{h(next_scenario["scenario_type"])} | Tier {next_scenario["difficulty_tier"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("▶️ Start Next Scenario", type="primary", use_container_width=True):
                start_scenario(next_scenario["scenario_id"])
        else:
            # All in tier mastered, check next tier
            if next_tier_unlocked or tier_all_mastered:
                next_tier_scenarios = [s for s in scenarios if s["difficulty_tier"] == tier_num + 1]
                if next_tier_scenarios:
                    next_scenario = next_tier_scenarios[0]
                    st.markdown(
                        f'<div style="background:#F8F7F4;border-radius:8px;padding:1rem;margin:0.5rem 0;">'
                        f'<div style="font-weight:600;color:#1B2A4A;">{h(next_scenario["title"])}</div>'
                        f'<div style="font-size:0.85rem;color:#5A6C7D;">'
                        f'{h(next_scenario["scenario_type"])} | Tier {next_scenario["difficulty_tier"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("▶️ Start Next Scenario", type="primary", use_container_width=True):
                        start_scenario(next_scenario["scenario_id"])
                else:
                    st.markdown("You've completed all available scenarios. Great work!")
            else:
                st.markdown("All scenarios in this tier are completed. Master them to unlock the next tier.")

    # Focus area guidance
    if not is_mastered:
        st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)
        score = progress.get("total_score", {})
        weak_areas = []
        for step in ANALYSIS_STEPS_ORDERED:
            key = f"analysis_{step}"
            data = score.get(key, {"correct": 0, "total": 0})
            if data["total"] > 0 and data["correct"] < data["total"]:
                weak_areas.append(f"{step.title()} analysis")
        for step in STEPS_ORDERED:
            data = score.get(step, {"correct": 0, "total": 0})
            if data["total"] > 0 and data["correct"] < data["total"]:
                weak_areas.append(f"{step.title()} strategy")
        cc_data = score.get("concept_check", {"correct": 0, "total": 0})
        if cc_data["total"] > 0 and cc_data["correct"] < cc_data["total"]:
            weak_areas.append("Concept check")
        if weak_areas:
            st.markdown(
                f'<div style="background:#FFF8F0;border-left:4px solid #F39C12;'
                f'padding:1rem 1.5rem;border-radius:8px;font-size:0.95rem;'
                f'color:#2C3E50;line-height:1.5;">'
                f'<strong>🎯 Focus area:</strong> Your weakest areas are: '
                f'{", ".join(weak_areas[:2])}. '
                f'Review the rationale for each question in the scenario results before your next attempt.</div>',
                unsafe_allow_html=True,
            )

    # Return to desk button
    st.markdown("<div style='margin:1rem 0;'></div>", unsafe_allow_html=True)
    if st.button("← Return to Scenario Desk", type="secondary", use_container_width=True):
        st.session_state.phase = "selection"
        st.session_state.current_scenario = None
        st.rerun()
