# SmartCityIoT

This project aims to explore various IoT solutions for smart cities.

## Feature: Smart Waste Management System

This system provides a simulated environment for managing city trash bins and optimizing waste collection routes.

### Overview

The system consists of:
*   **Data Models**: For `TrashBin`, `WasteCollectionTruck`, and `CollectionRoute`.
*   **Sensor Simulator**: To mimic IoT sensors reporting bin fill levels.
*   **Core Logic**:
    *   `bin_manager`: Manages bin data and status updates.
    *   `route_manager`: Generates collection routes based on full bins.
*   **Flask API**: Exposes endpoints to interact with the system.
*   **Simple Web Dashboard**: A basic web interface to view system status and trigger actions.
*   **Unit Tests**: For core logic modules.

### Prerequisites

*   Python 3.x
*   Flask (`pip install Flask`)

### Running the Application

1.  Navigate to the project directory.
2.  Ensure you are in the `waste_management` subdirectory if running modules directly, or manage Python paths appropriately.
3.  To start the API server (which also serves the dashboard):
    ```bash
    python -m waste_management.api
    ```
    The server will typically start on `http://127.0.0.1:5000/`.

### Accessing the Dashboard

Once the API server is running, open your web browser and go to:
`http://127.0.0.1:5000/dashboard`

### API Endpoints

All API endpoints are prefixed with the base URL (e.g., `http://127.0.0.1:5000`).

**Bins API (`/bins`)**

*   `GET /bins`: List all bins.
    *   Query param: `status` (e.g., `/bins?status=FULL`) to filter by status.
*   `POST /bins`: Create a new bin.
    *   Payload: `{"bin_id": "str", "location": {"lat": float, "lon": float}, "capacity_gallons": float}`
*   `GET /bins/<bin_id>`: Get details of a specific bin.
*   `PUT /bins/<bin_id>/sensor_data`: Update a bin's fill level.
    *   Payload: `{"fill_level": float}`

**Routes API (`/routes`)**

*   `GET /routes`: List all collection routes.
    *   Query param: `status` (e.g., `/routes?status=PENDING`) to filter.
*   `POST /routes/generate`: Generate a new collection route for full bins.
    *   Payload: `{"assigned_truck_id": "str"}`
*   `GET /routes/<route_id>`: Get details of a specific route.
*   `PUT /routes/<route_id>/status`: Update a route's status.
    *   Payload: `{"status": "str"}` (e.g., "IN_PROGRESS", "COMPLETED")

### Running Unit Tests

Unit tests are located in the `waste_management/tests` directory and use Python's `unittest` module.

To run all tests (from the project root, assuming `waste_management` is in your PYTHONPATH or you are in a suitable directory):
```bash
python -m unittest discover -s waste_management/tests -v
```
Or run individual test files:
```bash
python -m unittest waste_management.tests.test_bin_manager
python -m unittest waste_management.tests.test_route_manager
```
*(Note: Test execution may face timeouts in some sandboxed environments.)*

---

## Feature: Citizen Reporting & Issue Tracking Platform

This platform enables citizens to report various non-emergency issues (e.g., potholes, broken streetlights) within the city. City officials can then use the system to track and manage these reported issues.

### Overview

The system includes:
*   **Data Model**: For `ReportedIssue` (capturing details like category, description, location, status, etc.).
*   **Core Logic**: `issue_manager` for creating, retrieving, listing, and updating issues.
*   **Flask API**: Exposes endpoints for issue management.
*   **Simple Web Interface**:
    *   A form for citizens to submit new issue reports.
    *   A dashboard to view and filter all reported issues.
*   **Unit Tests**: For the `issue_manager` module.

### Prerequisites

*   Python 3.x
*   Flask (`pip install Flask`)

### Running the Application (Citizen Reporting)

1.  Navigate to the project directory.
2.  To start the Flask API server for the citizen reporting module:
    ```bash
    python -m citizen_reporting.api
    ```
    The server will typically start on `http://127.0.0.1:5001/`.

### Accessing the Web Interface

Once the Citizen Reporting API server is running, you can access the web pages:

*   **Report an Issue**: `http://127.0.0.1:5001/citizen`
*   **View Issues Dashboard**: `http://127.0.0.1:5001/citizen/dashboard`

### API Endpoints (Citizen Reporting)

All API endpoints are prefixed with the base URL `http://127.0.0.1:5001`.

*   **Create a new issue**
    *   `POST /issues`
    *   Payload: `{"category": "str", "description": "str", "location": {"lat": float, "lon": float}, "reporter_id": "str" (optional), "photo_filename": "str" (optional)}`
    *   Example Response (201 Created): `{"issue_id": "uuid", "timestamp": "datetime", "category": "...", ...}`

*   **List all issues**
    *   `GET /issues`
    *   Optional Query Parameters:
        *   `status`: e.g., `/issues?status=OPEN`
        *   `category`: e.g., `/issues?category=Pothole`
    *   Example Response (200 OK): `[{"issue_id": "...", ...}, ...]`

*   **Get details of a specific issue**
    *   `GET /issues/<issue_id>`
    *   Example Response (200 OK): `{"issue_id": "...", ...}`

*   **Update an issue's status**
    *   `PUT /issues/<issue_id>/status`
    *   Payload: `{"status": "str"}` (e.g., "IN_PROGRESS", "RESOLVED", "CLOSED")
    *   Example Response (200 OK): `{"issue_id": "...", "status": "NEW_STATUS", ...}`

### Running Unit Tests (Citizen Reporting)

Unit tests for the citizen reporting module are located in `citizen_reporting/tests/`.

To run these specific tests using Python's `unittest` module (from the project root):
```bash
python -m unittest citizen_reporting.tests.test_issue_manager
```
Alternatively, to discover and run all tests within the `citizen_reporting/tests` directory:
```bash
python -m unittest discover -s citizen_reporting/tests -v
```
