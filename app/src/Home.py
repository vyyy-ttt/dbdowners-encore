##################################################
# Entry point for the Encore app.
#
# There is no real authentication yet. Each button
# below mimics logging in as one of the four roles
# the database schema describes, by setting the
# role in st.session_state and switching to that
# role's landing page.
##################################################

# Set up basic logging infrastructure
import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

# streamlit supports regular and wide layout (how the controls
# are organized/displayed on the screen).
st.set_page_config(layout='wide')

# If a user is at this page, we assume they are not authenticated.
st.session_state['authenticated'] = False

# Use the SideBarLinks function from src/modules/nav.py to control
# the links displayed on the left-side panel.
# IMPORTANT: ensure src/.streamlit/config.toml sets
# showSidebarNavigation = false in the [client] section
SideBarLinks(show_home=True)

# ***************************************************
#    The major content of this page
# ***************************************************

logger.info("Loading the Home page of the app")
st.title('Encore')
st.write('#### Hi! As which user would you like to log in?')

# The four roles come straight from the schema: user, venue_manager,
# tour_manager, and app_admin.

if st.button("Act as Maya, a Concertgoer",
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'user'
    st.session_state['first_name'] = 'Maya'
    logger.info("Logging in as Concertgoer persona")
    st.switch_page('pages/00_Concertgoer_Home.py')

if st.button("Act as Teddy, a Venue Manager",
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'venue_manager'
    st.session_state['first_name'] = 'Teddy'
    logger.info("Logging in as Venue Manager persona")
    st.switch_page('pages/10_Venue_Manager_Home.py')

if st.button("Act as Enrica, a Tour Manager",
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'tour_manager'
    st.session_state['first_name'] = 'Enrica'
    logger.info("Logging in as Tour Manager persona")
    st.switch_page('pages/20_Tour_Manager_Home.py')

if st.button("Act as Andy, an App Administrator",
             type='primary',
             use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'app_admin'
    st.session_state['first_name'] = 'Andy'
    logger.info("Logging in as App Administrator persona")
    st.switch_page('pages/30_Admin_Home.py')
