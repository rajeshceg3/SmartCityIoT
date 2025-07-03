import datetime
import uuid
from typing import Optional, List, Dict

from .models import CollectionRoute
from .bin_manager import list_bins as manager_list_bins # Aliased to avoid conflict if we had a local list_bins
from .bin_manager import add_bin as manager_add_bin # For example usage
from .bin_manager import update_bin_from_sensor_data as manager_update_bin # For example usage
from .bin_manager import _bins as manager_bins_store # To clear for repeatable examples

# Module-level dictionary to store routes in memory
_routes: Dict[str, CollectionRoute] = {}

def generate_route(assigned_truck_id: str) -> Optional[CollectionRoute]:
    """
    Generates a new collection route for a given truck, based on currently 'FULL' bins.

    Args:
        assigned_truck_id: The ID of the truck to assign to this route.

    Returns:
        The created CollectionRoute instance if there are 'FULL' bins, otherwise None.
    """
    full_bins = manager_list_bins(status_filter='FULL')
    if not full_bins:
        return None

    bin_ids_to_collect = [bin_obj.bin_id for bin_obj in full_bins]
    route_id = str(uuid.uuid4())

    new_route = CollectionRoute(
        route_id=route_id,
        assigned_truck_id=assigned_truck_id,
        bin_ids_to_collect=bin_ids_to_collect,
        status='PENDING', # Default status for a new route
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        # started_at and completed_at default to None
    )
    _routes[route_id] = new_route
    return new_route

def get_route(route_id: str) -> Optional[CollectionRoute]:
    """
    Retrieves a collection route by its ID.

    Args:
        route_id: The ID of the route to retrieve.

    Returns:
        The CollectionRoute instance if found, otherwise None.
    """
    return _routes.get(route_id)

def list_routes(status_filter: Optional[str] = None) -> List[CollectionRoute]:
    """
    Lists all collection routes, optionally filtering by status.

    Args:
        status_filter: An optional status string (e.g., 'PENDING', 'COMPLETED') to filter routes by.

    Returns:
        A list of CollectionRoute instances.
    """
    if status_filter:
        return [route_obj for route_obj in _routes.values() if route_obj.status == status_filter]
    return list(_routes.values())

def update_route_status(route_id: str, new_status: str) -> Optional[CollectionRoute]:
    """
    Updates the status of a collection route.

    Sets `started_at` when status changes to 'IN_PROGRESS' (if not already set).
    Sets `completed_at` when status changes to 'COMPLETED' or 'CANCELLED'.

    Args:
        route_id: The ID of the route to update.
        new_status: The new status for the route.

    Returns:
        The updated CollectionRoute instance if found, otherwise None.
    """
    route_instance = get_route(route_id)
    if not route_instance:
        return None

    route_instance.status = new_status
    current_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if new_status == 'IN_PROGRESS' and route_instance.started_at is None:
        route_instance.started_at = current_time_iso

    if new_status in ['COMPLETED', 'CANCELLED'] and route_instance.completed_at is None:
        route_instance.completed_at = current_time_iso
        if new_status == 'COMPLETED':
            print(f"Route {route_id} completed. Emptying collected bins: {route_instance.bin_ids_to_collect}")
            for bin_id_to_empty in route_instance.bin_ids_to_collect:
                updated_bin = manager_update_bin(bin_id_to_empty, 0.0) # Set fill level to 0
                if updated_bin:
                    print(f"Bin {bin_id_to_empty} emptied. New status: {updated_bin.status}, Fill level: {updated_bin.current_fill_level_gallons}")
                else:
                    print(f"Warning: Bin {bin_id_to_empty} from route {route_id} not found in bin_manager for emptying.")

    return route_instance

