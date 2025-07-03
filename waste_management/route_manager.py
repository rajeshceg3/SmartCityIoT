import datetime
import logging
import uuid
from typing import Optional, List, Dict

from .models import CollectionRoute
from .bin_manager import list_bins as manager_list_bins
from .bin_manager import add_bin as manager_add_bin
from .bin_manager import update_bin_from_sensor_data as manager_update_bin
from .bin_manager import _bins as manager_bins_store # To clear for repeatable examples
from .bin_manager import mark_bin_as_empty # Added for route completion

# Module-level dictionary to store routes in memory
_routes: Dict[str, CollectionRoute] = {}
logger = logging.getLogger(__name__)

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
            logger.info(f"Route {route_id} completed. Marking collected bins as empty.")
            for bin_id in route_instance.bin_ids_to_collect:
                emptied_bin = mark_bin_as_empty(bin_id)
                if emptied_bin:
                    logger.info(f"Bin {bin_id} successfully marked as empty as part of route {route_id} completion.")
                else:
                    logger.warning(f"Failed to mark bin {bin_id} as empty for route {route_id} (bin not found).")
    return route_instance

if __name__ == "__main__":
    # As in bin_manager, basicConfig is ideally called by the application, not the library.
    # Placed here for direct script execution.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    logging.info("--- Initializing Route Manager ---")

    # Clear any existing bins from bin_manager for a clean example run
    # This is a bit of a hack for example purposes, directly accessing _bins
    manager_bins_store.clear()
    _routes.clear() # Also clear any routes from previous partial runs of this example

    logging.info("\n--- Setting up Bins (via bin_manager) ---")
    try:
        bin1 = manager_add_bin(bin_id="BIN_R01", location={'lat': 10.0, 'lon': 10.0}, capacity_gallons=100.0)
        bin2 = manager_add_bin(bin_id="BIN_R02", location={'lat': 20.0, 'lon': 20.0}, capacity_gallons=100.0)
        bin3 = manager_add_bin(bin_id="BIN_R03", location={'lat': 30.0, 'lon': 30.0}, capacity_gallons=100.0)
        logging.info(f"Added: {bin1.bin_id}, {bin2.bin_id}, {bin3.bin_id}")

        # Make some bins 'FULL'
        manager_update_bin(bin_id="BIN_R01", new_fill_level=90.0) # FULL
        manager_update_bin(bin_id="BIN_R03", new_fill_level=85.0) # FULL
        logging.info("Updated BIN_R01 and BIN_R03 to be FULL.")
    except ValueError as e:
        logging.error(f"Error setting up bins: {e}")

    logging.info("\n--- Generating Route ---")
    generated_route = generate_route(assigned_truck_id="TRUCK_A1")
    if generated_route:
        logging.info(f"Generated Route: {generated_route}")
    else:
        logging.info("No 'FULL' bins found, so no route generated.")

    logging.info("\n--- Listing All Routes ---")
    all_routes = list_routes()
    if all_routes:
        for r in all_routes:
            logging.info(r)
    else:
        logging.info("No routes available.")

    if generated_route:
        route_to_update_id = generated_route.route_id
        logging.info(f"\n--- Updating Route {route_to_update_id} to 'IN_PROGRESS' ---")
        updated_route = update_route_status(route_id=route_to_update_id, new_status='IN_PROGRESS')
        if updated_route:
            logging.info(f"Updated Route: {updated_route}")
        else:
            logging.warning(f"Route {route_to_update_id} not found for update.")

        logging.info(f"\n--- Updating Route {route_to_update_id} to 'COMPLETED' ---")
        # Simulate some time passing
        # In a real system, this would happen after some delay
        updated_route = update_route_status(route_id=route_to_update_id, new_status='COMPLETED')
        if updated_route:
            logging.info(f"Updated Route: {updated_route}")
        else:
            logging.warning(f"Route {route_to_update_id} not found for update.")

        logging.info("\n--- Listing 'COMPLETED' Routes ---")
        completed_routes = list_routes(status_filter='COMPLETED')
        if completed_routes:
            for r_comp in completed_routes:
                logging.info(r_comp)
        else:
            logging.info("No routes are 'COMPLETED'.")

    logging.info("\n--- Listing 'COMPLETED' Routes ---")
    completed_routes = list_routes(status_filter='COMPLETED')
    if completed_routes:
        for r_comp in completed_routes:
            logging.info(r_comp)
    else:
        logging.info("No routes are 'COMPLETED'.")

    # Check status of bins from the completed route (BIN_R01, BIN_R03)
    # They should now be EMPTY
    logging.info("\n--- Checking status of bins from completed route ---")
    if generated_route:
        for bin_id_completed in generated_route.bin_ids_to_collect:
            b_status = manager_list_bins() # inefficient, ideally get_bin(bin_id_completed)
            current_bin_instance = next((b for b in b_status if b.bin_id == bin_id_completed), None)
            if current_bin_instance:
                 logging.info(f"Bin {current_bin_instance.bin_id} status after route completion: {current_bin_instance.status}")
            else:
                logging.warning(f"Bin {bin_id_completed} not found after route completion check.")


    logging.info("\n--- Generating another route (should be None as bins from the first route were emptied) ---")
    another_route = generate_route(assigned_truck_id="TRUCK_A2")
    if not another_route:
        logging.info("No new route generated, as expected (bins from previous route should have been emptied).")
    else:
        logging.warning(f"A new route was generated when it wasn't expected: {another_route}")
        logging.warning("This might indicate bins from the first route weren't properly emptied or new full bins exist.")


    # Example: Create more full bins and generate a new route
    logging.info("\n--- Setting up more FULL bins (BIN_R02, BIN_R04) ---")
    try:
        # BIN_R02 was added but not filled, fill it now.
        manager_update_bin(bin_id="BIN_R02", new_fill_level=95.0) # FULL
        logging.info(f"Filled BIN_R02.")

        bin4 = manager_add_bin(bin_id="BIN_R04", location={'lat': 40.0, 'lon': 40.0}, capacity_gallons=50.0)
        manager_update_bin(bin_id="BIN_R04", new_fill_level=45.0) # FULL
        logging.info(f"Added and filled {bin4.bin_id}")
    except ValueError as e:
        logging.error(f"Error setting up more full bins: {e}")
    except Exception as e: # Catch if manager_update_bin fails for BIN_R02 for some reason
        logging.error(f"An unexpected error occurred setting up more full bins: {e}")


    new_generated_route = generate_route(assigned_truck_id="TRUCK_B1")
    if new_generated_route:
        logging.info(f"New Generated Route (for BIN_R02, BIN_R04): {new_generated_route}")
        # Verify it includes R02 and R04
        if "BIN_R02" in new_generated_route.bin_ids_to_collect and "BIN_R04" in new_generated_route.bin_ids_to_collect:
            logging.info("New route correctly includes BIN_R02 and BIN_R04.")
        else:
            logging.warning(f"New route does not include the expected bins. Contains: {new_generated_route.bin_ids_to_collect}")
    else:
        logging.info("No new route generated despite new full bins (BIN_R02, BIN_R04). This is unexpected.")


    logging.info("\n--- Final list of all routes ---")
    for r_final in list_routes():
        logging.info(r_final)
