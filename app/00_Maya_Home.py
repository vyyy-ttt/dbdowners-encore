import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show the sidebar links for Maya's role
SideBarLinks()

st.title(f"Welcome back, {st.session_state['first_name']}!")
st.write('### What would you like to do today?')

if st.button('Log & Review a Show',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/01_Maya_Log_Review.py')

if st.button('My Profile & Concert Stats',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/02_Maya_Profile.py')

if st.button('Search Shows & Plan My Night',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/03_Maya_Search.py')