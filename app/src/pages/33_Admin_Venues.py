import logging
logger = logging.getLogger(__name__)

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section

st.set_page_config(layout='wide', page_title="Encore | Manage Venues")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

# ISO 3166-1 alpha-3. Two-letter codes would make Canada 'CA', which reads as
# California next to the state column.
COUNTRIES = [
    "ABW", "AFG", "AGO", "AIA", "ALA", "ALB", "AND", "ARE", "ARG", "ARM",
    "ASM", "ATA", "ATF", "ATG", "AUS", "AUT", "AZE", "BDI", "BEL", "BEN",
    "BES", "BFA", "BGD", "BGR", "BHR", "BHS", "BIH", "BLM", "BLR", "BLZ",
    "BMU", "BOL", "BRA", "BRB", "BRN", "BTN", "BVT", "BWA", "CAF", "CAN",
    "CCK", "CHE", "CHL", "CHN", "CIV", "CMR", "COD", "COG", "COK", "COL",
    "COM", "CPV", "CRI", "CUB", "CUW", "CXR", "CYM", "CYP", "CZE", "DEU",
    "DJI", "DMA", "DNK", "DOM", "DZA", "ECU", "EGY", "ERI", "ESH", "ESP",
    "EST", "ETH", "FIN", "FJI", "FLK", "FRA", "FRO", "FSM", "GAB", "GBR",
    "GEO", "GGY", "GHA", "GIB", "GIN", "GLP", "GMB", "GNB", "GNQ", "GRC",
    "GRD", "GRL", "GTM", "GUF", "GUM", "GUY", "HKG", "HMD", "HND", "HRV",
    "HTI", "HUN", "IDN", "IMN", "IND", "IOT", "IRL", "IRN", "IRQ", "ISL",
    "ISR", "ITA", "JAM", "JEY", "JOR", "JPN", "KAZ", "KEN", "KGZ", "KHM",
    "KIR", "KNA", "KOR", "KWT", "LAO", "LBN", "LBR", "LBY", "LCA", "LIE",
    "LKA", "LSO", "LTU", "LUX", "LVA", "MAC", "MAF", "MAR", "MCO", "MDA",
    "MDG", "MDV", "MEX", "MHL", "MKD", "MLI", "MLT", "MMR", "MNE", "MNG",
    "MNP", "MOZ", "MRT", "MSR", "MTQ", "MUS", "MWI", "MYS", "MYT", "NAM",
    "NCL", "NER", "NFK", "NGA", "NIC", "NIU", "NLD", "NOR", "NPL", "NRU",
    "NZL", "OMN", "PAK", "PAN", "PCN", "PER", "PHL", "PLW", "PNG", "POL",
    "PRI", "PRK", "PRT", "PRY", "PSE", "PYF", "QAT", "REU", "ROU", "RUS",
    "RWA", "SAU", "SDN", "SEN", "SGP", "SGS", "SHN", "SJM", "SLB", "SLE",
    "SLV", "SMR", "SOM", "SPM", "SRB", "SSD", "STP", "SUR", "SVK", "SVN",
    "SWE", "SWZ", "SXM", "SYC", "SYR", "TCA", "TCD", "TGO", "THA", "TJK",
    "TKL", "TKM", "TLS", "TON", "TTO", "TUN", "TUR", "TUV", "TWN", "TZA",
    "UGA", "UKR", "UMI", "URY", "USA", "UZB", "VAT", "VCT", "VEN", "VGB",
    "VIR", "VNM", "VUT", "WLF", "WSM", "YEM", "ZAF", "ZMB", "ZWE"
]

TABLE_COLUMNS = [
    "venue_id", "venue_name", "street", "city", "state", "zip", "country",
    "capacity", "accessibility", "managed_by_id", "manager_name",
]


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


def post_json(path, body):
    try:
        response = requests.post(f"{API}{path}", json=body, timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API}: {e}")
        return None
    if response.status_code != 201:
        st.warning(f"`POST {path}` returned {response.status_code}.")
        return None
    return response.json()


def put_json(path, body):
    try:
        response = requests.put(f"{API}{path}", json=body, timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API}: {e}")
        return False
    if response.status_code != 200:
        st.warning(f"`PUT {path}` returned {response.status_code}.")
        return False
    return True


page_header("Manage Venues", "View, fix, or add a venue.")

