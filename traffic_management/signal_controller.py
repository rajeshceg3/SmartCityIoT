# This file will contain the logic for controlling traffic signals.
# This could include algorithms for adaptive signal timing, pedestrian detection, etc.
from typing import Optional # Added Optional for type hinting

from .models import TrafficSignal # EmergencyVehicle is not directly used by controller yet, but models.py is updated

class SignalController:
    """Manages the state of traffic signals, including emergency preemption."""

    def __init__(self, controller_id: str):
        """
        Initializes the SignalController.
        Args:
            controller_id (str): A unique identifier for this controller.
        """
        self.controller_id = controller_id
        self.signals = {}  # Stores registered TrafficSignal objects, keyed by signal_id
        self.active_emergency_mode = False # Flag to indicate if emergency preemption is active

        # Existing phase logic attributes - can be adapted or used for normal operation
        # self.timing_plan = {}
        # self.current_phase = None
        # self.phase_timer = 0
        # For now, we are focusing on emergency preemption, so regular cycle management is secondary.

    def register_signal(self, signal_object: TrafficSignal):
        """
        Adds a TrafficSignal object to be managed by this controller.
        Args:
            signal_object (TrafficSignal): The traffic signal to register.
        """
        if not isinstance(signal_object, TrafficSignal):
            raise ValueError("Invalid object type. Expected TrafficSignal.")

        if signal_object.id in self.signals:
            print(f"Warning: Signal with ID '{signal_object.id}' is already registered. Overwriting.")

        self.signals[signal_object.id] = signal_object
        print(f"SignalController '{self.controller_id}': Registered signal '{signal_object.id}'.")

    def set_signal_state(self, signal_id: str, new_state_dict: dict):
        """
        Sets the state of a specific traffic signal.
        Args:
            signal_id (str): The ID of the traffic signal to control.
            new_state_dict (dict): The new state for the signal's aspects
                                   (e.g., {"north_south": "green"}).
        """
        if signal_id not in self.signals:
            print(f"SignalController '{self.controller_id}': Error - Signal '{signal_id}' not found.")
            return

        signal = self.signals[signal_id]
        try:
            signal.change_state(new_state_dict)
            print(f"SignalController '{self.controller_id}': Signal '{signal_id}' state changed to {new_state_dict}. Current full state: {signal.current_state}")
        except ValueError as e:
            print(f"SignalController '{self.controller_id}': Error changing state for signal '{signal_id}': {e}")

    def handle_emergency_vehicle_approach(self, vehicle_id: str, vehicle_location: tuple, vehicle_route: list, emergency_state: Optional[dict] = None):
        """
        Handles an approaching emergency vehicle by prioritizing its route.
        Args:
            vehicle_id (str): The ID of the approaching emergency vehicle.
            vehicle_location (tuple): The current location of the vehicle.
            vehicle_route (list): The planned route of the vehicle.
                                  Simplified: first element is the ID of the next signal.
            emergency_state (Optional[dict]): An explicit state to set the signal to.
                                              If None, fallback logic is used.
        """
        print(f"SignalController '{self.controller_id}': Received emergency vehicle approach: ID='{vehicle_id}', Location={vehicle_location}, Route={vehicle_route}, EmergencyStateProvided={emergency_state is not None}")
        self.active_emergency_mode = True # Activate emergency mode

        if not vehicle_route:
            print(f"SignalController '{self.controller_id}': No route information for vehicle '{vehicle_id}'. Cannot determine target signal.")
            return

        # Simplified: Assume the first element of the route is the ID of the *next* signal to prioritize.
        # In a real system, this would involve more complex route/location matching.
        target_signal_id = vehicle_route[0]

        if target_signal_id not in self.signals:
            print(f"SignalController '{self.controller_id}': Target signal '{target_signal_id}' for vehicle '{vehicle_id}' not registered with this controller.")
            return

        relevant_signal = self.signals[target_signal_id]
        print(f"SignalController '{self.controller_id}': Controlling signal '{relevant_signal.id}' for vehicle '{vehicle_id}'.")

        # Simplified prioritization logic:
        # Determine which direction/lanes need to be green.
        # This is highly dependent on intersection layout and signal configuration.
        # For now, let's assume a common scenario: if a signal has "north_south" and "east_west" aspects,
        # we want to make one green and the other red.
        # This needs to be made more generic based on signal.lanes_controlled and vehicle_route.

        # Placeholder: Try to find a "main" and "cross" street aspect and set them.
        # This is a very naive approach.
        # A better approach would be to have pre-defined emergency preemption states for each signal.
        target_state = None
        if emergency_state is not None and isinstance(emergency_state, dict):
            target_state = emergency_state
            print(f"SignalController '{self.controller_id}': Using provided emergency_state {target_state} for signal '{relevant_signal.id}' for EV '{vehicle_id}'.")
        else:
            print(f"SignalController '{self.controller_id}': Warning - No explicit emergency_state provided for EV '{vehicle_id}' at signal '{relevant_signal.id}'. Falling back to naive logic. Provide 'emergency_state' for predictable behavior.")
            current_signal_aspects = relevant_signal.current_state
            if not current_signal_aspects: # Check if current_state itself is empty or None
                 print(f"SignalController '{self.controller_id}': Signal '{relevant_signal.id}' has no current state aspects defined. Cannot determine fallback target state.")
                 return

            # temp_target_state = {} # This variable was in the prompt but not used, so removed.
            if "north_south" in current_signal_aspects and "east_west" in current_signal_aspects:
                # Fallback: set N/S green, E/W red, others red.
                target_state = {aspect: "red" for aspect in current_signal_aspects.keys()}
                target_state["north_south"] = "green"
                # Ensure east_west is red, even if it wasn't in current_signal_aspects (though the check implies it is)
                if "east_west" in target_state: target_state["east_west"] = "red" # Redundant due to above line, but safe.

            elif current_signal_aspects: # current_signal_aspects is not empty
                aspect_keys = list(current_signal_aspects.keys())
                # Fallback: set first aspect to green, others to red
                target_state = {aspect: "red" for aspect in aspect_keys}
                if aspect_keys: # Ensure there's at least one aspect
                    target_state[aspect_keys[0]] = "green"

            if not target_state: # If target_state is still None or empty after fallback logic
                print(f"SignalController '{self.controller_id}': Signal '{relevant_signal.id}' fallback logic failed to determine a target state (e.g. no aspects). Cannot control.")
                return
            print(f"SignalController '{self.controller_id}': Using fallback emergency_state {target_state} for signal '{relevant_signal.id}' for EV '{vehicle_id}'.")

        self.set_signal_state(relevant_signal.id, target_state)

    def end_emergency_preemption(self, signal_id_to_reset: str = None):
        """
        Resets signals to normal operation after an emergency vehicle has passed.
        Args:
            signal_id_to_reset (str, optional): The specific signal that was preempted.
                                                If None, could try to reset all.
        """
        self.active_emergency_mode = False
        print(f"SignalController '{self.controller_id}': Emergency preemption mode ended.")
        if signal_id_to_reset and signal_id_to_reset in self.signals:
            signal = self.signals[signal_id_to_reset]
            # Restore to default timing or a safe state.
            # For now, let's assume we revert to its default_timing's "red" state for all aspects
            # or a predefined "safe" state. This is a placeholder.
            # A better way would be to resume the normal cycle.
            default_red_state = {aspect: "red" for aspect in signal.current_state.keys()}
            if default_red_state:
                 print(f"SignalController '{self.controller_id}': Reverting signal '{signal_id_to_reset}' to default red state: {default_red_state}.")
                 self.set_signal_state(signal_id_to_reset, default_red_state)
            # Ideally, here you would trigger logic to resume the normal timing plan.
            # self.resume_normal_operation(signal_id_to_reset)
        else:
            print(f"SignalController '{self.controller_id}': No specific signal ID to reset or signal not found. Consider logic to reset all managed signals or resume normal cycles.")


    # The methods below are from the previous version and might need adaptation or removal
    # if they conflict with the primary goal of emergency vehicle preemption.
    # For now, they are kept but commented out or made secondary.

    # def set_timing_plan(self, plan):
    #     """Sets a new timing plan for the signals (normal operation)."""
    #     if self.active_emergency_mode:
    #         print(f"SignalController '{self.controller_id}': Cannot set timing plan while emergency mode is active.")
    #         return
    #     self.timing_plan = plan
    #     if self.timing_plan and not self.current_phase:
    #         self.current_phase = list(self.timing_plan.keys())[0]
    #     print(f"SignalController '{self.controller_id}': Timing plan set: {plan}")


    # def update(self, time_delta):
    #     """
    #     Updates signal states based on the timing plan (normal operation).
    #     `time_delta` is the time elapsed since the last update, in seconds.
    #     """
    #     if self.active_emergency_mode:
    #         # print(f"SignalController '{self.controller_id}': Update paused due to active emergency mode.")
    #         return # Preemption overrides normal cycle

    #     if not self.timing_plan or not self.current_phase:
    #         return

    #     self.phase_timer += time_delta
    #     current_phase_duration = self.timing_plan[self.current_phase]

    #     if self.phase_timer >= current_phase_duration:
    #         self.transition_to_next_phase()
    #         self.phase_timer = 0

    # def transition_to_next_phase(self):
    #     """Transitions to the next phase in the normal cycle."""
    #     if self.active_emergency_mode:
    #         return

    #     phase_names = list(self.timing_plan.keys())
    #     if not phase_names: return

    #     current_index = phase_names.index(self.current_phase)
    #     next_index = (current_index + 1) % len(phase_names)
    #     self.current_phase = phase_names[next_index]
    #     print(f"SignalController '{self.controller_id}': Transitioning to phase {self.current_phase}")
        # Actual signal state changes based on phase would be implemented here for normal operation


    def get_signal_current_states(self, signal_id: str = None):
        """
        Returns the current state of a specific signal or all managed signals.
        Args:
            signal_id (str, optional): If provided, returns state for this signal.
                                       Otherwise, returns states for all signals.
        """
        if signal_id:
            if signal_id in self.signals:
                return self.signals[signal_id].current_state
            else:
                return None
        else:
            states = {}
            for s_id, signal_obj in self.signals.items():
                states[s_id] = signal_obj.current_state
            return states

    def __repr__(self):
        return (f"SignalController(id='{self.controller_id}', "
                f"managed_signals={list(self.signals.keys())}, "
                f"emergency_mode={self.active_emergency_mode})")
