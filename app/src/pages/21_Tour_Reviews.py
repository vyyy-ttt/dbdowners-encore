import logging
logger = logging.getLogger(__name__)

from email.utils import parsedate_to_datetime

import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, chip, page_header, section, stars, tile

st.set_page_config(layout='wide', page_title="Encore | Tour Reviews")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

# Enrica is tour_manager tm_id 1 in the seed data. Responses are attributed to
# whoever is logged in, so this comes from the session rather than a constant.
TM_ID = st.session_state.get("tm_id", 1)


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


def pretty_date(http_date):
    """upload_date arrives as an HTTP date, e.g. 'Tue, 11 Aug 2026 15:04:21 GMT'."""
    if not http_date:
        return "unknown date"
    try:
        return parsedate_to_datetime(http_date).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return str(http_date)


page_header("Tour Reviews", "Filter fan feedback, then respond on behalf of the artist.")


# ---- Filters ---------------------------------------------------------------

venues = get_json("/venue/venues") or []
tags = get_json("/tag/tags") or []

venue_options = {0: "All venues"}
venue_options.update({v["venue_id"]: v["venue_name"] for v in venues})

tag_options = {0: "All categories"}
tag_options.update({t["tag_id"]: t["tag_name"] for t in tags})

fcol1, fcol2, fcol3 = st.columns([1.3, 1.3, 1.4])
with fcol1:
    venue_id = st.selectbox(
        "Venue", options=list(venue_options.keys()),
        format_func=lambda k: venue_options[k],
    )
with fcol2:
    tag_id = st.selectbox(
        "Category", options=list(tag_options.keys()),
        format_func=lambda k: tag_options[k],
    )
with fcol3:
    st.write("")
    only_unanswered = st.checkbox("Awaiting a tour response", value=False)

params = {}
if venue_id:
    params["about_venue_id"] = venue_id
if tag_id:
    params["tag_id"] = tag_id

reviews = get_json("/review/reviews", params=params)
if reviews is None:
    st.stop()

if only_unanswered:
    reviews = [r for r in reviews if not r.get("tm_response")]

ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
answered = sum(1 for r in reviews if r.get("tm_response"))

st.write("")
k1, k2, k3, k4 = st.columns(4)
with k1:
    tile("Reviews", f"{len(reviews)}", sub="matching the filters", empty=not reviews)
with k2:
    tile(
        "Average",
        f"{sum(ratings) / len(ratings):.1f}" if ratings else "n/a",
        sub="out of 5",
        empty=not ratings,
    )
with k3:
    tile("Responded", f"{answered}", sub="by a tour manager", empty=not answered)
with k4:
    awaiting = len(reviews) - answered
    tile("Awaiting reply", f"{awaiting}", sub="no tour response yet", empty=not awaiting)

st.write("")
section("Recent reviews")

if venue_id and not reviews:
    st.info(
        "Filtering by venue matches `about_venue_id` only, so reviews written "
        "about a *show* at this venue will not appear. Clear the venue filter "
        "to see those.",
        icon="ℹ️",
    )

if not reviews:
    st.caption("Nothing matches the current filters.")


# ---- Review cards ----------------------------------------------------------

for review in reviews:
    review_id = review["review_id"]

    subject_chips = []
    if review.get("about_show_id"):
        subject_chips.append(chip(f"Show #{review['about_show_id']}", grey=True))
    if review.get("about_venue_id"):
        subject_chips.append(
            chip(
                venue_options.get(
                    review["about_venue_id"], f"Venue #{review['about_venue_id']}"
                ),
                grey=True,
            )
        )
    if review.get("about_artist_id"):
        subject_chips.append(chip(f"Artist #{review['about_artist_id']}", grey=True))
    if not subject_chips:
        subject_chips.append(chip("Unattributed", grey=True))

    reply_html = ""
    if review.get("vm_response"):
        reply_html += (
            '<div class="enc-reply enc-reply-vm">'
            '<span class="enc-reply-label">Venue manager replied</span>'
            f'{review["vm_response"]}</div>'
        )
    if review.get("tm_response"):
        reply_html += (
            '<div class="enc-reply">'
            '<span class="enc-reply-label">Your response</span>'
            f'{review["tm_response"]}</div>'
        )

    st.markdown(
        f"""
        <div class="enc-card">
          <div class="enc-card-top">
            <div>{stars(review.get("rating"))}</div>
            <div class="enc-meta">{pretty_date(review.get("upload_date"))}</div>
          </div>
          <div>{"".join(subject_chips)}</div>
          <p class="enc-quote">{review.get("review_text") or "<em>no text</em>"}</p>
          {reply_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    label = "Update response" if review.get("tm_response") else "Respond"
    with st.expander(label):
        with st.form(f"respond_{review_id}"):
            text = st.text_area(
                "Response on behalf of the artist",
                value=review.get("tm_response") or "",
                key=f"text_{review_id}",
                height=90,
                label_visibility="collapsed",
                placeholder="Write a public reply to this review…",
            )
            bcol1, bcol2, _ = st.columns([1, 1, 3])
            with bcol1:
                submitted = st.form_submit_button(label, type="primary",
                                                  use_container_width=True)
            with bcol2:
                st.form_submit_button(
                    "Mark Addressed",
                    disabled=True,
                    use_container_width=True,
                    help=(
                        "The wireframe has this button, but `review` has no column "
                        "to record it. Only responding_tm_id and tm_response "
                        "exist. It needs a schema change first."
                    ),
                )

            if submitted:
                if not text.strip():
                    st.error("Write a response first.")
                else:
                    payload = {"responding_tm_id": TM_ID, "tm_response": text.strip()}
                    try:
                        put = requests.put(
                            f"{API}/review/reviews/{review_id}", json=payload, timeout=10
                        )
                        if put.status_code == 200:
                            st.success("Response saved.")
                            st.rerun()
                        else:
                            st.error(
                                f"Failed ({put.status_code}): "
                                f"{put.json().get('error', put.text[:200])}"
                            )
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not reach the API: {e}")

st.write("")
if st.button("← Back to Tour Insights"):
    st.switch_page("pages/20_Tour_Manager_Home.py")