# Fetch a full unfiltered list once for the dropdowns on the edit tab,
# regardless of what filters are applied on the All Venues tab.
all_venues = get_json("/venue/venues") or []
managers = get_json("/venue_manager/venue_managers") or []
manager_names = {m["vm_id"]: f"{m['first_name']} {m['last_name']}" for m in managers}

tab_all, tab_edit, tab_add = st.tabs(["All Venues", "Edit Existing Venue", "Add New Venue"])

# All venues table, with filters

with tab_all:
    f1, f2, f3 = st.columns(3)
    with f1:
        city_filter = st.text_input("City", placeholder="e.g. Boston")
    with f2:
        country_filter = st.selectbox("Country", ["All"] + COUNTRIES)
    with f3:
        capacity_filter = st.number_input(
            "Max Capacity (Venues At or Below)", min_value=0, value=0,
            help="Leave at 0 for no capacity limit."
        )

    filter_params = {}
    if city_filter:
        filter_params["city"] = city_filter
    if country_filter != "All":
        filter_params["country"] = country_filter
    if capacity_filter > 0:
        filter_params["capacity"] = capacity_filter

    filtered_venues = get_json("/venue/venues", params=filter_params) or []

    section(f"All Venues ({len(filtered_venues)})")
    if not filtered_venues:
        st.info("No venues match this filter.")
    else:
        frame = pd.DataFrame(filtered_venues)
        existing_columns = [c for c in TABLE_COLUMNS if c in frame.columns]
        st.dataframe(
            frame[existing_columns],
            use_container_width=True,
            hide_index=True,
        )

# Edit existing venue

with tab_edit:
    if not all_venues:
        st.info("No venues found yet.")
    else:
        venue_names = {v["venue_id"]: v["venue_name"] for v in all_venues}
        chosen_id = st.selectbox(
            "Venue to edit",
            options=list(venue_names.keys()),
            format_func=lambda vid: venue_names[vid],
        )
        current = next(v for v in all_venues if v["venue_id"] == chosen_id)

        with st.form("edit_venue_form"):
            name = st.text_input("Venue name", value=current["venue_name"])
            street = st.text_input("Street", value=current.get("street") or "")
            city = st.text_input("City", value=current.get("city") or "")
            state = st.text_input(
                "State / Province", value=current.get("state") or ""
            )
            zip_code = st.text_input("Zip / Postal code", value=current.get("zip") or "")
            country = st.selectbox(
                "Country",
                options=COUNTRIES,
                index=COUNTRIES.index(current["country"])
                if current.get("country") in COUNTRIES else 0,
            )
            accessibility = st.text_input(
                "Accessibility notes", value=current.get("accessibility") or ""
            )
            capacity = st.number_input(
                "Capacity (max)", min_value=1, value=int(current["capacity"])
            )
            manager_id = st.selectbox(
                "Managed by",
                options=list(manager_names.keys()) or [current["managed_by_id"]],
                format_func=lambda mid: manager_names.get(mid, f"Manager #{mid}"),
                index=(
                    list(manager_names.keys()).index(current["managed_by_id"])
                    if current["managed_by_id"] in manager_names
                    else 0
                ),
            )

            if st.form_submit_button("Save changes", type="primary"):
                ok = put_json(f"/venue/venues/{chosen_id}", {
                    "venue_name": name,
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "country": country,
                    "accessibility": accessibility,
                    "capacity": capacity,
                    "managed_by_id": manager_id,
                })
                if ok:
                    st.success(f"{name} updated.")
                    st.rerun()

# Add new venue

with tab_add:
    section("New venue")
    with st.form("add_venue_form"):
        name = st.text_input("Venue name")
        street = st.text_input("Street")
        city = st.text_input("City")
        state = st.text_input("State / Province")
        zip_code = st.text_input("Zip / Postal code")
        country = st.selectbox("Country", options=COUNTRIES)
        accessibility = st.text_input("Accessibility notes")
        capacity = st.number_input("Capacity (max)", min_value=1, value=1000)
        manager_id = st.selectbox(
            "Managed by",
            options=list(manager_names.keys()),
            format_func=lambda mid: manager_names.get(mid, f"Manager #{mid}"),
        ) if manager_names else None

        if st.form_submit_button("Add venue", type="primary"):
            if not name or manager_id is None:
                st.error("Venue name and manager are required.")
            else:
                created = post_json("/venue/venues", {
                    "venue_name": name,
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "country": country,
                    "accessibility": accessibility,
                    "capacity": capacity,
                    "managed_by_id": manager_id,
                })
                if created:
                    st.success(f"{name} added (venue_id {created['venue_id']}).")
                    st.rerun()
