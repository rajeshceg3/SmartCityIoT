import uuid
from datetime import datetime
from typing import Optional, List, Dict

from .models import ReportedIssue

# In-memory storage for issues
_issues: Dict[str, ReportedIssue] = {}

# Allowed issue statuses
ALLOWED_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}


def create_issue(
    category: str,
    description: str,
    location: Dict[str, float],
    reporter_id: Optional[str] = None,
    photo_filename: Optional[str] = None,
) -> ReportedIssue:
    """Creates a new issue and stores it."""
    if not isinstance(location, dict) or 'lat' not in location or 'lon' not in location:
        raise ValueError("Location must be a dict with 'lat' and 'lon' keys.")
    if not isinstance(location['lat'], (int, float)) or not isinstance(location['lon'], (int, float)):
        raise ValueError("Location 'lat' and 'lon' must be numbers.")

    issue_id = str(uuid.uuid4())
    now = datetime.now()
    initial_status = "OPEN"

    issue = ReportedIssue(
        issue_id=issue_id,
        timestamp=now,
        category=category,
        description=description,
        location=location,
        status=initial_status,
        reporter_id=reporter_id,
        photo_filename=photo_filename,
        last_updated=now,
    )
    _issues[issue_id] = issue
    return issue


def get_issue(issue_id: str) -> Optional[ReportedIssue]:
    """Retrieves an issue by its ID."""
    return _issues.get(issue_id)


def list_issues(
    status_filter: Optional[str] = None, category_filter: Optional[str] = None
) -> List[ReportedIssue]:
    """Lists all issues, with optional filtering by status and/or category."""
    results = list(_issues.values())

    if status_filter:
        results = [
            issue for issue in results if issue.status.lower() == status_filter.lower()
        ]
    if category_filter:
        results = [
            issue
            for issue in results
            if issue.category.lower() == category_filter.lower()
        ]
    return results


def update_issue_status(
    issue_id: str, new_status: str
) -> Optional[ReportedIssue]:
    """Updates the status of an existing issue."""
    issue = _issues.get(issue_id)
    if not issue:
        return None

    normalized_new_status = new_status.upper()
    if normalized_new_status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Invalid status: '{new_status}'. Allowed statuses are: {', '.join(ALLOWED_STATUSES)}"
        )

    issue.status = normalized_new_status
    issue.last_updated = datetime.now()
    return issue
