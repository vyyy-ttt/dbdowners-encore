import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title(f"Welcome back, {st.session_state['first_name']}.")

st.write(
    "This is the venue manager landing page. Venue stats, review responses, "
    "attendance trends, tag breakdowns, and the transportation methods for a "
    "venue all belong here."
)

st.info(
    "The transportation routes are live, but the venue routes they pair with "
    "are not written yet, so there is nothing to browse from here so far.",
    icon="🚧",
)
