import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section, chip

st.set_page_config(layout='wide', page_title="Encore | Search Shows")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"
USER_ID = st.session_state.get("user_id", 1)


def get_json(path, params=None):
    try:
        response = requests.get(f"{API}{path}", params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API}: {e}")
        return None
    if response.status_code != 200:
        st.warning(f"`GET {path}` returned {response.status_code}.")
        return None
    return response.json()


page_header("Search Shows", f"Welcome back, {st.session_state['first_name']}!")

# ---------------------------------------------------------------
# Search  ->  GET /maya/shows?city=&from_date=   (User Story 1.5)
# ---------------------------------------------------------------
section("Find a show")

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

shows = get_json("/maya/shows", params=params) or []

st.caption(f"Found {len(shows)} show(s)")

for s in shows:
    st.markdown(
        f"""
        <div class="enc-card">
          <div class="enc-card-top">
            <span><strong>{s['artist_name']}</strong> · {s['tour_name']}</span>
            <span class="enc-meta">${s['avg_ticket_price']}</span>
          </div>
          <div class="enc-meta">
            {s['venue_name']}, {s['city']} · {s['show_date']} at {s['start_time']}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Plan my night & log this show"):
        # 1.6 — transportation + accessibility for this venue
        if st.button("Show transit & accessibility",
                     key=f"plan_{s['show_id']}", use_container_width=True):
            info = get_json(f"/maya/venues/{s['venue_id']}/transportation")
            if info:
                st.markdown(
                    f"**Accessibility:** {info.get('accessibility', 'N/A')}"
                )
                transit = info.get("transportation", [])
                if transit:
                    st.markdown("**Getting there:**")
                    for t in transit:
                        st.markdown(
                            f"- {t['transport_type']} "
                            f"(~${t['estimated_cost']}): {t['instructions']}"
                        )
                else:
                    st.info("No transportation info listed for this venue.")

        # 1.5 — log that Maya attended this show
        if st.button("Log this show", key=f"log_{s['show_id']}",
                     type="primary", use_container_width=True):
            try:
                r = requests.post(
                    f"{API}/maya/users/{USER_ID}/shows",
                    json={"show_id": s["show_id"]},
                    timeout=10,
                )
                if r.status_code == 201:
                    st.success("Added to your concert history!")
                else:
                    st.error(r.json().get("error", "Couldn't log show."))
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")