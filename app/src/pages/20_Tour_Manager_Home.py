import logging
logger = logging.getLogger(__name__)

import altair as alt
import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import VIOLET, apply_theme, meter, page_header, section, tile

st.set_page_config(layout='wide', page_title="Encore | Tour Insights")

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


def as_float(value):
    """AVG() columns arrive as JSON strings because MySQL returns DECIMAL."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


page_header("Tour Insights", f"Welcome back, {st.session_state['first_name']}!")

venues = get_json("/venue/venues")
if venues is None:
    st.stop()

venue_names = {v["venue_id"]: v["venue_name"] for v in venues}
capacities = {v["venue_id"]: v["capacity"] for v in venues}


# ---- Filter bar -------------------------------------------------------------

fcol1, fcol2, fcol3 = st.columns([1.3, 1.3, 1.4])
with fcol1:
    chosen_id = st.selectbox(
        "Venue",
        options=list(venue_names.keys()),
        format_func=lambda vid: venue_names[vid],
    )
with fcol2:
    band = st.select_slider(
        "Compare against venues sized",
        options=["10-15k", "15-20k", "20-30k", "All sizes"],
        value="15-20k",
    )
with fcol3:
    st.write("")

BANDS = {
    "10-15k": (10000, 15000),
    "15-20k": (15000, 20000),
    "20-30k": (20000, 30000),
    "All sizes": (0, 100000),
}
low, high = BANDS[band]

st.write("")


# ---- Headline tiles for the selected venue ---------------------------------

tag_rows = get_json(f"/venue/venues/{chosen_id}/tags") or []
by_tag = {row["tag_name"]: row for row in tag_rows}

rated = [as_float(r["avg_rating"]) for r in tag_rows if as_float(r["avg_rating"]) is not None]
overall = sum(rated) / len(rated) if rated else None
total_reviews = sum(r["review_count"] for r in tag_rows)

scored = [r for r in tag_rows if as_float(r["avg_rating"]) is not None]
best = max(scored, key=lambda r: as_float(r["avg_rating"]), default=None)
# Only meaningful once two categories have feedback. Otherwise the strongest
# and the weakest are the same row, which reads like a bug.
worst = min(scored, key=lambda r: as_float(r["avg_rating"])) if len(scored) > 1 else None

t1, t2, t3, t4 = st.columns(4)
with t1:
    tile(
        "Overall rating",
        f"{overall:.1f}" if overall is not None else "n/a",
        sub=venue_names[chosen_id],
        empty=overall is None,
    )
with t2:
    tile(
        "Tagged reviews",
        f"{total_reviews:,}" if total_reviews else "n/a",
        sub="across all categories",
        empty=not total_reviews,
    )
with t3:
    tile(
        "Strongest category",
        best["tag_name"] if best else "n/a",
        sub=f"{as_float(best['avg_rating']):.1f} average" if best else "no data yet",
        empty=best is None,
        text_value=True,
    )
with t4:
    tile(
        "Needs attention",
        worst["tag_name"] if worst else "n/a",
        sub=(
            f"{as_float(worst['avg_rating']):.1f} average" if worst
            else "needs two rated categories"
        ),
        empty=worst is None,
        text_value=True,
    )

st.write("")


# ---- Ratings by category + venue comparison --------------------------------

left, right = st.columns([1, 1], gap="large")

with left:
    section("Ratings by category")

    all_tags = get_json("/tag/tags") or []
    if not all_tags:
        st.info("No tag categories are defined yet.")
    else:
        for tag in all_tags:
            row = by_tag.get(tag["tag_name"])
            meter(tag["tag_name"], as_float(row["avg_rating"]) if row else None)

    st.caption(
        "Counts reviews about the venue itself as well as reviews about shows "
        "held there. A dash means no feedback in that category yet."
    )

with right:
    section(f"Fan sentiment for venues sized {band}")

    stats = get_json("/venue/venues/stats", params={"capacity": high}) or []
    banded = [s for s in stats if s["capacity"] >= low]

    if not banded:
        st.info(
            f"No venues in the {band} band have venue-level reviews yet. "
            "See the note below."
        )
    else:
        frame = pd.DataFrame(
            [
                {
                    "Venue": s["venue_name"],
                    "Rating": as_float(s["avg_rating"]),
                    "Reviews": s["review_count"],
                    "Capacity": s["capacity"],
                }
                for s in banded
            ]
        ).sort_values("Rating", ascending=False)

        chart = (
            alt.Chart(frame)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=44)
            .encode(
                x=alt.X("Venue:N", sort="-y", axis=alt.Axis(labelAngle=0, title=None)),
                y=alt.Y(
                    "Rating:Q",
                    scale=alt.Scale(domain=[0, 5]),
                    axis=alt.Axis(title=None, values=[0, 1, 2, 3, 4, 5], grid=True),
                ),
                color=alt.value(VIOLET),
                tooltip=["Venue", "Rating", "Reviews", "Capacity"],
            )
            .properties(height=248)
        )
        st.altair_chart(chart, use_container_width=True)

        st.markdown('<div class="enc-section">Top recommended venues</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            frame[["Venue", "Rating", "Reviews"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rating": st.column_config.NumberColumn(format="%.1f"),
            },
        )

st.write("")
lcol, rcol = st.columns([3, 1])
with lcol:
    st.info(
        "`/venue/venues/stats` joins reviews on `about_venue_id`, so a venue only "
        "appears in the comparison once someone reviews the venue itself. "
        "reviews about individual shows are not counted there yet. The category "
        "ratings on the left do count both.",
        icon="ℹ️",
    )
with rcol:
    st.write("")
    if st.button("Review feedback →", type="primary", use_container_width=True):
        st.switch_page("pages/21_Tour_Reviews.py")

with st.expander("Still needs API support"):
    st.markdown(
        """
        - **Per-tour rollup**: the wireframe's "Now viewing: *artist, tour*" header
          and the "▲ 0.3 vs last show" deltas need the tour routes, which supply
          per-show, per-category averages ordered by show date.
        - **Crowd Energy** is one of the four categories in the wireframe but is
          not a row in the `tag` table, so it never appears above.
        """
    )
