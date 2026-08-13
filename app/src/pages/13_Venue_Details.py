import logging
logger = logging.getLogger(__name__)

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section

st.set_page_config(layout='wide', page_title="Encore | Venue Details")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

VM_ID = st.session_state.get("vm_id", 1)

COUNTRIES = ["USA", "CAN", "GBR", "MEX", "DEU", "AUS"]


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


page_header("Venue Details", f"Welcome back, {st.session_state['first_name']}!")

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

tab_listing, tab_transport, tab_profile = st.tabs(
    ["Venue listing", "Getting here", "My details"]
)


# ---- Venue listing ----------------------------------------------------------

with tab_listing:
    section("Keep the listing accurate")
    st.caption(
        "This is what concertgoers see when they look up the venue, so the "
        "address and accessibility notes are worth keeping current."
    )

    with st.form("venue_listing"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Venue name", value=current["venue_name"])
            street = st.text_input("Street", value=current.get("street") or "")
            city = st.text_input("City", value=current.get("city") or "")
        with c2:
            state = st.text_input(
                "State / Province", value=current.get("state") or "",
                help="Two characters. Leave blank where it does not apply.",
            )
            zip_code = st.text_input("Zip / Postal code", value=current.get("zip") or "")
            country = st.selectbox(
                "Country", options=COUNTRIES,
                index=COUNTRIES.index(current["country"])
                if current.get("country") in COUNTRIES else 0,
            )

        accessibility = st.text_input(
            "Accessibility notes", value=current.get("accessibility") or ""
        )
        capacity = st.number_input(
            "Capacity", min_value=1, value=int(current["capacity"]), step=100
        )

        if st.form_submit_button("Save listing", type="primary"):
            try:
                put = requests.put(
                    f"{API}/venue/venues/{venue_id}",
                    json={
                        "venue_name": name, "street": street, "city": city,
                        "state": state or None, "zip": zip_code, "country": country,
                        "accessibility": accessibility, "capacity": int(capacity),
                    },
                    timeout=10,
                )
                if put.status_code == 200:
                    st.success("Listing updated.")
                    st.rerun()
                else:
                    st.error(
                        f"{put.status_code}: {put.json().get('error', put.text[:200])}"
                    )
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the API: {e}")


# ---- Transportation ---------------------------------------------------------

with tab_transport:
    section("How people get here")
    st.caption(
        "Concertgoers see these options on the venue page. Missing or wrong "
        "directions are one of the most common complaints."
    )

    detail = get_json(f"/venue/venues/{venue_id}/transportation") or {}
    options = detail.get("transportation_options", []) if isinstance(detail, dict) else []

    if not options:
        st.info("No transport options listed for this venue yet.")
    else:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Type": o["transport_type"],
                        "Est. cost": as_float(o["estimated_cost"]),
                        "Instructions": o["instructions"],
                    }
                    for o in options
                ]
            ),
            use_container_width=True,
            hide_index=True,
            column_config={"Est. cost": st.column_config.NumberColumn(format="$%.2f")},
        )

    add_col, remove_col = st.columns(2)

    with add_col:
        st.markdown('<div class="enc-section">Add an option</div>',
                    unsafe_allow_html=True)
        with st.form("add_transport"):
            kind = st.text_input("Type", placeholder="e.g. Commuter Rail")
            cost = st.number_input("Estimated cost", min_value=0.0,
                                   max_value=9999.99, value=5.0, step=0.5)
            instructions = st.text_area("Instructions", height=80)
            if st.form_submit_button("Add", type="primary"):
                if not kind:
                    st.error("Give the option a type.")
                else:
                    try:
                        post = requests.post(
                            f"{API}/transport/transportations",
                            json={
                                "venue_id": venue_id, "transport_type": kind,
                                "estimated_cost": float(cost),
                                "instructions": instructions,
                            },
                            timeout=10,
                        )
                        if post.status_code == 201:
                            st.success("Added.")
                            st.rerun()
                        else:
                            st.error(
                                f"{post.status_code}: "
                                f"{post.json().get('error', post.text[:200])}"
                            )
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not reach the API: {e}")

    with remove_col:
        st.markdown('<div class="enc-section">Update or remove</div>',
                    unsafe_allow_html=True)
        if not options:
            st.caption("Nothing to change yet.")
        else:
            labels = {
                o["transport_id"]: f"{o['transport_type']} (${as_float(o['estimated_cost']):.2f})"
                for o in options
            }
            chosen = st.selectbox(
                "Option", options=list(labels.keys()),
                format_func=lambda tid: labels[tid],
            )
            picked = next(o for o in options if o["transport_id"] == chosen)

            new_cost = st.number_input(
                "New estimated cost", min_value=0.0, max_value=9999.99,
                value=as_float(picked["estimated_cost"]) or 0.0, step=0.5,
                key="edit_cost",
            )
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Update cost", type="primary", use_container_width=True):
                    try:
                        put = requests.put(
                            f"{API}/transport/transportations/{chosen}",
                            json={"estimated_cost": float(new_cost)}, timeout=10,
                        )
                        if put.status_code == 200:
                            st.success("Updated.")
                            st.rerun()
                        else:
                            st.error(f"{put.status_code}: {put.text[:160]}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not reach the API: {e}")
            with b2:
                if st.button("Remove", use_container_width=True):
                    try:
                        gone = requests.delete(
                            f"{API}/transport/transportations/{chosen}", timeout=10
                        )
                        if gone.status_code == 200:
                            st.success("Removed.")
                            st.rerun()
                        else:
                            st.error(f"{gone.status_code}: {gone.text[:160]}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not reach the API: {e}")


# ---- Manager profile --------------------------------------------------------

with tab_profile:
    section("My contact details")
    st.caption("Shown to tour managers and administrators who need to reach you.")

    me = get_json(f"/venue_manager/venue_managers/{VM_ID}")
    if not me:
        st.info("Could not load your profile.")
    else:
        with st.form("vm_profile"):
            p1, p2 = st.columns(2)
            with p1:
                first = st.text_input("First name", value=me.get("first_name") or "")
            with p2:
                last = st.text_input("Last name", value=me.get("last_name") or "")
            email = st.text_input("Email", value=me.get("email_address") or "")

            if st.form_submit_button("Save details", type="primary"):
                if not email:
                    st.error("Email is required.")
                else:
                    try:
                        put = requests.put(
                            f"{API}/venue_manager/venue_managers/{VM_ID}",
                            json={
                                "first_name": first, "last_name": last,
                                "email_address": email,
                            },
                            timeout=10,
                        )
                        if put.status_code == 200:
                            st.success("Details updated.")
                            st.rerun()
                        else:
                            st.error(
                                f"{put.status_code}: "
                                f"{put.json().get('error', put.text[:200])}"
                            )
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not reach the API: {e}")

        st.markdown('<div class="enc-section">Venues I manage</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            pd.DataFrame(
                [
                    {"Venue": v["venue_name"], "City": v.get("city"),
                     "Country": v.get("country"), "Capacity": v["capacity"]}
                    for v in venues
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
