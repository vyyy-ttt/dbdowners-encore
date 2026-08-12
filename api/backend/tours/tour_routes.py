from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for tours routes
tours = Blueprint("tours", __name__)


# Get aggregated stats and ratings across every show on a given tour.
# Example: /tour/tours/1/stats
@tours.route("/tours/<int:tour_id>/stats", methods=["GET"])
def get_tour_stats(tour_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /tour/tours/{tour_id}/stats')

        query = """
            SELECT t.tour_id,
                   t.tour_name,
                   a.artist_name,
                   COUNT(DISTINCT s.show_id)   AS total_shows,
                   COUNT(r.review_id)          AS total_reviews,
                   AVG(r.rating)               AS avg_rating,
                   SUM(s.total_attendees)      AS total_attendees
            FROM tour t
            JOIN artist a  ON t.main_artist_id = a.artist_id
            LEFT JOIN `show` s ON s.tour_id = t.tour_id
            LEFT JOIN review r ON r.about_show_id = s.show_id
            WHERE t.tour_id = %s
            GROUP BY t.tour_id, t.tour_name, a.artist_name
        """
        cursor.execute(query, (tour_id,))
        stats = cursor.fetchone()

        if not stats:
            return jsonify({"error": "Tour not found"}), 404

        current_app.logger.info(f'Retrieved stats for tour {tour_id}')
        return jsonify(stats), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_tour_stats: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()