import os
from flask import Flask, request, jsonify, render_template # Ensure render_template is here
from dataclasses import asdict
from datetime import datetime # Required for sample data

from . import issue_manager
from .models import ReportedIssue # For type hinting if needed

app = Flask(__name__)
# Configure a basic upload folder.
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads', 'citizen_reporting')


# --- HTML Serving Routes ---

@app.route('/citizen', methods=['GET'])
def citizen_form_page():
    """Serves the citizen report submission form."""
    return render_template('citizen_report_form.html')


@app.route('/citizen/dashboard', methods=['GET'])
def citizen_dashboard_page():
    """Serves the issues dashboard page."""
    return render_template('issues_dashboard.html')


# --- API Endpoints ---

@app.route('/issues', methods=['POST'])
def create_issue_route():
    """Creates a new issue."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    category = data.get('category')
    description = data.get('description')
    location = data.get('location')
    reporter_id = data.get('reporter_id')
    photo_filename = data.get('photo_filename')

    if not all([category, description, location]):
        return jsonify({"error": "Missing required fields: category, description, location"}), 400

    try:
        issue = issue_manager.create_issue(
            category=category,
            description=description,
            location=location,
            reporter_id=reporter_id,
            photo_filename=photo_filename
        )
        return jsonify(asdict(issue)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/issues', methods=['GET'])
def list_issues_route():
    """Lists all issues, with optional filtering."""
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')

    issues = issue_manager.list_issues(
        status_filter=status_filter,
        category_filter=category_filter
    )
    return jsonify([asdict(issue) for issue in issues]), 200


@app.route('/issues/<string:issue_id>', methods=['GET'])
def get_issue_route(issue_id: str):
    """Retrieves a specific issue by its ID."""
    issue = issue_manager.get_issue(issue_id)
    if issue:
        return jsonify(asdict(issue)), 200
    else:
        return jsonify({"error": "Issue not found"}), 404


@app.route('/issues/<string:issue_id>/status', methods=['PUT'])
def update_issue_status_route(issue_id: str):
    """Updates the status of an existing issue."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({"error": "Missing 'status' field in request body"}), 400

    try:
        updated_issue = issue_manager.update_issue_status(issue_id, new_status)
        if updated_issue:
            return jsonify(asdict(updated_issue)), 200
        else:
            return jsonify({"error": "Issue not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


if __name__ == '__main__':
    # Ensure the upload folder exists
    # Using app.root_path to make it relative to the application's root directory
    upload_dir_config = app.config.get('UPLOAD_FOLDER', 'uploads/citizen_reporting')
    if not os.path.isabs(upload_dir_config):
        upload_dir_config = os.path.join(app.root_path, upload_dir_config)

    os.makedirs(upload_dir_config, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir_config # Ensure it's set to the absolute path

    # Create sample data only if no issues exist, to avoid duplication on reload
    if not issue_manager._issues:  # Accessing internal for demo setup
        print("No existing issues found, creating sample data...")
        try:
            issue_manager.create_issue(
                category="Pothole",
                description="Large pothole on Main St near Elm Ave",
                location={"lat": 34.0522, "lon": -118.2437},
                reporter_id="user123"
            )
            # For the second issue, create it then update its status for variety
            issue2 = issue_manager.create_issue(
                category="Streetlight Out",
                description="Streetlight at Oak and 5th is out.",
                location={"lat": 34.0530, "lon": -118.2440}
            )
            if issue2: # Check if issue creation was successful
                issue_manager.update_issue_status(issue2.issue_id, "IN_PROGRESS")

            issue_manager.create_issue(
                category="Pothole",
                description="Another pothole on Broadway",
                location={"lat": 34.0550, "lon": -118.2450},
                reporter_id="user456",
                photo_filename="pothole_broadway.jpg"
            )
            print(f"Sample data created. Total issues: {len(issue_manager.list_issues())}")
        except Exception as e:
            print(f"Error creating sample data: {e}")

    app.run(debug=True, port=5001)
