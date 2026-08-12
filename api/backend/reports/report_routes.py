from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for NGO routes
reports = Blueprint("reports", __name__)


# Get all Reports with optional filtering by report type and resolved status
# Example: /report/reports?report_type=review&is_resolved=false
@reports.route("/reports", methods=["GET"])
def get_all_reports():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /report/reports')

        # Query parameters are added after the main part of the URL.
        # Example: http://localhost:4000/report/reports?report_type=review
        report_type = request.args.get("report_type")
        is_resolved = request.args.get("is_resolved")

        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = "SELECT * FROM report WHERE 1=1"
        params = []

        if report_type:
            query += " AND report_type = %s"
            params.append(report_type)
        if is_resolved:
            query += " AND is_resolved = %s"
            params.append(is_resolved)


        cursor.execute(query, params)
        report_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(report_list)} reports')
        return jsonify(report_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_reportss: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a single report by its ID number
# Example: /report/reports/1
@reports.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM report WHERE report_id = %s", (report_id,))
        report = cursor.fetchone()

        if not report:
            return jsonify({"error": "Report not found"}), 404

        return jsonify(report), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new report
# Required fields: reporter_id, report_type
# Example: POST /report/reports with JSON body
@reports.route("/reports", methods=["POST"])
def create_report():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["reporter_id", "report_type"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO report (reporter_id, target_user_id, target_review_id, report_type, reason, is_resolved)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["reporter_id"],
            data.get("target_user_id"),
            data.get("target_review_id"),
            data["report_type"],
            data.get("reason"),
            data.get("is_resolved", False),
        ))

        get_db().commit()
        return jsonify({"message": "Report created successfully", "report_id": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a report
# Can update only is_resolved
# Example: PUT /ngo/ngos/1 with JSON body containing fields to update
@reports.route("/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        cursor.execute("SELECT report_id FROM report WHERE report_id = %s", (report_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Report not found"}), 404

        # Build update query dynamically based on provided fields
        allowed_fields = ["reason", "is_resolved"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(report_id)
        query = f"UPDATE report SET {', '.join(update_fields)} WHERE report_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "Report updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all reported reviews
# Example: /report/reports/reviews?is_resolved=false
@reports.route("/reports/reviews", methods=["GET"])
def get_reported_reviews():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /report/reports/reviews')
 
        is_resolved = request.args.get("is_resolved", "false")
 
        query = """
            SELECT r.report_id, rv.review_id, rv.review_text, rv.rating,
                   r.report_type, r.reason, r.is_resolved
            FROM report r
            JOIN review rv ON r.target_review_id = rv.review_id
            WHERE r.is_resolved = %s
        """
        cursor.execute(query, (is_resolved,))
        reported_reviews = cursor.fetchall()
 
        current_app.logger.info(f'Retrieved {len(reported_reviews)} reported reviews')
        return jsonify(reported_reviews), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_reported_reviews: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
