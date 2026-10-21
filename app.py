"""CMO Desk: private-by-default guided learning on Streamlit Community Cloud."""
import hashlib
import json
import streamlit as st
from data import load_scenarios
from learning import default_progress
from ui_components import CUSTOM_CSS
from ui_sidebar import render_sidebar
from ui_scenario import render_home, render_catalog, render_workspace
from ui_learning import render_notebook, render_progress, render_review, render_settings
from utils.persistence import browser_store, make_payload, validate_payload

st.set_page_config(page_title='CMO Desk', page_icon='📋', layout='centered')


def init_state():
    defaults = {'progress': default_progress(), 'draft': None, 'remember': False,
                'storage_ready': False, 'storage_clear_pending': False}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state.scenarios = load_scenarios()


def bootstrap_storage():
    if st.session_state.storage_ready:
        return
    st.title('Welcome to CMO Desk')
    st.caption('Checking this browser for learning you previously chose to save…')
    result = browser_store(operation='read', token='initial-read', key='browser_store', default=None)
    if result and result.get('token') == 'initial-read':
        if result.get('ok') and result.get('payload'):
            try:
                restored = validate_payload(result['payload'], st.session_state.scenarios)
                st.session_state.progress = restored['progress']
                st.session_state.draft = restored['draft']
                st.session_state.remember = True
            except (ValueError, KeyError, TypeError, AttributeError, OverflowError, RecursionError):
                st.session_state.storage_notice = 'Saved browser data could not be restored. It has not been overwritten. You can start a new session or restore a backup in Settings.'
        elif not result.get('ok'):
            st.session_state.storage_notice = 'Browser storage is unavailable. You can use the app in session mode and download backups in Settings.'
        st.session_state.storage_ready = True
        st.rerun()
    if st.button('Continue without restoring browser data'):
        st.session_state.storage_ready = True
        st.rerun()
    st.stop()


def sync_storage():
    if st.session_state.storage_clear_pending:
        operation, token, payload = 'clear', 'clear-learning', None
    elif st.session_state.remember:
        payload = make_payload(st.session_state.progress, st.session_state.draft)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        operation, token = 'write', digest
    else:
        operation, token, payload = 'idle', 'session-only', None
    result = browser_store(operation=operation, token=token, payload=payload, key='browser_store', default=None)
    if result and result.get('token') == token:
        if not result.get('ok'):
            st.warning('Browser saving is unavailable. Download a backup in Settings to keep your work.')
        elif operation == 'clear':
            st.session_state.storage_clear_pending = False
            st.session_state.storage_cleared = True
            st.rerun()
    if st.session_state.get('storage_cleared'):
        st.caption('Browser-saved learning data removed.')


def main():
    init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    pages = {
        'Home': st.Page(render_home, title='Home', icon=':material/home:', default=True),
        'Cases': st.Page(render_catalog, title='Cases', url_path='cases', icon=':material/explore:'),
        'Case workspace': st.Page(render_workspace, title='Case workspace', url_path='case', icon=':material/edit_note:'),
        'Notebook': st.Page(render_notebook, title='Notebook', url_path='notebook', icon=':material/book:'),
        'Review': st.Page(render_review, title='Review', url_path='review', icon=':material/psychology:'),
        'Progress': st.Page(render_progress, title='Progress', url_path='progress', icon=':material/trending_up:'),
        'Settings': st.Page(render_settings, title='Settings', icon=':material/settings:', url_path='settings'),
    }
    st.session_state.pages = pages
    page = st.navigation(list(pages.values()))
    bootstrap_storage()
    render_sidebar()
    if st.session_state.get('storage_notice'):
        st.info(st.session_state.storage_notice)
    page.run()
    sync_storage()
    st.divider()
    st.caption('CMO Desk · Free, open-source learning · No account required')
    st.markdown('[Source code](https://github.com/KaramelBytes/CMO-learning-desk) · [Your data and settings](/settings)')


if __name__ == '__main__':
    main()
