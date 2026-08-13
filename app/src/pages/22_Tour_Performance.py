import logging
logger = logging.getLogger(__name__)

import altair as alt
import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import VIOLET, apply_theme, page_header, section, tile

st.set_page_config(layout='wide', page_title="Encore | Tour Performance")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"


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


page_header("Tour Performance", "How every stop on the tour actually landed.")

tours = get_json("/tour/tours")
if tours is None:
    st.stop()

if not tours:
    st.info("No tours in the database yet.")
    st.stop()

# Busiest tours first, so the page opens on one that actually has stops to
# compare rather than an empty tour that happens to start soonest.
tours = sorted(tours, key=lambda t: (t.get("show_count") or 0), reverse=True)

labels = {
    t["tour_id"]: f"{t['tour_name']} ({t['artist_name']}) - {t['show_count']} shows"
    for t in tours
}

pick_col, _ = st.columns([2, 2])
with pick_col:
    tour_id = st.selectbox(
        "Tour", options=list(labels.keys()), format_func=lambda k: labels[k]
    )

stats = get_json(f"/tour/tours/{tour_id}/stats")
shows = get_json(f"/tour/tours/{tour_id}/shows")

if stats is None or shows is None:
    st.stop()

st.markdown(
    f"<p class='enc-welcome' style='margin-bottom:1rem;'>Now viewing: "
    f"<strong>{stats['artist_name']}</strong>, {stats['tour_name']} "
    f"({stats.get('start_date', 'n/a')} to {stats.get('end_date', 'n/a')})</p>",
    unsafe_allow_html=True,
)


# ---- Tour-level headline numbers -------------------------------------------

avg_rating = as_float(stats.get("avg_rating"))
attendees = stats.get("total_attendees")
avg_price = as_float(stats.get("avg_ticket_price"))

t1, t2, t3, t4 = st.columns(4)
with t1:
    tile("Shows on tour", f"{stats.get('total_shows') or 0}", sub="scheduled stops")
with t2:
    tile(
        "Average rating",
        f"{avg_rating:.1f}" if avg_rating is not None else "n/a",
        sub=f"{stats.get('total_reviews') or 0} reviews",
        empty=avg_rating is None,
    )
with t3:
    tile(
        "Total attendance",
        f"{int(attendees):,}" if attendees else "n/a",
        sub="across every stop",
        empty=not attendees,
    )
with t4:
    tile(
        "Average ticket",
        f"${avg_price:,.2f}" if avg_price is not None else "n/a",
        sub="mean across shows",
        empty=avg_price is None,
    )

st.write("")


# ---- Rating city by city ----------------------------------------------------

rated = [s for s in shows if as_float(s.get("avg_rating")) is not None]

left, right = st.columns([3, 2], gap="large")

with left:
    section("Fan rating, stop by stop")

    if not rated:
        st.info("No reviews on this tour's shows yet, so there is nothing to chart.")
    else:
        frame = pd.DataFrame(
            [
                {
                    "Date": s["show_date"],
                    "Venue": s["venue_name"],
                    "City": s["city"],
                    "Rating": as_float(s["avg_rating"]),
                    "Reviews": s["review_count"],
                    "Attendance": s["total_attendees"],
                }
                for s in rated
            ]
        )

        line = (
            alt.Chart(frame)
            .mark_line(point=alt.OverlayMarkDef(size=70, filled=True), strokeWidth=2.5)
            .encode(
                x=alt.X("Date:T", axis=alt.Axis(title=None, format="%b %d")),
                y=alt.Y("Rating:Q", scale=alt.Scale(domain=[0, 5]),
                        axis=alt.Axis(title=None, values=[0, 1, 2, 3, 4, 5])),
                color=alt.value(VIOLET),
                tooltip=["Date", "Venue", "City", "Rating", "Reviews", "Attendance"],
            )
            .properties(height=280)
        )
        st.altair_chart(line, use_container_width=True)
        st.caption(
            "Each point is one stop. Dips are where a city's fans reacted worse "
            "than the rest of the tour."
        )

with right:
    section("Categories across the tour")

    tag_rows = stats.get("tags") or []
    if not tag_rows:
        st.info("No tagged feedback on this tour yet.")
    else:
        tag_frame = pd.DataFrame(
            [
                {
                    "Category": t["tag_name"],
                    "Rating": as_float(t["avg_rating"]),
                    "Mentions": t["review_count"],
                }
                for t in tag_rows[:8]
            ]
        )
        bars = (
            alt.Chart(tag_frame)
            .mark_bar(cornerRadiusEnd=5, height=18)
            .encode(
                y=alt.Y("Category:N", sort="-x", axis=alt.Axis(title=None)),
                x=alt.X("Mentions:Q", axis=alt.Axis(title="mentions", tickMinStep=1)),
                color=alt.value(VIOLET),
                tooltip=["Category", "Mentions", "Rating"],
            )
            .properties(height=280)
        )
        st.altair_chart(bars, use_container_width=True)

