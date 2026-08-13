from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for NGO routes
reviews = Blueprint("reviews", __name__)


# Get all reviews with optional filtering by author, show, venue, artist, show date, and tag
# Example: /review/reviews?author_user_id=12&about_venue_id=1
@reviews.route("/reviews", methods=["GET"])
def get_all_reviews():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /review/reviews')

        # Query parameters are added after the main part of the URL.
        # Example: http://localhost:4000/review/reviews?author_user_id=12
        author_user_id = request.args.get("author_user_id")
        about_show_id = request.args.get("about_show_id")
        about_venue_id = request.args.get("about_venue_id")
        about_artist_id = request.args.get("about_artist_id")
        show_date = request.args.get("show_date")
        tag_id = request.args.get("tag_id")

        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        # The `r` alias is required: every condition below is written as r.<column>
        query = "SELECT DISTINCT r.* FROM review r"
        joins = []
        conditions = ["1=1"]
        params = []

        if show_date:
            joins.append("JOIN `show` s ON r.about_show_id = s.show_id")
            conditions.append("s.show_date = %s")
            params.append(show_date)
 
        if tag_id:
            joins.append("JOIN review_tag rt ON r.review_id = rt.review_id")
            conditions.append("rt.tag_id = %s")
            params.append(tag_id)
 
        if author_user_id:
            conditions.append("r.author_user_id = %s")
            params.append(author_user_id)
        if about_show_id:
            conditions.append("r.about_show_id = %s")
            params.append(about_show_id)
        if about_venue_id:
            conditions.append("r.about_venue_id = %s")
            params.append(about_venue_id)
        if about_artist_id:
            conditions.append("r.about_artist_id = %s")
            params.append(about_artist_id)

        if joins:
            query += " " + " ".join(joins)
        query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        review_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(review_list)} reviews')
        return jsonify(review_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_reviews: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a single review by its ID number
# Example: /review/reviews/1
@reviews.route("/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM review WHERE review_id = %s", (review_id,))
        review = cursor.fetchone()

        if not review:
            return jsonify({"error": "Review not found"}), 404

        return jsonify(review), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new review
# Required fields: author_user_id, rating
# One of the following review subject ids is also required: about_show_id, about_venue_id, about_artist_id
# Example: POST /review/reviews with JSON body
@reviews.route("/reviews", methods=["POST"])
def create_review():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["author_user_id", "rating"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
            
        # A review must be about exactly one of: a show, a venue, or an artist.
        subject_fields = ["about_show_id", "about_venue_id", "about_artist_id"]
        provided_subjects = [f for f in subject_fields if data.get(f) is not None]
        if len(provided_subjects) != 1:
            return jsonify({
                "error": "Exactly one of about_show_id, about_venue_id, or about_artist_id must be provided"
            }), 400

        query = """
            INSERT INTO review (author_user_id, about_show_id, about_venue_id, about_artist_id,
                                 rating, review_text)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["author_user_id"],
            data.get("about_show_id"),
            data.get("about_venue_id"),
            data.get("about_artist_id"),
            data["rating"],
            data.get("review_text"),
        ))

        get_db().commit()
        return jsonify({"message": "Review created successfully", "review_id": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a review — either the author editing rating/text, or a venue/tour manager responding
# Can update rating, review_text, last_updated, responding_tm_id, tm_response, responding_vm_id, vm_response
# Example: PUT /review/reviews/1 with JSON body containing fields to update
@reviews.route("/reviews/<int:review_id>", methods=["PUT"])
def update_review(review_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        cursor.execute("SELECT review_id FROM review WHERE review_id = %s", (review_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Review not found"}), 404

        # Build update query dynamically based on provided fields
        allowed_fields = [
            "rating", "review_text", "last_updated",
            "responding_tm_id", "tm_response",
            "responding_vm_id", "vm_response",
        ]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(review_id)
        query = f"UPDATE review SET {', '.join(update_fields)} WHERE review_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "Review updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a review that violates community guidelines
# Example: DELETE /review/reviews/1
@reviews.route("/reviews/<int:review_id>", methods=["DELETE"])
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
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get platform-wide analytics: review volume by month
# Example: /review/reviews/stats
@reviews.route("/reviews/stats", methods=["GET"])
def get_review_stats():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /review/reviews/stats')
 
        query = """
            SELECT DATE_FORMAT(upload_date, '%Y-%m') AS month, COUNT(review_id) AS review_count
            FROM review
            GROUP BY DATE_FORMAT(upload_date, '%Y-%m')
            ORDER BY month ASC
        """
        cursor.execute(query)
        stats = cursor.fetchall()
 
        return jsonify(stats), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_review_stats: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
