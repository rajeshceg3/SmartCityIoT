import datetime # Not directly used in API functions but good practice if time manipulation was needed
from flask import Flask, request, jsonify, render_template
from dataclasses import asdict # To convert dataclass instances to dicts

# Importing from our existing modules
from .models import TrashBin # Primarily for type hinting and understanding data structures
from . import bin_manager # Import the module itself to call its functions
from . import route_manager # Import the module itself to call its functions

app = Flask(__name__)

# --- Bin Endpoints ---

@app.route('/bins', methods=['GET'])
def get_all_bins_api():
    """
    Retrieves a list of all trash bins, optionally filtered by status.
    Query parameter: status (e.g., /bins?status=FULL)
    """
    status_filter = request.args.get('status')
    bins_list = bin_manager.list_bins(status_filter=status_filter)
    # Convert list of TrashBin objects to list of dictionaries
    bins_as_dicts = [asdict(b) for b in bins_list]
    return jsonify(bins_as_dicts), 200

@app.route('/bins', methods=['POST'])
def create_new_bin_api():
    """
    Creates a new trash bin.
    Expects JSON payload: {"bin_id": "str", "location": {"lat": float, "lon": float}, "capacity_gallons": float}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        bin_id = data['bin_id']
        location = data['location']
        capacity_gallons = data['capacity_gallons']

        if not isinstance(location, dict) or 'lat' not in location or 'lon' not in location:
            raise KeyError("Location must be a dict with 'lat' and 'lon'")

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except TypeError: # If data is not a dict
        return jsonify({"error": "Payload must be a JSON object"}), 400


    try:
        new_bin = bin_manager.add_bin(
            bin_id=bin_id,
            location=location,
            capacity_gallons=float(capacity_gallons) # Ensure capacity is float
        )
        return jsonify(asdict(new_bin)), 201
    except ValueError as e: # Handles duplicate bin_id
        return jsonify({"error": str(e)}), 409 # Conflict
    except Exception as e: # Catch any other unexpected errors
        app.logger.error(f"Error creating bin: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/bins/<string:bin_id>', methods=['GET'])
def get_specific_bin_api(bin_id: str):
    """
    Retrieves a specific trash bin by its ID.
    """
    bin_obj = bin_manager.get_bin(bin_id)
    if bin_obj:
        return jsonify(asdict(bin_obj)), 200
    else:
        return jsonify({"error": f"Bin with ID '{bin_id}' not found"}), 404

@app.route('/bins/<string:bin_id>/sensor_data', methods=['PUT'])
def update_bin_sensor_data_api(bin_id: str):
    """
    Updates the fill level of a specific trash bin from sensor data.
    Expects JSON payload: {"fill_level": float}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        fill_level = data['fill_level']
    except KeyError:
        return jsonify({"error": "Missing required field: 'fill_level'"}), 400
    except TypeError: # If data is not a dict
        return jsonify({"error": "Payload must be a JSON object"}), 400

    try:
        updated_bin = bin_manager.update_bin_from_sensor_data(bin_id, float(fill_level))
        if updated_bin:
            return jsonify(asdict(updated_bin)), 200
        else:
            return jsonify({"error": f"Bin with ID '{bin_id}' not found for update"}), 404
    except ValueError as e: # e.g. if fill_level is not a float
         return jsonify({"error": f"Invalid data for fill_level: {e}"}), 400
    except Exception as e: # Catch any other unexpected errors
        app.logger.error(f"Error updating bin sensor data: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# --- Route Endpoints ---

@app.route('/routes', methods=['GET'])
def get_all_routes_api():
    """
    Retrieves a list of all collection routes, optionally filtered by status.
    Query parameter: status (e.g., /routes?status=PENDING)
    """
    status_filter = request.args.get('status')
    routes_list = route_manager.list_routes(status_filter=status_filter)
    routes_as_dicts = [asdict(r) for r in routes_list]
    return jsonify(routes_as_dicts), 200

@app.route('/routes/generate', methods=['POST'])
def create_new_route_api():
    """
    Generates a new collection route.
    Expects JSON payload: {"assigned_truck_id": "str"}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        assigned_truck_id = data['assigned_truck_id']
    except KeyError:
        return jsonify({"error": "Missing required field: 'assigned_truck_id'"}), 400
    except TypeError: # If data is not a dict
        return jsonify({"error": "Payload must be a JSON object"}), 400

    try:
        new_route = route_manager.generate_route(assigned_truck_id=assigned_truck_id)
        if new_route:
            return jsonify(asdict(new_route)), 201
        else:
            # No full bins were found to generate a route.
            return jsonify({"message": "No full bins to generate a route for at this time."}), 200
    except Exception as e: # Catch any other unexpected errors during route generation
        app.logger.error(f"Error generating route: {e}")
        return jsonify({"error": "An unexpected error occurred during route generation"}), 500


@app.route('/routes/<string:route_id>', methods=['GET'])
def get_specific_route_api(route_id: str):
    """
    Retrieves a specific collection route by its ID.
    """
    route_obj = route_manager.get_route(route_id)
    if route_obj:
        return jsonify(asdict(route_obj)), 200
    else:
        return jsonify({"error": f"Route with ID '{route_id}' not found"}), 404

@app.route('/routes/<string:route_id>/status', methods=['PUT'])
def update_specific_route_status_api(route_id: str):
    """
    Updates the status of a specific collection route.
    Expects JSON payload: {"status": "str"} (e.g., "IN_PROGRESS", "COMPLETED")
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        new_status = data['status']
    except KeyError:
        return jsonify({"error": "Missing required field: 'status'"}), 400
    except TypeError: # If data is not a dict
        return jsonify({"error": "Payload must be a JSON object"}), 400

    try:
        updated_route = route_manager.update_route_status(route_id, new_status)
        if updated_route:
            return jsonify(asdict(updated_route)), 200
        else:
            # This implies route_id was not found.
            return jsonify({"error": f"Route with ID '{route_id}' not found for status update"}), 404
    except Exception as e: # Catch any other unexpected errors
        app.logger.error(f"Error updating route status: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/dashboard')
def dashboard():
    """Serves the main dashboard HTML page."""
    # Assumes 'index.html' is in a 'templates' folder
    # relative to where the Flask app is defined (i.e., waste_management/templates/index.html)
    # Flask's default template folder is 'templates' co-located with the app module or blueprint.
    # Since api.py is in waste_management, and templates is in waste_management/templates,
    # this should work if Flask is run with waste_management as part of the Python path
    # or if the app's root_path is correctly inferred.
    return render_template('index.html')

if __name__ == '__main__':
    # For demonstration, add some sample data using bin_manager directly.
    # This helps if running the API directly and wanting some initial data.
    # It's important that this is idempotent or handles existing data if the server reloads.

    # Clear existing bins and routes for a clean start when running directly,
    # useful for development and testing this specific script.
    # In a real deployment, you wouldn't typically clear data like this on startup.
    if bin_manager._bins:
        bin_manager._bins.clear()
    if route_manager._routes:
        route_manager._routes.clear()

    print("Attempting to add sample data for API testing...")
    try:
        b1 = bin_manager.add_bin("bin1", {"lat": 10.0, "lon": 20.0}, 100.0)
        print(f"Added sample bin: {b1.bin_id}")
        b2 = bin_manager.add_bin("bin2", {"lat": 10.05, "lon": 20.05}, 120.0)
        print(f"Added sample bin: {b2.bin_id}")

        updated_b1 = bin_manager.update_bin_from_sensor_data("bin1", 90.0)
        if updated_b1:
            print(f"Updated sample bin {updated_b1.bin_id} to status {updated_b1.status}")

    except ValueError as e:
        print(f"Sample data setup error (possibly already exists or other): {e}")
    except Exception as e:
        print(f"An unexpected error occurred during sample data setup: {e}")

    print("Starting Flask server...")
    app.run(debug=True, port=5000, host='0.0.0.0')
