import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

API = "http://web-api:4000/maya"
USER_ID = st.session_state.get("user_id", 1)

st.title("Search Shows & Plan My Night")

# ---------------------------------------------------------------
# Search  ->  GET /maya/shows?city=&from_date=   (User Story 1.5)
# ---------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    city = st.text_input("City (leave blank for all)")
with col2:
    from_date = st.date_input("On or after", value=None)

params = {}
if city:
    params["city"] = city
if from_date:
    params["from_date"] = from_date.isoformat()

try:
    shows = requests.get(f"{API}/shows", params=params).json()
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {e}")
    shows = []

st.write(f"Found {len(shows)} show(s)")

for s in shows:
    with st.expander(
        f"{s['artist_name']} — {s['venue_name']}, {s['city']} ({s['show_date']})"
    ):
        st.write(f"**Tour:** {s['tour_name']}")
        st.write(f"**Start:** {s['start_time']}  |  **Avg ticket:** ${s['avg_ticket_price']}")

        # 1.6 — transportation + accessibility for this venue
        if st.button("Plan my night (transit & accessibility)",
                     key=f"plan_{s['show_id']}"):
            try:
                info = requests.get(
                    f"{API}/venues/{s['venue_id']}/transportation"
                ).json()
                st.write(f"**Accessibility:** {info.get('accessibility', 'N/A')}")
                transit = info.get("transportation", [])
                if transit:
                    st.write("**Getting there:**")
                    for t in transit:
                        st.write(
                            f"- {t['transport_type']} "
                            f"(~${t['estimated_cost']}): {t['instructions']}"
                        )
                else:
                    st.info("No transportation info listed for this venue.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")

        # 1.5 — log that Maya attended this show
        if st.button("Log this show", key=f"log_{s['show_id']}"):
            try:
                r = requests.post(
                    f"{API}/users/{USER_ID}/shows",
                    json={"show_id": s["show_id"]},
                )
                if r.status_code == 201:
                    st.success("Added to your concert history!")
                else:
                    st.error(r.json().get("error", "Couldn't log show."))
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")
                