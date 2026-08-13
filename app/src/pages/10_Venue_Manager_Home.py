import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, tile

st.set_page_config(layout='wide', page_title="Encore | Venue Manager Home")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

VM_ID = st.session_state.get("vm_id", 1)

page_header("Venue Manager Home", f"Welcome back, {st.session_state['first_name']}!")


def get_json(path, params=None):
    try:
        response = requests.get(f"{API}{path}", params=params, timeout=10)
    except requests.exceptions.RequestException:
        return None
    if response.status_code != 200:
        return None
    return response.json()


venues = get_json(f"/venue_manager/venue_managers/{VM_ID}/venues") or []

# A quick read on the portfolio before drilling into any one room
review_total = 0
awaiting = 0
for venue in venues:
    reviews = get_json("/review/reviews", params={"about_venue_id": venue["venue_id"]}) or []
    review_total += len(reviews)
    awaiting += sum(1 for r in reviews if not r.get("vm_response"))

t1, t2, t3 = st.columns(3)
with t1:
    tile("Venues", f"{len(venues)}", sub="under your management", empty=not venues)
with t2:
    tile("Venue reviews", f"{review_total}", sub="written about your rooms",
         empty=not review_total)
with t3:
    tile("Awaiting reply", f"{awaiting}", sub="no response yet", empty=not awaiting)

st.write("")
st.write("### What would you like to do?")

if st.button("Venue Overview", type='primary', use_container_width=True):
    st.switch_page('pages/11_Venue_Overview.py')
st.caption("Ratings by category, attendance over time, and how you compare to similar venues.")

if st.button("Venue Reviews", type='primary', use_container_width=True):
    st.switch_page('pages/12_Venue_Reviews.py')
st.caption("Read feedback by show date, reply publicly, or flag a review as inaccurate.")

if st.button("Venue Details", type='primary', use_container_width=True):
    st.switch_page('pages/13_Venue_Details.py')
st.caption("Keep the listing, the transport options, and your contact details current.")
