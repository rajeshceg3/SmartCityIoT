import unittest
from .. import streetlight_manager
from ..models import Streetlight # Assuming models.py is in the parent directory of tests/
from typing import Dict

class TestStreetlightManager(unittest.TestCase):

    def setUp(self):
        """Clear streetlight data before each test."""
        # Access the internal dictionary for clearing, or use a dedicated reset function if available
        streetlight_manager._reset_streetlights_data()
        # streetlight_manager._streetlights.clear()

    def test_add_streetlight_success(self):
        """Test adding a new streetlight successfully."""
        light = streetlight_manager.add_streetlight("SL001", {"lat": 10, "lon": 20}, 60)
        self.assertIsInstance(light, Streetlight)
        self.assertEqual(light.light_id, "SL001")
        self.assertEqual(light.location, {"lat": 10, "lon": 20})
        self.assertEqual(light.power_consumption_watts, 60)
        self.assertEqual(light.status, "OFF") # Default
        self.assertEqual(light.brightness_level, 0) # Default
        self.assertIn("SL001", streetlight_manager._streetlights)

    def test_add_streetlight_duplicate_id(self):
        """Test adding a streetlight with a duplicate ID."""
        streetlight_manager.add_streetlight("SL002", {"lat": 11, "lon": 21})
        with self.assertRaisesRegex(ValueError, "Streetlight with ID 'SL002' already exists."):
            streetlight_manager.add_streetlight("SL002", {"lat": 12, "lon": 22})

    def test_get_streetlight_found(self):
        """Test retrieving an existing streetlight."""
        streetlight_manager.add_streetlight("SL003", {"lat": 12, "lon": 22})
        light = streetlight_manager.get_streetlight("SL003")
        self.assertIsNotNone(light)
        self.assertEqual(light.light_id, "SL003")

    def test_get_streetlight_not_found(self):
        """Test retrieving a non-existent streetlight."""
        light = streetlight_manager.get_streetlight("SL999")
        self.assertIsNone(light)

    def test_list_streetlights_empty(self):
        """Test listing streetlights when none are added."""
        lights = streetlight_manager.list_streetlights()
        self.assertEqual(len(lights), 0)

    def test_list_streetlights_with_items(self):
        """Test listing streetlights when some are added."""
        streetlight_manager.add_streetlight("SL004", {"lat": 13, "lon": 23})
        streetlight_manager.add_streetlight("SL005", {"lat": 14, "lon": 24})
        lights = streetlight_manager.list_streetlights()
        self.assertEqual(len(lights), 2)
        light_ids = {light.light_id for light in lights}
        self.assertSetEqual(light_ids, {"SL004", "SL005"})

    def test_list_streetlights_with_status_filter(self):
        """Test listing streetlights filtered by status."""
        streetlight_manager.add_streetlight("SL006", {"lat": 15, "lon": 25}) # Default OFF
        sl007 = streetlight_manager.add_streetlight("SL007", {"lat": 16, "lon": 26})
        streetlight_manager.update_streetlight_status("SL007", "ON", 75)

        off_lights = streetlight_manager.list_streetlights(status_filter="OFF")
        self.assertEqual(len(off_lights), 1)
        self.assertEqual(off_lights[0].light_id, "SL006")

        on_lights = streetlight_manager.list_streetlights(status_filter="ON")
        self.assertEqual(len(on_lights), 1)
        self.assertEqual(on_lights[0].light_id, "SL007")

        faulty_lights = streetlight_manager.list_streetlights(status_filter="FAULTY")
        self.assertEqual(len(faulty_lights), 0)

    def test_list_streetlights_with_invalid_status_filter(self):
        """Test listing streetlights with an invalid status filter."""
        streetlight_manager.add_streetlight("SL008", {"lat": 17, "lon": 27})
        lights = streetlight_manager.list_streetlights(status_filter="UNKNOWN_STATUS")
        self.assertEqual(len(lights), 0) # Expect empty list for invalid filter

    def test_update_streetlight_status_success(self):
        """Test updating a streetlight's status and brightness successfully."""
        streetlight_manager.add_streetlight("SL009", {"lat": 18, "lon": 28})
        updated_light = streetlight_manager.update_streetlight_status("SL009", "ON", 90)
        self.assertIsNotNone(updated_light)
        self.assertEqual(updated_light.status, "ON")
        self.assertEqual(updated_light.brightness_level, 90)
        self.assertNotEqual(updated_light.last_updated, Streetlight("temp", {}).last_updated) # Check timestamp updated

    def test_update_streetlight_status_turn_off(self):
        """Test that brightness goes to 0 when status is set to OFF."""
        streetlight_manager.add_streetlight("SL010", {"lat": 19, "lon": 29})
        streetlight_manager.update_streetlight_status("SL010", "ON", 100) # Turn ON first
        updated_light = streetlight_manager.update_streetlight_status("SL010", "OFF")
        self.assertEqual(updated_light.status, "OFF")
        self.assertEqual(updated_light.brightness_level, 0)

    def test_update_streetlight_status_turn_on_default_brightness(self):
        """Test that brightness goes to default (e.g., 100) if turned ON from 0 brightness without explicit level."""
        streetlight_manager.add_streetlight("SL011", {"lat": 20, "lon": 30}) # Starts OFF, brightness 0
        updated_light = streetlight_manager.update_streetlight_status("SL011", "ON")
        self.assertEqual(updated_light.status, "ON")
        self.assertEqual(updated_light.brightness_level, 100) # Default ON brightness

    def test_update_streetlight_status_invalid_status(self):
        """Test updating with an invalid status value."""
        streetlight_manager.add_streetlight("SL012", {"lat": 21, "lon": 31})
        with self.assertRaisesRegex(ValueError, "Status must be one of 'ON', 'OFF', or 'FAULTY'."):
            streetlight_manager.update_streetlight_status("SL012", "BROKEN")

    def test_update_streetlight_status_invalid_brightness(self):
        """Test updating with an invalid brightness level."""
        streetlight_manager.add_streetlight("SL013", {"lat": 22, "lon": 32})
        with self.assertRaisesRegex(ValueError, "Brightness level must be between 0 and 100."):
            streetlight_manager.update_streetlight_status("SL013", "ON", 150)
        with self.assertRaisesRegex(ValueError, "Brightness level must be between 0 and 100."):
            streetlight_manager.update_streetlight_status("SL013", "ON", -10)

    def test_update_streetlight_status_not_found(self):
        """Test updating a non-existent streetlight."""
        updated_light = streetlight_manager.update_streetlight_status("SL998", "ON")
        self.assertIsNone(updated_light)

    def test_report_streetlight_fault_success(self):
        """Test reporting a fault for a streetlight."""
        streetlight_manager.add_streetlight("SL014", {"lat": 23, "lon": 33})
        faulty_light = streetlight_manager.report_streetlight_fault("SL014", "Flickering badly")
        self.assertIsNotNone(faulty_light)
        self.assertEqual(faulty_light.status, "FAULTY")
        # self.assertEqual(faulty_light.brightness_level, 0) # Or specific fault brightness if defined
        self.assertNotEqual(faulty_light.last_updated, Streetlight("temp", {}).last_updated)

    def test_report_streetlight_fault_not_found(self):
        """Test reporting a fault for a non-existent streetlight."""
        faulty_light = streetlight_manager.report_streetlight_fault("SL997", "Does not exist")
        self.assertIsNone(faulty_light)

