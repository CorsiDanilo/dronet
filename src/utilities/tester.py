
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.simulation.simulator import Simulator
    from src.entities.uav_entities import Depot, Drone, AckDiscoveryPacket
from src.utilities import utilities
from src.utilities import printer

class Tester():
    def __init__(self, simulator):
        self.simulator: Simulator = simulator

    # Debugging for lost acks
    ##########################################################################      
    def add_ack(self, ack_packet: AckDiscoveryPacket, parent_node: Drone | Depot):
        if ack_packet.sender_id not in self.simulator.metrics.sent_acks:
            self.simulator.metrics.sent_acks[parent_node.identifier] = []
        self.simulator.metrics.sent_acks[parent_node.identifier] += [self]

    def check_if_lost_ack(self, drone: Drone):
        if drone.identifier in self.simulator.metrics.sent_acks:
            acks_received = self.simulator.metrics.sent_acks[drone.identifier]
            neighbor_table = drone.neighbor_table.get_drones()
            lost_drones = set(acks_received).difference(neighbor_table)
            return lost_drones
        return set()

    def check_if_lost_ack_depot(self):
        if self.simulator.depot.identifier in self.simulator.metrics.sent_acks:
            acks_received = self.simulator.metrics.sent_acks[self.simulator.depot.identifier]
            neighbor_table = set(self.simulator.depot.nodes_table.nodes_list.keys())
            lost_drones = {drone.identifier for drone in acks_received}.difference(neighbor_table)
            return lost_drones
        return set()
    
    def lost_drones(self):
        for drone in self.drones:
            lost_drones = self.check_if_lost_ack(drone)
            if lost_drones != set():
                print(f"Lost drones: {lost_drones}")
        depot_lost_drones = self.check_if_lost_ack_depot()
        if depot_lost_drones != set():
            print(f"Depot lost drones: {depot_lost_drones}")
    
    def reset_state(self):
        self.simulator.metrics.sent_acks = {}
    ##########################################################################
    


    # Debugging for hop_count update
    ##########################################################################
    def hop_count_tester(self):
        drone: Drone
        for drone in [self.simulator.drones[id] for id in self.simulator.depot.nodes_table.nodes_list.keys() if utilities.euclidean_distance(self.simulator.drones[id].coords, self.simulator.depot.coords) <= self.simulator.depot.communication_range]:
            if drone.hop_from_depot > 1:
                printer.print_debug_colored(200, 0, 0, f"{drone} is in the neighborhood of the depot with hop count {drone.hop_from_depot}")
    
    def test_wrong_hop_from_depot(self):
        if len(self.simulator.depot.nodes_table.nodes_list) != 0:
            hop_counts = [node_info.hop_count > 1 for node_info in self.simulator.depot.nodes_table.nodes_list.values()]
            if any(hop_counts):
                print(f"Depot neighbors: {self.simulator.depot.nodes_table.nodes_list}")
    ##########################################################################