# This file will contain the simulation environment for the traffic management system.
# It demonstrates emergency vehicle preemption.

import time # For potential pauses, not for simulation steps here
from .models import TrafficSignal, EmergencyVehicle
from .signal_controller import SignalController
from .communication import CentralCommunicator

class TrafficSimulation:
    """
    Simulates a scenario involving an emergency vehicle and traffic signal preemption.
    """
    def __init__(self, sim_id="Sim01"):
        self.sim_id = sim_id
        self.controller = None
        self.communicator = None
        self.signals = {} # Store signal objects keyed by id
        self.emergency_vehicles = {} # Store EV objects keyed by id
        self.log = []

        self._setup_simulation_entities()

    def _setup_simulation_entities(self):
        """Initializes the core components of the simulation."""
        self.log_event("Setting up simulation entities...")

        # 1. Instantiate SignalController
        self.controller = SignalController(controller_id="Ctrl001")
        self.log_event(f"SignalController '{self.controller.controller_id}' instantiated.")

        # 2. Instantiate CentralCommunicator, linking it to the SignalController
        self.communicator = CentralCommunicator(signal_controller=self.controller, server_id="CommHub01")
        self.log_event(f"CentralCommunicator '{self.communicator.server_id}' instantiated and linked to controller.")

        # 3. Create TrafficSignal objects
        signal1_initial_state = {"north_south": "red", "east_west": "green"}
        signal1 = TrafficSignal(
            signal_id="TS001",
            location=(10,20),
            current_state=signal1_initial_state.copy(),
            lanes_controlled=["north_south_traffic", "east_west_traffic"],
            default_timing={"green": 30, "yellow": 5, "red": 25}
        )
        self.signals[signal1.id] = signal1

        signal2_initial_state = {"main_st": "green", "side_st": "red"}
        signal2 = TrafficSignal(
            signal_id="TS002",
            location=(30,40),
            current_state=signal2_initial_state.copy(),
            lanes_controlled=["main_st_flow", "side_st_access"],
            default_timing={"green": 40, "yellow": 5, "red": 20}
        )
        self.signals[signal2.id] = signal2

        # 4. Register signals with the SignalController
        self.controller.register_signal(self.signals["TS001"])
        self.controller.register_signal(self.signals["TS002"])
        self.log_event(f"Registered signals: {list(self.signals.keys())} with controller.")

        # 5. Create an EmergencyVehicle instance
        ev_route = ["TS001", "TS003"] # Targeting TS001 first
        emergency_vehicle = EmergencyVehicle(
            vehicle_id="EV007",
            type="ambulance",
            location=(0,0),
            speed=60.0,
            route=ev_route,
            status="en_route_to_emergency"
        )
        self.emergency_vehicles[emergency_vehicle.id] = emergency_vehicle
        self.log_event(f"EmergencyVehicle '{emergency_vehicle.id}' created with route {ev_route}.")
        self.log_event("Simulation entities setup complete.")

    def print_all_signal_states(self, stage_description: str):
        """Helper function to print the current states of all registered signals."""
        print(f"\n--- Signal States: {stage_description} ---")
        if not self.controller.signals:
            print("No signals registered with the controller.")
            return
        for signal_id, signal_obj in self.controller.signals.items():
            print(f"Signal ID: {signal_id}, Location: {signal_obj.location}, Current State: {signal_obj.current_state}")
        print("-------------------------------------------")

    def log_event(self, message: str):
        """Logs a simulation event."""
        entry = f"[{self.sim_id} Log] {message}"
        self.log.append(entry)
        print(entry) # Also print to console for immediate feedback

    def run_emergency_preemption_scenario(self):
        """Executes the emergency vehicle preemption demonstration."""
        self.log_event("Starting emergency preemption scenario...")

        # a. Print initial state of all registered traffic signals
        self.print_all_signal_states("Initial State")

        # b. Simulate the emergency vehicle approaching the first signal in its route
        ev = self.emergency_vehicles.get("EV007")
        if not ev:
            self.log_event("Error: Emergency vehicle EV007 not found for simulation.")
            return

        if not ev.route:
            self.log_event(f"Error: Emergency vehicle {ev.id} has no route defined.")
            return

        target_signal_id = ev.route[0]
        self.log_event(f"Simulating approach of {ev.id} (type: {ev.type}) towards signal {target_signal_id}...")

        # Use the CentralCommunicator instance to send this data
        self.communicator.send_emergency_vehicle_data(
            vehicle_id=ev.id,
            location=ev.location,
            route=ev.route
        )

        # c. Print the state of all registered traffic signals *after* the communication
        self.print_all_signal_states(f"After EV {ev.id} Approach (Targeting {target_signal_id})")

        # d. Simulate the emergency vehicle having passed and ending the preemption
        self.log_event(f"Simulating {ev.id} has passed signal {target_signal_id}...")

        # Use CentralCommunicator to trigger end of preemption
        self.communicator.trigger_end_emergency_preemption(signal_id_to_reset=target_signal_id)

        # e. Print the state of signals again after ending preemption
        self.print_all_signal_states(f"After EV {ev.id} Passed (Preemption Ended for {target_signal_id})")

        self.log_event("Emergency preemption scenario finished.")
        self.print_simulation_log()


    def print_simulation_log(self):
        """Prints all logged events for the simulation run."""
        print("\n--- Full Simulation Log ---")
        for entry in self.log:
            # Re-print without the live prefix if it was already printed
            if entry.startswith(f"[{self.sim_id} Log] "):
                 print(entry)
            else: # Should not happen if log_event is used consistently
                 print(f"RAW: {entry}")
        print("---------------------------")


# Main execution block
if __name__ == "__main__":
    # Instantiate TrafficSimulation and run the scenario
    simulation_instance = TrafficSimulation(sim_id="EmergencyDemoSim")
    simulation_instance.run_emergency_preemption_scenario()

    # Old simulation logic (time-step based) is commented out as it's not used for this specific scenario.
    # sim = TrafficSimulation()
    # sim.add_intersection("Int001")
    # ... (rest of old setup) ...
    # for i in range(10):
    #     sim.run_step(time_delta=5)
    # sim.print_log()
    # ...
