

import numpy as np
import pickle
import pandas as pd
import seaborn as sb
import json
import matplotlib.pyplot as plt

from src.entities.uav_entities import DataPacket
from collections import defaultdict
from src.utilities import utilities as util
from src.utilities import config

""" Metrics class keeps track of all the metrics during all the simulation. """


class Metrics:

    def __init__(self, simulator):

        self.simulator = simulator

        # The mean number of possible relays when i want to communicate
        self.mean_numbers_of_possible_relays = []

        # all packets in the simulation
        self.all_control_packets_in_simulation = 0
        self.all_data_packets_in_simulation = 0
        
        # all the events generated during the simulation
        self.events = set()

        # all events not listened due to move routing
        self.events_not_listened = set()

        # all the packets generated by the drones, either delivered or not (union of all the buffers)
        self.drones_packets = set()

        # all the packets notified to the depot
        self.drones_packets_to_depot = set()

        # all packets notified to depot -- but with order
        self.drones_packets_to_depot_list = []

        # number of time steps on mission, incremented each time drone is doing sensing mission
        self.time_on_mission = 0

        self.time_on_active_routing = 0

        self.sent_acks = {} # Used for debug reasons
        
        
    def score(self, undelivered_penalty=1.5):
        """ returns a score for the exectued simulation: 

                sum( event delays )  / number of events

            Notice that, expired or not found events will be counted with a max_delay*penalty
        """
        # mean delivery time
        # get best delivery time for each event  
        all_delivered_events = set([pck.event_ref for pck, _ in self.drones_packets_to_depot])
        event_delivery_times_dict = {ev.identifier: [] for ev in all_delivered_events}

        # DELIVERY TIME -> METRIC FOR PLOT
        for pck, delivery_ts in self.drones_packets_to_depot:
            # time between event generation and packet delivery to depot -> dict to help computation
            event_delivery_times_dict[pck.event_ref.identifier].append(delivery_ts - pck.event_ref.current_time)

        # maps every event to the minimum delay of the packet arrival to the depot
        event_delivery_times = []
        for ev_id in event_delivery_times_dict.keys():
            event_delivery_times.append(np.nanmin(event_delivery_times_dict[ev_id]))

        not_delivered_events = len(self.events) - len(all_delivered_events) 
        assert not_delivered_events >= 0
         
        event_delivery_times.extend([undelivered_penalty * self.simulator.event_duration] * not_delivered_events)  # add penalities to not delivered or not found packets

        return np.nanmean(event_delivery_times)       

    def other_metrics(self):
        """
        Post-execution metrics
        @return: None
        """

        # the number of all the events generated during the simulation
        self.number_of_generated_events = len(self.events)
        self.number_of_not_generated_events = len(self.events_not_listened)

        # the number of all events that the drones discovers, either notified or not
        all_detected_events = set([pck.event_ref for pck in self.drones_packets])
        self.number_of_detected_events = len(all_detected_events)

        # the number of all events that the drones notify (before the event deadline) to the depot
        all_delivered_events = set([pck.event_ref for pck, _ in self.drones_packets_to_depot])

        self.number_of_events_to_depot = len(all_delivered_events)
        self.number_of_packets_to_depot = len(self.drones_packets_to_depot)  # may contain duplicates
        
        # NOTE: THE DEPOT PACKETS ARE NOT COUNTED, WE ADD THEM HERE!! 
        # self.all_data_packets_in_simulation += len(self.drones_packets_to_depot)

        # mean delivery time 
        packet_delivery_times = []

        # maps an event to the time steps in which it was delivered
        event_delivery_times_dict = {ev.identifier: [] for ev in all_delivered_events}

        # DELIVERY TIME -> METRIC FOR PLOT
        for pck, delivery_ts in self.drones_packets_to_depot:
            # time between packet generation and packet delivery to depot
            packet_delivery_times.append(delivery_ts - pck.time_step_creation)

            # time between event generation and packet delivery to depot -> dict to help computation
            event_delivery_times_dict[pck.event_ref.identifier].append(delivery_ts - pck.event_ref.current_time)

        # maps every event to the minimum delay of the packet arrival at the depot
        event_delivery_times = []
        for ev_id in event_delivery_times_dict.keys():
            event_delivery_times.append(np.nanmin(event_delivery_times_dict[ev_id]))

        # averaged delays over all packets/events
        self.event_delivery_times = event_delivery_times
        self.packet_mean_delivery_time = np.mean(packet_delivery_times) * self.simulator.time_step_duration
        self.event_mean_delivery_time = np.mean(event_delivery_times) * self.simulator.time_step_duration

    def print_overall_stats(self):
        """
        print the overall stats of the alg execution
        @return:
        """
        self.other_metrics()
        print(f"*** Relays ***")
        print("Mean number of relays: ", np.nanmean(self.mean_numbers_of_possible_relays))

        print(f"*** Events ***")
        print("Number of generated events: ", self.number_of_generated_events)
        print("Number of detected events: ", self.number_of_detected_events)
        print("Number of events to depot: ", self.number_of_events_to_depot)
        print("Event mean delivery time (seconds): ", self.event_mean_delivery_time)

        print(f"*** Packets ***")
        print("Control packets exchanged during simulation: ", self.all_control_packets_in_simulation)
        print("Data packets generated during simulation: ", self.all_data_packets_in_simulation)
        print("Number of packets to depot: ", len(self.drones_packets_to_depot_list))
        print("Packet mean delivery time (seconds): ", self.packet_mean_delivery_time)
        print("Packet delivery ratio: ", len(self.drones_packets_to_depot_list)/self.all_data_packets_in_simulation)

    def info_mission(self):
        """
        save all the mission / sim setup
        @return: None
        """

        self.mission_setup = {
            "len_simulation": self.simulator.len_simulation,
            "time_step_duration": self.simulator.time_step_duration,
            "seed": self.simulator.seed,
            "n_drones": self.simulator.n_drones,
            "env_width": self.simulator.env_width,
            "env_height": self.simulator.env_height,
            "drone_com_range": self.simulator.drone_com_range,
            "drone_sen_range": self.simulator.drone_sen_range,
            "drone_speed": self.simulator.drone_speed,
            "drone_max_buffer_size": self.simulator.drone_max_buffer_size,
            "drone_max_energy": self.simulator.drone_max_energy,
            "drone_retransmission_delta": self.simulator.drone_retransmission_delta,
            "drone_communication_success": self.simulator.drone_communication_success,
            "depot_com_range": self.simulator.depot_com_range,
            "depot_coordinates": self.simulator.depot_coordinates,
            "event_duration": self.simulator.event_duration,
            "packets_max_ttl": self.simulator.packets_max_ttl,
            "show_plot": self.simulator.show_plot,
            "routing_algorithm": str(self.simulator.routing_algorithm),
            "communication_error_type": str(self.simulator.communication_error_type),
            "time_on_active_routing" : str(self.time_on_active_routing)
        }

    def __dictionary_represenation(self):
        """ compute the dictionary to save as json """
        self.other_metrics()

        out_results = {"mission_setup": self.mission_setup}
        out_results["number_of_generated_events"] = self.number_of_generated_events
        out_results["number_of_detected_events"] = self.number_of_detected_events
        out_results["number_of_not_generated_events"] = self.number_of_not_generated_events
        out_results["throughput"] = self.number_of_packets_to_depot / (self.mission_setup["len_simulation"] * self.mission_setup["time_step_duration"])        
        out_results["number_of_events_to_depot"] = self.number_of_events_to_depot
        out_results["number_of_packets_to_depot"] = self.number_of_packets_to_depot
        out_results["packet_mean_delivery_time"] = self.packet_mean_delivery_time
        out_results["event_mean_delivery_time"] = self.event_mean_delivery_time
        out_results["time_on_mission"] = self.time_on_mission
        out_results["packet_delivery_ratio"] = self.number_of_packets_to_depot/self.all_data_packets_in_simulation
        out_results["all_control_packets_in_simulation"] = self.all_control_packets_in_simulation
        out_results["all_data_packets_in_simulation"] = self.all_data_packets_in_simulation
        out_results["all_events"] = [ev.to_json() for ev in self.events]
        out_results["not_listened_events"] = [ev.to_json() for ev in self.events_not_listened]
        out_results["events_delivery_times"] = [str(e) for e in self.event_delivery_times]
        out_results["drones_packets"] = [pck.to_json() for pck in self.drones_packets]
        out_results["drones_to_depot_packets"] = [(pck.to_json(), delivery_ts) for pck, delivery_ts in self.drones_packets_to_depot]
        out_results["mean_number_of_relays"] = np.nanmean(self.mean_numbers_of_possible_relays)

        return out_results

    def save(self, filename):
        """ save the metrics on file """
        with open(filename, 'wb') as out:
            pickle.dump(self, out)

    @staticmethod
    def from_file(filename):
        """ load the metrics from a file """
        with open(filename, 'rb') as handle:
            obj = pickle.load(handle)
        return obj

    def save_as_json(self, filename):
        """ save all the metrics into a json file """
        out = self.__dictionary_represenation()
        js = json.dumps(out)
        f = open(filename, "w")
        f.write(js)
        f.close()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str(self.__dictionary_represenation())

if __name__ == "__main__":
    m = Metrics().from_file("data/experiments/test_stats.pickle")