import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome back, {st.session_state['first_name']}.")

st.write(
    "This is the tour manager landing page. Tour rosters, per-tour stats across "
    "every show, and responses to reviews about a tour all belong here."
)

st.info(
    "No tour routes exist in the API yet. The pages arrive as the route files land.",
    icon="🚧",
)
