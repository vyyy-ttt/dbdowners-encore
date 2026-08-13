import logging
logger = logging.getLogger(__name__)

from email.utils import parsedate_to_datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import VIOLET, apply_theme, meter, page_header, section, tile

st.set_page_config(layout='wide', page_title="Encore | Venue Overview")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

# Teddy is venue_manager vm_id 1 in the seed data.
VM_ID = st.session_state.get("vm_id", 1)


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
    """AVG() columns arrive as JSON strings because MySQL returns DECIMAL."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_date(http_date):
    """show_date arrives as an HTTP date, e.g. 'Wed, 30 Apr 2025 00:00:00 GMT'."""
    if not http_date:
        return None
    try:
        return parsedate_to_datetime(http_date).date()
    except (TypeError, ValueError):
        return None


page_header("Venue Overview", f"Welcome back, {st.session_state['first_name']}!")

venues = get_json(f"/venue_manager/venue_managers/{VM_ID}/venues")
if venues is None:
    st.stop()

if not venues:
    st.info("No venues are assigned to you yet.")
    st.stop()

names = {v["venue_id"]: v["venue_name"] for v in venues}

pick, _ = st.columns([2, 2])
with pick:
    venue_id = st.selectbox(
        "Venue", options=list(names.keys()), format_func=lambda vid: names[vid]
    )

current = next(v for v in venues if v["venue_id"] == venue_id)
st.markdown(
    f"<p class='enc-welcome' style='margin-bottom:1rem;'>"
    f"{current.get('street', '')}, {current.get('city', '')} "
    f"{current.get('state') or ''} {current.get('country', '')} &nbsp;·&nbsp; "
    f"capacity {current['capacity']:,}</p>",
    unsafe_allow_html=True,
)


# ---- Headline numbers -------------------------------------------------------
# Reviews written about the venue itself, which is what a venue manager is
# answerable for. Reviews about individual shows are counted in the category
# breakdown below, which joins through the show table.

venue_reviews = get_json("/review/reviews", params={"about_venue_id": venue_id}) or []
ratings = [r["rating"] for r in venue_reviews if r.get("rating") is not None]
answered = sum(1 for r in venue_reviews if r.get("vm_response"))
awaiting = len(venue_reviews) - answered

t1, t2, t3, t4 = st.columns(4)
with t1:
    tile(
        "Overall rating",
        f"{sum(ratings) / len(ratings):.1f}" if ratings else "n/a",
        sub=f"{len(venue_reviews)} venue reviews",
        empty=not ratings,
    )
with t2:
    tile(
        "Response rate",
        f"{(answered / len(venue_reviews) * 100):.0f}%" if venue_reviews else "n/a",
        sub=f"{answered} replied to",
        empty=not venue_reviews,
    )
with t3:
    tile(
        "Awaiting reply",
        f"{awaiting}",
        sub="no response yet",
        empty=not awaiting,
    )
with t4:
    tile(
        "Capacity",
        f"{current['capacity']:,}",
        sub=current.get("accessibility") or "no accessibility notes",
    )

st.write("")


# ---- Ratings by category, and attendance over time -------------------------

left, right = st.columns([1, 1], gap="large")

with left:
    section("Ratings by category")

    tag_rows = get_json(f"/venue/venues/{venue_id}/tags") or []
    scored = sorted(
        (r for r in tag_rows if as_float(r["avg_rating"]) is not None),
        key=lambda r: as_float(r["avg_rating"]),
    )

    if not scored:
        st.info("No tagged feedback for this venue yet.")
    else:
        # worst first: the whole point is spotting what to fix
        for row in scored[:8]:
            meter(row["tag_name"], as_float(row["avg_rating"]))
        st.caption(
            "Lowest-rated categories first. Counts reviews about the venue "
            "itself as well as reviews about shows held here."
        )

with right:
    section("Attendance over time")

    attendance = get_json(f"/venue/venues/{venue_id}/attendance") or []
    points = [
        {"Date": as_date(a["show_date"]), "Attendance": a["total_attendees"]}
        for a in attendance
        if as_date(a["show_date"]) and a.get("total_attendees")
    ]

    if len(points) < 2:
        st.info(
            "Not enough shows with recorded attendance at this venue to plot a "
            "trend yet."
        )
    else:
        frame = pd.DataFrame(points).sort_values("Date")
        chart = (
            alt.Chart(frame)
            .mark_line(point=alt.OverlayMarkDef(size=70, filled=True), strokeWidth=2.5)
            .encode(
                x=alt.X("Date:T", axis=alt.Axis(title=None, format="%b %Y")),
                y=alt.Y("Attendance:Q", axis=alt.Axis(title=None)),
                color=alt.value(VIOLET),
                tooltip=["Date", "Attendance"],
            )
            .properties(height=280)
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption(
            f"{len(points)} shows. Is turnout growing or falling off?"
        )

st.write("")


# ---- How this venue compares -----------------------------------------------

section("How this venue compares")

band = st.slider(
    "Compare against venues within this capacity range",
    min_value=0, max_value=45000,
    value=(max(0, current["capacity"] - 8000), current["capacity"] + 8000),
    step=1000,
)

stats = get_json("/venue/venues/stats", params={"capacity": band[1]}) or []
peers = [s for s in stats if s["capacity"] >= band[0]]

if not peers:
    st.info("No venues with reviews fall in this capacity range.")
else:
    frame = pd.DataFrame(
        [
            {
                "Venue": s["venue_name"],
                "Rating": as_float(s["avg_rating"]),
                "Reviews": s["review_count"],
                "Capacity": s["capacity"],
                "Mine": "This venue" if s["venue_id"] == venue_id else "Other venues",
            }
            for s in peers
        ]
    ).sort_values("Rating", ascending=False)

    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Venue:N", sort="-y", axis=alt.Axis(labelAngle=-35, title=None)),
            y=alt.Y("Rating:Q", scale=alt.Scale(domain=[0, 5]),
                    axis=alt.Axis(title=None, values=[0, 1, 2, 3, 4, 5])),
            color=alt.Color(
                "Mine:N",
                scale=alt.Scale(domain=["This venue", "Other venues"],
                                range=[VIOLET, "#C9C9DA"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=["Venue", "Rating", "Reviews", "Capacity"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    if not any(s["venue_id"] == venue_id for s in peers):
        st.caption(
            "This venue is not in the chart: `/venue/venues/stats` only includes "
            "venues that have reviews written about the venue itself."
        )

if st.button("Read and answer reviews →", type="primary"):
    st.switch_page("pages/12_Venue_Reviews.py")
