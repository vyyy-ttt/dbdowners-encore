import logging
logger = logging.getLogger(__name__)

import time

import pandas as pd
import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title("API Endpoint Tester")
st.write(
    "Exercise the transportation and tag routes and inspect the raw request, "
    "status code, and response body for each one."
)

# Inside the compose network the API answers on its service name. If you run
# Streamlit outside Docker, point this at http://localhost:4000 instead.
DEFAULT_BASE_URL = "http://web-api:4000"

with st.sidebar:
    st.divider()
    base_url = st.text_input("API base URL", value=DEFAULT_BASE_URL).rstrip("/")


# ---- Request helpers --------------------------------------------------------

def api_call(method, path, params=None, json_body=None):
    """Make one API request and return everything the UI needs to describe it."""
    url = f"{base_url}{path}"
    started = time.perf_counter()

    try:
        response = requests.request(
            method, url, params=params, json=json_body, timeout=10
        )
    except requests.exceptions.RequestException as e:
        logger.warning(f"{method} {url} failed: {e}")
        return {"reached": False, "error": str(e), "method": method, "url": url}

    elapsed_ms = (time.perf_counter() - started) * 1000

    # Error responses are JSON too, but a stack trace from the dev server is not
    try:
        body = response.json()
    except ValueError:
        body = response.text

    return {
        "reached": True,
        "status": response.status_code,
        "body": body,
        "elapsed_ms": elapsed_ms,
        "method": method,
        "url": response.url,
        "sent": json_body,
    }


def show_result(result, expected_status=None):
    """Render a request/response block for a single api_call() result."""
    if not result["reached"]:
        st.error(f"Could not reach the API: {result['error']}")
        st.info(
            f"Tried `{result['method']} {result['url']}`. Check that the "
            "`web-api` container is running, then confirm the base URL in the sidebar."
        )
        return

    status = result["status"]
    summary = f"`{result['method']} {result['url']}` → **{status}** ({result['elapsed_ms']:.0f} ms)"

    if expected_status is not None and status != expected_status:
        st.error(f"{summary} — expected {expected_status}")
    elif status < 300:
        st.success(summary)
    elif status < 500:
        st.warning(summary)
    else:
        st.error(summary)

    if result.get("sent") is not None:
        with st.expander("Request body"):
            st.json(result["sent"])

    with st.expander("Response body", expanded=True):
        st.json(result["body"])


def show_table(rows):
    """Show a list of dicts as a table, without blowing up on an empty list."""
    if not rows:
        st.info("No rows returned.")
        return
    st.caption(f"{len(rows)} row(s)")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def fetch_list(path):
    """Fetch a collection for populating dropdowns. Returns [] on any failure."""
    result = api_call("GET", path)
    if result["reached"] and result["status"] == 200 and isinstance(result["body"], list):
        return result["body"]
    return []


transport_tab, tag_tab, smoke_tab = st.tabs(
    ["Transportation", "Tags", "Run all checks"]
)


# ---- Transportation --------------------------------------------------------