st.write("")


# ---- Every stop -------------------------------------------------------------

section("Every stop on this tour")

if not shows:
    st.info("This tour has no shows scheduled yet.")
else:
    table = pd.DataFrame(
        [
            {
                "Date": s["show_date"],
                "Venue": s["venue_name"],
                "City": f"{s['city']}, {s['state']}",
                "Doors": s["start_time"],
                "Attendance": s["total_attendees"],
                "Capacity": s["capacity"],
                "Ticket": as_float(s["avg_ticket_price"]),
                "Rating": as_float(s["avg_rating"]),
                "Reviews": s["review_count"],
            }
            for s in shows
        ]
    )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticket": st.column_config.NumberColumn(format="$%.2f"),
            "Rating": st.column_config.NumberColumn(format="%.1f"),
            "Attendance": st.column_config.NumberColumn(format="%d"),
            "Capacity": st.column_config.NumberColumn(format="%d"),
        },
    )

st.divider()


# ---- Manage tours -----------------------------------------------------------

section("Manage tours")

edit_tab, new_tab, remove_tab = st.tabs(["Edit this tour", "Add a tour", "Remove a tour"])

current = next((t for t in tours if t["tour_id"] == tour_id), {})

with edit_tab:
    with st.form("edit_tour"):
        e1, e2, e3 = st.columns(3)
        with e1:
            new_name = st.text_input("Tour name", value=current.get("tour_name", ""))
        with e2:
            new_start = st.text_input("Start date", value=current.get("start_date") or "")
        with e3:
            new_end = st.text_input("End date", value=current.get("end_date") or "")

        if st.form_submit_button("Save changes", type="primary"):
            payload = {"tour_name": new_name}
            if new_start:
                payload["start_date"] = new_start
            if new_end:
                payload["end_date"] = new_end
            try:
                put = requests.put(f"{API}/tour/tours/{tour_id}", json=payload, timeout=10)
                if put.status_code == 200:
                    st.success("Tour updated.")
                    st.rerun()
                else:
                    st.error(f"{put.status_code}: {put.json().get('error', put.text[:200])}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the API: {e}")

with new_tab:
    with st.form("new_tour"):
        n1, n2 = st.columns(2)
        with n1:
            name = st.text_input("Tour name")
            artist_id = st.number_input("Artist id", min_value=1, value=1, step=1)
        with n2:
            start = st.text_input("Start date", placeholder="2026-09-01")
            end = st.text_input("End date", placeholder="2026-12-15")
        manager_id = st.number_input(
            "Tour manager id", min_value=1,
            value=int(st.session_state.get("tm_id", 1)), step=1,
        )

        if st.form_submit_button("Create tour", type="primary"):
            if not name:
                st.error("A tour needs a name.")
            else:
                payload = {
                    "tour_name": name,
                    "main_artist_id": int(artist_id),
                    "managed_by_id": int(manager_id),
                }
                if start:
                    payload["start_date"] = start
                if end:
                    payload["end_date"] = end
                try:
                    post = requests.post(f"{API}/tour/tours", json=payload, timeout=10)
                    if post.status_code == 201:
                        st.success(f"Created tour {post.json().get('tour_id')}.")
                        st.rerun()
                    else:
                        st.error(f"{post.status_code}: {post.json().get('error', post.text[:200])}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not reach the API: {e}")

with remove_tab:
    st.caption(
        "A tour with shows scheduled on it cannot be deleted, because show.tour_id "
        "is a foreign key. The API returns 409 and says how many shows are in the way."
    )
    victim = st.selectbox(
        "Tour to remove", options=list(labels.keys()),
        format_func=lambda k: labels[k], key="delete_pick",
    )
    if st.button("Delete tour", type="primary"):
        try:
            gone = requests.delete(f"{API}/tour/tours/{victim}", timeout=10)
            if gone.status_code == 200:
                st.success("Tour deleted.")
                st.rerun()
            elif gone.status_code == 409:
                body = gone.json()
                st.warning(
                    f"{body.get('error')} ({body.get('shows_on_tour')} shows scheduled)."
                )
            else:
                st.error(f"{gone.status_code}: {gone.json().get('error', gone.text[:200])}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the API: {e}")
