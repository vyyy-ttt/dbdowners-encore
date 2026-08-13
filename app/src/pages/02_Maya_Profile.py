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
#   GET    /follower/followers/<id>
#   POST   /follower/follow/<a>/<b>
#   DELETE /follower/follow/<a>/<b>
# ---------------------------------------------------------------
following = get_json(f"/follower/following/{USER_ID}") or []
followers = get_json(f"/follower/followers/{USER_ID}") or []

section("My circle")

c1, c2 = st.columns(2)
with c1:
    tile("Following", f"{len(following)}", sub="people you follow",
         empty=not following)
with c2:
    tile("Followers", f"{len(followers)}", sub="people following you",
         empty=not followers)

if followers:
    st.caption(
        "Following you: "
        + ", ".join(f"@{f['username']}" for f in followers[:8])
        + (" and more" if len(followers) > 8 else "")
    )

st.write("")
section("Friends I follow")

col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
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

        # Pull every user, then drop yourself and anyone you already follow
        all_users = get_json("/maya/users") or []
        already_following = {f["user_id"] for f in following}
        candidates = [
            u for u in all_users
            if u["user_id"] != USER_ID and u["user_id"] not in already_following
        ]

        if not candidates:
            st.caption("No one new to follow right now.")
        else:
            # Label shown to the user -> hidden user_id we actually send
            name_to_id = {
                f"{u.get('first_name', '')} {u.get('last_name', '')} (@{u['username']})".strip(): u["user_id"]
                for u in candidates
            }
            with st.form("follow_form"):
                choice = st.selectbox(
                    "Who do you want to follow?", list(name_to_id.keys())
                )
                if st.form_submit_button("Follow", type="primary",
                                         use_container_width=True):
                    followee_id = name_to_id[choice]
                    try:
                        r = requests.post(
                            f"{API}/follower/follow/{USER_ID}/{followee_id}",
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