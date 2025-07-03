import unittest
import datetime # For checking last_updated format, approximately

# Assuming the test runner will handle PYTHONPATH or that waste_management is discoverable
# If running this file directly, ensure waste_management is in PYTHONPATH or run as module from root
from waste_management.models import TrashBin
from waste_management.bin_manager import (
    add_bin,
    get_bin,
    update_bin_from_sensor_data,
    list_bins,
    mark_bin_as_empty, # Added for testing
    _bins # For direct manipulation in setUp/tearDown
)

class TestBinManager(unittest.TestCase):

    def setUp(self):
        """Clear the _bins dictionary before each test."""
        _bins.clear()

    def tearDown(self):
        """Clear the _bins dictionary after each test to ensure test isolation."""
        _bins.clear()

    def test_add_bin_success(self):
        """Test successfully adding a new bin."""
        location = {'lat': 40.7128, 'lon': -74.0060}
        added_bin = add_bin(bin_id="bin1", location=location, capacity_gallons=100.0)

        self.assertIn("bin1", _bins)
        self.assertEqual(_bins["bin1"], added_bin)
        self.assertEqual(added_bin.bin_id, "bin1")
        self.assertEqual(added_bin.location, location)
        self.assertEqual(added_bin.capacity_gallons, 100.0)
        self.assertEqual(added_bin.current_fill_level_gallons, 0.0)
        self.assertEqual(added_bin.status, 'EMPTY')
        # Check last_updated is a recent ISO format datetime string
        self.assertTrue(isinstance(added_bin.last_updated, str))
        try:
            datetime.datetime.fromisoformat(added_bin.last_updated.replace('Z', '+00:00')) # Handle Z if present
        except ValueError:
            self.fail("last_updated is not a valid ISO format datetime string")

    def test_add_bin_duplicate(self):
        """Test adding a bin with an ID that already exists."""
        add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=50)
        with self.assertRaisesRegex(ValueError, "Bin with ID 'bin1' already exists."):
            add_bin(bin_id="bin1", location={'lat': 20, 'lon': 20}, capacity_gallons=70)

    def test_get_bin_exists(self):
        """Test retrieving an existing bin."""
        original_bin = add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=50)
        retrieved_bin = get_bin("bin1")
        self.assertEqual(original_bin, retrieved_bin)

    def test_get_bin_not_exists(self):
        """Test retrieving a non-existent bin."""
        retrieved_bin = get_bin("nonexistent_bin")
        self.assertIsNone(retrieved_bin)

    def test_update_bin_from_sensor_data(self):
        """Test updating a bin's fill level and status."""
        bin_to_update = add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100.0)
        original_last_updated = bin_to_update.last_updated

        # Update to 'FILLING'
        updated_bin_filling = update_bin_from_sensor_data(bin_id="bin1", new_fill_level=50.0)
        self.assertIsNotNone(updated_bin_filling)
        self.assertEqual(updated_bin_filling.current_fill_level_gallons, 50.0)
        self.assertEqual(updated_bin_filling.status, 'FILLING')
        self.assertNotEqual(updated_bin_filling.last_updated, original_last_updated)

        # Update to 'FULL'
        original_last_updated_filling = updated_bin_filling.last_updated
        updated_bin_full = update_bin_from_sensor_data(bin_id="bin1", new_fill_level=85.0)
        self.assertIsNotNone(updated_bin_full)
        self.assertEqual(updated_bin_full.current_fill_level_gallons, 85.0)
        self.assertEqual(updated_bin_full.status, 'FULL')
        self.assertNotEqual(updated_bin_full.last_updated, original_last_updated_filling)

        # Update to 'EMPTY' (e.g. fill level very low)
        original_last_updated_full = updated_bin_full.last_updated
        updated_bin_empty = update_bin_from_sensor_data(bin_id="bin1", new_fill_level=5.0)
        self.assertIsNotNone(updated_bin_empty)
        self.assertEqual(updated_bin_empty.current_fill_level_gallons, 5.0)
        self.assertEqual(updated_bin_empty.status, 'EMPTY')
        self.assertNotEqual(updated_bin_empty.last_updated, original_last_updated_full)


    def test_update_non_existent_bin(self):
        """Test updating a non-existent bin."""
        result = update_bin_from_sensor_data(bin_id="nonexistent_bin", new_fill_level=50.0)
        self.assertIsNone(result)

    def test_list_bins_empty(self):
        """Test listing bins when no bins have been added."""
        self.assertEqual(list_bins(), [])

    def test_list_bins_all(self):
        """Test listing all bins when multiple bins have been added."""
        bin1 = add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=50)
        bin2 = add_bin(bin_id="bin2", location={'lat': 20, 'lon': 20}, capacity_gallons=70)

        listed_bins = list_bins()
        self.assertIn(bin1, listed_bins)
        self.assertIn(bin2, listed_bins)
        self.assertEqual(len(listed_bins), 2)

    def test_list_bins_filter_status(self):
        """Test filtering bins by status."""
        bin_empty = add_bin(bin_id="bin_empty", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        # bin_filling will be created and then updated
        bin_filling_id = "bin_filling"
        add_bin(bin_id=bin_filling_id, location={'lat': 20, 'lon': 20}, capacity_gallons=100)
        update_bin_from_sensor_data(bin_id=bin_filling_id, new_fill_level=50.0) # Status: FILLING

        # bin_full will be created and then updated
        bin_full_id = "bin_full"
        add_bin(bin_id=bin_full_id, location={'lat': 30, 'lon': 30}, capacity_gallons=100)
        update_bin_from_sensor_data(bin_id=bin_full_id, new_fill_level=90.0) # Status: FULL

        # Retrieve updated instances for assertion
        bin_filling = get_bin(bin_filling_id)
        bin_full = get_bin(bin_full_id)

        self.assertEqual(list_bins(status_filter='EMPTY'), [bin_empty])
        self.assertEqual(list_bins(status_filter='FILLING'), [bin_filling])
        self.assertEqual(list_bins(status_filter='FULL'), [bin_full])
        self.assertEqual(list_bins(status_filter='NEEDS_MAINTENANCE'), [])
        self.assertEqual(list_bins(status_filter='NON_EXISTENT_STATUS'), [])

    def test_mark_bin_as_empty(self):
        """Test marking a bin as empty and attempting to mark a non-existent bin."""
        # Scenario 1: Successfully marking an existing bin as empty
        bin_id_existing = "bin_to_empty"
        add_bin(bin_id=bin_id_existing, location={'lat': 50, 'lon': 50}, capacity_gallons=100.0)

        # Update it to be 'FULL' so we can see the change
        updated_bin = update_bin_from_sensor_data(bin_id=bin_id_existing, new_fill_level=90.0)
        self.assertIsNotNone(updated_bin)
        self.assertEqual(updated_bin.status, 'FULL')
        original_last_updated = updated_bin.last_updated

        # Introduce a tiny delay to ensure the timestamp can change if the operation is very fast.
        # This might not always be necessary with high-precision timestamps but is safer.
        # For most practical purposes on typical systems, datetime.isoformat() resolution changes.
        # If tests become flaky here, a more robust time mocking/advancing strategy might be needed.
        # For now, a direct call is usually sufficient.

        emptied_bin = mark_bin_as_empty(bin_id_existing)

        self.assertIsNotNone(emptied_bin, "mark_bin_as_empty should return the bin object.")
        self.assertEqual(emptied_bin.current_fill_level_gallons, 0.0, "Bin fill level should be 0.0.")
        self.assertEqual(emptied_bin.status, 'EMPTY', "Bin status should be 'EMPTY'.")
        self.assertNotEqual(emptied_bin.last_updated, original_last_updated, "last_updated timestamp should have changed.")

        # Verify the change is also reflected in the main store (though mark_bin_as_empty should handle this)
        stored_bin_after_empty = get_bin(bin_id_existing)
        self.assertIsNotNone(stored_bin_after_empty)
        self.assertEqual(stored_bin_after_empty.status, 'EMPTY')

        # Scenario 2: Attempting to mark a non-existent bin as empty
        bin_id_non_existent = "bin_does_not_exist"
        result_non_existent = mark_bin_as_empty(bin_id_non_existent)
        self.assertIsNone(result_non_existent, "Attempting to mark a non-existent bin as empty should return None.")

if __name__ == '__main__':
    unittest.main()
