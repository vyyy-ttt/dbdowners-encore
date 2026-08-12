from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for tag routes
tags = Blueprint("tags", __name__)


def _tag_exists(cursor, tag_id):
    cursor.execute("SELECT tag_id FROM tag WHERE tag_id = %s", (tag_id,))
    return cursor.fetchone() is not None


# Return a list of all tag names
# Example: /tag/tags
@tags.route("/tags", methods=["GET"])
def get_all_tags():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /tag/tags')

        cursor.execute("SELECT tag_id, tag_name FROM tag ORDER BY tag_name")
        tag_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(tag_list)} tags')
        return jsonify(tag_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_tags: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Return the tag name associated with <tag_id>
# Example: /tag/tags/1
@tags.route("/tags/<int:tag_id>", methods=["GET"])
def get_tag(tag_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /tag/tags/{tag_id}')

        cursor.execute("SELECT tag_id, tag_name FROM tag WHERE tag_id = %s", (tag_id,))
        tag = cursor.fetchone()

        if not tag:
            return jsonify({"error": "Tag not found"}), 404

        return jsonify(tag), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_tag: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Shared by both POST routes below.
# tag.tag_name is NOT NULL, so it is always required; tag.tag_id is a plain INT
# primary key rather than AUTO_INCREMENT, so the id has to come from the caller
# or be derived here.
def _create_tag(tag_id, data):
    cursor = get_db().cursor(dictionary=True)
    try:
        if not data or "tag_name" not in data:
            return jsonify({"error": "Missing required field: tag_name"}), 400

        if tag_id is None:
            # Same caveat as transportation: concurrent inserts could pick the
            # same id and one would lose on the primary key. AUTO_INCREMENT on
            # tag.tag_id in encore.sql is the real fix.
            cursor.execute("SELECT COALESCE(MAX(tag_id), 0) + 1 AS next_id FROM tag")
            tag_id = cursor.fetchone()["next_id"]
        elif _tag_exists(cursor, tag_id):
            return jsonify({"error": f"Tag ID {tag_id} already exists"}), 409

        # tag_name is only 50 chars and has no UNIQUE constraint, so duplicate
        # names are legal in the schema. Rejecting them here keeps the tag list
        # usable as a set of filter categories.
        cursor.execute("SELECT tag_id FROM tag WHERE tag_name = %s", (data["tag_name"],))
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                "error": f"A tag named '{data['tag_name']}' already exists",
                "tag_id": existing["tag_id"],
            }), 409

        cursor.execute(
            "INSERT INTO tag (tag_id, tag_name) VALUES (%s, %s)",
            (tag_id, data["tag_name"]),
        )
        get_db().commit()

        current_app.logger.info(f'Created tag {tag_id}')
        return jsonify({"message": "Tag created successfully", "tag_id": tag_id}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_tag: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new tag with the given <tag_id>
# Required fields: tag_name
# Example: POST /tag/tags/5 with {"tag_name": "Parking"}
@tags.route("/tags/<int:tag_id>", methods=["POST"])
def create_tag_with_id(tag_id):
    return _create_tag(tag_id, request.get_json(silent=True))


# Create a new tag and let the API assign the next tag_id. Not in the resources
# table, but without it a caller has to invent an unused id before it can add a
# tag, which a form in the app has no good way to do.
# Example: POST /tag/tags with {"tag_name": "Parking"}
@tags.route("/tags", methods=["POST"])
def create_tag():
    data = request.get_json(silent=True) or {}
    return _create_tag(data.get("tag_id"), data)


# Delete a tag
# Blocked while any review still carries the tag, because review_tag.tag_id is
# declared ON DELETE RESTRICT.
# Example: DELETE /tag/tags/5
@tags.route("/tags/<int:tag_id>", methods=["DELETE"])
def delete_tag(tag_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        if not _tag_exists(cursor, tag_id):
            return jsonify({"error": "Tag not found"}), 404

        # Without this check the RESTRICT constraint raises MySQL error 1451 and
        # the caller gets an opaque 500. Counting first lets us say why instead.
        cursor.execute(
            "SELECT COUNT(*) AS usage_count FROM review_tag WHERE tag_id = %s",
            (tag_id,),
        )
        usage_count = cursor.fetchone()["usage_count"]

        if usage_count > 0:
            current_app.logger.info(f'Refused to delete tag {tag_id}, used by {usage_count} reviews')
            return jsonify({
                "error": "Tag is still applied to reviews and cannot be deleted",
                "reviews_using_tag": usage_count,
            }), 409

        cursor.execute("DELETE FROM tag WHERE tag_id = %s", (tag_id,))
        get_db().commit()

        current_app.logger.info(f'Deleted tag {tag_id}')
        return jsonify({"message": "Tag deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_tag: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
