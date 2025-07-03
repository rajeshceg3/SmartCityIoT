import unittest
import datetime

from waste_management.models import CollectionRoute
from waste_management.route_manager import (
    generate_route,
    get_route,
    update_route_status,
    list_routes,
    _routes  # For direct manipulation in setUp/tearDown
)
from waste_management.bin_manager import (
    add_bin as manager_add_bin, # Alias to avoid confusion if we had local add_bin
    update_bin_from_sensor_data as manager_update_bin,
    get_bin as manager_get_bin, # For verifying bin status after route completion
    _bins as bin_manager_bins # For direct manipulation
)

class TestRouteManager(unittest.TestCase):

    def setUp(self):
        """Clear the _routes and bin_manager_bins dictionaries before each test."""
        _routes.clear()
        bin_manager_bins.clear()

    def tearDown(self):
        """Clear the _routes and bin_manager_bins dictionaries after each test."""
        _routes.clear()
        bin_manager_bins.clear()

    def test_generate_route_no_full_bins(self):
        """Test generating a route when no bins are 'FULL'."""
        manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_update_bin(bin_id="bin1", new_fill_level=50.0) # Status 'FILLING'

        route = generate_route(assigned_truck_id="truck1")
        self.assertIsNone(route, "Route should be None if no bins are FULL.")

    def test_generate_route_with_full_bins(self):
        """Test generating a route when there are 'FULL' bins."""
        bin1 = manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        bin2 = manager_add_bin(bin_id="bin2", location={'lat': 20, 'lon': 20}, capacity_gallons=100)
        manager_add_bin(bin_id="bin3", location={'lat': 30, 'lon': 30}, capacity_gallons=100) # Not full

        manager_update_bin(bin_id="bin1", new_fill_level=90.0) # FULL
        manager_update_bin(bin_id="bin2", new_fill_level=85.0) # FULL

        route = generate_route(assigned_truck_id="truck1")
        self.assertIsNotNone(route, "Route should be generated.")
        self.assertIsInstance(route, CollectionRoute)
        self.assertEqual(route.status, 'PENDING')
        self.assertEqual(route.assigned_truck_id, "truck1")
        self.assertIn("bin1", route.bin_ids_to_collect)
        self.assertIn("bin2", route.bin_ids_to_collect)
        self.assertNotIn("bin3", route.bin_ids_to_collect)
        self.assertEqual(len(route.bin_ids_to_collect), 2)
        self.assertIn(route.route_id, _routes)
        self.assertEqual(_routes[route.route_id], route)

    def test_get_route_exists(self):
        """Test retrieving an existing route."""
        manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_update_bin(bin_id="bin1", new_fill_level=90.0) # FULL
        generated_route = generate_route(assigned_truck_id="truck1")

        retrieved_route = get_route(generated_route.route_id)
        self.assertEqual(generated_route, retrieved_route)

    def test_get_route_not_exists(self):
        """Test retrieving a non-existent route."""
        retrieved_route = get_route("non_existent_id")
        self.assertIsNone(retrieved_route)

    def test_list_routes_empty(self):
        """Test listing routes when no routes have been generated."""
        self.assertEqual(list_routes(), [])

    def test_list_routes_all(self):
        """Test listing all routes when multiple routes have been generated."""
        # Route 1
        manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_update_bin(bin_id="bin1", new_fill_level=90.0)
        route1 = generate_route(assigned_truck_id="truck1")

        # Clear bins to generate a distinct route, or use different bins
        bin_manager_bins.clear()
        manager_add_bin(bin_id="bin2", location={'lat': 20, 'lon': 20}, capacity_gallons=100)
        manager_update_bin(bin_id="bin2", new_fill_level=90.0)
        route2 = generate_route(assigned_truck_id="truck2")

        listed_routes = list_routes()
        self.assertIn(route1, listed_routes)
        self.assertIn(route2, listed_routes)
        self.assertEqual(len(listed_routes), 2)

    def test_list_routes_filter_status(self):
        """Test filtering routes by status."""
        # Route 1 - PENDING
        manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_update_bin(bin_id="bin1", new_fill_level=90.0)
        route1 = generate_route(assigned_truck_id="truck1")

        # Route 2 - IN_PROGRESS
        bin_manager_bins.clear()
        manager_add_bin(bin_id="bin2", location={'lat': 20, 'lon': 20}, capacity_gallons=100)
        manager_update_bin(bin_id="bin2", new_fill_level=90.0)
        route2 = generate_route(assigned_truck_id="truck2")
        update_route_status(route2.route_id, 'IN_PROGRESS')

        self.assertEqual(list_routes(status_filter='PENDING'), [route1])
        self.assertEqual(list_routes(status_filter='IN_PROGRESS'), [route2])
        self.assertEqual(list_routes(status_filter='COMPLETED'), [])

    def test_update_route_status(self):
        """Test updating a route's status and relevant timestamps."""
        manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_update_bin(bin_id="bin1", new_fill_level=90.0) # FULL
        route = generate_route(assigned_truck_id="truck1")
        self.assertIsNone(route.started_at)
        self.assertIsNone(route.completed_at)

        # Update to IN_PROGRESS
        updated_route_inprogress = update_route_status(route.route_id, 'IN_PROGRESS')
        self.assertEqual(updated_route_inprogress.status, 'IN_PROGRESS')
        self.assertIsNotNone(updated_route_inprogress.started_at)
        self.assertIsNone(updated_route_inprogress.completed_at) # Should still be None
        try:
            datetime.datetime.fromisoformat(updated_route_inprogress.started_at.replace('Z', '+00:00'))
        except ValueError:
            self.fail("started_at is not a valid ISO format datetime string")

        original_started_at = updated_route_inprogress.started_at

        # Update to COMPLETED
        updated_route_completed = update_route_status(route.route_id, 'COMPLETED')
        self.assertEqual(updated_route_completed.status, 'COMPLETED')
        self.assertEqual(updated_route_completed.started_at, original_started_at) # Should not change
        self.assertIsNotNone(updated_route_completed.completed_at)
        try:
            datetime.datetime.fromisoformat(updated_route_completed.completed_at.replace('Z', '+00:00'))
        except ValueError:
            self.fail("completed_at is not a valid ISO format datetime string")

    def test_update_route_status_idempotency_timestamps(self):
        """Test that timestamps (started_at, completed_at) are set only once."""
        manager_add_bin(bin_id="bin1", location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_update_bin(bin_id="bin1", new_fill_level=90.0)
        route = generate_route(assigned_truck_id="truck1")

        # First update to IN_PROGRESS
        update_route_status(route.route_id, 'IN_PROGRESS')
        first_started_at = route.started_at

        # Second update to IN_PROGRESS (e.g., redundant call)
        update_route_status(route.route_id, 'IN_PROGRESS')
        self.assertEqual(route.started_at, first_started_at, "started_at should not change on subsequent IN_PROGRESS updates.")

        # First update to COMPLETED
        update_route_status(route.route_id, 'COMPLETED')
        first_completed_at = route.completed_at

        # Second update to COMPLETED
        update_route_status(route.route_id, 'COMPLETED')
        self.assertEqual(route.completed_at, first_completed_at, "completed_at should not change on subsequent COMPLETED updates.")


    def test_update_non_existent_route(self):
        """Test updating a non-existent route."""
        result = update_route_status(route_id="non_existent_id", new_status="COMPLETED")
        self.assertIsNone(result)

    def test_update_route_status_completed_empties_bins(self):
        """Test that completing a route empties the collected bins in bin_manager."""
        # 1. Setup bins
        bin1_id = "b_comp01"
        bin2_id = "b_comp02"
        manager_add_bin(bin_id=bin1_id, location={'lat': 10, 'lon': 10}, capacity_gallons=100)
        manager_add_bin(bin_id=bin2_id, location={'lat': 20, 'lon': 20}, capacity_gallons=100)

        # 2. Make bins FULL
        manager_update_bin(bin_id=bin1_id, new_fill_level=90.0) # FULL
        manager_update_bin(bin_id=bin2_id, new_fill_level=85.0) # FULL

        # 3. Generate route
        route = generate_route(assigned_truck_id="truck_comp_test")
        self.assertIsNotNone(route, "Route should be generated for full bins.")
        self.assertIn(bin1_id, route.bin_ids_to_collect)
        self.assertIn(bin2_id, route.bin_ids_to_collect)

        # 4. Complete the route
        update_route_status(route.route_id, 'COMPLETED')

        # 5. Verify bins are emptied
        bin1_after = manager_get_bin(bin1_id)
        bin2_after = manager_get_bin(bin2_id)

        self.assertIsNotNone(bin1_after)
        self.assertEqual(bin1_after.status, 'EMPTY', f"Bin {bin1_id} should be EMPTY after route completion.")
        self.assertEqual(bin1_after.current_fill_level_gallons, 0.0, f"Bin {bin1_id} fill level should be 0 after route completion.")

        self.assertIsNotNone(bin2_after)
        self.assertEqual(bin2_after.status, 'EMPTY', f"Bin {bin2_id} should be EMPTY after route completion.")
        self.assertEqual(bin2_after.current_fill_level_gallons, 0.0, f"Bin {bin2_id} fill level should be 0 after route completion.")

        # Optional: Check a bin not on the route is unaffected
        bin_not_on_route_id = "b_not_on_route"
        manager_add_bin(bin_id=bin_not_on_route_id, location={'lat': 30, 'lon': 30}, capacity_gallons=100)
        manager_update_bin(bin_id=bin_not_on_route_id, new_fill_level=70.0) # FILLING
        # bin_not_on_route_before = manager_get_bin(bin_not_on_route_id) # Store state before just in case

        # Re-fetch after route completion (though it shouldn't have changed)
        bin_not_on_route_after = manager_get_bin(bin_not_on_route_id)
        self.assertIsNotNone(bin_not_on_route_after, "Bin not on route should exist.")
        self.assertEqual(bin_not_on_route_after.status, 'FILLING', f"Bin {bin_not_on_route_id} status should be unaffected.")
        self.assertEqual(bin_not_on_route_after.current_fill_level_gallons, 70.0, f"Bin {bin_not_on_route_id} fill level should be unaffected.")

if __name__ == '__main__':
    unittest.main()
