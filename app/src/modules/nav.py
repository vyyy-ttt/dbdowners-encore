# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.
# The roles match the ones in the database schema: user, venue_manager,
# tour_manager, and app_admin.

import streamlit as st


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/40_About.py", label="About", icon="🧠")


# ---- Role: user (concertgoer) ------------------------------------------------

def concertgoer_home_nav():
    st.sidebar.page_link(
        "pages/00_Concertgoer_Home.py", label="Concertgoer Home", icon="🎟️"
    )


# ---- Role: venue_manager ----------------------------------------------------

def venue_manager_home_nav():
    st.sidebar.page_link(
        "pages/10_Venue_Manager_Home.py", label="Venue Manager Home", icon="🏟️"
    )


# ---- Role: tour_manager -----------------------------------------------------

def tour_manager_home_nav():
    st.sidebar.page_link(
        "pages/20_Tour_Manager_Home.py", label="Tour Manager Home", icon="🚌"
    )


# ---- Role: app_admin --------------------------------------------------------

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

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/logo.png", width=150)

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "user":
            concertgoer_home_nav()

        if st.session_state["role"] == "venue_manager":
            venue_manager_home_nav()

        if st.session_state["role"] == "tour_manager":
            tour_manager_home_nav()

        if st.session_state["role"] == "app_admin":
            admin_home_nav()
            api_endpoint_tester_nav()

    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
