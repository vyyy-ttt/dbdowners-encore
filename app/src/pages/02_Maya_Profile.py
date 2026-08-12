import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

API = "http://web-api:4000/maya"
USER_ID = st.session_state.get("user_id", 1)

st.title(f"{st.session_state['first_name']}'s Profile")

# ---------------------------------------------------------------
# Concert stats  ->  GET /maya/users/<id>/stats   (User Story 1.2)
# ---------------------------------------------------------------
st.subheader("My Concert Stats")
try:
    stats = requests.get(f"{API}/users/{USER_ID}/stats").json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Shows Attended", stats.get("total_shows_attended", 0))
    avg = stats.get("average_ticket_price", 0) or 0
    c2.metric("Avg Ticket Price", f"${avg:,.2f}")
    most = stats.get("most_seen_artist") or "—"
    c3.metric("Most-Seen Artist", most,
              f"{stats.get('most_seen_count', 0)}x" if stats.get("most_seen_count") else None)
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {e}")

st.divider()

# ---------------------------------------------------------------
# Following management  ->  GET / POST / DELETE follows  (1.3)
# ---------------------------------------------------------------
st.subheader("Friends I Follow")

col_left, col_right = st.columns([2, 1])

with col_left:
    try:
        following = requests.get(f"{API}/users/{USER_ID}/following").json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {e}")
        following = []

    if not following:
        st.info("You're not following anyone yet.")
    for f in following:
        fc1, fc2 = st.columns([3, 1])
        fc1.write(f"**@{f['username']}** — {f['first_name']} {f['last_name']}")
        if fc2.button("Unfollow", key=f"unfollow_{f['user_id']}"):
            try:
                r = requests.delete(f"{API}/follows/{USER_ID}/{f['user_id']}")
                if r.status_code == 200:
                    st.success(f"Unfollowed @{f['username']}")
                    st.rerun()
                else:
                    st.error(r.json().get("error", "Unfollow failed."))
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")

with col_right:
    st.write("**Follow someone new**")
    with st.form("follow_form"):
        followee_id = st.number_input("Their user ID", min_value=1, step=1)
        if st.form_submit_button("Follow"):
            try:
                r = requests.post(
                    f"{API}/follows",
                    json={"follower_id": USER_ID, "followee_id": int(followee_id)},
                )
                if r.status_code == 201:
                    st.success("Now following!")
                    st.rerun()
                else:
                    st.error(r.json().get("error", "Follow failed."))
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")

st.divider()

# ---------------------------------------------------------------
# Friends' recent reviews  ->  GET /maya/users/<id>/friends-reviews  (1.3)
# ---------------------------------------------------------------
st.subheader("What My Friends Are Saying")
try:
    friend_reviews = requests.get(f"{API}/users/{USER_ID}/friends-reviews").json()
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {e}")
    friend_reviews = []

if not friend_reviews:
    st.info("No reviews from people you follow yet.")
for rev in friend_reviews:
    target = rev.get("about_artist") or rev.get("about_venue") or "a show"
    st.markdown(f"**@{rev['username']}** rated {target} **{rev['rating']}/5**")
    if rev.get("review_text"):
        st.caption(rev["review_text"])
        