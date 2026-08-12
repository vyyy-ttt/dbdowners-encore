import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.write("# About Encore")

st.markdown(
    """
    Encore is a concert review app built for the CS 3200 Summer B 2026 Database
    Design Project Course.

    Concertgoers review the shows, venues, and artists they see, keep a private
    diary of what they attended, and follow each other. Venue and tour managers
    respond to those reviews and read the aggregated stats behind them. App
    administrators handle reports and moderation.

    **Stack:** a Streamlit front end, a Flask REST API, and a MySQL database,
    each in its own Docker container.
    """
)

st.markdown(
    """
    #### Implemented so far

    | Blueprint | Prefix | Routes |
    | --- | --- | --- |
    | `transport_routes.py` | `/transport` | 8 |
    | `tag_routes.py` | `/tag` | 5 |
    | `report_routes.py` | `/report` | 5 |

    The API Endpoint Tester page, available to the administrator role, exercises
    the transportation and tag routes directly.
    """
)

# Add a button to return to home page
if st.button("Return to Home", type="primary"):
    st.switch_page("Home.py")
