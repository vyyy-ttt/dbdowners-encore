# pyright: reportArgumentType=false, reportIndexIssue=false, reportCallIssue=false, reportOptionalMemberAccess=false
########################################################
# Maya ("Casual Concertgoer") persona blueprint.
#
# Covers Maya's user stories that are specific to her own
# concert history and reviews. Follow/unfollow lives in the
# separate `followers` blueprint.
#
#   1.1  Write / update / delete a review        (POST / PUT / DELETE)
#   1.2  See personal concert stats              (GET)
#   1.3  View reviews from people she follows     (GET)
#   1.5  Search shows + log a show she attended   (GET / POST)
#   1.6  See how people get to a venue + access   (GET)
#
# Registered in rest_entry.py with url_prefix="/maya".
########################################################

import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

maya = Blueprint("maya", __name__)


# MySQL TIME columns come back as datetime.timedelta, which Flask cannot
# serialize at all, so selecting show.start_time raises TypeError and the route
# 500s. DATE renders as an HTTP date and DECIMAL as a string, neither of which
# is much use to the UI either. Run rows through this before jsonify.

def _time_to_str(delta):
    total_seconds = int(delta.total_seconds())
    sign = "-" if total_seconds < 0 else ""
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def as_json(row):
    if row is None:
        return None

    cleaned = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            cleaned[key] = float(value)
        elif isinstance(value, datetime.timedelta):
            cleaned[key] = _time_to_str(value)
        elif isinstance(value, datetime.datetime):
            cleaned[key] = value.isoformat(sep=" ")
        elif isinstance(value, datetime.date):
            cleaned[key] = value.isoformat()
        else:
            cleaned[key] = value
    return cleaned


def rows_as_json(rows):
    return [as_json(row) for row in rows]


