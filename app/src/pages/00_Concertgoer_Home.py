import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome back, {st.session_state['first_name']}.")

st.write(
    "This is the concertgoer landing page. Reviews, diary entries, following "
    "other users, and venue transport details all belong here."
)

st.info(
    "No concertgoer routes exist in the API yet. The pages arrive as the route "
    "files land — see the resources table for what each one owes this role.",
    icon="🚧",
)
