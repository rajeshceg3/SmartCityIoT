import unittest
from traffic_management.models import TrafficSignal # EmergencyVehicle not used in tests directly yet
from traffic_management.signal_controller import SignalController

class TestSignalController(unittest.TestCase):
    """Unit tests for the SignalController class, focusing on emergency preemption."""

    def setUp(self):
        """Set up a common environment for tests."""
        # Initialize a SignalController
        self.controller = SignalController(controller_id="TestController01")

        # Create and register sample TrafficSignal objects
        # Signal 1: Typical North/South and East/West intersection signal
        self.initial_state_signal1 = {"north_south": "red", "east_west": "red", "pedestrian_button": "off"}
        self.signal1 = TrafficSignal(
            signal_id="signal_001",
            location=(10, 20),
            current_state=self.initial_state_signal1.copy(), # Use a copy for initial state check
            lanes_controlled=["north_south_traffic", "east_west_traffic", "ped_crossing_A"],
            default_timing={"green": 30, "yellow": 5, "red": 25}
        )
        self.controller.register_signal(self.signal1)

        # Signal 2: A different signal, e.g., for a one-way street or a simpler setup
        self.initial_state_signal2 = {"main_street_flow": "red", "side_street_access": "red"}
        self.signal2 = TrafficSignal(
            signal_id="signal_002",
            location=(30, 40),
            current_state=self.initial_state_signal2.copy(), # Use a copy
            lanes_controlled=["main_st_oneway", "side_st_access_ctrl"],
            default_timing={"green": 40, "red": 20}
        )
        self.controller.register_signal(self.signal2)

        # Store initial states for easy comparison later
        self.signal1_original_full_state = self.signal1.current_state.copy()
        self.signal2_original_full_state = self.signal2.current_state.copy()


    def test_registration(self):
        """Test that signals are registered correctly."""
        self.assertIn("signal_001", self.controller.signals)
        self.assertIn("signal_002", self.controller.signals)
        self.assertEqual(self.controller.signals["signal_001"], self.signal1)

    def test_set_signal_state_valid(self):
        """Test setting a valid state for a registered signal."""
        new_state = {"north_south": "green"}
        self.controller.set_signal_state("signal_001", new_state)
        self.assertEqual(self.controller.signals["signal_001"].current_state["north_south"], "green")
        # Other aspects of signal1 should remain as they were if not specified in new_state
        self.assertEqual(self.controller.signals["signal_001"].current_state["east_west"], self.signal1_original_full_state["east_west"])

    def test_set_signal_state_invalid_signal_id(self):
        """Test setting state for an unregistered signal ID."""
        # This should be handled gracefully by set_signal_state (e.g., print error, not raise exception)
        # No direct assertion on state, but ensure no crash and perhaps check logs if possible (not here)
        self.controller.set_signal_state("signal_999", {"north_south": "green"})
        # Assert that existing signals were not affected
        self.assertEqual(self.controller.signals["signal_001"].current_state, self.signal1_original_full_state)

    def test_handle_emergency_vehicle_approach_prioritizes_correct_signal(self):
        """Test that the correct signal is prioritized for an EV and others are not."""
        vehicle_id = "ambulance_123"
        vehicle_location = (5, 15)  # Approaching signal1
        vehicle_route = ["signal_001", "signal_003"]  # signal_001 is the next relevant signal

        self.controller.handle_emergency_vehicle_approach(vehicle_id, vehicle_location, vehicle_route)

        # Expected state for signal1 based on current SignalController logic:
        # It tries to set the first listed aspect ("north_south") to green and the second ("east_west") to red.
        # If signal1 has "north_south" and "east_west" aspects defined in its current_state:
        # The new fallback logic sets all to red, then north_south to green.
        expected_state_signal1 = {"north_south": "green", "east_west": "red", "pedestrian_button": "red"}
        # If the logic is more generic (first aspect green, rest red):
        # aspects_s1 = list(self.signal1_original_full_state.keys())
        # expected_state_signal1 = {aspects_s1[0]: "green"}
        # for aspect in aspects_s1[1:]:
        #    expected_state_signal1[aspect] = "red"

        self.assertEqual(self.controller.signals["signal_001"].current_state, expected_state_signal1)
        self.assertTrue(self.controller.active_emergency_mode)

        # Ensure signal2 (the unrelated signal) has not changed
        self.assertEqual(self.controller.signals["signal_002"].current_state, self.signal2_original_full_state)

    def test_handle_emergency_vehicle_approach_unknown_signal_in_route(self):
        """Test EV approach when the target signal in route is not registered."""
        vehicle_id = "fire_truck_007"
        vehicle_location = (1, 1)
        vehicle_route = ["signal_999", "signal_001"]  # signal_999 is not registered

        self.controller.handle_emergency_vehicle_approach(vehicle_id, vehicle_location, vehicle_route)

        # No signals should change state
        self.assertEqual(self.controller.signals["signal_001"].current_state, self.signal1_original_full_state)
        self.assertEqual(self.controller.signals["signal_002"].current_state, self.signal2_original_full_state)
        self.assertTrue(self.controller.active_emergency_mode) # Mode might still activate

    def test_handle_emergency_vehicle_approach_empty_route(self):
        """Test EV approach with an empty route."""
        vehicle_id = "police_car_01"
        vehicle_location = (2, 2)
        vehicle_route = []  # Empty route

        self.controller.handle_emergency_vehicle_approach(vehicle_id, vehicle_location, vehicle_route)

        # No signals should change state
        self.assertEqual(self.controller.signals["signal_001"].current_state, self.signal1_original_full_state)
        self.assertEqual(self.controller.signals["signal_002"].current_state, self.signal2_original_full_state)
        self.assertTrue(self.controller.active_emergency_mode) # Mode might still activate

    def test_end_emergency_preemption_resets_signal(self):
        """Test that ending emergency preemption resets the specified signal."""
        vehicle_id = "ambulance_123"
        vehicle_location = (5, 15)
        vehicle_route = ["signal_001", "signal_003"]

        # Trigger preemption first
        self.controller.handle_emergency_vehicle_approach(vehicle_id, vehicle_location, vehicle_route)
        # Verify it changed - this uses the fallback logic
        expected_preempted_state_signal1 = {"north_south": "green", "east_west": "red", "pedestrian_button": "red"}
        self.assertEqual(self.controller.signals["signal_001"].current_state, expected_preempted_state_signal1)
        self.assertTrue(self.controller.active_emergency_mode)

        # Now, end preemption for signal_001
        self.controller.end_emergency_preemption(signal_id_to_reset="signal_001")

        # Controller's end_emergency_preemption logic reverts to an all-red state for specified signal
        expected_reset_state_signal1 = {"north_south": "red", "east_west": "red", "pedestrian_button": "red"} # Assuming all aspects go red
        # This depends on the exact implementation of end_emergency_preemption in SignalController
        # Current implementation of end_emergency_preemption makes all aspects 'red'.
        self.assertEqual(self.controller.signals["signal_001"].current_state, expected_reset_state_signal1)
        self.assertFalse(self.controller.active_emergency_mode)

        # Ensure signal2 was not affected by ending preemption on signal1
        self.assertEqual(self.controller.signals["signal_002"].current_state, self.signal2_original_full_state)

    def test_end_emergency_preemption_no_specific_signal(self):
        """Test ending emergency preemption without specifying a signal."""
        # Activate emergency mode (e.g. by a previous call)
        self.controller.active_emergency_mode = True

        self.controller.end_emergency_preemption() # No specific signal_id
        self.assertFalse(self.controller.active_emergency_mode)
        # In this case, no signal states are actively changed by end_emergency_preemption,
        # but the mode flag is reset. So, original states should persist if they weren't changed.
        self.assertEqual(self.controller.signals["signal_001"].current_state, self.signal1_original_full_state)
        self.assertEqual(self.controller.signals["signal_002"].current_state, self.signal2_original_full_state)

    # Previous tests related to Intersection and phase-based timing might be outdated
    # due to changes in SignalController's __init__ and focus.
    # They are removed or commented out if no longer applicable.
    # For example, SignalController no longer takes an Intersection object directly.

    # def test_initialization(self): ... - this would need rework
    # def test_set_timing_plan(self): ... - this logic is currently secondary in SignalController
    # def test_update_within_phase_duration(self): ...
    # def test_transition_to_next_phase(self): ...
    # def test_full_cycle_phase_transitions(self): ...
    # def test_update_multiple_small_deltas(self): ...
    # def test_emergency_override(self): ... - this was a different method name
    # def test_get_signal_states(self): ... - this method name changed

    def test_handle_emergency_vehicle_approach_with_explicit_emergency_state(self):
        """Test EV approach with an explicit emergency_state provided."""
        vehicle_id = "ambulance_789"
        vehicle_location = (5, 15)
        vehicle_route = ["signal_001"] # Target signal1

        # Define a custom emergency state for signal1
        # signal1 aspects: "north_south", "east_west", "pedestrian_button"
        explicit_state_for_signal1 = {
            "north_south": "green",
            "east_west": "yellow", # Non-standard for preemption, but tests if controller obeys
            "pedestrian_button": "flashing_yellow"
        }
        # Ensure the explicit state is valid for the signal's defined aspects.
        # If signal1 doesn't have 'pedestrian_button': 'flashing_yellow' as a valid state,
        # the TrafficSignal.change_state() might reject it or behave unexpectedly.
        # For this test, we assume these are valid states for demonstration.

        self.controller.handle_emergency_vehicle_approach(
            vehicle_id,
            vehicle_location,
            vehicle_route,
            emergency_state=explicit_state_for_signal1
        )

        self.assertEqual(self.controller.signals["signal_001"].current_state, explicit_state_for_signal1,
                         "Signal 1 state should match the explicit emergency state.")
        self.assertTrue(self.controller.active_emergency_mode)

        # Ensure signal2 (the unrelated signal) has not changed
        self.assertEqual(self.controller.signals["signal_002"].current_state, self.signal2_original_full_state,
                         "Signal 2 state should remain unaffected.")

if __name__ == '__main__':
    unittest.main()
