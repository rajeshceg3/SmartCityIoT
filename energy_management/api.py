from flask import Blueprint, request, jsonify, render_template
from dataclasses import asdict

from . import streetlight_manager

energy_bp = Blueprint('energy', __name__, template_folder='templates')

@energy_bp.route('/streetlights', methods=['GET'])
def get_all_streetlights_api():
    """
    Retrieves a list of all streetlights, optionally filtered by status.
    Query parameter: status (e.g., /streetlights?status=ON)
    """
    status_filter = request.args.get('status')
    lights_list = streetlight_manager.list_streetlights(status_filter=status_filter)
    lights_as_dicts = [asdict(light) for light in lights_list]
    return jsonify(lights_as_dicts), 200


@energy_bp.route('/streetlights', methods=['POST'])
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
        energy_bp.logger.error(f"Error creating streetlight: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@energy_bp.route('/streetlights/<string:light_id>', methods=['GET'])
def get_specific_streetlight_api(light_id: str):
    """Retrieves a specific streetlight by its ID."""
    light = streetlight_manager.get_streetlight(light_id)
    if light:
        return jsonify(asdict(light)), 200
    else:
        return jsonify({"error": f"Streetlight with ID '{light_id}' not found"}), 404

@energy_bp.route('/streetlights/<string:light_id>/status', methods=['PUT'])
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
        energy_bp.logger.error(f"Error updating streetlight status: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@energy_bp.route('/streetlights/<string:light_id>/report_fault', methods=['POST'])
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
        energy_bp.logger.error(f"Error reporting fault for streetlight {light_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@energy_bp.route('/dashboard')
def dashboard():
    """Serves the energy management dashboard HTML page."""
    # This will render energy_management/templates/dashboard.html
    return render_template('dashboard.html')

@energy_bp.route('/energy/simulation/run', methods=['POST'])
def run_energy_simulation_api():
    """
    Runs an energy consumption simulation for a given duration.
    Expects JSON payload: {"duration_hours": float}
    Returns the total energy consumed by all streetlights.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    duration_hours = data.get('duration_hours')

    if duration_hours is None:
        return jsonify({"error": "Missing 'duration_hours' in payload"}), 400

    if not isinstance(duration_hours, (int, float)):
        return jsonify({"error": "'duration_hours' must be a number"}), 400

    if duration_hours <= 0:
        return jsonify({"error": "'duration_hours' must be a positive number"}), 400

    try:
        total_consumed = streetlight_manager.simulate_energy_consumption(float(duration_hours))
        return jsonify({"total_energy_consumed_kwh": total_consumed}), 200
    except Exception as e:
        # Log the exception for debugging purposes
        energy_bp.logger.error(f"Error during energy simulation: {e}")
        return jsonify({"error": "An unexpected error occurred during simulation"}), 500

@energy_bp.route('/energy/streetlights/<string:light_id>/adaptive', methods=['PUT'])
def toggle_adaptive_lighting_api(light_id: str):
    """
    Enables or disables adaptive lighting for a specific streetlight.
    Expects JSON payload: {"enabled": bool}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    enabled_value = data.get('enabled')

    if enabled_value is None:
        return jsonify({"error": "Missing 'enabled' field in payload"}), 400

    if not isinstance(enabled_value, bool):
        return jsonify({"error": "'enabled' field must be a boolean"}), 400

    light = streetlight_manager.get_streetlight(light_id)
    if not light:
        return jsonify({"error": f"Streetlight with ID '{light_id}' not found"}), 404

    try:
        light.adaptive_lighting_enabled = enabled_value
        light.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # No need to call _streetlights[light_id] = light, direct modification
        # streetlight_manager._streetlights[light_id] = light # This would be needed if manager copied objects

        return jsonify(asdict(light)), 200
    except Exception as e:
        energy_bp.logger.error(f"Error toggling adaptive lighting for {light_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@energy_bp.route('/energy/adaptive_lighting/apply', methods=['POST'])
def apply_adaptive_lighting_schedule_api():
    """
    Applies the adaptive lighting schedule based on the provided hour.
    Expects JSON payload: {"current_time_hour": int}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    current_time_hour = data.get('current_time_hour')

    if current_time_hour is None:
        return jsonify({"error": "Missing 'current_time_hour' in payload"}), 400

    if not isinstance(current_time_hour, int):
        return jsonify({"error": "'current_time_hour' must be an integer"}), 400

    # Validation for current_time_hour (0-23) is handled by the manager function,
    # but a basic check here can be good practice too.
    # If manager raises ValueError, it will be caught by the generic Exception.

    try:
        result_summary = streetlight_manager.apply_adaptive_lighting_schedule(current_time_hour)
        return jsonify(result_summary), 200
    except ValueError as e: # Catch specific error from manager for bad hour
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        energy_bp.logger.error(f"Error applying adaptive lighting schedule: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
