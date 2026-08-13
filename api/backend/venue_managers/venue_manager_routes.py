from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for venue manager routes
venue_managers = Blueprint("venue_managers", __name__)


# Get all venue managers
# Example: /vm/venue_managers
@venue_managers.route("/venue_managers", methods=["GET"])
def get_all_venue_managers():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /venue_manager/venue_managers')

        cursor.execute("SELECT * FROM venue_manager")
        manager_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(manager_list)} venue managers')
        return jsonify(manager_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_venue_managers: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a single venue manager by ID
# Example: /vm/venue_managers/1
@venue_managers.route("/venue_managers/<int:vm_id>", methods=["GET"])
def get_venue_manager(vm_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM venue_manager WHERE vm_id = %s", (vm_id,))
        manager = cursor.fetchone()

        if not manager:
            return jsonify({"error": "Venue manager not found"}), 404

        return jsonify(manager), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new venue manager
# Required fields: email_address
# Example: POST /vm/venue_managers with JSON body
@venue_managers.route("/venue_managers", methods=["POST"])
def create_venue_manager():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["email_address"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO venue_manager (first_name, last_name, email_address)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            data.get("first_name"),
            data.get("last_name"),
            data["email_address"],
        ))

        get_db().commit()
        return jsonify({"message": "Venue manager created successfully", "vm_id": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update an existing venue manager's information
# Example: PUT /vm/venue_managers/1 with JSON body containing fields to update
@venue_managers.route("/venue_managers/<int:vm_id>", methods=["PUT"])
def update_venue_manager(vm_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        cursor.execute("SELECT vm_id FROM venue_manager WHERE vm_id = %s", (vm_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue manager not found"}), 404

        allowed_fields = ["first_name", "last_name", "email_address"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(vm_id)
        query = f"UPDATE venue_manager SET {', '.join(update_fields)} WHERE vm_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "Venue manager updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a venue manager
# Example: DELETE /vm/venue_managers/1
@venue_managers.route("/venue_managers/<int:vm_id>", methods=["DELETE"])
def delete_venue_manager(vm_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT vm_id FROM venue_manager WHERE vm_id = %s", (vm_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue manager not found"}), 404

        cursor.execute("DELETE FROM venue_manager WHERE vm_id = %s", (vm_id,))
        get_db().commit()

        return jsonify({"message": "Venue manager deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all venues managed by a specific venue manager
# Example: /vm/venue_managers/1/venues
@venue_managers.route("/venue_managers/<int:vm_id>/venues", methods=["GET"])
def get_venues_for_manager(vm_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT vm_id FROM venue_manager WHERE vm_id = %s", (vm_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Venue manager not found"}), 404

        cursor.execute("SELECT * FROM venue WHERE managed_by_id = %s", (vm_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
