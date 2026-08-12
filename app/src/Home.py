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
from modules.theme import apply_theme

# streamlit supports regular and wide layout (how the controls
# are organized/displayed on the screen).
st.set_page_config(layout='wide', page_title="Encore")

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

apply_theme()

# Centre the sign-in card rather than letting it stretch across a wide screen.
_, middle, _ = st.columns([1, 2, 1])

with middle:
    st.markdown(
        """
        <div style="text-align:center;margin:1.5rem 0 0.4rem 0;">
          <div style="font-size:3rem;font-weight:800;letter-spacing:-0.03em;
                      color:#7C4DFF;line-height:1;">Encore</div>
          <p style="color:#6B6C85;font-size:1.02rem;margin:0.6rem 0 0 0;">
            Rate every layer of a live show: the artist, the openers,
            and the venue itself.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown(
        '<div class="enc-section" style="text-align:center;margin-bottom:0.2rem;">'
        'Pick a persona to explore</div>'
        '<p style="text-align:center;color:#6B6C85;font-size:0.88rem;'
        'margin:0 0 1.1rem 0;">No account needed. Each persona just switches '
        'which view of the app you see.</p>',
        unsafe_allow_html=True,
    )

# The four roles are the personas from the design document.

with middle:
    if st.button("Maya, Casual Concertgoer",
                 type='primary',
                 use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'user'
        st.session_state['first_name'] = 'Maya'
        logger.info("Switching to the Concertgoer persona")
        st.switch_page('pages/00_Concertgoer_Home.py')
    st.caption("Logs the shows she attends and reviews the artist, venue, and night.")

    if st.button("Teddy, Venue Manager at Fenway Park",
                 type='primary',
                 use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'venue_manager'
        st.session_state['first_name'] = 'Teddy'
        logger.info("Switching to the Venue Manager persona")
        st.switch_page('pages/10_Venue_Manager_Home.py')
    st.caption("Reads structured feedback about his venue and replies to it.")

    if st.button("Enrica, Tour Manager",
                 type='primary',
                 use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'tour_manager'
        st.session_state['first_name'] = 'Enrica'
        # Enrica is tour_manager tm_id 1 in the seed data; her pages attribute
        # responses to this id.
        st.session_state['tm_id'] = 1
        logger.info("Switching to the Tour Manager persona")
        st.switch_page('pages/20_Tour_Manager_Home.py')
    st.caption("Compares fan sentiment venue by venue and responds for the artist.")

    if st.button("Andy, App Administrator",
                 type='primary',
                 use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'app_admin'
        st.session_state['first_name'] = 'Andy'
        logger.info("Switching to the App Administrator persona")
        st.switch_page('pages/30_Admin_Home.py')
    st.caption("Keeps the platform clean: reports, moderation, and app health.")
