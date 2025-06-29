from flask import Blueprint, jsonify, request, render_template # Added render_template
from traffic_management.signal_controller import SignalController
from traffic_management.simulation import TrafficSimulation
from traffic_management.models import TrafficSignal # Required for simulation setup
import time # Added for unique IDs

# --- Global Instances (for demonstration purposes) ---
# In a production app, state management would need to be more robust (e.g., database, app context)

# Initialize SignalController
# Signals will be registered to this controller instance.
# The simulation setup in TrafficSimulation also creates signals;
# we will use that setup to populate our global_traffic_controller.
global_traffic_controller = SignalController(controller_id="GlobalCtrl001_TrafficAPI")
print(f"Global Traffic Controller '{global_traffic_controller.controller_id}' initialized in traffic_management.api.")

# Use a TrafficSimulation instance to pre-populate signals for the global_traffic_controller
# This way, the API has some signals to manage from the start, based on the simulation's default setup.
# This simulation instance is just for setup; API calls for /simulation/run will create fresh instances.
_setup_sim_instance = TrafficSimulation(sim_id="APISetupSim")
if hasattr(_setup_sim_instance, 'signals') and _setup_sim_instance.signals:
    for signal_id, signal_obj in _setup_sim_instance.signals.items():
        if signal_id not in global_traffic_controller.signals:
            # Create a new signal object for the global controller if needed,
            # or use the one from simulation if its controller is not what we want globally.
            # For simplicity, let's re-register (or register if not present).
            # The TrafficSignal objects themselves are stateful.
            global_traffic_controller.register_signal(signal_obj) # Assumes register_signal can handle existing if needed or we check
            print(f"Registered signal '{signal_id}' from APISetupSim to '{global_traffic_controller.controller_id}'.")
    print(f"Signals registered in '{global_traffic_controller.controller_id}': {list(global_traffic_controller.signals.keys())}")
else:
    print(f"Warning: APISetupSim did not have 'signals' or it was empty. Global controller will have no pre-registered signals from sim.")


traffic_bp = Blueprint('traffic_bp', __name__, url_prefix='/traffic')

# --- API Endpoints ---

@traffic_bp.route('/signals', methods=['GET'])
def list_signals_api():
    """Lists all traffic signals and their current states managed by the global_traffic_controller."""
    states = global_traffic_controller.get_signal_current_states()
    if states is not None:
        # Enhance with more details if available
        detailed_signals = []
        for signal_id, current_state in states.items():
            signal_obj = global_traffic_controller.signals.get(signal_id)
            if signal_obj:
                detailed_signals.append({
                    "signal_id": signal_id,
                    "location": signal_obj.location,
                    "current_state": current_state,
                    "lanes_controlled": signal_obj.lanes_controlled,
                    "default_timing": signal_obj.default_timing,
                })
            else: # Should ideally not happen if states are from controller.signals
                detailed_signals.append({
                    "signal_id": signal_id,
                    "current_state": current_state,
                    "error": "Details not found, object missing from controller.signals"
                })
        return jsonify(detailed_signals), 200
    else:
        return jsonify({"error": "Could not retrieve signal states or no signals registered"}), 404 # 404 if no signals

@traffic_bp.route('/signals/<string:signal_id>', methods=['GET'])
def get_signal_api(signal_id: str):
    """Gets details of a specific signal from the global_traffic_controller."""
    signal_obj = global_traffic_controller.signals.get(signal_id)
    if signal_obj:
        state = signal_obj.current_state # Use the object's current state
        return jsonify({
            "signal_id": signal_id,
            "location": signal_obj.location,
            "lanes_controlled": signal_obj.lanes_controlled,
            "current_state": state,
            "default_timing": signal_obj.default_timing,
            "controller_emergency_mode": global_traffic_controller.active_emergency_mode
        }), 200
    else:
        return jsonify({"error": f"Signal {signal_id} not found in global_traffic_controller."}), 404