class TestSimulateEnergyConsumption(unittest.TestCase):
    def setUp(self):
        streetlight_manager._reset_streetlights_data()
        # Light 1: Will be ON, 100W, 100% brightness
        self.sl1 = streetlight_manager.add_streetlight("SL1", {"lat": 1, "lon": 1}, 100)
        streetlight_manager.update_streetlight_status("SL1", "ON", 100)
        self.sl1.current_energy_usage = 0.0 # Explicitly set for clarity in tests

        # Light 2: Will be ON, 50W, 50% brightness
        self.sl2 = streetlight_manager.add_streetlight("SL2", {"lat": 2, "lon": 2}, 50)
        streetlight_manager.update_streetlight_status("SL2", "ON", 50)
        self.sl2.current_energy_usage = 0.0

        # Light 3: Will be OFF
        self.sl3 = streetlight_manager.add_streetlight("SL3", {"lat": 3, "lon": 3}, 100)
        streetlight_manager.update_streetlight_status("SL3", "OFF", 0)
        self.sl3.current_energy_usage = 0.0

        # Light 4: ON, but 0 power_consumption_watts
        self.sl4 = streetlight_manager.add_streetlight("SL4", {"lat": 4, "lon": 4}, 0)
        streetlight_manager.update_streetlight_status("SL4", "ON", 100)
        self.sl4.current_energy_usage = 0.0

        # Light 5: ON, but None power_consumption_watts
        self.sl5 = streetlight_manager.add_streetlight("SL5", {"lat": 5, "lon": 5}, None)
        streetlight_manager.update_streetlight_status("SL5", "ON", 100)
        self.sl5.current_energy_usage = 0.0


    def test_simulate_energy_consumption_basic(self):
        """Test basic energy simulation for 2 hours."""
        duration = 2.0 # hours
        expected_sl1_consumption = (100 * (100/100) * duration) / 1000  # 0.2 kWh
        expected_sl2_consumption = (50 * (50/100) * duration) / 1000   # 0.05 kWh

        total_consumed = streetlight_manager.simulate_energy_consumption(duration)

        self.assertAlmostEqual(self.sl1.current_energy_usage, expected_sl1_consumption)
        self.assertAlmostEqual(self.sl2.current_energy_usage, expected_sl2_consumption)
        self.assertEqual(self.sl3.current_energy_usage, 0.0) # OFF light
        self.assertEqual(self.sl4.current_energy_usage, 0.0) # 0 Watt light
        self.assertEqual(self.sl5.current_energy_usage, 0.0) # None Watt light

        expected_total_consumption = expected_sl1_consumption + expected_sl2_consumption
        self.assertAlmostEqual(total_consumed, expected_total_consumption)

    def test_simulate_energy_consumption_zero_duration(self):
        """Test simulation with zero duration."""
        self.sl1.current_energy_usage = 1.0 # Pre-existing usage

        total_consumed = streetlight_manager.simulate_energy_consumption(0.0)

        self.assertEqual(self.sl1.current_energy_usage, 1.0) # Should not change
        self.assertEqual(self.sl2.current_energy_usage, 0.0)
        self.assertEqual(total_consumed, 0.0)

    def test_simulate_energy_consumption_negative_duration(self):
        """Test simulation with negative duration."""
        self.sl1.current_energy_usage = 1.0 # Pre-existing usage

        total_consumed = streetlight_manager.simulate_energy_consumption(-1.0)

        self.assertEqual(self.sl1.current_energy_usage, 1.0) # Should not change
        self.assertEqual(self.sl2.current_energy_usage, 0.0)
        self.assertEqual(total_consumed, 0.0)

    def test_simulate_energy_consumption_accumulation(self):
        """Test that energy consumption accumulates over multiple simulations."""
        duration1 = 1.0 # hours
        expected_sl1_consumption1 = (100 * 1.0 * duration1) / 1000  # 0.1 kWh
        expected_sl2_consumption1 = (50 * 0.5 * duration1) / 1000   # 0.025 kWh

        total_consumed1 = streetlight_manager.simulate_energy_consumption(duration1)
        self.assertAlmostEqual(self.sl1.current_energy_usage, expected_sl1_consumption1)
        self.assertAlmostEqual(self.sl2.current_energy_usage, expected_sl2_consumption1)
        self.assertAlmostEqual(total_consumed1, expected_sl1_consumption1 + expected_sl2_consumption1)

        duration2 = 2.0 # hours
        expected_sl1_consumption2 = (100 * 1.0 * duration2) / 1000  # 0.2 kWh
        expected_sl2_consumption2 = (50 * 0.5 * duration2) / 1000   # 0.05 kWh

        total_consumed2 = streetlight_manager.simulate_energy_consumption(duration2)
        self.assertAlmostEqual(self.sl1.current_energy_usage, expected_sl1_consumption1 + expected_sl1_consumption2)
        self.assertAlmostEqual(self.sl2.current_energy_usage, expected_sl2_consumption1 + expected_sl2_consumption2)
        self.assertAlmostEqual(total_consumed2, expected_sl1_consumption2 + expected_sl2_consumption2)


