import logging
logger = logging.getLogger(__name__)

from datetime import date

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section

st.set_page_config(layout='wide', page_title="Encore | Manage Users")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

# Andy is app_admin admin_id 1 in the seed data.
ADMIN_ID = st.session_state.get("admin_id", 1)

TABLE_COLUMNS = [
    "user_id", "first_name", "last_name", "username", "email_address",
    "account_status", "created_at", "last_login",
    "suspended_by_id", "suspended_by_name", "sus_start_date", "sus_end_date",
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


page_header("Manage Users", "View all users, and suspend or reinstate an account.")

# Full unfiltered list for the manage tab's dropdown, independent of
# whatever filter is applied on the All Users tab.
all_users = get_json("/user/users") or []

tab_all, tab_manage = st.tabs(["All Users", "Suspend / Reactivate"])

# All users table, with account_status filter

with tab_all:
    status_filter = st.selectbox("Account Status", ["All", "Active", "Suspended"])

    filter_params = {}
    if status_filter == "Active":
        filter_params["account_status"] = "1"
    elif status_filter == "Suspended":
        filter_params["account_status"] = "0"

    filtered_users = get_json("/user/users", params=filter_params) or []

    section(f"All Users ({len(filtered_users)})")
    if not filtered_users:
        st.info("No users match this filter.")
    else:
        frame = pd.DataFrame(filtered_users)
        existing_columns = [c for c in TABLE_COLUMNS if c in frame.columns]
        st.dataframe(
            frame[existing_columns],
            use_container_width=True,
            hide_index=True,
        )

# Suspend / Reactivate a user's account

with tab_manage:
    if not all_users:
        st.info("No users found yet.")
    else:
        user_labels = {
            u["user_id"]: f"{u['first_name']} {u['last_name']} (@{u['username']})"
            for u in all_users
        }
        chosen_id = st.selectbox(
            "User",
            options=list(user_labels.keys()),
            format_func=lambda uid: user_labels[uid],
        )
        current = next(u for u in all_users if u["user_id"] == chosen_id)

        is_active = bool(current["account_status"])

        section("Current status")
        if is_active:
            st.success(f"{user_labels[chosen_id]} is active.")
        else:
            st.error(
                f"{user_labels[chosen_id]} is suspended "
                f"(since {current.get('sus_start_date') or 'unknown'}) "
                f"by {current.get('suspended_by_name') or 'unknown admin'}."
            )

        st.write("")

        if is_active:
            if st.button("Suspend Account", type="primary"):
                ok = put_json(f"/user/users/{chosen_id}", {
                    "account_status": False,
                    "suspended_by_id": ADMIN_ID,
                    "sus_start_date": date.today().isoformat(),
                    "sus_end_date": None,
                })
                if ok:
                    st.success(f"{user_labels[chosen_id]} has been suspended.")
                    st.rerun()
        else:
            if st.button("Reactivate Account", type="primary"):
                ok = put_json(f"/user/users/{chosen_id}", {
                    "account_status": True,
                    "sus_end_date": date.today().isoformat(),
                })
                if ok:
                    st.success(f"{user_labels[chosen_id]} has been reactivated.")
                    st.rerun()
