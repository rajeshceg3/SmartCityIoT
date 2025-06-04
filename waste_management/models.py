import datetime
from dataclasses import dataclass, field
from typing import Optional # Used for Optional attributes like started_at, completed_at

@dataclass
class TrashBin:
    """Represents a single trash bin in the waste management system."""
    bin_id: str
    location: dict[str, float]  # e.g., {'lat': 40.7128, 'lon': -74.0060}
    capacity_gallons: float
    current_fill_level_gallons: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    status: str = 'EMPTY'  # e.g., 'EMPTY', 'FILLING', 'FULL', 'NEEDS_MAINTENANCE'

@dataclass
class WasteCollectionTruck:
    """Represents a waste collection truck."""
    truck_id: str
    current_location: dict[str, float]  # e.g., {'lat': 40.7128, 'lon': -74.0060}
    capacity_gallons: float
    current_load_gallons: float = 0.0
    status: str = 'IDLE'  # e.g., 'IDLE', 'ON_ROUTE', 'DUMPING_LOAD', 'MAINTENANCE'

@dataclass
class CollectionRoute:
    """Represents a collection route for a waste collection truck."""
    route_id: str
    assigned_truck_id: str
    bin_ids_to_collect: list[str]
    status: str = 'PENDING'  # e.g., 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
    generated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
