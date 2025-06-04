# Intelligent Traffic Signal Management for Emergency Vehicles

## Description

This project simulates a basic traffic management system designed to prioritize emergency vehicles (EVs) at traffic signals. When an EV approaches an intersection, the system aims to adjust the traffic signal states to grant the EV right-of-way, thereby reducing response times.

## Components

The system is composed of the following Python modules:

*   **`models.py`**: Defines the core data structures used in the simulation:
    *   `EmergencyVehicle`: Represents an emergency vehicle, storing its ID, type, location, route, and status.
    *   `TrafficSignal`: Represents a traffic signal, storing its ID, location, current state of its different aspects (e.g., north-south, east-west), lanes controlled, and default timing.

*   **`signal_controller.py`**: Contains the `SignalController` class. This class is responsible for:
    *   Managing the state of registered `TrafficSignal` objects.
    *   Implementing the logic for emergency preemption (i.e., changing signal states when an EV approaches).
    *   Reverting signals to a normal or safe state after an EV has passed.

*   **`communication.py`**: Includes the `CentralCommunicator` class. This class simulates the communication link:
    *   It acts as a bridge between an emergency vehicle (or a system tracking it) and the `SignalController`.
    *   It relays information about an approaching EV to the controller to trigger preemption.

*   **`simulation.py`**: Provides the `TrafficSimulation` class. This module is used to:
    *   Set up a demonstration scenario involving traffic signals and an emergency vehicle.
    *   Run a step-by-step simulation showing the initial state of signals, the change in signal state upon EV approach, and the state after the EV has passed.

*   **`tests/test_signal_controller.py`**: Contains unit tests for the `SignalController` class. These tests verify the functionality of signal registration, state changes, and the emergency preemption logic.

## How to Run the Simulation

To run the basic emergency vehicle preemption scenario:

1.  Navigate to the root directory of this repository in your terminal.
2.  Execute the simulation module as a Python package:

    ```bash
    python -m traffic_management.simulation
    ```

    This will print output to the console, showing the different stages of the simulation, including signal state changes.

## How to Run Tests

To run the unit tests for the `SignalController`:

1.  Navigate to the root directory of this repository in your terminal.
2.  Execute the tests using Python's `unittest` module:

    ```bash
    python -m unittest traffic_management.tests.test_signal_controller
    ```

    Alternatively, to discover and run all tests within the `traffic_management/tests` directory (if more test files were added):

    ```bash
    python -m unittest discover -s traffic_management/tests -p "test_*.py"
    ```

    The test results will be displayed in the console.
