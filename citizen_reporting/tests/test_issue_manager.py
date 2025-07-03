import unittest
from datetime import datetime, timedelta
from typing import Dict, Any # For type hinting test data

# Adjust imports based on how Python resolves modules in your test environment.
# If running `python -m unittest discover` from the project root, these should work:
from citizen_reporting import issue_manager
from citizen_reporting.models import ReportedIssue

# If the above don't work, you might need relative imports if tests are run as a package:
# from .. import issue_manager
# from ..models import ReportedIssue


class TestIssueManager(unittest.TestCase):

    def setUp(self):
        """Clear the in-memory issue storage before each test."""
        issue_manager._issues.clear()
        # It's also good to reset any other global state if applicable, e.g. Allowed Statuses
        # For this example, ALLOWED_STATUSES is a constant, so no reset needed.

    def _create_sample_issue(self, **kwargs: Any) -> ReportedIssue:
        """Helper method to create a sample issue with default values."""
        data: Dict[str, Any] = {
            "category": "Pothole",
            "description": "A big pothole",
            "location": {"lat": 34.0, "lon": -118.0},
            "reporter_id": "user1",
            **kwargs,  # Allows overriding defaults
        }
        return issue_manager.create_issue(
            category=data["category"],
            description=data["description"],
            location=data["location"],
            reporter_id=data.get("reporter_id"),
            photo_filename=data.get("photo_filename"),
        )

    def test_create_issue_success(self):
        """Test successful creation of an issue."""
        category = "Streetlight Out"
        description = "Light at Main and 1st is out"
        location = {"lat": 34.0522, "lon": -118.2437}
        reporter_id = "test_user_123"
        photo_filename = "light_out.jpg"

        issue = issue_manager.create_issue(
            category, description, location, reporter_id, photo_filename
        )

        self.assertIsInstance(issue, ReportedIssue)
        self.assertIn(issue.issue_id, issue_manager._issues)
        self.assertEqual(issue.category, category)
        self.assertEqual(issue.description, description)
        self.assertEqual(issue.location, location)
        self.assertEqual(issue.reporter_id, reporter_id)
        self.assertEqual(issue.photo_filename, photo_filename)
        self.assertEqual(issue.status, "OPEN")
        self.assertIsInstance(issue.timestamp, datetime)
        self.assertIsInstance(issue.last_updated, datetime)
        self.assertAlmostEqual(issue.timestamp, issue.last_updated, delta=timedelta(seconds=1))

        stored_issue = issue_manager._issues[issue.issue_id]
        self.assertEqual(issue, stored_issue)

    def test_create_issue_invalid_location(self):
        """Test create_issue with invalid location data."""
        with self.assertRaisesRegex(ValueError, "Location must be a dict with 'lat' and 'lon' keys."):
            issue_manager.create_issue("Test", "Test desc", {"lat": 1.0}) # Missing lon
        with self.assertRaisesRegex(ValueError, "Location must be a dict with 'lat' and 'lon' keys."):
            issue_manager.create_issue("Test", "Test desc", {"lon": 1.0}) # Missing lat
        with self.assertRaisesRegex(ValueError, "Location must be a dict with 'lat' and 'lon' keys."):
            issue_manager.create_issue("Test", "Test desc", {})
        with self.assertRaisesRegex(ValueError, "Location 'lat' and 'lon' must be numbers."):
            issue_manager.create_issue("Test", "Test desc", {"lat": "invalid", "lon": 1.0})
        with self.assertRaisesRegex(ValueError, "Location 'lat' and 'lon' must be numbers."):
            issue_manager.create_issue("Test", "Test desc", {"lat": 1.0, "lon": "invalid"})


    def test_get_issue_existing(self):
        """Test retrieving an existing issue."""
        created_issue = self._create_sample_issue(category="Test Category")
        retrieved_issue = issue_manager.get_issue(created_issue.issue_id)
        self.assertEqual(created_issue, retrieved_issue)

    def test_get_issue_non_existent(self):
        """Test retrieving a non-existent issue."""
        retrieved_issue = issue_manager.get_issue("non_existent_id")
        self.assertIsNone(retrieved_issue)

    def test_list_issues_empty(self):
        """Test listing issues when none exist."""
        self.assertEqual(issue_manager.list_issues(), [])

    def test_list_issues_multiple(self):
        """Test listing multiple issues."""
        issue1 = self._create_sample_issue(category="Cat1")
        issue2 = self._create_sample_issue(category="Cat2")
        issues = issue_manager.list_issues()
        self.assertIn(issue1, issues)
        self.assertIn(issue2, issues)
        self.assertEqual(len(issues), 2)

    def test_list_issues_filter_by_status(self):
        """Test filtering issues by status (case-insensitive)."""
        issue_open = self._create_sample_issue() # Status will be OPEN by default

        issue_in_progress = self._create_sample_issue(category="InProgressCategory")
        issue_manager.update_issue_status(issue_in_progress.issue_id, "IN_PROGRESS")

        issue_to_be_closed = self._create_sample_issue(category="ToBeClosedCategory") # Status will be OPEN initially
        issue_manager.update_issue_status(issue_to_be_closed.issue_id, "CLOSED")

        # Verify counts first
        all_issues = issue_manager.list_issues()
        self.assertEqual(len(all_issues), 3, "Should be three issues in total")

        open_issues = issue_manager.list_issues(status_filter="open")
        self.assertEqual(len(open_issues), 1, "Should be one OPEN issue")
        if open_issues: # Check if list is not empty
            self.assertEqual(open_issues[0].status, "OPEN")
            self.assertEqual(open_issues[0].issue_id, issue_open.issue_id)

        in_progress_issues = issue_manager.list_issues(status_filter="In_PrOgReSs")
        self.assertEqual(len(in_progress_issues), 1, "Should be one IN_PROGRESS issue")
        if in_progress_issues: # Check if list is not empty
            self.assertEqual(in_progress_issues[0].status, "IN_PROGRESS")
            self.assertEqual(in_progress_issues[0].issue_id, issue_in_progress.issue_id)

        closed_issues = issue_manager.list_issues(status_filter="CLOSED")
        self.assertEqual(len(closed_issues), 1, "Should be one CLOSED issue")
        if closed_issues: # Check if list is not empty
            self.assertEqual(closed_issues[0].status, "CLOSED")
            self.assertEqual(closed_issues[0].issue_id, issue_to_be_closed.issue_id)


    def test_list_issues_filter_by_category(self):
        """Test filtering issues by category (case-insensitive)."""
        self._create_sample_issue(category="Pothole")
        self._create_sample_issue(category="Graffiti")
        self._create_sample_issue(category="POTHOLE") # Different case

        pothole_issues = issue_manager.list_issues(category_filter="pothole")
        self.assertEqual(len(pothole_issues), 2)
        for issue in pothole_issues:
            self.assertEqual(issue.category.lower(), "pothole")

        graffiti_issues = issue_manager.list_issues(category_filter="Graffiti")
        self.assertEqual(len(graffiti_issues), 1)
        self.assertEqual(graffiti_issues[0].category, "Graffiti")

    def test_list_issues_filter_by_status_and_category(self):
        """Test filtering by both status and category."""
        issue1 = self._create_sample_issue(category="Pothole") # Status OPEN
        issue2 = self._create_sample_issue(category="Pothole")
        issue_manager.update_issue_status(issue2.issue_id, "IN_PROGRESS")
        self._create_sample_issue(category="Graffiti") # Status OPEN

        filtered_issues = issue_manager.list_issues(status_filter="open", category_filter="Pothole")
        self.assertEqual(len(filtered_issues), 1)
        self.assertEqual(filtered_issues[0].issue_id, issue1.issue_id)

    def test_update_issue_status_success(self):
        """Test successfully updating an issue's status."""
        issue = self._create_sample_issue()
        original_last_updated = issue.last_updated

        # Ensure time changes for last_updated
        # A small delay might be needed on very fast systems if datetime.now() resolution is an issue
        # For most practical purposes, subsequent calls to datetime.now() will be different.
        # If tests are flaky here, add a time.sleep(0.000001) or similar.

        updated_issue = issue_manager.update_issue_status(issue.issue_id, "RESOLVED")

        self.assertIsNotNone(updated_issue)
        self.assertEqual(updated_issue.status, "RESOLVED")
        self.assertGreater(updated_issue.last_updated, original_last_updated)

        stored_issue = issue_manager.get_issue(issue.issue_id)
        self.assertEqual(stored_issue.status, "RESOLVED")
        self.assertEqual(stored_issue.last_updated, updated_issue.last_updated)

    def test_update_issue_status_invalid_status(self):
        """Test updating with an invalid status."""
        issue = self._create_sample_issue()
        with self.assertRaisesRegex(ValueError, "Invalid status: 'INVALID_STATUS'. Allowed statuses are:"):
            issue_manager.update_issue_status(issue.issue_id, "INVALID_STATUS")

    def test_update_issue_status_non_existent(self):
        """Test updating a non-existent issue."""
        result = issue_manager.update_issue_status("non_existent_id", "OPEN")
        self.assertIsNone(result)

    def test_update_issue_status_case_insensitivity(self):
        """Test that status update is case-insensitive for new_status argument."""
        issue = self._create_sample_issue()
        updated_issue = issue_manager.update_issue_status(issue.issue_id, "rEsOlVeD")
        self.assertIsNotNone(updated_issue)
        self.assertEqual(updated_issue.status, "RESOLVED") # Should be stored in upper case as per ALLOWED_STATUSES

if __name__ == '__main__':
    unittest.main()
