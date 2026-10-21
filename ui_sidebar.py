import streamlit as st
from ui_components import glossary


def render_sidebar():
    with st.sidebar:
        st.caption('CMO DESK · LEARN BY DECIDING')
        draft = st.session_state.draft
        if draft:
            scenario = next(s for s in st.session_state.scenarios if s['scenario_id'] == draft['scenario_id'])
            st.write('**Your active case**')
            st.write(scenario['title'])
            st.progress(min(draft['step'] / 11, 1), text=f"Task {min(draft['step'] + 1, 12)} of 12")
        glossary()
        st.caption('Progress stays in this session unless you enable browser saving in Settings.')