with transport_tab:
    st.subheader("GET /transport/transportations")
    st.caption("List transportation methods, with optional filters.")

    fcol1, fcol2, fcol3, fcol4 = st.columns([1, 1, 1, 1])
    with fcol1:
        f_venue = st.text_input("venue_id", key="t_f_venue", placeholder="any")
    with fcol2:
        f_type = st.text_input("transport_type", key="t_f_type", placeholder="any")
    with fcol3:
        f_cost = st.text_input("max_cost", key="t_f_cost", placeholder="any")
    with fcol4:
        st.write("")
        run_list = st.button("Send", key="t_list", use_container_width=True)

    if run_list:
        params = {}
        if f_venue:
            params["venue_id"] = f_venue
        if f_type:
            params["transport_type"] = f_type
        if f_cost:
            params["max_cost"] = f_cost

        result = api_call("GET", "/transport/transportations", params=params)
        show_result(result)
        if result["reached"] and result["status"] == 200:
            show_table(result["body"])

    st.divider()

    st.subheader("GET /transport/transportations/<transport_id>")
    gcol1, gcol2 = st.columns([1, 3])
    with gcol1:
        get_id = st.number_input(
            "transport_id", min_value=1, value=1, step=1, key="t_get_id"
        )
    with gcol2:
        st.write("")
        if st.button("Send", key="t_get"):
            show_result(api_call("GET", f"/transport/transportations/{int(get_id)}"))

    st.divider()

    st.subheader("GET /transport/venues/<venue_id>/transportations")
    st.caption("Every transportation method serving one venue, cheapest first.")
    vcol1, vcol2 = st.columns([1, 3])
    with vcol1:
        venue_lookup_id = st.number_input(
            "venue_id", min_value=1, value=1, step=1, key="t_venue_id"
        )
    with vcol2:
        st.write("")
        if st.button("Send", key="t_venue"):
            result = api_call(
                "GET", f"/transport/venues/{int(venue_lookup_id)}/transportations"
            )
            show_result(result)
            if result["reached"] and result["status"] == 200:
                show_table(result["body"])

    st.divider()

    st.subheader("POST /transport/transportations")
    st.caption(
        "Leave transport_id blank to let the API assign the next one. "
        "`venue_id` is required."
    )
    with st.form("t_create"):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_transport_id = st.text_input("transport_id", placeholder="auto")
            new_venue_id = st.text_input("venue_id *", value="1")
        with c2:
            new_cost = st.text_input("estimated_cost", placeholder="e.g. 7.25")
            new_type = st.text_input("transport_type", placeholder="e.g. Commuter Rail")
        with c3:
            new_instructions = st.text_area("instructions", height=120)

        if st.form_submit_button("Send POST"):
            payload = {}
            if new_transport_id:
                payload["transport_id"] = int(new_transport_id)
            if new_venue_id:
                payload["venue_id"] = int(new_venue_id)
            if new_cost:
                payload["estimated_cost"] = float(new_cost)
            if new_type:
                payload["transport_type"] = new_type
            if new_instructions:
                payload["instructions"] = new_instructions

            show_result(
                api_call("POST", "/transport/transportations", json_body=payload)
            )

    st.divider()

    st.subheader("PUT /transport/transportations")
    st.caption(
        "The resources table lists PUT on the collection, so the API accepts the id "
        "in the URL or in the body. Both are wired up here."
    )
    with st.form("t_update"):
        put_shape = st.radio(
            "Request shape",
            ["id in URL", "id in body"],
            horizontal=True,
        )
        u1, u2 = st.columns(2)
        with u1:
            up_id = st.number_input("transport_id", min_value=1, value=1, step=1)
            up_venue = st.text_input("venue_id", placeholder="leave blank to skip")
        with u2:
            up_cost = st.text_input("estimated_cost", placeholder="leave blank to skip")
            up_type = st.text_input("transport_type", placeholder="leave blank to skip")
        up_instructions = st.text_area("instructions", placeholder="leave blank to skip")

        if st.form_submit_button("Send PUT"):
            payload = {}
            if up_venue:
                payload["venue_id"] = int(up_venue)
            if up_cost:
                payload["estimated_cost"] = float(up_cost)
            if up_type:
                payload["transport_type"] = up_type
            if up_instructions:
                payload["instructions"] = up_instructions

            if put_shape == "id in URL":
                path = f"/transport/transportations/{int(up_id)}"
            else:
                path = "/transport/transportations"
                payload["transport_id"] = int(up_id)

            show_result(api_call("PUT", path, json_body=payload))

    st.divider()

    st.subheader("DELETE /transport/transportations")
    st.caption("Also accepts the id in the URL or as a query parameter.")
    d1, d2, d3 = st.columns([1, 1, 2])
    with d1:
        del_id = st.number_input(
            "transport_id", min_value=1, value=1, step=1, key="t_del_id"
        )
    with d2:
        del_shape = st.radio(
            "Shape", ["id in URL", "id in query"], key="t_del_shape"
        )
    with d3:
        st.write("")
        if st.button("Send DELETE", key="t_del", type="primary"):
            if del_shape == "id in URL":
                result = api_call(
                    "DELETE", f"/transport/transportations/{int(del_id)}"
                )
            else:
                result = api_call(
                    "DELETE",
                    "/transport/transportations",
                    params={"transport_id": int(del_id)},
                )
            show_result(result)


# ---- Tags ------------------------------------------------------------------