@traffic_bp.route('/signals/<string:signal_id>/set_state', methods=['POST'])
def set_signal_state_api(signal_id: str):
    """Allows manual override of a signal's state in the global_traffic_controller."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request must be JSON"}), 400

    if signal_id not in global_traffic_controller.signals:
        return jsonify({"error": f"Signal {signal_id} not registered with the global_traffic_controller."}), 404

    try:
        global_traffic_controller.set_signal_state(signal_id, data)
        updated_state = global_traffic_controller.get_signal_current_states(signal_id)
        return jsonify({"message": f"State for signal {signal_id} updated.", "new_state": updated_state}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Unexpected error in set_signal_state_api for '{signal_id}': {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@traffic_bp.route('/emergency/trigger', methods=['POST'])
def trigger_emergency_api():
    """Triggers emergency preemption for a signal via global_traffic_controller."""
    data = request.get_json()
    if not data: return jsonify({"error": "Request must be JSON"}), 400

    signal_id = data.get('signal_id')
    if not signal_id: return jsonify({"error": "Missing 'signal_id'"}), 400
    if signal_id not in global_traffic_controller.signals:
        return jsonify({"error": f"Target signal '{signal_id}' not registered."}), 404

    vehicle_id = data.get('vehicle_id', 'API_EV_Trigger')
    vehicle_route = [signal_id] # Controller expects target signal in route
    vehicle_location = data.get('location', (0.0, 0.0)) # Default location

    global_traffic_controller.handle_emergency_vehicle_approach(
        vehicle_id=vehicle_id,
        vehicle_location=tuple(vehicle_location) if isinstance(vehicle_location, list) else vehicle_location, # ensure tuple
        vehicle_route=vehicle_route
    )
    return jsonify({
        "message": f"Emergency preemption triggered for signal {signal_id}.",
        "signal_state": global_traffic_controller.get_signal_current_states(signal_id),
        "emergency_mode_active": global_traffic_controller.active_emergency_mode
    }), 200

@traffic_bp.route('/emergency/end', methods=['POST'])
def end_emergency_api():
    """Ends emergency preemption for a signal via global_traffic_controller."""
    data = request.get_json()
    if not data: return jsonify({"error": "Request must be JSON"}), 400
    signal_id = data.get('signal_id')
    if not signal_id: return jsonify({"error": "Missing 'signal_id'"}), 400
    if signal_id not in global_traffic_controller.signals:
         return jsonify({"error": f"Signal '{signal_id}' not registered."}), 404

    global_traffic_controller.end_emergency_preemption(signal_id_to_reset=signal_id)
    return jsonify({
        "message": f"Emergency preemption ended for signal {signal_id}.",
        "signal_state": global_traffic_controller.get_signal_current_states(signal_id),
        "emergency_mode_active": global_traffic_controller.active_emergency_mode
    }), 200

@traffic_bp.route('/simulation/run', methods=['POST'])
def run_simulation_api():
    """Triggers a new run of the TrafficSimulation's scenario."""
    # Each call creates and runs a new, independent simulation instance.
    # Its controller and signals are internal to the simulation run.
    # This does not affect global_traffic_controller unless explicitly designed to.
    sim_run_id = f"APISimRun_{int(time.time())}" # pseudo-unique ID
    current_simulation_instance = TrafficSimulation(sim_id=sim_run_id)
    current_simulation_instance.run_emergency_preemption_scenario() # This method logs to its own .log

    return jsonify({
        "message": "Traffic simulation scenario executed.",
        "simulation_id": current_simulation_instance.sim_id,
        "log_preview": current_simulation_instance.log[-5:] if current_simulation_instance.log else []
    }), 200

@traffic_bp.route('/simulation/log', methods=['GET'])
def get_simulation_log_api():
    """
    Runs a new simulation and returns its full log.
    This endpoint demonstrates fetching a log from a simulation run.
    The log is for a fresh simulation instance created on this GET request.
    """
    sim_log_id = f"APISimLog_{int(time.time())}"
    log_simulation_instance = TrafficSimulation(sim_id=sim_log_id)
    log_simulation_instance.run_emergency_preemption_scenario() # Run to populate the log fully

    if hasattr(log_simulation_instance, 'log') and log_simulation_instance.log:
        return jsonify({
            "simulation_id": log_simulation_instance.sim_id,
            "log_source": "A new simulation run was executed for this log request.",
            "log": log_simulation_instance.log
        }), 200
    else:
        return jsonify({"error": "No simulation log available or simulation failed to produce log."}), 404

@traffic_bp.route('/') # This will be the root of the blueprint, e.g., /traffic/
def dashboard():
    """Serves the main dashboard page for Traffic Management."""
    # The template path is relative to the blueprint's template_folder,
    # or the application's template_folder if not found in blueprint's.
    # If traffic_bp is defined with template_folder='templates',
    # Flask will look for 'traffic_management/templates/traffic/dashboard.html'.
    return render_template('traffic/dashboard.html')
