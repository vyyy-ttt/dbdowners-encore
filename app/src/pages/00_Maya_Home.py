import logging
logger = logging.getLogger(__name__)

import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section

st.set_page_config(layout='wide', page_title="Encore | Concertgoer Home")

SideBarLinks()
apply_theme()

page_header("Concertgoer Home", f"Welcome back, {st.session_state['first_name']}!")

section("What would you like to do?")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown("### ✍️ Log & Review")
        st.write("Write, update, or delete reviews for the artists, shows, and venues you've seen.")
        if st.button("Open", key="go_review", type="primary", use_container_width=True):
            st.switch_page("pages/01_Maya_Log_Review.py")

with c2:
    with st.container(border=True):
        st.markdown("### 👤 My Profile")
        st.write("See your concert stats, manage who you follow, and read your friends' reviews.")
        if st.button("Open", key="go_profile", type="primary", use_container_width=True):
            st.switch_page("pages/02_Maya_Profile.py")

with c3:
    with st.container(border=True):
        st.markdown("### 🔎 Search Shows")
        st.write("Find upcoming shows, plan transit and accessibility, and log the ones you attend.")
        if st.button("Open", key="go_search", type="primary", use_container_width=True):
            st.switch_page("pages/03_Maya_Search.py")