with tag_tab:
    st.subheader("GET /tag/tags")
    if st.button("Send", key="g_tags"):
        result = api_call("GET", "/tag/tags")
        show_result(result)
        if result["reached"] and result["status"] == 200:
            show_table(result["body"])

    st.divider()

    st.subheader("GET /tag/tags/<tag_id>")
    tcol1, tcol2 = st.columns([1, 3])
    with tcol1:
        tag_get_id = st.number_input(
            "tag_id", min_value=1, value=1, step=1, key="g_tag_id"
        )
    with tcol2:
        st.write("")
        if st.button("Send", key="g_tag"):
            show_result(api_call("GET", f"/tag/tags/{int(tag_get_id)}"))

    st.divider()

    st.subheader("POST /tag/tags")
    st.caption(
        "The resources table creates a tag at `/tags/<tag_id>`. Leaving tag_id "
        "blank posts to the collection instead and lets the API pick the id."
    )
    with st.form("tag_create"):
        p1, p2 = st.columns(2)
        with p1:
            new_tag_id = st.text_input("tag_id", placeholder="auto")
        with p2:
            new_tag_name = st.text_input("tag_name *", placeholder="e.g. Parking")

        if st.form_submit_button("Send POST"):
            payload = {}
            if new_tag_name:
                payload["tag_name"] = new_tag_name

            if new_tag_id:
                path = f"/tag/tags/{int(new_tag_id)}"
            else:
                path = "/tag/tags"

            show_result(api_call("POST", path, json_body=payload))

    st.divider()

    st.subheader("DELETE /tag/tags/<tag_id>")
    st.warning(
        "`review_tag.tag_id` is declared `ON DELETE RESTRICT`, so a tag that any "
        "review still carries cannot be deleted. Every seeded tag is in use, so "
        "deleting one should come back **409** with a `reviews_using_tag` count — "
        "that is the constraint working, not a failure."
    )

    existing_tags = fetch_list("/tag/tags")
    if existing_tags:
        labels = {
            f"{t['tag_id']} — {t['tag_name']}": t["tag_id"] for t in existing_tags
        }
        dcol1, dcol2 = st.columns([2, 1])
        with dcol1:
            chosen = st.selectbox("Tag to delete", list(labels.keys()))
        with dcol2:
            st.write("")
            if st.button("Send DELETE", key="tag_del", type="primary"):
                show_result(api_call("DELETE", f"/tag/tags/{labels[chosen]}"))
    else:
        st.info(
            "Could not load the tag list, so there is nothing to pick from. "
            "Run the GET above to see the underlying error."
        )


# ---- Smoke test ------------------------------------------------------------

