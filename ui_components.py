"""Small native Streamlit components and a restrained visual theme."""
import streamlit as st

CUSTOM_CSS = '''<style>
.block-container {max-width: 860px; padding-top: 2.5rem; padding-bottom: 3rem;}
h1,h2,h3 {letter-spacing:-.025em;}
h1 {font-family: Georgia,serif;}
a:focus-visible,button:focus-visible {outline:3px solid #9B6500;outline-offset:3px;}
@media(max-width:640px) {.block-container {padding:1.2rem 1rem 3rem;}}
</style>'''

GLOSSARY = {
'Company': 'What can this business credibly deliver? Consider capabilities, resources, and constraints.',
'Competitors': 'What alternatives could customers choose, including doing nothing?',
'Customers': 'Who has distinct needs, behaviors, or benefits sought?',
'Collaborators': 'Which partners and channels enable or constrain the offer?',
'Climate': 'Which broader trends and external constraints affect the decision?',
'Segmentation': 'Group customers by meaningful differences in needs or behavior.',
'Targeting': 'Choose which segment to serve, considering appeal, reach, and company fit.',
'Positioning': 'Define the distinctive value you want the target to associate with the offer.'}


def glossary():
    with st.expander('Concept guide'):
        term = st.selectbox('Explain a concept', list(GLOSSARY), key='glossary_term')
        st.write(GLOSSARY[term])


def go(page):
    st.switch_page(st.session_state.pages[page])
