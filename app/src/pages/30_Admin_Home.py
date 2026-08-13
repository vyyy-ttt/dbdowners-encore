import logging
logger = logging.getLogger(__name__)

import altair as alt
import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import VIOLET, apply_theme, page_header, section, tile

st.set_page_config(layout='wide', page_title="Encore | Admin Overview")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"


def get_json(path, params=None):
    """GET a JSON payload, returning None (and showing why) on any failure."""
    try:
        response = requests.get(f"{API}{path}", params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API}: {e}")
        return None

    if response.status_code != 200:
        st.warning(f"`GET {path}` returned {response.status_code}.")
        return None

    return response.json()


page_header("Admin Overview", f"Welcome back, {st.session_state['first_name']}!")

# Headline tiles

monthly = get_json("/review/reviews/stats") or []
unresolved = get_json("/report/reports/reviews", params={"is_resolved": "false"}) or []

total_reviews = sum(row["review_count"] for row in monthly)
latest_month = monthly[-1] if monthly else None

t1, t2, t3 = st.columns(3)
with t1:
    tile(
        "Total reviews",
        f"{total_reviews:,}" if total_reviews else "n/a",
        sub="All time, across the platform",
        empty=not total_reviews,
    )
with t2:
    tile(
        "This month's reviews",
        f"{latest_month['review_count']:,}" if latest_month else "n/a",
        sub=latest_month["month"] if latest_month else "no data yet",
        empty=latest_month is None,
    )
with t3:
    tile(
        "Needs attention",
        f"{len(unresolved)}",
        sub="Unresolved flagged reviews",
        empty=len(unresolved) == 0,
    )

st.write("")

# Review volume trend

section("Review Volume Over Time")

if not monthly:
    st.info("No reviews have been written yet.")
else:
    frame = pd.DataFrame(monthly)
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=28)
        .encode(
            x=alt.X("month:N", axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("review_count:Q", axis=alt.Axis(title="Reviews", format="d")),
            color=alt.value(VIOLET),
            tooltip=["month", "review_count"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)

st.write("")

# Quick links to task pages

section("Moderation & Management")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Manage Reports**")
    st.caption("Review flagged users and reviews that break the rules.")
    if st.button("Go to Reports →", type="primary", use_container_width=True):
        st.switch_page("pages/32_Admin_Reports.py")
with c2:
    st.markdown("**Manage Venues**")
    st.caption("Fix inaccurate listings or add a new venue to the platform.")
    if st.button("Go to Venues →", type="primary", use_container_width=True):
        st.switch_page("pages/33_Admin_Venues.py")
with c3:
    st.markdown("**Manage Users**")
    st.caption("Suspend or reinstate a user account.")
    if st.button("Go to Users →", type="primary", use_container_width=True):
        st.switch_page("pages/34_Admin_Users.py")
