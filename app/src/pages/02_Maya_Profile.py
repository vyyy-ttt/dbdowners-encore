import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section, tile, stars

st.set_page_config(layout='wide', page_title="Encore | My Profile")

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


def as_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


page_header("My Profile", f"Welcome back, {st.session_state['first_name']}!")

# ---------------------------------------------------------------
# Concert stats  ->  GET /maya/users/<id>/stats   (User Story 1.2)
# ---------------------------------------------------------------
section("My concert stats")

stats = get_json(f"/maya/users/{USER_ID}/stats") or {}

t1, t2, t3 = st.columns(3)
with t1:
    total = stats.get("total_shows_attended", 0)
    tile("Shows attended", f"{total}", sub="in your history", empty=not total)
with t2:
    avg = as_float(stats.get("average_ticket_price"))
    tile(
        "Avg ticket price",
        f"${avg:,.2f}" if avg else "n/a",
        sub="across attended shows",
        empty=not avg,
    )
with t3:
    most = stats.get("most_seen_artist")
    tile(
        "Most-seen artist",
        most or "n/a",
        sub=f"{stats.get('most_seen_count', 0)} shows" if most else "no data yet",
        empty=most is None,
        text_value=True,
    )

st.write("")

# ---------------------------------------------------------------
# Following management  ->  followers blueprint  (User Story 1.3)
#   GET    /follower/following/<id>
#   POST   /follower/follow/<a>/<b>
#   DELETE /follower/follow/<a>/<b>
# ---------------------------------------------------------------
section("Friends I follow")

col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    following = get_json(f"/follower/following/{USER_ID}") or []

    if not following:
        st.info("You're not following anyone yet.")
    for f in following:
        fc1, fc2 = st.columns([3, 1])
        fc1.markdown(
            f"**@{f['username']}** — {f.get('first_name', '')} {f.get('last_name', '')}"
        )
        if fc2.button("Unfollow", key=f"unfollow_{f['user_id']}",
                      use_container_width=True):
            try:
                r = requests.delete(
                    f"{API}/follower/follow/{USER_ID}/{f['user_id']}", timeout=10)
                if r.status_code == 200:
                    st.success(f"Unfollowed @{f['username']}")
                    st.rerun()
                else:
                    st.error(r.json().get("error", "Unfollow failed."))
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")

with col_right:
    with st.container(border=True):
        st.markdown("**Follow someone new**")
        with st.form("follow_form"):
            followee_id = st.number_input("Their user ID", min_value=1, step=1)
            if st.form_submit_button("Follow", type="primary",
                                     use_container_width=True):
                try:
                    r = requests.post(
                        f"{API}/follower/follow/{USER_ID}/{int(followee_id)}",
                        timeout=10,
                    )
                    if r.status_code == 201:
                        st.success("Now following!")
                        st.rerun()
                    else:
                        st.error(r.json().get("error", "Follow failed."))
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the API: {e}")

st.write("")

# ---------------------------------------------------------------
# Friends' recent reviews  ->  GET /maya/users/<id>/friends-reviews  (1.3)
# ---------------------------------------------------------------
section("What my friends are saying")

friend_reviews = get_json(f"/maya/users/{USER_ID}/friends-reviews") or []

if not friend_reviews:
    st.info("No reviews from people you follow yet.")
for rev in friend_reviews:
    target = rev.get("about_artist") or rev.get("about_venue") or "a show"
    st.markdown(
        f"""
        <div class="enc-card">
          <div class="enc-card-top">
            <span><strong>@{rev['username']}</strong> · about {target}</span>
            <span>{stars(rev['rating'])}</span>
          </div>
          <div class="enc-quote">{rev.get('review_text') or ''}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )