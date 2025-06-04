# This file will handle communication aspects of the traffic management system.
# For this iteration, it focuses on centralized communication to a SignalController.

from .signal_controller import SignalController
# from .models import EmergencyVehicle # Not directly using EmergencyVehicle objects as parameters yet

class CentralCommunicator:
    """
    Handles simulated communication from a central point to a SignalController.
    """
    def __init__(self, signal_controller: SignalController, server_id: str = "CentralHub01"):
        """
        Initializes the CentralCommunicator.
        Args:
            signal_controller (SignalController): The signal controller instance to communicate with.
            server_id (str): An identifier for this central communicator/server.
        """
        if not isinstance(signal_controller, SignalController):
            raise ValueError("Invalid signal_controller object. Expected an instance of SignalController.")

        self.signal_controller = signal_controller
        self.server_id = server_id
        print(f"CentralCommunicator '{self.server_id}' initialized and linked to SignalController '{self.signal_controller.controller_id}'.")

    def send_emergency_vehicle_data(self, vehicle_id: str, location: tuple, route: list):
        """
        Simulates sending emergency vehicle data to the linked SignalController.

        Args:
            vehicle_id (str): Unique identifier of the emergency vehicle.
            location (tuple): Current location of the vehicle (e.g., (x, y) or (lat, lon)).
            route (list): Planned route of the vehicle. For the SignalController,
                          the first element is expected to be the ID of the next signal.
        """
        print(f"CentralCommunicator '{self.server_id}': Simulating sending emergency data for vehicle '{vehicle_id}' to controller '{self.signal_controller.controller_id}'.")
        print(f"Data: Vehicle ID='{vehicle_id}', Location={location}, Route={route}")

        if self.signal_controller:
            # Call the SignalController's method to handle this data
            self.signal_controller.handle_emergency_vehicle_approach(
                vehicle_id=vehicle_id,
                vehicle_location=location,
                vehicle_route=route
            )
            print(f"CentralCommunicator '{self.server_id}': Data for vehicle '{vehicle_id}' relayed to SignalController.")
        else:
            print(f"CentralCommunicator '{self.server_id}': Error - No SignalController linked. Cannot send emergency data.")

    def trigger_end_emergency_preemption(self, signal_id_to_reset: str = None):
        """
        Simulates a command to the SignalController to end emergency preemption.
        Args:
            signal_id_to_reset (str, optional): The specific signal that was preempted.
        """
        print(f"CentralCommunicator '{self.server_id}': Simulating command to end emergency preemption for signal '{signal_id_to_reset if signal_id_to_reset else 'any active'}'.")
        if self.signal_controller:
            self.signal_controller.end_emergency_preemption(signal_id_to_reset=signal_id_to_reset)
            print(f"CentralCommunicator '{self.server_id}': End preemption command relayed to SignalController.")
        else:
            print(f"CentralCommunicator '{self.server_id}': Error - No SignalController linked. Cannot send end preemption command.")

    # The methods below are from the previous version and are less relevant now,
    # or would need significant adaptation if multiple controllers were managed.
    # For simplicity with a single linked controller, they are commented out or simplified.

    # def connect_controller(self, controller_id, controller_interface):
    #     """ Retained for conceptual reference, but direct linking is used now. """
    #     print(f"Conceptual: Connect controller {controller_id}. Current model uses direct link.")

    # def disconnect_controller(self, controller_id):
    #     """ Conceptual: Disconnect controller. """
    #     print(f"Conceptual: Disconnect controller {controller_id}. Current model uses direct link.")

    # def broadcast_timing_update(self, new_timing_plan):
    #     """ Sends a new timing plan to the linked controller. """
    #     print(f"CentralCommunicator '{self.server_id}': Broadcasting timing plan to {self.signal_controller.controller_id if self.signal_controller else 'N/A'}.")
    #     if self.signal_controller and hasattr(self.signal_controller, 'set_timing_plan'):
    #         # self.signal_controller.set_timing_plan(new_timing_plan) # Assuming set_timing_plan exists and is relevant
    #         print(f"CentralCommunicator '{self.server_id}': Timing plan sent (conceptual, method may be disabled in SignalController).")
    #     elif self.signal_controller:
    #         print(f"CentralCommunicator '{self.server_id}': SignalController does not have 'set_timing_plan' or it's not active.")
    #     else:
    #         print(f"CentralCommunicator '{self.server_id}': No SignalController linked.")


    # def request_status_from_controller(self):
    #     """ Requests the current status from the linked controller. """
    #     if self.signal_controller:
    #         status = self.signal_controller.get_signal_current_states() # Assuming this method exists
    #         print(f"CentralCommunicator '{self.server_id}': Status from {self.signal_controller.controller_id}: {status}")
    #         return status
    #     else:
    #         print(f"CentralCommunicator '{self.server_id}': No SignalController linked.")
    #         return None

    def __repr__(self):
        linked_controller_id = self.signal_controller.controller_id if self.signal_controller else "None"
        return (f"CentralCommunicator(server_id='{self.server_id}', "
                f"linked_signal_controller='{linked_controller_id}')")

# Example of a controller interface (could be part of SignalController or a separate class)
# class ControllerInterface:
#     def __init__(self, controller_id):
#         self.controller_id = controller_id
#
#     def receive_message(self, message):
#         print(f"Controller {self.controller_id} received message: {message}")
#
#     def update_timing_plan(self, plan):
#         print(f"Controller {self.controller_id} updating timing plan to: {plan}")
#         # Actual logic to update its SignalController instance would go here
#
#     def get_status(self):
#         # Actual logic to get status from its SignalController instance
#         return {"id": self.controller_id, "status": "nominal", "current_phase": "example_phase"}

# V2X (Vehicle-to-Everything) Communication (Conceptual)
# class V2XCommunicator:
#     """
#     Handles V2X communication, enabling vehicles to communicate with
#     infrastructure (V2I) and other vehicles (V2V).
#     """
#     def __init__(self):
#         self.nearby_vehicles = {} # Store information about detected vehicles
#         self.emergency_alerts = []
#
#     def broadcast_signal_phase_and_timing(self, intersection_id, phase_info):
#         """
#         Broadcasts SPaT (Signal Phase and Timing) information to nearby vehicles.
#         `phase_info` could include current phase, time to next phase, etc.
#         """
#         print(f"[V2X] Broadcasting SPaT for intersection {intersection_id}: {phase_info}")
#         # In a real system, this would use DSRC, C-V2X, or other radio tech
#
#     def receive_vehicle_data(self, vehicle_id, data):
#         """
#         Receives data from a vehicle (e.g., speed, location, intent).
#         """
#         self.nearby_vehicles[vehicle_id] = data
#         print(f"[V2X] Received data from vehicle {vehicle_id}: {data}")
#         if data.get("request_priority"):
#             self._handle_priority_request(vehicle_id, data)
#
#     def _handle_priority_request(self, vehicle_id, data):
#         """Handles a priority request from a vehicle (e.g., emergency vehicle)."""
#         print(f"[V2X] Priority request from {vehicle_id} (type: {data.get('vehicle_type', 'unknown')}).")
#         # This would typically involve notifying the relevant SignalController
#         # to initiate an emergency override or green light preemption.
#         # For simulation, we might just log it or trigger a flag.
#
#     def send_emergency_alert(self, alert_message):
#         """Broadcasts an emergency alert to vehicles and infrastructure."""
#         self.emergency_alerts.append(alert_message)
#         print(f"[V2X] Broadcasting emergency alert: {alert_message}")
#
#     def __repr__(self):
#         return f"V2XCommunicator(vehicles_detected={len(self.nearby_vehicles)})"
