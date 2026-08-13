from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for NGO routes
venues = Blueprint("venues", __name__)


# Get all venues with optional filtering by city, country, and capacity
# Example: /venue/venues?city=Boston
@venues.route("/venues", methods=["GET"])
def get_all_venues():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /venue/venues')

        city = request.args.get("city")
        country = request.args.get("country")
        capacity = request.args.get("capacity")
 
        query = """
            SELECT v.*,
                   CONCAT(vm.first_name, ' ', vm.last_name) AS manager_name
            FROM venue v
            LEFT JOIN venue_manager vm ON v.managed_by_id = vm.vm_id
            WHERE 1=1
        """
        params = []
 
        if city:
            query += " AND city = %s"
            params.append(city)
        if country:
            query += "AND country = %s"
            params.append(country)
        if capacity:
            query += " AND capacity <= %s"
            params.append(capacity)
 
        cursor.execute(query, params)
        venue_list = cursor.fetchall()
 
        current_app.logger.info(f'Retrieved {len(venue_list)} venues')
        return jsonify(venue_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_venues: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a single venue by its ID number
# Example: /venue/venues/1
@venues.route("/venues/<int:venue_id>", methods=["GET"])
def get_venue(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM venue WHERE venue_id = %s", (venue_id,))
        venue = cursor.fetchone()
 
        if not venue:
            return jsonify({"error": "Venue not found"}), 404
 
        return jsonify(venue), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new venue
# Required fields: venue_name, capacity, managed_by_id
# Example: POST /venue/venues with JSON body
@venues.route("/venues", methods=["POST"])
def create_venue():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["venue_name", "capacity", "managed_by_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
 
        query = """
            INSERT INTO venue (venue_name, street, city, state, zip, country, 
                                accessibility, capacity, managed_by_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["venue_name"],
            data.get("street"),
            data.get("city"),
            data.get("state"),
            data.get("zip"),
            data.get("country", "US"),
            data.get("accessibility"),
            data["capacity"],
            data["managed_by_id"],
        ))
 
        get_db().commit()
        return jsonify({"message": "Venue created successfully", "venue_id": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update an existing venue's information
# Can update any field except venue_id
# Example: PUT /venue/venues/1 with JSON body containing fields to update
@venues.route("/venues/<int:venue_id>", methods=["PUT"])
def update_venue(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        cursor.execute("SELECT venue_id FROM venue WHERE venue_id = %s", (venue_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue not found"}), 404
 
        allowed_fields = [
            "venue_name", "street", "city", "state", "zip", "country",
            "accessibility", "capacity", "managed_by_id",
        ]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]
 
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
 
        params.append(venue_id)
        query = f"UPDATE venue SET {', '.join(update_fields)} WHERE venue_id = %s"
        cursor.execute(query, params)
        get_db().commit()
 
        return jsonify({"message": "Venue updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a venue
# Example: DELETE /venue/venues/1
@venues.route("/venues/<int:venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT venue_id FROM venue WHERE venue_id = %s", (venue_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue not found"}), 404
 
        cursor.execute("DELETE FROM venue WHERE venue_id = %s", (venue_id,))
        get_db().commit()
 
        return jsonify({"message": "Venue deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get reviews about a venue with optional filtering to a specific show date at that venue
# Example: /venue/venues/1/reviews?show_date=2026-07-15
@venues.route("/venues/<int:venue_id>/reviews", methods=["GET"])
def get_venue_reviews(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT venue_id FROM venue WHERE venue_id = %s", (venue_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue not found"}), 404
 
        show_date = request.args.get("show_date")
 
        if show_date:
            query = """
                SELECT r.review_id, r.rating, r.review_text, r.upload_date
                FROM review r
                JOIN `show` s ON r.about_show_id = s.show_id
                WHERE s.venue_id = %s AND s.show_date = %s
            """
            params = [venue_id, show_date]
        else:
            query = """
                SELECT review_id, rating, review_text, upload_date
                FROM review
                WHERE about_venue_id = %s
            """
            params = [venue_id]
 
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get feedback broken down by tag category, for a specific venue
# Example: /venue/venues/1/tags
@venues.route("/venues/<int:venue_id>/tags", methods=["GET"])
def get_venue_tags(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT venue_id FROM venue WHERE venue_id = %s", (venue_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue not found"}), 404
 
        query = """
            SELECT tg.tag_name,
                   AVG(r.rating) AS avg_rating,
                   COUNT(r.review_id) AS review_count
            FROM review_tag rt
            JOIN review r ON rt.review_id = r.review_id
            JOIN tag tg ON rt.tag_id = tg.tag_id
            LEFT JOIN `show` s ON r.about_show_id = s.show_id
            WHERE r.about_venue_id = %s OR s.venue_id = %s
            GROUP BY tg.tag_id, tg.tag_name
            ORDER BY avg_rating DESC
        """
        cursor.execute(query, (venue_id, venue_id))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get aggregated stats across all venues, for comparison, with optional filtering for capacity
# Example: /venue/venues/stats?capacity=20000
@venues.route("/venues/stats", methods=["GET"])
def get_all_venue_stats():
    cursor = get_db().cursor(dictionary=True)
    try:
        capacity = request.args.get("capacity")
 
        query = """
            SELECT v.venue_id, v.venue_name, v.capacity,
                   AVG(r.rating) AS avg_rating, COUNT(r.review_id) AS review_count
            FROM venue v
            JOIN review r ON v.venue_id = r.about_venue_id
            WHERE 1=1
        """
        params = []
 
        if capacity:
            query += " AND v.capacity <= %s"
            params.append(capacity)
 
        query += " GROUP BY v.venue_id, v.venue_name, v.capacity"
        query += " ORDER BY avg_rating DESC"
 
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
 
 
# Get attendance trends over time for shows held at a specific venue, with optional date filtering
# Example: /venue/venues/1/attendance?start_date=2025-01-01&end_date=2026-08-12
@venues.route("/venues/<int:venue_id>/attendance", methods=["GET"])
def get_venue_attendance(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT venue_id FROM venue WHERE venue_id = %s", (venue_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue not found"}), 404
 
        start_date = request.args.get("start_date", "2025-01-01")
        end_date = request.args.get("end_date")
 
        query = """
            SELECT show_date, total_attendees
            FROM `show`
            WHERE venue_id = %s AND show_date >= %s
        """
        params = [venue_id, start_date]
 
        if end_date:
            query += " AND show_date <= %s"
            params.append(end_date)
        else:
            query += " AND show_date <= CURRENT_DATE"
 
        query += " ORDER BY show_date"
 
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
 
 
# Get transportation options for a venue
# Example: /venue/venues/1/transportation
@venues.route("/venues/<int:venue_id>/transportation", methods=["GET"])
def get_venue_transportation(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT venue_id, accessibility FROM venue WHERE venue_id = %s", (venue_id,))
        venue = cursor.fetchone()
        if not venue:
            return jsonify({"error": "Venue not found"}), 404
 
        cursor.execute(
            "SELECT transport_id, transport_type, estimated_cost, instructions "
            "FROM transportation WHERE venue_id = %s",
            (venue_id,)
        )
        venue["transportation_options"] = cursor.fetchall()
 
        return jsonify(venue), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
