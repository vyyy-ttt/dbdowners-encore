from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for transportation routes
transportations = Blueprint("transportations", __name__)


# estimated_cost is a DECIMAL column, so mysql.connector hands it back as a
# decimal.Decimal. Flask can serialize that, but only by turning it into a JSON
# string ("3.50"), which forces every caller to cast it before doing math.
# Converting to float here keeps estimated_cost a JSON number.
def _as_json(row):
    if row is not None and row.get("estimated_cost") is not None:
        row["estimated_cost"] = float(row["estimated_cost"])
    return row


# transportation.venue_id is NOT NULL with a FK to venue, so a bad venue_id
# would surface as a generic 500 from the database. Checking first lets us
# return a 400 that actually says what went wrong.
def _venue_exists(cursor, venue_id):
    cursor.execute("SELECT venue_id FROM venue WHERE venue_id = %s", (venue_id,))
    return cursor.fetchone() is not None


def _transport_exists(cursor, transport_id):
    cursor.execute(
        "SELECT transport_id FROM transportation WHERE transport_id = %s",
        (transport_id,),
    )
    return cursor.fetchone() is not None


# Return a list of transportation methods, with optional filtering by venue,
# type, and cost ceiling
# Example: /transport/transportations?venue_id=1&max_cost=10
@transportations.route("/transportations", methods=["GET"])
def get_all_transportations():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /transport/transportations')

        # Query parameters are added after the main part of the URL.
        # Example: http://localhost:4000/transport/transportations?transport_type=Rideshare
        venue_id = request.args.get("venue_id")
        transport_type = request.args.get("transport_type")
        max_cost = request.args.get("max_cost")

        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT t.transport_id, t.estimated_cost, t.transport_type, t.instructions,
                   t.venue_id, v.venue_name, v.city, v.state
            FROM transportation t
            JOIN venue v ON t.venue_id = v.venue_id
            WHERE 1=1
        """
        params = []

        if venue_id:
            query += " AND t.venue_id = %s"
            params.append(venue_id)
        if transport_type:
            query += " AND t.transport_type = %s"
            params.append(transport_type)
        if max_cost:
            query += " AND t.estimated_cost <= %s"
            params.append(max_cost)

        query += " ORDER BY t.venue_id, t.estimated_cost"

        cursor.execute(query, params)
        transport_list = [_as_json(row) for row in cursor.fetchall()]

        current_app.logger.info(f'Retrieved {len(transport_list)} transportation options')
        return jsonify(transport_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_transportations: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Return the transportation method associated with <transport_id> and all its
# attributes, including the details of the venue it serves
# Example: /transport/transportations/1
@transportations.route("/transportations/<int:transport_id>", methods=["GET"])
def get_transportation(transport_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /transport/transportations/{transport_id}')

        query = """
            SELECT t.transport_id, t.estimated_cost, t.transport_type, t.instructions,
                   t.venue_id, v.venue_name, v.street, v.city, v.state, v.zip,
                   v.accessibility
            FROM transportation t
            JOIN venue v ON t.venue_id = v.venue_id
            WHERE t.transport_id = %s
        """
        cursor.execute(query, (transport_id,))
        transport = cursor.fetchone()

        if not transport:
            return jsonify({"error": "Transportation method not found"}), 404

        return jsonify(_as_json(transport)), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_transportation: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Return every transportation method for one venue, cheapest first.
# Supports user story 1.6 — seeing how to get to a specific venue.
# Example: /transport/venues/1/transportations
@transportations.route("/venues/<int:venue_id>/transportations", methods=["GET"])
def get_venue_transportations(venue_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /transport/venues/{venue_id}/transportations')

        if not _venue_exists(cursor, venue_id):
            return jsonify({"error": "Venue not found"}), 404

        query = """
            SELECT transport_id, estimated_cost, transport_type, instructions, venue_id
            FROM transportation
            WHERE venue_id = %s
            ORDER BY estimated_cost
        """
        cursor.execute(query, (venue_id,))
        return jsonify([_as_json(row) for row in cursor.fetchall()]), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_venue_transportations: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new transportation method
# Required fields: venue_id
# Optional fields: transport_id, estimated_cost, transport_type, instructions
# Example: POST /transport/transportations with JSON body
@transportations.route("/transportations", methods=["POST"])
def create_transportation():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["venue_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        if not _venue_exists(cursor, data["venue_id"]):
            return jsonify({"error": f"Venue {data['venue_id']} does not exist"}), 400

        # transportation.transport_id is a plain INT primary key, not AUTO_INCREMENT,
        # so the database will not assign one and cursor.lastrowid stays 0. The caller
        # can pass an explicit transport_id; otherwise we take the next one after the
        # current max. Two simultaneous inserts could pick the same id and one would
        # lose on the primary key — acceptable here, but making the column
        # AUTO_INCREMENT in encore.sql is the real fix.
        transport_id = data.get("transport_id")
        if transport_id is None:
            cursor.execute("SELECT COALESCE(MAX(transport_id), 0) + 1 AS next_id FROM transportation")
            transport_id = cursor.fetchone()["next_id"]
        elif _transport_exists(cursor, transport_id):
            return jsonify({"error": f"Transport ID {transport_id} already exists"}), 409

        query = """
            INSERT INTO transportation (transport_id, estimated_cost, transport_type, instructions, venue_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            transport_id,
            data.get("estimated_cost"),
            data.get("transport_type"),
            data.get("instructions"),
            data["venue_id"],
        ))

        get_db().commit()
        current_app.logger.info(f'Created transportation method {transport_id}')
        return jsonify({
            "message": "Transportation method created successfully",
            "transport_id": transport_id,
        }), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_transportation: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Shared by both PUT routes below. The resources table lists PUT and DELETE on
