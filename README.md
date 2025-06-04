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
