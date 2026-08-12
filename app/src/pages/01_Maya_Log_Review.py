import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

API = "http://web-api:4000/maya"

# In the mock app, Maya is user_id 1 (see seed data in the DDL).
USER_ID = st.session_state.get("user_id", 1)

st.title("Log & Review a Show")
st.write("Write a new review, or update / delete one of your existing reviews.")

tab_write, tab_manage = st.tabs(["Write a Review", "My Reviews"])

# ---------------------------------------------------------------
# Write a review  ->  POST /maya/reviews   (User Story 1.1)
# ---------------------------------------------------------------
with tab_write:
    st.subheader("Write a new review")

    target_type = st.radio(
        "What are you reviewing?",
        ["Artist", "Show", "Venue"],
        horizontal=True,
    )

    # Pull shows once and derive artist / venue / show options from them.
    options = {}
    try:
        shows = requests.get(f"{API}/shows").json()
        if target_type == "Show":
            options = {
                f"{s['artist_name']} @ {s['venue_name']} ({s['show_date']})": s["show_id"]
                for s in shows
            }
        elif target_type == "Venue":
            options = {s["venue_name"]: s["venue_id"] for s in shows}
        else:  # Artist
            options = {s["artist_name"]: s["artist_id"] for s in shows}
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't reach the API: {e}")

    with st.form("write_review_form"):
        choice = st.selectbox(f"Choose a {target_type.lower()}", ["--"] + list(options.keys()))
        rating = st.slider("Rating", 1, 5, 4)
        review_text = st.text_area("Your review")
        submitted = st.form_submit_button("Post Review")

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
                    r = requests.post(f"{API}/reviews", json=payload)
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
    st.subheader("My reviews")

    try:
        reviews = requests.get(f"{API}/users/{USER_ID}/reviews").json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {e}")
        reviews = []

    if not reviews:
        st.info("You haven't written any reviews yet.")

    for rev in reviews:
        target = rev.get("about_artist") or rev.get("about_venue") or "a show"
        with st.expander(f"{target} — {rev['rating']}/5"):
            st.write(rev.get("review_text") or "_No text_")
            st.caption(f"Last updated: {rev.get('last_updated')}")

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
                if st.button("Save changes", key=f"save_{rev['review_id']}"):
                    try:
                        r = requests.put(
                            f"{API}/reviews/{rev['review_id']}",
                            json={"rating": new_rating, "review_text": new_text},
                        )
                        if r.status_code == 200:
                            st.success("Review updated!")
                            st.rerun()
                        else:
                            st.error(r.json().get("error", "Update failed."))
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error connecting to the API: {e}")
            with col2:
                if st.button("Delete review", key=f"del_{rev['review_id']}"):
                    try:
                        r = requests.delete(f"{API}/reviews/{rev['review_id']}")
                        if r.status_code == 200:
                            st.success("Review deleted.")
                            st.rerun()
                        else:
                            st.error(r.json().get("error", "Delete failed."))
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error connecting to the API: {e}")
                        