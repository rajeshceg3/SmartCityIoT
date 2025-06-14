import datetime
from typing import Optional, List, Dict

from .models import TrashBin
from .sensor_simulator import update_bin_fill_level as sim_update_bin_fill_level # Renamed to avoid confusion

# Module-level dictionary to store bins in memory
_bins: Dict[str, TrashBin] = {}

def add_bin(bin_id: str, location: Dict[str, float], capacity_gallons: float) -> TrashBin:
    """
    Adds a new trash bin to the system.

    Args:
        bin_id: The unique identifier for the bin.
        location: A dictionary with 'lat' and 'lon' keys for the bin's location.
        capacity_gallons: The total capacity of the bin in gallons.

    Returns:
        The created TrashBin instance.

    Raises:
        ValueError: If a bin with the given bin_id already exists.
    """
    if bin_id in _bins:
        raise ValueError(f"Bin with ID '{bin_id}' already exists.")

    # Use current UTC time for initial last_updated
    # The TrashBin dataclass defaults last_updated and status, so explicit setting is optional
    # but good for clarity in this manager context.
    new_bin = TrashBin(
        bin_id=bin_id,
        location=location,
        capacity_gallons=capacity_gallons,
        current_fill_level_gallons=0.0, # Explicitly set, though default is 0.0
        last_updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='EMPTY' # Explicitly set, though default is 'EMPTY'
    )
    _bins[bin_id] = new_bin
    return new_bin

def get_bin(bin_id: str) -> Optional[TrashBin]:
    """
    Retrieves a trash bin by its ID.

    Args:
        bin_id: The ID of the bin to retrieve.

    Returns:
        The TrashBin instance if found, otherwise None.
    """
    return _bins.get(bin_id)

def update_bin_from_sensor_data(bin_id: str, new_fill_level: float) -> Optional[TrashBin]:
    """
    Updates a bin's fill level based on new sensor data.

    Args:
        bin_id: The ID of the bin to update.
        new_fill_level: The new fill level reported by the sensor.

    Returns:
        The updated TrashBin instance if the bin was found and updated, otherwise None.
    """
    bin_instance = get_bin(bin_id)
    if not bin_instance:
        return None

    # The imported update_bin_fill_level function updates the bin instance in-place
    # and also returns it. Since it's updated in-place, and _bins stores references,
    # the object in _bins is directly modified.
    updated_bin = sim_update_bin_fill_level(bin_instance, new_fill_level)
    return updated_bin

def list_bins(status_filter: Optional[str] = None) -> List[TrashBin]:
    """
    Lists all trash bins, optionally filtering by status.

    Args:
        status_filter: An optional status string (e.g., 'FULL', 'EMPTY') to filter bins by.

    Returns:
        A list of TrashBin instances.
    """
    if status_filter:
        return [bin_obj for bin_obj in _bins.values() if bin_obj.status == status_filter]
    return list(_bins.values())

if __name__ == "__main__":
    print("--- Initializing Bin Manager ---")

    # Add a couple of bins
    try:
        bin1 = add_bin(bin_id="BIN_001", location={'lat': 40.7128, 'lon': -74.0060}, capacity_gallons=100.0)
        print(f"Added Bin: {bin1}")
        bin2 = add_bin(bin_id="BIN_002", location={'lat': 34.0522, 'lon': -118.2437}, capacity_gallons=75.0)
        print(f"Added Bin: {bin2}")
    except ValueError as e:
        print(f"Error adding bin: {e}")

    print("\n--- Current Bins ---")
    all_bins = list_bins()
    for b in all_bins:
        print(b)

    # Update one bin using sensor data
    print("\n--- Updating BIN_001 ---")
    # Simulate BIN_001 being filled to 85 gallons (which should make it 'FULL')
    updated_bin1 = update_bin_from_sensor_data(bin_id="BIN_001", new_fill_level=85.0)
    if updated_bin1:
        print(f"Updated BIN_001: {updated_bin1}")
    else:
        print("BIN_001 not found for update.")

    # Update a non-existent bin
    print("\n--- Attempting to update non-existent BIN_003 ---")
    non_existent_bin = update_bin_from_sensor_data(bin_id="BIN_003", new_fill_level=50.0)
    if not non_existent_bin:
        print("BIN_003 not found, as expected.")

    print("\n--- Listing All Bins After Update ---")
    all_bins_after_update = list_bins()
    for b in all_bins_after_update:
        print(b)

    print("\n--- Listing 'FULL' Bins ---")
    full_bins = list_bins(status_filter='FULL')
    if full_bins:
        for b in full_bins:
            print(b)
    else:
        print("No bins are currently 'FULL'.")

    print("\n--- Listing 'EMPTY' Bins ---")
    empty_bins = list_bins(status_filter='EMPTY')
    if empty_bins:
        for b in empty_bins:
            print(b)
    else:
        print("No bins are currently 'EMPTY'.")

    # Example of trying to add an existing bin
    print("\n--- Attempting to add existing BIN_001 again ---")
    try:
        add_bin(bin_id="BIN_001", location={'lat': 0, 'lon': 0}, capacity_gallons=10)
    except ValueError as e:
        print(f"Error adding existing bin: {e}")