class TestApplyAdaptiveLightingSchedule(unittest.TestCase):
    def setUp(self):
        streetlight_manager._reset_streetlights_data()
        # Light 1: Adaptive enabled, initial state to be changed
        self.adapt_light = streetlight_manager.add_streetlight("ADAPT01", {"lat": 10, "lon": 10}, 75)
        self.adapt_light.adaptive_lighting_enabled = True
        self.adapt_light.status = "ON"
        self.adapt_light.brightness_level = 77 # Arbitrary initial
        self.initial_last_updated_adapt = self.adapt_light.last_updated

        # Light 2: Adaptive disabled, should not change
        self.non_adapt_light = streetlight_manager.add_streetlight("NONADAPT02", {"lat": 11, "lon": 11}, 75)
        self.non_adapt_light.adaptive_lighting_enabled = False
        self.non_adapt_light.status = "ON"
        self.non_adapt_light.brightness_level = 88 # Arbitrary initial
        self.initial_last_updated_non_adapt = self.non_adapt_light.last_updated

        # Light 3: Adaptive enabled, but already matching a schedule state (for "no change" test)
        self.adapt_no_change_light = streetlight_manager.add_streetlight("ADAPTNC03", {"lat": 12, "lon": 12}, 75)
        self.adapt_no_change_light.adaptive_lighting_enabled = True
        self.adapt_no_change_light.status = "ON" # Matches Late Night
        self.adapt_no_change_light.brightness_level = 50 # Matches Late Night
        self.initial_last_updated_adapt_nc = self.adapt_no_change_light.last_updated


    def test_apply_schedule_late_night(self):
        """Test schedule for Late Night (0-5 AM)."""
        hour = 2
        result = streetlight_manager.apply_adaptive_lighting_schedule(hour)

        self.assertEqual(self.adapt_light.status, "ON")
        self.assertEqual(self.adapt_light.brightness_level, 50)
        self.assertNotEqual(self.adapt_light.last_updated, self.initial_last_updated_adapt)

        self.assertEqual(self.non_adapt_light.status, "ON") # Unchanged
        self.assertEqual(self.non_adapt_light.brightness_level, 88) # Unchanged
        self.assertEqual(self.non_adapt_light.last_updated, self.initial_last_updated_non_adapt) # Unchanged

        self.assertEqual(result["updated_lights"], 1)
        self.assertEqual(len(result["details"]), 1)
        self.assertEqual(result["details"][0]["light_id"], "ADAPT01")
        self.assertEqual(result["details"][0]["new_status"], "ON")
        self.assertEqual(result["details"][0]["new_brightness"], 50)

    def test_apply_schedule_day_time(self):
        """Test schedule for Day Time (8-17)."""
        hour = 10
        result = streetlight_manager.apply_adaptive_lighting_schedule(hour)

        self.assertEqual(self.adapt_light.status, "OFF")
        self.assertEqual(self.adapt_light.brightness_level, 0)
        self.assertNotEqual(self.adapt_light.last_updated, self.initial_last_updated_adapt)

        self.assertEqual(result["updated_lights"], 2) # ADAPT01 and ADAPTNC03 changed
        # ADAPTNC03 also changes from ON/50 to OFF/0
        # Check if ADAPTNC03 was affected
        detail_ids = [d["light_id"] for d in result["details"]]
        self.assertIn("ADAPT01", detail_ids)
        self.assertIn("ADAPTNC03", detail_ids) # ADAPTNC03 will also be turned off
        self.assertEqual(self.adapt_no_change_light.status, "OFF")
        self.assertEqual(self.adapt_no_change_light.brightness_level, 0)


    def test_apply_schedule_evening(self):
        """Test schedule for Evening (18-23)."""
        hour = 19
        result = streetlight_manager.apply_adaptive_lighting_schedule(hour)

        self.assertEqual(self.adapt_light.status, "ON")
        self.assertEqual(self.adapt_light.brightness_level, 100)
        self.assertNotEqual(self.adapt_light.last_updated, self.initial_last_updated_adapt)

        self.assertEqual(result["updated_lights"], 1) # ADAPT01 changed
        # ADAPTNC03 also changes from ON/50 to ON/100
        detail_ids = [d["light_id"] for d in result["details"]]
        self.assertIn("ADAPT01", detail_ids)
        self.assertIn("ADAPTNC03", detail_ids) # ADAPTNC03 will also be set to 100%
        self.assertEqual(self.adapt_no_change_light.status, "ON")
        self.assertEqual(self.adapt_no_change_light.brightness_level, 100)

    def test_apply_schedule_no_change_due_to_time_slot(self):
        """Test schedule for a time slot not explicitly covered (e.g. 0-5 for ADAPTNC03)."""
        # ADAPTNC03 is already ON, 50. Late night is 0-5, ON, 50.
        hour = 3
        # Reset ADAPT01 to something that will change
        self.adapt_light.status = "OFF"
        self.adapt_light.brightness_level = 0
        self.initial_last_updated_adapt = self.adapt_light.last_updated

        result = streetlight_manager.apply_adaptive_lighting_schedule(hour)

        # ADAPT01 should change to ON/50
        self.assertEqual(self.adapt_light.status, "ON")
        self.assertEqual(self.adapt_light.brightness_level, 50)
        self.assertNotEqual(self.adapt_light.last_updated, self.initial_last_updated_adapt)

        # ADAPTNC03 should not change as it already matches the target state for this hour
        self.assertEqual(self.adapt_no_change_light.status, "ON")
        self.assertEqual(self.adapt_no_change_light.brightness_level, 50)
        self.assertEqual(self.adapt_no_change_light.last_updated, self.initial_last_updated_adapt_nc) # Timestamp not changed

        self.assertEqual(result["updated_lights"], 1) # Only ADAPT01 changed
        self.assertEqual(len(result["details"]), 1)
        self.assertEqual(result["details"][0]["light_id"], "ADAPT01")


    def test_apply_schedule_invalid_hour(self):
        """Test applying schedule with an invalid hour."""
        with self.assertRaisesRegex(ValueError, "current_time_hour must be between 0 and 23."):
            streetlight_manager.apply_adaptive_lighting_schedule(25)
        with self.assertRaisesRegex(ValueError, "current_time_hour must be between 0 and 23."):
            streetlight_manager.apply_adaptive_lighting_schedule(-1)

    def test_apply_schedule_no_adaptive_lights(self):
        """Test when no lights have adaptive_lighting_enabled."""
        streetlight_manager._reset_streetlights_data()
        streetlight_manager.add_streetlight("NOADAPT1", {"lat": 1, "lon": 1}, 100)
        streetlight_manager.add_streetlight("NOADAPT2", {"lat": 2, "lon": 2}, 50)

        result = streetlight_manager.apply_adaptive_lighting_schedule(2) # Any valid hour
        self.assertEqual(result["updated_lights"], 0)
        self.assertEqual(len(result["details"]), 0)


if __name__ == '__main__':
    unittest.main()
