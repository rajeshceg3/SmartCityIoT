import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class Streetlight:
    """Represents a single streetlight in the energy management system."""
    light_id: str
    location: Dict[str, float]  # e.g., {'lat': 40.7128, 'lon': -74.0060}
    status: str = 'OFF'  # Default status: 'OFF', 'ON', 'FAULTY'
    brightness_level: int = 0  # Percentage, 0-100
    last_updated: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    power_consumption_watts: Optional[float] = None
    current_energy_usage: float = 0.0  # Accumulated energy consumption in kWh
    adaptive_lighting_enabled: bool = False  # Adaptive lighting schedule active

    def __post_init__(self):
        if not 0 <= self.brightness_level <= 100:
            raise ValueError("Brightness level must be between 0 and 100.")
        if self.status not in ['ON', 'OFF', 'FAULTY']:
            raise ValueError("Status must be one of 'ON', 'OFF', or 'FAULTY'.")
