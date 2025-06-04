from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class ReportedIssue:
    """Represents a citizen-reported issue."""
    issue_id: str
    timestamp: datetime
    category: str
    description: str
    location: Dict[str, float]  # e.g., {"lat": 0.0, "lon": 0.0}
    status: str  # e.g., "open", "in_progress", "resolved", "closed"
    last_updated: datetime
    reporter_id: Optional[str] = None
    photo_filename: Optional[str] = None
