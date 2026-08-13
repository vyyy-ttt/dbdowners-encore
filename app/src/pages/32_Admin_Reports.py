import logging
logger = logging.getLogger(__name__)

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import apply_theme, page_header, section

st.set_page_config(layout='wide', page_title="Encore | Reports")

SideBarLinks()
apply_theme()

API = "http://web-api:4000"

TABLE_COLUMNS = [
    "report_id", "report_type", "is_resolved",
    "reporter_id", "reporter_username",
    "target_user_id", "target_username",
    "target_review_id", "review_author_username",
    "reason",
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


def delete_json(path):
    try:
        response = requests.delete(f"{API}{path}", timeout=10)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API}: {e}")
        return False
    if response.status_code != 200:
        st.warning(f"`DELETE {path}` returned {response.status_code}.")
        return False
    return True


page_header("Reports", "All reports filed on the platform.")

# ---- Filter bar --------------------------------------------------------------

f1, f2 = st.columns(2)
with f1:
    status_choice = st.selectbox("Resolution Status", ["All", "Unresolved", "Resolved"])
with f2:
    type_choice = st.selectbox("Report Type", ["All", "Review", "User"])

params = {}
if status_choice != "All":
    params["is_resolved"] = "true" if status_choice == "Resolved" else "false"
if type_choice != "All":
    params["report_type"] = type_choice

reports = get_json("/report/reports", params=params) or []

# ---- Full table ---------------------------------------------------------

section(f"All Reports ({len(reports)})")

if not reports:
    st.info("No reports match this filter.")
else:
    frame = pd.DataFrame(reports)
    existing_columns = [c for c in TABLE_COLUMNS if c in frame.columns]
    st.dataframe(
        frame[existing_columns],
        use_container_width=True,
        hide_index=True,
    )

st.write("")

# Actionable widgets for unresolved reports

unresolved = [r for r in reports if not r["is_resolved"]]

if unresolved:
    section(f"Needs Action ({len(unresolved)})")

    for row in unresolved:
        with st.container(border=True):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(f"**Report #{row['report_id']}** · {row['report_type']}")
                if row["report_type"] == "review":
                    st.caption(
                        f"Target review #{row['target_review_id']} "
                        f"by @{row.get('reviewed_username', 'unknown')}"
                    )
                else:
                    st.caption(
                        f"Target user #{row['target_user_id']} "
                        f"(@{row.get('target_username', 'unknown')})"
                    )
                st.caption(f"Reported by @{row.get('reporter_username', 'unknown')}")
                st.write(row.get("reason") or "_No reason given._")

            with col_actions:
                if st.button(
                    "Mark Resolved",
                    key=f"resolve_{row['report_id']}",
                    use_container_width=True,
                ):
                    if put_json(f"/report/reports/{row['report_id']}",
                                {"is_resolved": True}):
                        st.success("Marked Resolved.")
                        st.rerun()

                if row["report_type"] == "review":
                    review_id = row["target_review_id"]
                    confirm_key = f"confirm_delete_{review_id}"

                    if not st.session_state.get(confirm_key, False):
                        if st.button(
                            "Delete Review",
                            key=f"delete_{row['report_id']}",
                            use_container_width=True,
                        ):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("Delete this review permanently?")
                        yes, no = st.columns(2)
                        with yes:
                            if st.button(
                                "Yes, delete",
                                key=f"confirm_yes_{row['report_id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                if delete_json(f"/review/reviews/{review_id}"):
                                    st.success("Review deleted.")
                                    del st.session_state[confirm_key]
                                    st.rerun()
                        with no:
                            if st.button(
                                "Cancel",
                                key=f"confirm_no_{row['report_id']}",
                                use_container_width=True,
                            ):
                                del st.session_state[confirm_key]
                                st.rerun()
                else:
                    st.caption("Suspend this user from the Manage Users page.")
