from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for follower / following routes
followers = Blueprint("followers", __name__)


# Get all users who follow a given user.
# Example: /followers/followers/1
@followers.route("/followers/<int:user_id>", methods=["GET"])
def get_followers(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /followers/followers/{user_id}')

        query = """
            SELECT u.user_id, u.first_name, u.last_name,
                   u.username, f.followed_on
            FROM follows f
            JOIN user u ON f.follower_id = u.user_id
            WHERE f.followee_id = %s
            ORDER BY f.followed_on DESC
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(result)} followers')
        return jsonify(result), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_followers: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all users a given user is following.
# Example: /followers/following/1
@followers.route("/following/<int:user_id>", methods=["GET"])
def get_following(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /followers/following/{user_id}')

        query = """
            SELECT u.user_id, u.first_name, u.last_name,
                   u.username, f.followed_on
            FROM follows f
            JOIN user u ON f.followee_id = u.user_id
            WHERE f.follower_id = %s
            ORDER BY f.followed_on DESC
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(result)} following')
        return jsonify(result), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_following: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Check whether follower_id follows followee_id.
# Example: /followers/follow/1/2
@followers.route("/follow/<int:follower_id>/<int:followee_id>", methods=["GET"])
def check_follow(follower_id, followee_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /followers/follow/{follower_id}/{followee_id}')

        cursor.execute(
            "SELECT followed_on FROM follows WHERE follower_id = %s AND followee_id = %s",
            (follower_id, followee_id),
        )
        row = cursor.fetchone()

        return jsonify({"follows": row is not None}), 200
    except Error as e:
        current_app.logger.error(f'Database error in check_follow: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a follow relationship (follower_id follows followee_id).
# Example: POST /followers/follow/1/2
@followers.route("/follow/<int:follower_id>/<int:followee_id>", methods=["POST"])
def create_follow(follower_id, followee_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        if follower_id == followee_id:
            return jsonify({"error": "A user cannot follow themselves"}), 400

        cursor.execute(
            "INSERT INTO follows (follower_id, followee_id) VALUES (%s, %s)",
            (follower_id, followee_id),
        )
        get_db().commit()
        return jsonify({"message": "Follow relationship created"}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_follow: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a follow relationship (unfollow).
# Example: DELETE /followers/follow/1/2
@followers.route("/follow/<int:follower_id>/<int:followee_id>", methods=["DELETE"])
def delete_follow(follower_id, followee_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "DELETE FROM follows WHERE follower_id = %s AND followee_id = %s",
            (follower_id, followee_id),
        )
        get_db().commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Follow relationship not found"}), 404
        return jsonify({"message": "Unfollowed successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_follow: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()