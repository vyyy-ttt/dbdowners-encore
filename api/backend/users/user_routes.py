from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for user CRUD routes.
# Follow / follower routes live in the separate `followers` blueprint.
users = Blueprint("users", __name__)


# Get all users, with optional filtering by account_status.
# Example: /user/users?account_status=1
@users.route("/users", methods=["GET"])
def get_all_users():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /user/users')

        account_status = request.args.get("account_status")

        query = "SELECT * FROM user WHERE 1=1"
        params = []

        if account_status:
            query += " AND account_status = %s"
            params.append(account_status)

        cursor.execute(query, params)
        user_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(user_list)} users')
        return jsonify(user_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_users: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a single user by id.
# Example: /user/users/1
@users.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /user/users/{user_id}')

        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_user: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new user.
# Example: POST /user/users
# body: { user_id, first_name, last_name, email_address, username }
@users.route("/users", methods=["POST"])
def create_user():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}

        required = ["user_id", "email_address", "username"]
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """INSERT INTO user
                   (user_id, first_name, last_name, email_address, username)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                data["user_id"],
                data.get("first_name"),
                data.get("last_name"),
                data["email_address"],
                data["username"],
            ),
        )
        get_db().commit()
        return jsonify({"message": "User created successfully",
                        "user_id": data["user_id"]}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_user: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a user's account status and/or profile fields.
# Example: PUT /user/users/1  body: { "account_status": 0 }
@users.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}

        cursor.execute("SELECT user_id FROM user WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        allowed = ["account_status", "first_name", "last_name",
                   "email_address", "username", "suspended_by_id"]
        update_fields = [f"{f} = %s" for f in allowed if f in data]
        params = [data[f] for f in allowed if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(user_id)
        query = f"UPDATE user SET {', '.join(update_fields)} WHERE user_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "User updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_user: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a user.
# Example: DELETE /user/users/1
@users.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM user WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
        get_db().commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_user: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()