# ------------------------------------------------------------
# 1.5  Search shows (optionally by city / on-or-after a date).
# GET /maya/shows?city=Boston&from_date=2026-08-09
# ------------------------------------------------------------
@maya.route("/shows", methods=["GET"])
def search_shows():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /maya/shows")

        city = request.args.get("city")
        from_date = request.args.get("from_date")

        query = """
            SELECT s.show_id,
                   t.tour_name,
                   a.artist_id,
                   a.artist_name,
                   s.show_date,
                   s.start_time,
                   s.avg_ticket_price,
                   v.venue_id,
                   v.venue_name,
                   v.city,
                   v.state
            FROM `show` s
            JOIN venue  v ON s.venue_id = v.venue_id
            JOIN tour   t ON s.tour_id  = t.tour_id
            JOIN artist a ON t.main_artist_id = a.artist_id
            WHERE 1=1
        """
        params = []

        if city:
            query += " AND v.city = %s"
            params.append(city)
        if from_date:
            query += " AND s.show_date >= %s"
            params.append(from_date)

        query += " ORDER BY s.show_date ASC, s.start_time ASC"

        cursor.execute(query, params)
        shows = rows_as_json(cursor.fetchall())

        current_app.logger.info(f"Retrieved {len(shows)} shows")
        return jsonify(shows), 200
    except Error as e:
        current_app.logger.error(f"DB error in search_shows: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.5 (log a show) — record that Maya attended a show.
# POST /maya/users/<user_id>/shows   body: { "show_id": 1 }
# ------------------------------------------------------------
@maya.route("/users/<int:user_id>/shows", methods=["POST"])
def log_show(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        if not data or "show_id" not in data:
            return jsonify({"error": "Missing required field: show_id"}), 400

        cursor.execute(
            "INSERT INTO user_show (user_id, show_id) VALUES (%s, %s)",
            (user_id, data["show_id"]),
        )
        get_db().commit()
        return jsonify({"message": "Show logged successfully"}), 201
    except Error as e:
        current_app.logger.error(f"DB error in log_show: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.6  Transportation + accessibility info for a venue.
# GET /maya/venues/<venue_id>/transportation
# ------------------------------------------------------------
@maya.route("/venues/<int:venue_id>/transportation", methods=["GET"])
def get_venue_transportation(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /maya/venues/{venue_id}/transportation")

        cursor.execute(
            "SELECT venue_id, venue_name, accessibility FROM venue WHERE venue_id = %s",
            (venue_id,),
        )
        venue = cursor.fetchone()
        if not venue:
            return jsonify({"error": "Venue not found"}), 404

        cursor.execute(
            """SELECT transport_id, transport_type, estimated_cost, instructions
               FROM transportation
               WHERE venue_id = %s
               ORDER BY estimated_cost ASC""",
            (venue_id,),
        )
        venue["transportation"] = cursor.fetchall()

        return jsonify(venue), 200
    except Error as e:
        current_app.logger.error(f"DB error in get_venue_transportation: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.2  Aggregated personal stats for a user.
# GET /maya/users/<user_id>/stats
# ------------------------------------------------------------
@maya.route("/users/<int:user_id>/stats", methods=["GET"])
def get_user_stats(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /maya/users/{user_id}/stats")

        cursor.execute(
            """SELECT COUNT(*)               AS total_shows_attended,
                      AVG(s.avg_ticket_price) AS average_ticket_price
               FROM user_show us
               JOIN `show` s ON us.show_id = s.show_id
               WHERE us.user_id = %s""",
            (user_id,),
        )
        totals = cursor.fetchone()

        cursor.execute(
            """SELECT a.artist_name, COUNT(*) AS times_seen
               FROM user_show us
               JOIN `show` s  ON us.show_id = s.show_id
               JOIN tour   t  ON s.tour_id  = t.tour_id
               JOIN artist a  ON t.main_artist_id = a.artist_id
               WHERE us.user_id = %s
               GROUP BY a.artist_id, a.artist_name
               ORDER BY times_seen DESC
               LIMIT 1""",
            (user_id,),
        )
        most_seen = cursor.fetchone()

        stats = {
            "user_id": user_id,
            "total_shows_attended": totals["total_shows_attended"] if totals else 0,
            "average_ticket_price": (
                float(totals["average_ticket_price"])
                if totals and totals["average_ticket_price"] is not None
                else 0
            ),
            "most_seen_artist": most_seen["artist_name"] if most_seen else None,
            "most_seen_count": most_seen["times_seen"] if most_seen else 0,
        }
        return jsonify(stats), 200
    except Error as e:
        current_app.logger.error(f"DB error in get_user_stats: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.1 / 1.2  All reviews written by a user (their own history).
# GET /maya/users/<user_id>/reviews
# ------------------------------------------------------------
@maya.route("/users/<int:user_id>/reviews", methods=["GET"])
def get_user_reviews(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /maya/users/{user_id}/reviews")
        cursor.execute(
            """SELECT r.review_id,
                      r.rating,
                      r.review_text,
                      r.upload_date,
                      r.last_updated,
                      a.artist_name  AS about_artist,
                      v.venue_name   AS about_venue,
                      s.show_date    AS about_show_date
               FROM review r
               LEFT JOIN artist a ON r.about_artist_id = a.artist_id
               LEFT JOIN venue  v ON r.about_venue_id  = v.venue_id
               LEFT JOIN `show` s ON r.about_show_id   = s.show_id
               WHERE r.author_user_id = %s
               ORDER BY r.upload_date DESC""",
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"DB error in get_user_reviews: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.1  Write a new review for an artist, show, or venue.
# POST /maya/reviews
# body: { author_user_id, rating, review_text,
#         about_artist_id? , about_show_id? , about_venue_id? }
# ------------------------------------------------------------
@maya.route("/reviews", methods=["POST"])
def create_review():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}

        if "author_user_id" not in data or "rating" not in data:
            return jsonify({"error": "Missing required field: author_user_id and rating"}), 400

        targets = [
            data.get("about_artist_id"),
            data.get("about_show_id"),
            data.get("about_venue_id"),
        ]
        if sum(1 for t in targets if t) != 1:
            return jsonify(
                {"error": "Provide exactly one of about_artist_id, about_show_id, about_venue_id"}
            ), 400

        cursor.execute(
            """INSERT INTO review
                   (author_user_id, about_show_id, about_venue_id,
                    about_artist_id, rating, review_text, last_updated)
               VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
            (
                data["author_user_id"],
                data.get("about_show_id"),
                data.get("about_venue_id"),
                data.get("about_artist_id"),
                data["rating"],
                data.get("review_text"),
            ),
        )
        get_db().commit()
        return jsonify(
            {"message": "Review created successfully", "review_id": cursor.lastrowid}
        ), 201
    except Error as e:
        current_app.logger.error(f"DB error in create_review: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.4  Update a review after seeing an artist again.
# PUT /maya/reviews/<review_id>   body: { rating?, review_text? }
# ------------------------------------------------------------
@maya.route("/reviews/<int:review_id>", methods=["PUT"])
def update_review(review_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}

        cursor.execute("SELECT review_id FROM review WHERE review_id = %s", (review_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Review not found"}), 404

        allowed = ["rating", "review_text"]
        update_fields = [f"{f} = %s" for f in allowed if f in data]
        params = [data[f] for f in allowed if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        update_fields.append("last_updated = NOW()")
        params.append(review_id)

        query = f"UPDATE review SET {', '.join(update_fields)} WHERE review_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "Review updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f"DB error in update_review: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.1  Delete one of Maya's own reviews.
# DELETE /maya/reviews/<review_id>
# ------------------------------------------------------------
@maya.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT review_id FROM review WHERE review_id = %s", (review_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Review not found"}), 404

        cursor.execute("DELETE FROM review WHERE review_id = %s", (review_id,))
        get_db().commit()
        return jsonify({"message": "Review deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f"DB error in delete_review: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ------------------------------------------------------------
# 1.3  View reviews from everyone a user follows (friends' feed).
# GET /maya/users/<user_id>/friends-reviews
# ------------------------------------------------------------
@maya.route("/users/<int:user_id>/friends-reviews", methods=["GET"])
def get_friends_reviews(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /maya/users/{user_id}/friends-reviews")
        cursor.execute(
            """SELECT r.review_id,
                      u.username,
                      r.rating,
                      r.review_text,
                      r.upload_date,
                      a.artist_name AS about_artist,
                      v.venue_name  AS about_venue
               FROM follows f
               JOIN review r ON r.author_user_id = f.followee_id
               JOIN user   u ON u.user_id = r.author_user_id
               LEFT JOIN artist a ON r.about_artist_id = a.artist_id
               LEFT JOIN venue  v ON r.about_venue_id  = v.venue_id
               WHERE f.follower_id = %s
               ORDER BY r.upload_date DESC""",
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"DB error in get_friends_reviews: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()