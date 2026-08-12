import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome back, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('Test API Endpoints',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/31_API_Endpoint_Tester.py')

st.caption(
    "Report moderation and user suspension belong to this role too, but those "
    "routes are not written yet."
)