# the /transportations row rather than the /transportations/<transport_id> row,
# so both URL shapes are registered and the update logic lives here once.
def _update_transportation(transport_id, data):
    cursor = get_db().cursor(dictionary=True)
    try:
        if not _transport_exists(cursor, transport_id):
            return jsonify({"error": "Transportation method not found"}), 404

        # Moving a method to a different venue still has to satisfy the FK
        if "venue_id" in data and not _venue_exists(cursor, data["venue_id"]):
            return jsonify({"error": f"Venue {data['venue_id']} does not exist"}), 400

        # Build update query dynamically based on provided fields
        allowed_fields = ["estimated_cost", "transport_type", "instructions", "venue_id"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(transport_id)
        query = f"UPDATE transportation SET {', '.join(update_fields)} WHERE transport_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        current_app.logger.info(f'Updated transportation method {transport_id}')
        return jsonify({"message": "Transportation method updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_transportation: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a transportation method, with transport_id supplied in the JSON body
# Example: PUT /transport/transportations with {"transport_id": 1, "estimated_cost": 4.25}
@transportations.route("/transportations", methods=["PUT"])
def update_transportation_from_body():
    data = request.get_json()

    if "transport_id" not in data:
        return jsonify({"error": "Missing required field: transport_id"}), 400

    return _update_transportation(data["transport_id"], data)


# Update the transportation method associated with <transport_id>
# Can update any field except transport_id
# Example: PUT /transport/transportations/1 with JSON body containing fields to update
@transportations.route("/transportations/<int:transport_id>", methods=["PUT"])
def update_transportation(transport_id):
    return _update_transportation(transport_id, request.get_json())


# Shared by both DELETE routes below
def _delete_transportation(transport_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        # No other table references transport_id, so nothing cascades from this
        cursor.execute("DELETE FROM transportation WHERE transport_id = %s", (transport_id,))

        if cursor.rowcount == 0:
            return jsonify({"error": "Transportation method not found"}), 404

        get_db().commit()
        current_app.logger.info(f'Deleted transportation method {transport_id}')
        return jsonify({"message": "Transportation method deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_transportation: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a transportation method, with transport_id supplied in the JSON body
# or as a query parameter
# Example: DELETE /transport/transportations?transport_id=1
@transportations.route("/transportations", methods=["DELETE"])
def delete_transportation_from_body():
    transport_id = request.args.get("transport_id")

    if transport_id is None:
        # silent=True so a DELETE sent with no body at all returns our 400
        # rather than raising a 415/400 out of Flask's JSON parsing
        data = request.get_json(silent=True) or {}
        transport_id = data.get("transport_id")

    if transport_id is None:
        return jsonify({"error": "Missing required field: transport_id"}), 400

    return _delete_transportation(transport_id)


# Delete the transportation method associated with <transport_id>
# Example: DELETE /transport/transportations/1
@transportations.route("/transportations/<int:transport_id>", methods=["DELETE"])
def delete_transportation(transport_id):
    return _delete_transportation(transport_id)
