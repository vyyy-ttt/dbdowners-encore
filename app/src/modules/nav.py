# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.
# The roles are the four personas from the design document: the concertgoer
# (Maya), venue_manager (Teddy), tour_manager (Enrica), and app_admin (Andy).

import base64
from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


@st.cache_data(show_spinner=False)
def _logo_data_uri():
    """Inline the logo so the brand block is one centred unit.

    st.sidebar.image() renders in its own container that needs extra CSS to
    centre, and that CSS is only injected on pages using modules.theme. Inlining
    the PNG keeps the logo centred with the wordmark on every page.
    """
    try:
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    except OSError:
        return None
    return f"data:image/png;base64,{encoded}"


def brand_header():
    """Centred logo with the Encore wordmark beneath it."""
    data_uri = _logo_data_uri()

    if data_uri is None:
        # Missing asset should not take the whole sidebar down with it
        st.sidebar.markdown(
            "<div style='text-align:center;font-size:1.3rem;font-weight:800;"
            "letter-spacing:-0.02em;margin:0.6rem 0 1.1rem 0;'>Encore</div>",
            unsafe_allow_html=True,
        )
        return

    st.sidebar.markdown(
        f"""
        <div style="text-align:center;margin:0.4rem 0 1.2rem 0;">
          <img src="{data_uri}" width="74"
               style="display:block;margin:0 auto 0.45rem auto;
                      border-radius:18px;" alt="Encore logo" />
          <div style="font-size:1.3rem;font-weight:800;letter-spacing:-0.02em;
                      line-height:1;">Encore</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


# ---- Role: user (concertgoer) -----------------------------------------------

def concertgoer_home_nav():
    st.sidebar.page_link(
        "pages/00_Concertgoer_Home.py", label="Concertgoer Home", icon="🎟️"
    )


# ---- Role: casual_concertgoer (Maya) ----------------------------------------

def maya_home_nav():
    st.sidebar.page_link("pages/00_Maya_Home.py", label="Concertgoer Home", icon="🎟️")


def maya_log_review_nav():
    st.sidebar.page_link("pages/01_Maya_Log_Review.py", label="Log & Review", icon="✍️")


def maya_profile_nav():
    st.sidebar.page_link("pages/02_Maya_Profile.py", label="My Profile", icon="👤")


def maya_search_nav():
    st.sidebar.page_link("pages/03_Maya_Search.py", label="Search Shows", icon="🔎")


# ---- Role: venue_manager (Teddy) --------------------------------------------

def venue_manager_home_nav():
    st.sidebar.page_link(
        "pages/10_Venue_Manager_Home.py", label="Venue Manager Home", icon="🏟️"
    )


# ---- Role: tour_manager (Enrica) --------------------------------------------

def tour_manager_home_nav():
    st.sidebar.page_link(
        "pages/20_Tour_Manager_Home.py", label="Tour Insights", icon="🚌"
    )


def tour_reviews_nav():
    st.sidebar.page_link(
        "pages/21_Tour_Reviews.py", label="Tour Reviews", icon="💬"
    )


def tour_performance_nav():
    st.sidebar.page_link(
        "pages/22_Tour_Performance.py", label="Tour Performance", icon="📈"
    )


# ---- Role: app_admin (Andy) -------------------------------------------------

def admin_home_nav():
    st.sidebar.page_link("pages/30_Admin_Home.py", label="Admin Home", icon="🖥️")


def api_endpoint_tester_nav():
    st.sidebar.page_link(
        "pages/31_API_Endpoint_Tester.py", label="API Endpoint Tester", icon="🧪"
    )


# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    # Brand mark at the top of the sidebar on every page. The logo is a
    # transparent PNG so it sits on the dark sidebar without a white box.
    brand_header()

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "user":
            concertgoer_home_nav()

        if st.session_state["role"] == "casual_concertgoer":
            maya_home_nav()
            maya_log_review_nav()
            maya_profile_nav()
            maya_search_nav()

        if st.session_state["role"] == "venue_manager":
            venue_manager_home_nav()

        if st.session_state["role"] == "tour_manager":
            tour_manager_home_nav()
            tour_reviews_nav()
            tour_performance_nav()

        if st.session_state["role"] == "app_admin":
            admin_home_nav()
            api_endpoint_tester_nav()

    # There are no real accounts. This just clears the chosen persona and
    # returns to the picker on Home.py.
    if st.session_state["authenticated"]:
        if st.sidebar.button("Switch persona", use_container_width=True):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
