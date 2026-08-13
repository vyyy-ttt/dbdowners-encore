import logging
logger = logging.getLogger(__name__)

from email.utils import parsedate_to_datetime

import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, chip, page_header, section, stars, tile

st.set_page_config(layout='wide', page_title="Encore | Venue Reviews")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

# Teddy is venue_manager vm_id 1 in the seed data. Responses are attributed to
# whoever is signed in rather than hardcoded.
VM_ID = st.session_state.get("vm_id", 1)

# A report needs a reporter_id, which is a user. When a venue manager flags a
# review the report is filed against the platform's own moderation queue.
REPORTING_USER_ID = 1


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
    if not http_date:
        return "unknown date"
    try:
        return parsedate_to_datetime(http_date).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return str(http_date)


page_header("Venue Reviews", f"Welcome back, {st.session_state['first_name']}!")

venues = get_json(f"/venue_manager/venue_managers/{VM_ID}/venues")
if venues is None:
    st.stop()
if not venues:
    st.info("No venues are assigned to you yet.")
    st.stop()

names = {v["venue_id"]: v["venue_name"] for v in venues}


# ---- Filters ----------------------------------------------------------------

f1, f2, f3 = st.columns([1.2, 1.2, 1.4])
with f1:
    venue_id = st.selectbox(
        "Venue", options=list(names.keys()), format_func=lambda vid: names[vid]
    )
with f2:
    scope = st.radio(
        "Reviews about",
        ["The venue itself", "A specific show date"],
        help=(
            "Venue-level reviews are written about the room. Picking a date "
            "instead pulls the reviews of the show played here that night."
        ),
    )
with f3:
    st.write("")
    only_unanswered = st.checkbox("Only ones I have not answered", value=False)

show_date = None
if scope == "A specific show date":
    attendance = get_json(f"/venue/venues/{venue_id}/attendance") or []
    dates = []
    for row in attendance:
        try:
            dates.append(parsedate_to_datetime(row["show_date"]).date())
        except (TypeError, ValueError, KeyError):
            continue
    if not dates:
        st.info("No shows on record at this venue yet.")
        st.stop()
    show_date = st.selectbox(
        "Show date", options=sorted(dates, reverse=True), format_func=str
    )

# Reviews about the venue come back with the full row, which is what the
# respond form needs. The date-filtered endpoint returns a slimmer shape.
if show_date:
    reviews = get_json(
        f"/venue/venues/{venue_id}/reviews", params={"show_date": str(show_date)}
    )
else:
    reviews = get_json("/review/reviews", params={"about_venue_id": venue_id})

if reviews is None:
    st.stop()

if only_unanswered:
    reviews = [r for r in reviews if not r.get("vm_response")]

ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
answered = sum(1 for r in reviews if r.get("vm_response"))

st.write("")
k1, k2, k3 = st.columns(3)
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
    tile("Answered", f"{answered}", sub="by a venue manager", empty=not answered)

st.write("")
section("Feedback")

if not reviews:
    st.caption("Nothing matches the current filters.")


# ---- Review cards -----------------------------------------------------------

for review in reviews:
    review_id = review["review_id"]

    chips = []
    if show_date:
        chips.append(chip(f"Show on {show_date}", grey=True))
    else:
        chips.append(chip(names[venue_id], grey=True))

    reply_html = ""
    if review.get("tm_response"):
        reply_html += (
            '<div class="enc-reply enc-reply-vm">'
            '<span class="enc-reply-label">Tour manager replied</span>'
            f'{review["tm_response"]}</div>'
        )
    if review.get("vm_response"):
        reply_html += (
            '<div class="enc-reply">'
            '<span class="enc-reply-label">Your response</span>'
            f'{review["vm_response"]}</div>'
        )

    st.markdown(
        f"""
        <div class="enc-card">
          <div class="enc-card-top">
            <div>{stars(review.get("rating"))}</div>
            <div class="enc-meta">{pretty_date(review.get("upload_date"))}</div>
          </div>
          <div>{"".join(chips)}</div>
          <p class="enc-quote">{review.get("review_text") or "<em>no text</em>"}</p>
          {reply_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    label = "Update response" if review.get("vm_response") else "Respond"
    with st.expander(f"{label} or flag this review"):
        with st.form(f"vm_respond_{review_id}"):
            text = st.text_area(
                "Public response",
                value=review.get("vm_response") or "",
                key=f"vm_text_{review_id}",
                height=90,
                label_visibility="collapsed",
                placeholder="Reply publicly on behalf of the venue…",
            )
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                responded = st.form_submit_button(
                    label, type="primary", use_container_width=True
                )
            with c2:
                flagged = st.form_submit_button(
                    "Flag as inaccurate", use_container_width=True,
                    help="Files a report for the platform administrators to review.",
                )

            if responded:
                if not text.strip():
                    st.error("Write a response first.")
                else:
                    try:
                        put = requests.put(
                            f"{API}/review/reviews/{review_id}",
                            json={"responding_vm_id": VM_ID,
                                  "vm_response": text.strip()},
                            timeout=10,
                        )
                        if put.status_code == 200:
                            st.success("Response saved.")
                            st.rerun()
                        else:
                            st.error(
                                f"{put.status_code}: "
                                f"{put.json().get('error', put.text[:200])}"
                            )
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not reach the API: {e}")

            if flagged:
                try:
                    post = requests.post(
                        f"{API}/report/reports",
                        json={
                            "reporter_id": REPORTING_USER_ID,
                            "target_review_id": review_id,
                            "report_type": "review",
                            "reason": (
                                f"Flagged by the venue manager of "
                                f"{names[venue_id]} as inaccurate."
                            ),
                            "is_resolved": False,
                        },
                        timeout=10,
                    )
                    if post.status_code == 201:
                        st.success(
                            f"Flagged for moderation (report "
                            f"#{post.json().get('report_id')})."
                        )
                    else:
                        st.error(
                            f"{post.status_code}: "
                            f"{post.json().get('error', post.text[:200])}"
                        )
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not reach the API: {e}")

st.write("")
if st.button("← Back to overview"):
    st.switch_page("pages/11_Venue_Overview.py")
