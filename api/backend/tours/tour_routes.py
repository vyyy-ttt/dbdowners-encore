import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for tours routes
tours = Blueprint("tours", __name__)


# ---- Serialization ---------------------------------------------------------
# Three column types on the tour/show tables do not survive jsonify() as-is:
#
#   TIME     -> datetime.timedelta, which Flask cannot serialize at all, so a
#               route selecting show.start_time raises TypeError and 500s.
#   DATE     -> rendered as an HTTP date ("Sat, 01 Aug 2026 00:00:00 GMT").
#   DECIMAL  -> rendered as a JSON string, so callers must cast before doing
#               any arithmetic.

def _time_to_str(delta):
    total_seconds = int(delta.total_seconds())
    sign = "-" if total_seconds < 0 else ""
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def _as_json(row):
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


def _rows_as_json(rows):
    return [_as_json(row) for row in rows]


def _tour_exists(cursor, tour_id):
    cursor.execute("SELECT tour_id FROM tour WHERE tour_id = %s", (tour_id,))
    return cursor.fetchone() is not None


# Get a list of all tours, with the headlining artist and managing tour manager
# resolved. Optional filters narrow by artist, manager, or a date the tour runs.
# Used by user story 3.1
# Example: /tour/tours?main_artist_id=1&active_on=2026-08-12
@tours.route("/tours", methods=["GET"])
def get_all_tours():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /tour/tours')

        main_artist_id = request.args.get("main_artist_id")
        managed_by_id = request.args.get("managed_by_id")
        active_on = request.args.get("active_on")

        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT t.tour_id, t.tour_name, t.start_date, t.end_date,
                   t.main_artist_id, a.artist_name, a.genre,
                   t.managed_by_id, tm.first_name AS manager_first_name,
                   tm.last_name AS manager_last_name,
                   COUNT(s.show_id) AS show_count
            FROM tour t
            JOIN artist a ON t.main_artist_id = a.artist_id
            JOIN tour_manager tm ON t.managed_by_id = tm.tm_id
            LEFT JOIN `show` s ON s.tour_id = t.tour_id
            WHERE 1=1
        """
        params = []

        if main_artist_id:
            query += " AND t.main_artist_id = %s"
            params.append(main_artist_id)
        if managed_by_id:
            query += " AND t.managed_by_id = %s"
            params.append(managed_by_id)
        if active_on:
            query += " AND t.start_date <= %s AND t.end_date >= %s"
            params.extend([active_on, active_on])

        query += """
            GROUP BY t.tour_id, t.tour_name, t.start_date, t.end_date,
                     t.main_artist_id, a.artist_name, a.genre, t.managed_by_id,
                     tm.first_name, tm.last_name
            ORDER BY t.start_date DESC
        """

        cursor.execute(query, params)
        tour_list = _rows_as_json(cursor.fetchall())

        current_app.logger.info(f'Retrieved {len(tour_list)} tours')
        return jsonify(tour_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_tours: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one tour and all its attributes
# Example: /tour/tours/1
@tours.route("/tours/<int:tour_id>", methods=["GET"])
def get_tour(tour_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /tour/tours/{tour_id}')

        query = """
            SELECT t.tour_id, t.tour_name, t.start_date, t.end_date,
                   t.main_artist_id, a.artist_name, a.genre,
                   t.managed_by_id, tm.first_name AS manager_first_name,
                   tm.last_name AS manager_last_name, tm.email_address AS manager_email
            FROM tour t
            JOIN artist a ON t.main_artist_id = a.artist_id
            JOIN tour_manager tm ON t.managed_by_id = tm.tm_id
            WHERE t.tour_id = %s
        """
        cursor.execute(query, (tour_id,))
        tour = cursor.fetchone()

        if not tour:
            return jsonify({"error": "Tour not found"}), 404

        return jsonify(_as_json(tour)), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_tour: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get every stop on a tour, in date order, with the fan rating for each show.
# This is what lets a tour manager spot patterns city to city.
# Used by user story 3.1
# Example: /tour/tours/1/shows
@tours.route("/tours/<int:tour_id>/shows", methods=["GET"])
def get_tour_shows(tour_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /tour/tours/{tour_id}/shows')

        if not _tour_exists(cursor, tour_id):
            return jsonify({"error": "Tour not found"}), 404

        # Grouping by show keeps the show-level columns correct even though the
        # LEFT JOIN to review repeats a show once per review.
        query = """
            SELECT s.show_id, s.show_date, s.start_time, s.expected_end_time,
                   s.total_attendees, s.avg_ticket_price,
                   s.venue_id, v.venue_name, v.city, v.state, v.capacity,
                   COUNT(r.review_id) AS review_count,
                   AVG(r.rating) AS avg_rating
            FROM `show` s
            JOIN venue v ON s.venue_id = v.venue_id
            LEFT JOIN review r ON r.about_show_id = s.show_id
            WHERE s.tour_id = %s
            GROUP BY s.show_id, s.show_date, s.start_time, s.expected_end_time,
                     s.total_attendees, s.avg_ticket_price, s.venue_id,
                     v.venue_name, v.city, v.state, v.capacity
            ORDER BY s.show_date
        """
        cursor.execute(query, (tour_id,))
        show_list = _rows_as_json(cursor.fetchall())

        current_app.logger.info(f'Retrieved {len(show_list)} shows for tour {tour_id}')
        return jsonify(show_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_tour_shows: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get aggregated stats and ratings across every show on a given tour.
# Used by user story 3.1
# Example: /tour/tours/1/stats
@tours.route("/tours/<int:tour_id>/stats", methods=["GET"])
def get_tour_stats(tour_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /tour/tours/{tour_id}/stats')

        cursor.execute(
            """
            SELECT t.tour_id, t.tour_name, t.start_date, t.end_date, a.artist_name
            FROM tour t
            JOIN artist a ON t.main_artist_id = a.artist_id
            WHERE t.tour_id = %s
            """,
            (tour_id,),
        )
        tour = cursor.fetchone()
        if not tour:
            return jsonify({"error": "Tour not found"}), 404

        # The show totals and the review totals are deliberately two separate
        # queries. Joining review onto show repeats a show row once per review,
        # so SUM(total_attendees) would count that show's attendance several
        # times over. COUNT(DISTINCT ...) protects the counts but not the sums.
        cursor.execute(
            """
            SELECT COUNT(*) AS total_shows,
                   CAST(SUM(total_attendees) AS SIGNED) AS total_attendees,
                   AVG(total_attendees) AS avg_attendees,
                   AVG(avg_ticket_price) AS avg_ticket_price,
                   MIN(show_date) AS first_show_date,
                   MAX(show_date) AS last_show_date
            FROM `show`
            WHERE tour_id = %s
            """,
            (tour_id,),
        )
        show_stats = _as_json(cursor.fetchone()) or {}

        cursor.execute(
            """
            SELECT COUNT(r.review_id) AS total_reviews,
                   AVG(r.rating) AS avg_rating,
                   MIN(r.rating) AS lowest_rating,
                   MAX(r.rating) AS highest_rating
            FROM review r
            JOIN `show` s ON r.about_show_id = s.show_id
            WHERE s.tour_id = %s
            """,
            (tour_id,),
        )
        review_stats = _as_json(cursor.fetchone()) or {}

        # The categories fans reacted to most across the whole tour
        cursor.execute(
            """
            SELECT tg.tag_id, tg.tag_name,
                   COUNT(rt.review_id) AS review_count,
                   AVG(r.rating) AS avg_rating
            FROM review_tag rt
            JOIN tag tg ON rt.tag_id = tg.tag_id
            JOIN review r ON rt.review_id = r.review_id
            JOIN `show` s ON r.about_show_id = s.show_id
            WHERE s.tour_id = %s
            GROUP BY tg.tag_id, tg.tag_name
            ORDER BY review_count DESC, tg.tag_name
            """,
            (tour_id,),
        )
        tag_breakdown = _rows_as_json(cursor.fetchall())

        payload = _as_json(tour)
        payload.update(show_stats)
        payload.update(review_stats)
        payload["tags"] = tag_breakdown

        return jsonify(payload), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_tour_stats: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new tour
# Required fields: tour_name, main_artist_id, managed_by_id
# Example: POST /tour/tours with JSON body
@tours.route("/tours", methods=["POST"])
def create_tour():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}

        required_fields = ["tour_name", "main_artist_id", "managed_by_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute("SELECT artist_id FROM artist WHERE artist_id = %s", (data["main_artist_id"],))
        if not cursor.fetchone():
            return jsonify({"error": f"Artist {data['main_artist_id']} does not exist"}), 400

        cursor.execute("SELECT tm_id FROM tour_manager WHERE tm_id = %s", (data["managed_by_id"],))
        if not cursor.fetchone():
            return jsonify({"error": f"Tour manager {data['managed_by_id']} does not exist"}), 400

        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date and end_date and str(start_date) > str(end_date):
            return jsonify({"error": "start_date must be on or before end_date"}), 400

        # encore.sql declares tour_id as a plain INT primary key, so the database
        # will not assign one and cursor.lastrowid stays 0.
        cursor.execute("SELECT COALESCE(MAX(tour_id), 0) + 1 AS next_id FROM tour")
        tour_id = cursor.fetchone()["next_id"]

        cursor.execute(
            """
            INSERT INTO tour (tour_id, tour_name, start_date, end_date, main_artist_id, managed_by_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (tour_id, data["tour_name"], start_date, end_date,
             data["main_artist_id"], data["managed_by_id"]),
        )
        get_db().commit()

        current_app.logger.info(f'Created tour {tour_id}')
        return jsonify({"message": "Tour created successfully", "tour_id": tour_id}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_tour: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a tour's details
# Example: PUT /tour/tours/1 with JSON body containing fields to update
@tours.route("/tours/<int:tour_id>", methods=["PUT"])
def update_tour(tour_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json(silent=True) or {}

        if not _tour_exists(cursor, tour_id):
            return jsonify({"error": "Tour not found"}), 404

        # Build update query dynamically based on provided fields
        allowed_fields = ["tour_name", "start_date", "end_date",
                          "main_artist_id", "managed_by_id"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(tour_id)
        query = f"UPDATE tour SET {', '.join(update_fields)} WHERE tour_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        current_app.logger.info(f'Updated tour {tour_id}')
        return jsonify({"message": "Tour updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_tour: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a tour. Blocked while shows are still scheduled on it, because
# show.tour_id is a foreign key with no ON DELETE action, so MySQL restricts it.
# Example: DELETE /tour/tours/1
@tours.route("/tours/<int:tour_id>", methods=["DELETE"])
def delete_tour(tour_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        if not _tour_exists(cursor, tour_id):
            return jsonify({"error": "Tour not found"}), 404

        # Without this check the foreign key raises MySQL error 1451 and the
        # caller gets an opaque 500. Counting first lets us say why.
        cursor.execute("SELECT COUNT(*) AS n FROM `show` WHERE tour_id = %s", (tour_id,))
        show_count = cursor.fetchone()["n"]

        if show_count > 0:
            return jsonify({
                "error": "Tour still has shows scheduled and cannot be deleted",
                "shows_on_tour": show_count,
            }), 409

        cursor.execute("DELETE FROM tour WHERE tour_id = %s", (tour_id,))
        get_db().commit()

        current_app.logger.info(f'Deleted tour {tour_id}')
        return jsonify({"message": "Tour deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_tour: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
