# This file will contain the data models for the traffic management system.

class EmergencyVehicle:
    """Represents an emergency vehicle and its status."""
    def __init__(self, vehicle_id: str, type: str, location: tuple, speed: float, route: list, status: str):
        self.id = vehicle_id
        self.type = type  # e.g., "ambulance", "fire_truck", "police_car"
        self.location = location  # e.g., (latitude, longitude) or (x, y)
        self.speed = speed  # e.g., in km/h or m/s
        self.route = route  # List of waypoints or road segments
        self.status = status  # e.g., "en_route_to_emergency", "returning_to_base"

    def update_location(self, new_location: tuple, new_speed: float):
        """Updates the vehicle's current location and speed."""
        self.location = new_location
        self.speed = new_speed

    def update_status(self, new_status: str):
        """Updates the vehicle's operational status."""
        self.status = new_status

    def __repr__(self):
        return (f"EmergencyVehicle(id='{self.id}', type='{self.type}', "
                f"location={self.location}, status='{self.status}')")

class TrafficSignal:
    """Represents a traffic signal with its detailed properties."""
    def __init__(self, signal_id: str, location: tuple, current_state: dict,
                 lanes_controlled: list, default_timing: dict):
        self.id = signal_id
        self.location = location  # e.g., (latitude, longitude)
        # Example: {"north_south": "green", "east_west": "red"}
        # Keys could also be specific lane IDs or signal group IDs.
        self.current_state = current_state
        # Example: ["northbound_main_st", "southbound_main_st", "eastbound_cross_ave"]
        self.lanes_controlled = lanes_controlled
        # Example: {"green": 30, "yellow": 5, "red": 25} (in seconds)
        self.default_timing = default_timing

    def change_state(self, new_state_component: dict):
        """
        Changes a part of the traffic signal's state.
        `new_state_component` is a dictionary with aspects to update,
        e.g., {"north_south": "yellow"}
        """
        # Basic validation: ensure keys in new_state_component are valid signal aspects
        for aspect, state in new_state_component.items():
            if aspect in self.current_state:
                if state in ['red', 'yellow', 'green', 'flashing_red', 'flashing_yellow', 'off']: # Extended states
                    self.current_state[aspect] = state
                else:
                    raise ValueError(f"Invalid state '{state}' for aspect '{aspect}'.")
            else:
                raise ValueError(f"Invalid signal aspect '{aspect}'. Valid aspects: {list(self.current_state.keys())}")

    def get_aspect_state(self, aspect: str):
        """Returns the state of a specific aspect/face of the signal."""
        return self.current_state.get(aspect)

    def __repr__(self):
        return (f"TrafficSignal(id='{self.id}', location={self.location}, "
                f"current_state={self.current_state})")

# class Intersection:
#     """Represents an intersection with multiple traffic signals."""
#     def __init__(self, intersection_id):
#         self.intersection_id = intersection_id
#         self.signals = {}  # Stores TrafficSignal objects, keyed by signal_id
#
#     def add_signal(self, signal: TrafficSignal):
#         """Adds a traffic signal to the intersection."""
#         self.signals[signal.signal_id] = signal
#
#     def get_signal_state(self, signal_id):
#         """Returns the state of a specific traffic signal."""
#         if signal_id in self.signals:
#             return self.signals[signal_id].current_state # Adjusted to new TrafficSignal structure
#         else:
#             return None # Or raise an error
#
#     def __repr__(self):
#         return f"Intersection(intersection_id='{self.intersection_id}', signals={list(self.signals.keys())})"
