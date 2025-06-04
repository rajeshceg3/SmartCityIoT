import datetime
import random
from typing import Tuple

from .models import TrashBin

def generate_sensor_reading(bin_id: str, current_fill_level: float, capacity: float) -> float:
    """
    Simulates a new sensor reading for a trash bin.

    Randomly increases the current_fill_level by a small amount,
    ensuring it doesn't exceed capacity.

    Args:
        bin_id: The ID of the bin (currently unused in logic but good for context).
        current_fill_level: The current fill level of the bin in gallons.
        capacity: The total capacity of the bin in gallons.

    Returns:
        The new simulated fill level in gallons.
    """
    increase = random.uniform(0.1, 1.0)
    new_fill_level = current_fill_level + increase
    return min(new_fill_level, capacity)

def update_bin_fill_level(bin_instance: TrashBin, new_fill_level: float) -> TrashBin:
    """
    Updates a TrashBin object with a new fill level and derived status.

    Args:
        bin_instance: The TrashBin instance to update.
        new_fill_level: The new fill level in gallons.

    Returns:
        The updated TrashBin instance.
    """
    bin_instance.current_fill_level_gallons = new_fill_level
    bin_instance.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()

    fill_ratio = new_fill_level / bin_instance.capacity_gallons
    if fill_ratio < 0.1:
        bin_instance.status = 'EMPTY'
    elif fill_ratio < 0.8:
        bin_instance.status = 'FILLING'
    else:
        bin_instance.status = 'FULL'

    # Potentially add 'NEEDS_MAINTENANCE' logic here if other sensors were involved
    # For now, it's based purely on fill level.

    return bin_instance

if __name__ == "__main__":
    # Create a sample TrashBin instance
    sample_bin = TrashBin(
        bin_id="BIN_001",
        location={'lat': 40.7128, 'lon': -74.0060},
        capacity_gallons=100.0
    )

    print(f"Initial Bin State: {sample_bin}")

    # Simulate a few sensor readings and updates
    for i in range(5):
        print(f"\n--- Simulation Step {i+1} ---")

        # 1. Generate a new sensor reading based on the current state
        simulated_new_level = generate_sensor_reading(
            sample_bin.bin_id,
            sample_bin.current_fill_level_gallons,
            sample_bin.capacity_gallons
        )
        print(f"Generated sensor reading (new fill level): {simulated_new_level:.2f} gallons")

        # 2. Update the bin instance with this new reading
        sample_bin = update_bin_fill_level(sample_bin, simulated_new_level)
        print(f"Updated Bin State: {sample_bin}")

        # If bin is full, simulate it being emptied for further simulations
        if sample_bin.status == 'FULL' and i < 4: # Don't empty on the very last step
            print(f"Bin is FULL. Simulating emptying for next cycle.")
            sample_bin = update_bin_fill_level(sample_bin, 0.0) # Reset to empty
            print(f"Bin State after emptying: {sample_bin}")

    print("\n--- Final Bin State after simulations ---")
    print(sample_bin)
