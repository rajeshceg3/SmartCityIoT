# SmartCityIoT - Unified Dashboard

This project explores various IoT solutions for smart cities, now integrated into a unified web dashboard.

## Overview

The SmartCityIoT platform consists of several modules, each addressing a specific aspect of urban management. These modules are accessible through a central Flask-based web dashboard.

**Core Components:**

*   **Main Dashboard (`main_dashboard.py`):** The central Flask application that serves as the entry point to all modules.
*   **Citizen Reporting (`citizen_reporting/`):** Enables citizens to report issues (e.g., potholes, broken streetlights) and officials to track them.
*   **Waste Management (`waste_management/`):** Simulates smart trash bin monitoring and optimizes waste collection routes.
*   **Traffic Management (`traffic_management/`):** Provides tools for monitoring traffic signals, managing emergency vehicle preemption, and running traffic simulations.

## Prerequisites

*   Python 3.x
*   Flask (`pip install Flask`)

## Running the Unified Dashboard

The primary way to use the platform is by running the main dashboard application:

1.  Navigate to the project root directory.
2.  Run the main dashboard application:
    ```bash
    python main_dashboard.py
    ```
    The server will typically start on `http://127.0.0.1:5005/`.

3.  Open your web browser and go to `http://127.0.0.1:5005/` to access the main dashboard. From there, you can navigate to the individual modules.

---

## Modules

### 1. Citizen Reporting & Issue Tracking

This platform enables citizens to report various non-emergency issues and city officials to manage them.

*   **Access via Main Dashboard:** Navigate to the "Citizen Reporting" section from the main dashboard (links to `/citizen/dashboard`).
*   **Features:**
    *   Form for citizens to submit new issue reports.
    *   Dashboard to view, filter, and manage all reported issues.
*   **Standalone Operation (Optional):**
    ```bash
    python -m citizen_reporting.api
    ```
    This typically runs on `http://127.0.0.1:5001/`. The UI would then be accessed at `http://127.0.0.1:5001/citizen` and `http://127.0.0.1:5001/citizen/dashboard`.
*   **API Endpoints (prefixed by its own server URL, e.g., `http://127.0.0.1:5001` if run standalone, or by the main dashboard URL `/citizen` if fully integrated as a blueprint in future):**
    *   `POST /issues`: Create a new issue.
        *   Payload: `{"category": "str", "description": "str", "location": {"lat": float, "lon": float}, "reporter_id": "str" (optional), "photo_filename": "str" (optional)}`
    *   `GET /issues`: List all issues (filterable by `status` and `category`).
    *   `GET /issues/<issue_id>`: Get details of a specific issue.
    *   `PUT /issues/<issue_id>/status`: Update an issue's status.
        *   Payload: `{"status": "str"}`
*   **Unit Tests:**
    ```bash
    python -m unittest citizen_reporting.tests.test_issue_manager
    # or
    python -m unittest discover -s citizen_reporting/tests -v
    ```

---

### 2. Smart Waste Management System

This system provides a simulated environment for managing city trash bins and optimizing waste collection routes.

*   **Access via Main Dashboard:** Navigate to the "Waste Management" section from the main dashboard (links to `/waste/dashboard`).
*   **Features:**
    *   View bin statuses, fill levels, and locations.
    *   View collection routes.
    *   Generate new collection routes.
*   **Standalone Operation (Optional):**
    ```bash
    python -m waste_management.api
    ```
    This typically runs on `http://127.0.0.1:5000/`. The UI would then be accessed at `http://127.0.0.1:5000/dashboard`.
*   **API Endpoints (prefixed by its own server URL, e.g., `http://127.0.0.1:5000` if run standalone, or by the main dashboard URL `/waste` if fully integrated as a blueprint in future):**
    *   `GET /bins`: List all bins (filterable by `status`).
    *   `POST /bins`: Create a new bin.
        *   Payload: `{"bin_id": "str", "location": {"lat": float, "lon": float}, "capacity_gallons": float}`
    *   `GET /bins/<bin_id>`: Get details of a specific bin.
    *   `PUT /bins/<bin_id>/sensor_data`: Update a bin's fill level.
        *   Payload: `{"fill_level": float}`
    *   `GET /routes`: List all collection routes (filterable by `status`).
    *   `POST /routes/generate`: Generate a new collection route.
        *   Payload: `{"assigned_truck_id": "str"}`
    *   `GET /routes/<route_id>`: Get details of a specific route.
    *   `PUT /routes/<route_id>/status`: Update a route's status.
        *   Payload: `{"status": "str"}`
*   **Unit Tests:**
    ```bash
    python -m unittest discover -s waste_management/tests -v
    ```

---

### 3. Traffic Management System

This module provides tools for monitoring traffic signals, managing emergency vehicle preemption, and running traffic simulations.

*   **Access via Main Dashboard:** Navigate to the "Traffic Management" section from the main dashboard (this module is integrated and served at `/traffic`).
*   **Features:**
    *   View the status and configuration of all traffic signals.
    *   Manually override signal states (for authorized users/simulation).
    *   Trigger and end emergency vehicle preemption for specific signals.
    *   Run a full emergency preemption simulation scenario.
    *   View simulation logs.
*   **API Endpoints (prefixed by `/traffic` relative to the main dashboard URL):**
    *   `GET /traffic/signals`: List all traffic signals and their current states.
    *   `GET /traffic/signals/<signal_id>`: Get details of a specific signal.
    *   `POST /traffic/signals/<signal_id>/set_state`: Manually override a signal's state.
        *   Payload: `{"aspect_name": "color", ...}` (e.g. `{"north_south": "green"}`)
    *   `POST /traffic/emergency/trigger`: Trigger emergency preemption.
        *   Payload: `{"signal_id": "str", "vehicle_id": "str" (optional), "location": [lat, lon] (optional)}`
    *   `POST /traffic/emergency/end`: End emergency preemption.
        *   Payload: `{"signal_id": "str"}`
    *   `POST /traffic/simulation/run`: Run the traffic simulation scenario.
    *   `GET /traffic/simulation/log`: Get the log from the latest simulation run (runs a new simulation for the log).
*   **Unit Tests:** *(Note: Unit tests for `traffic_management` core logic like `signal_controller` are present, but API/UI level tests are not yet included in this section.)*
    ```bash
    python -m unittest traffic_management.tests.test_signal_controller
    ```

---

*(Note: Test execution may face timeouts in some sandboxed environments.)*