with smoke_tab:
    st.subheader("Run every check in sequence")
    st.write(
        "Walks all read routes, then creates a temporary transportation method and "
        "a temporary tag, updates them, and deletes them again. Nothing that was "
        "already in the database is modified or removed."
    )
    st.caption(
        "The in-use tag DELETE case is not included here, because confirming it "
        "would mean deleting a real tag if the constraint were missing. Use the "
        "Tags tab for that one."
    )

    if st.button("Run all checks", type="primary"):
        checks = []

        def record(label, result, expected_status):
            """Run one assertion and remember the outcome for the summary table."""
            if not result["reached"]:
                checks.append({
                    "Check": label,
                    "Expected": expected_status,
                    "Got": "unreachable",
                    "Result": "FAIL",
                })
                return False

            ok = result["status"] == expected_status
            checks.append({
                "Check": label,
                "Expected": expected_status,
                "Got": result["status"],
                "Result": "PASS" if ok else "FAIL",
            })
            return ok

        with st.status("Running checks...", expanded=True) as status_box:
            # --- reads
            st.write("Read routes")
            record("GET /transport/transportations", api_call("GET", "/transport/transportations"), 200)
            record(
                "GET /transport/transportations?venue_id=1",
                api_call("GET", "/transport/transportations", params={"venue_id": 1}),
                200,
            )
            record("GET /transport/transportations/1", api_call("GET", "/transport/transportations/1"), 200)
            record("GET /transport/transportations/9999 (missing)", api_call("GET", "/transport/transportations/9999"), 404)
            record("GET /transport/venues/1/transportations", api_call("GET", "/transport/venues/1/transportations"), 200)
            record("GET /transport/venues/9999/transportations (missing)", api_call("GET", "/transport/venues/9999/transportations"), 404)
            record("GET /tag/tags", api_call("GET", "/tag/tags"), 200)
            record("GET /tag/tags/1", api_call("GET", "/tag/tags/1"), 200)
            record("GET /tag/tags/9999 (missing)", api_call("GET", "/tag/tags/9999"), 404)

            # --- validation
            st.write("Validation routes")
            record(
                "POST transportation, bad venue",
                api_call("POST", "/transport/transportations", json_body={"venue_id": 9999}),
                400,
            )
            record(
                "POST transportation, no venue_id",
                api_call("POST", "/transport/transportations", json_body={"estimated_cost": 1}),
                400,
            )
            record(
                "POST transportation, duplicate id",
                api_call("POST", "/transport/transportations", json_body={"transport_id": 1, "venue_id": 1}),
                409,
            )
            record("POST tag, no tag_name", api_call("POST", "/tag/tags", json_body={}), 400)
            record("PUT transportation, no id in body", api_call("PUT", "/transport/transportations", json_body={"transport_type": "x"}), 400)
            record("DELETE transportation, no id", api_call("DELETE", "/transport/transportations"), 400)

            # --- transportation write cycle
            st.write("Transportation create / update / delete")
            created = api_call(
                "POST",
                "/transport/transportations",
                json_body={
                    "venue_id": 1,
                    "estimated_cost": 4.75,
                    "transport_type": "Endpoint Tester",
                    "instructions": "Temporary row created by the API tester page.",
                },
            )
            temp_transport_id = None
            if record("POST transportation", created, 201):
                temp_transport_id = created["body"].get("transport_id")
                st.write(f"created transport_id `{temp_transport_id}`")

            if temp_transport_id:
                record(
                    "PUT transportation by URL",
                    api_call("PUT", f"/transport/transportations/{temp_transport_id}", json_body={"estimated_cost": 6.5}),
                    200,
                )
                record(
                    "PUT transportation by body",
                    api_call("PUT", "/transport/transportations", json_body={"transport_id": temp_transport_id, "transport_type": "Ferry"}),
                    200,
                )
                verify = api_call("GET", f"/transport/transportations/{temp_transport_id}")
                record("GET the updated row", verify, 200)
                if verify["reached"] and verify["status"] == 200:
                    cost = verify["body"].get("estimated_cost")
                    checks.append({
                        "Check": "estimated_cost is a JSON number, not a string",
                        "Expected": "float",
                        "Got": type(cost).__name__,
                        "Result": "PASS" if isinstance(cost, float) else "FAIL",
                    })
                    checks.append({
                        "Check": "updates round-tripped (6.5 / Ferry)",
                        "Expected": "6.5 / Ferry",
                        "Got": f"{cost} / {verify['body'].get('transport_type')}",
                        "Result": "PASS" if cost == 6.5 and verify["body"].get("transport_type") == "Ferry" else "FAIL",
                    })

                record(
                    "DELETE transportation (cleanup)",
                    api_call("DELETE", f"/transport/transportations/{temp_transport_id}"),
                    200,
                )
                record(
                    "GET deleted transportation",
                    api_call("GET", f"/transport/transportations/{temp_transport_id}"),
                    404,
                )

            # --- tag write cycle
            st.write("Tag create / delete")
            temp_tag_name = f"Endpoint Tester {int(time.time())}"
            created_tag = api_call("POST", "/tag/tags", json_body={"tag_name": temp_tag_name})
            temp_tag_id = None
            if record("POST tag with derived id", created_tag, 201):
                temp_tag_id = created_tag["body"].get("tag_id")
                st.write(f"created tag_id `{temp_tag_id}`")

            if temp_tag_id:
                record("GET the new tag", api_call("GET", f"/tag/tags/{temp_tag_id}"), 200)
                record(
                    "POST tag, duplicate name",
                    api_call("POST", "/tag/tags", json_body={"tag_name": temp_tag_name}),
                    409,
                )
                record(
                    "POST tag, duplicate id",
                    api_call("POST", f"/tag/tags/{temp_tag_id}", json_body={"tag_name": "Something Else"}),
                    409,
                )
                record("DELETE unused tag (cleanup)", api_call("DELETE", f"/tag/tags/{temp_tag_id}"), 200)
                record("GET deleted tag", api_call("GET", f"/tag/tags/{temp_tag_id}"), 404)

            failures = sum(1 for c in checks if c["Result"] == "FAIL")
            if failures:
                status_box.update(label=f"{failures} of {len(checks)} checks failed", state="error")
            else:
                status_box.update(label=f"All {len(checks)} checks passed", state="complete")

        passed = sum(1 for c in checks if c["Result"] == "PASS")
        mcol1, mcol2 = st.columns(2)
        mcol1.metric("Passed", passed)
        mcol2.metric("Failed", len(checks) - passed)

        st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)

        leftovers = []
        if temp_transport_id:
            leftovers.append(f"transportation `{temp_transport_id}`")
        if temp_tag_id:
            leftovers.append(f"tag `{temp_tag_id}`")
        if leftovers and failures:
            st.info(
                "If a cleanup step failed, these temporary records may still be in "
                f"the database: {', '.join(leftovers)}. The tabs above can remove them."
            )
