from flask import Flask, request, jsonify, render_template
from dataclasses import asdict

from . import streetlight_manager
from .models import Streetlight # For type hinting and understanding structure

app = Flask(__name__) # This will be used as a Blueprint in main_dashboard

@app.route('/streetlights', methods=['GET'])
def get_all_streetlights_api():
    """
    Retrieves a list of all streetlights, optionally filtered by status.
    Query parameter: status (e.g., /streetlights?status=ON)
    """
    status_filter = request.args.get('status')
    lights_list = streetlight_manager.list_streetlights(status_filter=status_filter)
    lights_as_dicts = [asdict(light) for light in lights_list]
    return jsonify(lights_as_dicts), 200

@app.route('/streetlights', methods=['POST'])
def create_streetlight_api():
    """
    Creates a new streetlight.
    Expects JSON payload: {"light_id": "str", "location": {"lat": float, "lon": float}, "power_consumption_watts": float (optional)}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        light_id = data['light_id']
        location = data['location']
        power_consumption_watts = data.get('power_consumption_watts') # Optional

        if not isinstance(location, dict) or 'lat' not in location or 'lon' not in location:
            raise KeyError("Location must be a dict with 'lat' and 'lon'")

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except TypeError:
        return jsonify({"error": "Payload must be a JSON object"}), 400

    try:
        new_light = streetlight_manager.add_streetlight(
            light_id=light_id,
            location=location,
            power_consumption_watts=float(power_consumption_watts) if power_consumption_watts is not None else None
        )
        return jsonify(asdict(new_light)), 201
    except ValueError as e: # Handles duplicate light_id or other validation errors from manager/model
        return jsonify({"error": str(e)}), 409 # Conflict or Bad Request
    except Exception as e:
        app.logger.error(f"Error creating streetlight: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/streetlights/<string:light_id>', methods=['GET'])
def get_specific_streetlight_api(light_id: str):
    """Retrieves a specific streetlight by its ID."""
    light = streetlight_manager.get_streetlight(light_id)
    if light:
        return jsonify(asdict(light)), 200
    else:
        return jsonify({"error": f"Streetlight with ID '{light_id}' not found"}), 404

@app.route('/streetlights/<string:light_id>/status', methods=['PUT'])
def update_streetlight_status_api(light_id: str):
    """
    Updates the status and optionally brightness of a streetlight.
    Expects JSON payload: {"status": "str (ON/OFF/FAULTY)", "brightness_level": int (0-100, optional)}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        status = data['status']
        brightness_level = data.get('brightness_level') # Optional

        if brightness_level is not None:
            brightness_level = int(brightness_level)

    except KeyError:
        return jsonify({"error": "Missing required field: 'status'"}), 400
    except (TypeError, ValueError): # If brightness_level is not int, or data is not dict
        return jsonify({"error": "Invalid data type for payload values"}), 400

    try:
        updated_light = streetlight_manager.update_streetlight_status(
            light_id=light_id,
            status=status,
            brightness_level=brightness_level
        )
        if updated_light:
            return jsonify(asdict(updated_light)), 200
        else:
            return jsonify({"error": f"Streetlight with ID '{light_id}' not found for update"}), 404
    except ValueError as e: # Handles invalid status or brightness from manager/model
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error updating streetlight status: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/streetlights/<string:light_id>/report_fault', methods=['POST'])
def report_streetlight_fault_api(light_id: str):
    """
    Reports a fault for a specific streetlight.
    Expects JSON payload: {"description": "str"}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    description = data.get('description', '') # Description is optional for the backend logic for now

    try:
        # This directly uses the report_streetlight_fault function
        faulty_light = streetlight_manager.report_streetlight_fault(light_id, description)

        # Alternative: use update_streetlight_status if report_fault is just a specific case of update
        # faulty_light = streetlight_manager.update_streetlight_status(light_id, status='FAULTY')

        if faulty_light:
            return jsonify(asdict(faulty_light)), 200
        else:
            return jsonify({"error": f"Streetlight with ID '{light_id}' not found to report fault"}), 404
    except Exception as e:
        app.logger.error(f"Error reporting fault for streetlight {light_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/dashboard')
def dashboard():
    """Serves the energy management dashboard HTML page."""
    # This will render energy_management/templates/dashboard.html
    return render_template('dashboard.html')

if __name__ == '__main__':
    # Sample data for direct testing of this API module
    try:
        streetlight_manager._reset_streetlights_data() # Clear previous data
        streetlight_manager.add_streetlight("SL101", {"lat": 34.0522, "lon": -118.2437}, 70)
        streetlight_manager.add_streetlight("SL102", {"lat": 34.0530, "lon": -118.2445}, 70)
        streetlight_manager.update_streetlight_status("SL101", "ON", 80)
        print("Sample streetlights added for testing energy_management.api")
    except ValueError as e:
        print(f"Error adding sample data: {e}")

    app.run(debug=True, port=5003, host='0.0.0.0')
