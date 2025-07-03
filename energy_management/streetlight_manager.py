import datetime
from typing import Dict, Optional, List
from .models import Streetlight

# In-memory storage for streetlights
_streetlights: Dict[str, Streetlight] = {}

def add_streetlight(light_id: str, location: Dict[str, float], power_consumption_watts: Optional[float] = None) -> Streetlight:
    """
    Adds a new streetlight to the system.
    Raises ValueError if the light_id already exists.
    """
    if light_id in _streetlights:
        raise ValueError(f"Streetlight with ID '{light_id}' already exists.")

    new_streetlight = Streetlight(
        light_id=light_id,
        location=location,
        power_consumption_watts=power_consumption_watts
        # status, brightness_level, last_updated will use defaults from the model
    )
    _streetlights[light_id] = new_streetlight
    return new_streetlight

def get_streetlight(light_id: str) -> Optional[Streetlight]:
    """Retrieves a streetlight by its ID."""
    return _streetlights.get(light_id)

def list_streetlights(status_filter: Optional[str] = None) -> List[Streetlight]:
    """
    Lists all streetlights, optionally filtered by status.
    Valid status_filter values are 'ON', 'OFF', 'FAULTY'.
    """
    if status_filter:
        if status_filter not in ['ON', 'OFF', 'FAULTY']:
            # Or raise ValueError, but returning empty list for invalid filter might be acceptable too
            return []
        return [light for light in _streetlights.values() if light.status == status_filter]
    return list(_streetlights.values())

def update_streetlight_status(light_id: str, status: str, brightness_level: Optional[int] = None) -> Optional[Streetlight]:
    """
    Updates the status and optionally the brightness level of a streetlight.
    Validates status values ('ON', 'OFF', 'FAULTY').
    Brightness level must be between 0 and 100 if provided.
    Updates the 'last_updated' timestamp.
    Returns the updated streetlight or None if not found.
    """
    light = get_streetlight(light_id)
    if not light:
        return None

    # Validate status
    if status not in ['ON', 'OFF', 'FAULTY']:
        raise ValueError("Status must be one of 'ON', 'OFF', or 'FAULTY'.")

    light.status = status

    if brightness_level is not None:
        if not 0 <= brightness_level <= 100:
            raise ValueError("Brightness level must be between 0 and 100.")
        light.brightness_level = brightness_level
    elif status == 'OFF': # If turned off, brightness should be 0
        light.brightness_level = 0
    elif status == 'ON' and light.brightness_level == 0: # If turned ON and brightness is 0, set to a default (e.g. 100)
        light.brightness_level = 100


    light.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _streetlights[light_id] = light # Update the stored object
    return light

def report_streetlight_fault(light_id: str, description: str) -> Optional[Streetlight]:
    """
    Reports a fault for a streetlight. Sets status to 'FAULTY'.
    The description is currently not stored but is included for API compatibility.
    Returns the updated streetlight or None if not found.
    """
    # For now, a fault report simply sets the status to 'FAULTY'.
    # The description parameter is kept for future enhancements (e.g., logging faults).
    # We can use update_streetlight_status to handle this.
    # If a specific brightness is associated with 'FAULTY', it can be set here.
    # For example, some systems might keep faulty lights ON at a dim level for safety.
    # Here, we'll just set it to FAULTY and let brightness be handled by update_streetlight_status logic.
    # If brightness_level is not specified for FAULTY, it will retain its current level unless explicitly set.
    # Let's assume FAULTY lights maintain their current brightness or are handled by a separate rule.
    # For simplicity, we'll just set status to FAULTY.

    # A more direct approach without calling update_streetlight_status:
    light = get_streetlight(light_id)
    if not light:
        return None

    light.status = 'FAULTY'
    # Optionally, set a specific brightness for faulty lights, e.g., light.brightness_level = 0 or some dim value
    light.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _streetlights[light_id] = light
    # print(f"Fault reported for {light_id}: {description}") # Placeholder for logging
    return light

def simulate_energy_consumption(duration_hours: float) -> float:
    """
    Simulates energy consumption for all 'ON' streetlights.

    Iterates through all streetlights, calculates energy consumed based on
    power_consumption_watts, brightness_level, and duration_hours.
    Updates the current_energy_usage for each streetlight and returns the
    total energy consumed in this simulation run.

    Args:
        duration_hours: The duration of the simulation in hours.

    Returns:
        The total energy consumed by all lights in kWh.
    """
    total_energy_consumed_kwh = 0.0

    if duration_hours <= 0:
        # No consumption if duration is zero or negative
        return 0.0

    for light in _streetlights.values():
        if light.status == 'ON' and \
           light.power_consumption_watts is not None and \
           light.power_consumption_watts > 0:

            # Energy (kWh) = (Power (Watts) * Brightness (%) * Time (hours)) / 1000
            # Brightness is a percentage, so divide by 100
            energy_kwh = (light.power_consumption_watts * \
                          (light.brightness_level / 100.0) * \
                          duration_hours) / 1000.0

            light.current_energy_usage += energy_kwh
            total_energy_consumed_kwh += energy_kwh
            # No need to call _streetlights[light.light_id] = light as we are modifying the object directly

    return total_energy_consumed_kwh

def apply_adaptive_lighting_schedule(current_time_hour: int) -> Dict:
    """
    Applies an adaptive lighting schedule to streetlights with the feature enabled.

    Adjusts status and brightness based on the current hour of the day.
    - 0-5 AM (0-5): ON, Brightness 50%
    - 8 AM-5 PM (8-17): OFF, Brightness 0%
    - 6-7 AM (6-7) or 6 PM-11 PM (18-23): ON, Brightness 100%
    - Other times: No change.

    Updates 'last_updated' for any lights that are changed.

    Args:
        current_time_hour: The current hour of the day (0-23).

    Returns:
        A dictionary summarizing the changes, including the count of updated
        lights and details for each.
    """
    if not 0 <= current_time_hour <= 23:
        raise ValueError("current_time_hour must be between 0 and 23.")

    updated_lights_count = 0
    update_details = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for light in _streetlights.values():
        if not light.adaptive_lighting_enabled:
            continue

        original_status = light.status
        original_brightness = light.brightness_level

        new_status = original_status
        new_brightness = original_brightness

        if 0 <= current_time_hour <= 5: # Late Night (0-5 AM)
            new_status = 'ON'
            new_brightness = 50
        elif 8 <= current_time_hour <= 17: # Day Time (8 AM - 5 PM)
            new_status = 'OFF'
            new_brightness = 0
        elif (6 <= current_time_hour <= 7) or (18 <= current_time_hour <= 23): # Evening/Early Morning
            new_status = 'ON'
            new_brightness = 100
        # else: No change for other times, as per requirement.

        if new_status != original_status or new_brightness != original_brightness:
            light.status = new_status
            light.brightness_level = new_brightness
            light.last_updated = now_iso
            # _streetlights[light.light_id] = light # Not strictly necessary, modifying object in place

            updated_lights_count += 1
            update_details.append({
                "light_id": light.light_id,
                "new_status": new_status,
                "new_brightness": new_brightness
            })

    return {
        "updated_lights": updated_lights_count,
        "details": update_details
    }

# Helper function for tests to clear data
def _reset_streetlights_data():
    _streetlights.clear()
