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

if __name__ == '__main__':
    unittest.main()
