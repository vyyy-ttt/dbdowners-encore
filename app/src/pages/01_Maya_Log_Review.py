import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section, stars, chip

st.set_page_config(layout='wide', page_title="Encore | Log & Review")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

# In the mock app, Maya is user_id 1 (see seed data in the DDL).
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


page_header("Log & Review", f"Welcome back, {st.session_state['first_name']}!")

tab_write, tab_manage = st.tabs(["Write a Review", "My Reviews"])

# ---------------------------------------------------------------
# Write a review  ->  POST /review/reviews   (User Story 1.1)
# ---------------------------------------------------------------
with tab_write:
    section("Write a new review")

    target_type = st.radio(
        "What are you reviewing?",
        ["Artist", "Show", "Venue"],
        horizontal=True,
    )

    # Pull shows once and derive artist / venue / show options from them.
    options = {}
    shows = get_json("/maya/shows") or []
    if target_type == "Show":
        options = {
            f"{s['artist_name']} @ {s['venue_name']} ({s['show_date']})": s["show_id"]
            for s in shows
        }
    elif target_type == "Venue":
        options = {s["venue_name"]: s["venue_id"] for s in shows}
    else:  # Artist
        options = {s["artist_name"]: s["artist_id"] for s in shows}

    with st.form("write_review_form"):
        choice = st.selectbox(f"Choose a {target_type.lower()}", ["--"] + list(options.keys()))
        rating = st.slider("Rating", 1, 5, 4)
        review_text = st.text_area("Your review")
        submitted = st.form_submit_button("Post Review", type="primary")

        if submitted:
            if choice == "--":
                st.error(f"Please choose a {target_type.lower()}.")
            else:
                payload = {
                    "author_user_id": USER_ID,
                    "rating": rating,
                    "review_text": review_text,
                }
                key = {"Artist": "about_artist_id",
                       "Show": "about_show_id",
                       "Venue": "about_venue_id"}[target_type]
                payload[key] = options[choice]

                try:
                    r = requests.post(f"{API}/review/reviews", json=payload, timeout=10)
                    if r.status_code == 201:
                        st.success("Review posted!")
                    else:
                        st.error(r.json().get("error", "Failed to post review."))
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the API: {e}")

# ---------------------------------------------------------------
# Manage reviews  ->  PUT / DELETE /maya/reviews/<id>  (1.4 + 1.1)
# ---------------------------------------------------------------
with tab_manage:
    section("My reviews")

    reviews = get_json(f"/maya/users/{USER_ID}/reviews") or []

    if not reviews:
        st.info("You haven't written any reviews yet.")

    for rev in reviews:
        target = rev.get("about_artist") or rev.get("about_venue") or "a show"
        st.markdown(
            f"""
            <div class="enc-card">
              <div class="enc-card-top">
                <span>{stars(rev['rating'])}</span>
                <span class="enc-meta">about {target}</span>
              </div>
              <div class="enc-quote">{rev.get('review_text') or '<em>No text</em>'}</div>
              <div class="enc-meta">Last updated: {rev.get('last_updated') or '—'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Edit / delete"):
            new_rating = st.slider(
                "Update rating", 1, 5, int(rev["rating"]),
                key=f"rating_{rev['review_id']}",
            )
            new_text = st.text_area(
                "Update text", rev.get("review_text") or "",
                key=f"text_{rev['review_id']}",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save changes", key=f"save_{rev['review_id']}",
                             type="primary", use_container_width=True):
                    try:
                        r = requests.put(
                            f"{API}/review/reviews/{rev['review_id']}",
                            json={"rating": new_rating, "review_text": new_text},
                            timeout=10,
                        )
                        if r.status_code == 200:
                            st.success("Review updated!")
                            st.rerun()
                        else:
                            st.error(r.json().get("error", "Update failed."))
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error connecting to the API: {e}")
            with col2:
                if st.button("Delete review", key=f"del_{rev['review_id']}",
                             use_container_width=True):
                    try:
                        r = requests.delete(
                            f"{API}/review/reviews/{rev['review_id']}", timeout=10)
                        if r.status_code == 200:
                            st.success("Review deleted.")
                            st.rerun()
                        else:
                            st.error(r.json().get("error", "Delete failed."))
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error connecting to the API: {e}")