if __name__ == "__main__":
    print("--- Initializing Route Manager ---")

    # Clear any existing bins from bin_manager for a clean example run
    # This is a bit of a hack for example purposes, directly accessing _bins
    manager_bins_store.clear()
    _routes.clear() # Also clear any routes from previous partial runs of this example

    print("\n--- Setting up Bins (via bin_manager) ---")
    try:
        bin1 = manager_add_bin(bin_id="BIN_R01", location={'lat': 10.0, 'lon': 10.0}, capacity_gallons=100.0)
        bin2 = manager_add_bin(bin_id="BIN_R02", location={'lat': 20.0, 'lon': 20.0}, capacity_gallons=100.0)
        bin3 = manager_add_bin(bin_id="BIN_R03", location={'lat': 30.0, 'lon': 30.0}, capacity_gallons=100.0)
        print(f"Added: {bin1.bin_id}, {bin2.bin_id}, {bin3.bin_id}")

        # Make some bins 'FULL'
        manager_update_bin(bin_id="BIN_R01", new_fill_level=90.0) # FULL
        manager_update_bin(bin_id="BIN_R03", new_fill_level=85.0) # FULL
        print("Updated BIN_R01 and BIN_R03 to be FULL.")
    except ValueError as e:
        print(f"Error setting up bins: {e}")

    print("\n--- Generating Route ---")
    generated_route = generate_route(assigned_truck_id="TRUCK_A1")
    if generated_route:
        print(f"Generated Route: {generated_route}")
    else:
        print("No 'FULL' bins found, so no route generated.")

    print("\n--- Listing All Routes ---")
    all_routes = list_routes()
    if all_routes:
        for r in all_routes:
            print(r)
    else:
        print("No routes available.")

    if generated_route:
        route_to_update_id = generated_route.route_id
        print(f"\n--- Updating Route {route_to_update_id} to 'IN_PROGRESS' ---")
        updated_route = update_route_status(route_id=route_to_update_id, new_status='IN_PROGRESS')
        if updated_route:
            print(f"Updated Route: {updated_route}")
        else:
            print(f"Route {route_to_update_id} not found for update.")

        print(f"\n--- Updating Route {route_to_update_id} to 'COMPLETED' ---")
        # Simulate some time passing
        # In a real system, this would happen after some delay
        updated_route = update_route_status(route_id=route_to_update_id, new_status='COMPLETED')
        if updated_route:
            print(f"Updated Route: {updated_route}")
        else:
            print(f"Route {route_to_update_id} not found for update.")

        print("\n--- Listing 'COMPLETED' Routes ---")
        completed_routes = list_routes(status_filter='COMPLETED')
        if completed_routes:
            for r_comp in completed_routes:
                print(r_comp)
        else:
            print("No routes are 'COMPLETED'.")

    print("\n--- Generating another route (should be None as bins were not re-filled) ---")
    another_route = generate_route(assigned_truck_id="TRUCK_A2")
    if not another_route:
        print("No new route generated, as expected (bins from previous route are still marked FULL in bin_manager).")
        print("Note: For a real system, completing a route should ideally trigger emptying the bins.")

    # Example: Create more full bins and generate a new route
    print("\n--- Setting up more FULL bins ---")
    try:
        bin4 = manager_add_bin(bin_id="BIN_R04", location={'lat': 40.0, 'lon': 40.0}, capacity_gallons=50.0)
        manager_update_bin(bin_id="BIN_R04", new_fill_level=45.0) # FULL
        print(f"Added and filled {bin4.bin_id}")
    except ValueError as e:
        print(f"Error setting up bin4: {e}")

    new_generated_route = generate_route(assigned_truck_id="TRUCK_B1")
    if new_generated_route:
        print(f"New Generated Route (for BIN_R04 and others still full): {new_generated_route}")
    else:
        print("No new route generated despite new full bin (check logic if BIN_R01, R03 are still full).")
        # Note: The generate_route will pick up BIN_R01 and BIN_R03 again if they haven't been emptied.
        # This is expected based on current logic.

    print("\n--- Final list of all routes ---")
    for r in list_routes():
        print(r)
