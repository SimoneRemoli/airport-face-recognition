from typing import List

import numpy as np

from globs import CLOUD_FICT
from misc.timeutils import hours_to_secs, seconds_to_hhmmss
from sim.autoscaler import AutoScaler
from sim.executor import ExecutionMode
from sim.stats_types import StatsType
from simio.simprint import sprint_verbose

INFINITE = 9999
INFINITE_TIME = hours_to_secs(INFINITE)
INIT_INV = -INFINITE
INIT = 0


class Time:
    def __init__(self):
        self.arrival = INIT_INV  # next arrival time
        self.current = INIT_INV  # current time
        self.next = INIT_INV  # next (most imminent) event time
        self.last = INIT_INV  # last arrival time


class Track:
    def __init__(self):
        self.node = INIT  # time integrated number in the node
        self.queue = INIT  # time integrated number in the queue
        self.service = INIT  # time integrated number in service


# statistics for a single node/nodetype
class NodeStats:
    def __init__(self, stats_type: StatsType):
        self.stats_type = stats_type  # node name
        self.index = 0  # departed jobs
        self.number = 0  # number of jobs in server (i.e., l(t))
        self.area = Track()  # stats-area track

        self.current_servers_no = 1
        self.waits = None  # wait times
        self.delays = None  # delay times
        self.rhos = None
        self.services = None
        self.numbers_queue = None
        self.numbers_node = None

    def reset(self, edge_max_no):
        self.index = 0
        self.number = 0
        self.area = Track()
        self.waits = [0]
        self.delays = [0]

        self.rhos = [[0] * edge_max_no] if self.stats_type is not StatsType.CLOUD else None
        self.services = [[0] * edge_max_no] if self.stats_type is not StatsType.CLOUD else [[0] * CLOUD_FICT]

        self.numbers_node = [0]
        self.numbers_queue = [0]


class Statistics:
    def __init__(self):

        self.seed = None

        # global jobs count
        self.sys_arrivals_count = 0
        self.sys_number_catE = 0
        self.sys_number_catC = 0

        self.sys_index_catE = 0
        self.sys_index_catC = 0
        self.pcs = [0]

        self.lastcurrent = 0

        # node stats (index, number, track)
        self.stats_edge = NodeStats(StatsType.EDGE)
        self.stats_edge_E = NodeStats(StatsType.EDGE_E)
        self.stats_edge_C = NodeStats(StatsType.EDGE_C)
        self.stats_cloud = NodeStats(StatsType.CLOUD)

        # tuple (categoria, servizio rimanente, servizio svolto)
        self.edge_jobs_queuetrack = []

        self.times_sampling = []

        # final stats
        self.final_edge_rho = []
        self.final_pc = []
        self.final_cloud_serv_S = []
        self.final_cloud_number = []
        self.final_edge_serv_S = []
        self.final_edge_serv_Si = []
        self.final_edge_serv_number = []
        self.final_edge_number = []
        self.final_edge_wait = []
        self.final_edge_queue = []
        self.final_edge_delay = []
        self.final_pc = None

        # scalability
        self.lambda_probed = []
        self.edge_autoscaled_servers = []

    def get_nodestats(self) -> List[NodeStats]:
        return [self.stats_edge, self.stats_edge_E, self.stats_edge_C, self.stats_cloud]

    # update all integrals
    def update_integrals(self, t):
        for node_stat in self.get_nodestats():
            if node_stat.number > 0:
                node_stat.area.node += (t.next - t.current) * node_stat.number
                node_stat.area.queue += (t.next - t.current) * (node_stat.number * node_stat.current_servers_no)
                node_stat.area.service += (t.next - t.current) * min(node_stat.number, node_stat.current_servers_no)

    def reset(self, start_time, edge_max_no):
        self.edge_jobs_queuetrack = []
        self.stats_edge.waits = []
        self.stats_cloud.waits = []
        self.stats_edge_E.waits = []
        self.stats_edge_C.waits = []
        self.lambda_probed = []
        self.edge_autoscaled_servers = []
        self.times_sampling = [start_time]
        for node_stat in [self.stats_edge, self.stats_edge_E, self.stats_edge_C, self.stats_cloud]:
            node_stat.reset(edge_max_no)

    def reset_infinite(self, current_time):

        self.stats_edge.area = Track()
        self.stats_edge.index = 0

        self.stats_edge_E.area = Track()
        self.stats_edge_E.index = 0

        self.stats_edge_C.area = Track()
        self.stats_edge_C.index = 0

        self.stats_cloud.area = Track()
        self.stats_cloud.index = 0

        self.lastcurrent = current_time

    def is_system_empty(self) -> bool:
        return self.stats_edge.number + self.stats_cloud.number == 0

    def sanity_checks(self):
        for stat in [self.stats_edge, self.stats_edge_E, self.stats_edge_C, self.stats_cloud]:
            if stat.number < 0:
                raise ValueError("number < 0 for statistic", stat.stats_type.__str__(), "(value =", stat.number, ")")
            if stat.index < 0:
                raise ValueError("index < 0 for statistic", stat.stats_type.__str__(), "(value =", stat.index, ")")

    def finalize(self, sampler, edge_servers_max, accum_sums, start_time, current_time, execution_mode):

        stats = self
        self.final_edge_rho = np.average([rho for rho in stats.stats_edge.rhos[-1]])
        self.final_edge_serv_Si = np.average([service for service in stats.stats_edge.services[-1]])
        self.final_edge_serv_S = self.final_edge_serv_Si / edge_servers_max
        self.final_edge_wait = stats.stats_edge.waits[-1]
        self.final_edge_delay = stats.stats_edge.delays[-1]
        self.final_edge_queue = stats.stats_edge.numbers_queue[-1]
        self.final_edge_number = stats.stats_edge.numbers_node[-1]
        self.final_cloud_serv_Si = np.average(
            [service for service in stats.stats_cloud.services[-1]])  # if len(stats.stats_cloud.services)>0 else 0
        self.final_cloud_serv_S = self.final_cloud_serv_Si
        self.final_cloud_number = stats.stats_cloud.numbers_node[-1]
        self.final_pc = stats.pcs[-1]

    def dict_filtered(self):
        return {
            # final stats
            "seed": self.seed,

            "E_rho": self.final_edge_rho,
            "E_Si": self.final_edge_serv_Si,
            "E_S": self.final_edge_serv_S,
            "E_Ns": self.final_edge_number,
            "E_Ts": self.final_edge_wait,
            "E_Nq": self.final_edge_queue,
            "E_Tq": self.final_edge_delay,

            "C_S": self.final_cloud_serv_S,
            "C_Ns": self.final_cloud_number,

            "pc": self.final_pc,

            "times_sampling": self.times_sampling,

            "edge_rhos": self.stats_edge.rhos,
            "edge_services": self.stats_edge.services,
            "edge_delays": self.stats_edge.delays,
            "edge_waits": self.stats_edge.waits,
            "edge_numbers_queue": self.stats_edge.numbers_queue,
            "edge_numbers_node": self.stats_edge.numbers_node,

            "edge_delays_E": self.stats_edge_E.delays,
            "edge_waits_E": self.stats_edge_E.waits,
            "edge_rhos_E": self.stats_edge_E.rhos,
            "edge_numbers_E": self.stats_edge_E.numbers_queue,

            "edge_delays_C": self.stats_edge_C.delays,
            "edge_waits_C": self.stats_edge_C.waits,
            "edge_rhos_C": self.stats_edge_C.rhos,
            "edge_numbers_C": self.stats_edge_C.numbers_queue,

            "cloud_services": self.stats_cloud.services,
            "cloud_numbers": self.stats_cloud.numbers_node,

            "scalability_lambda": self.lambda_probed,
            "scalability_edgeno": self.edge_autoscaled_servers,

        }


SAMPLING_TIME_FIN = 100  # s


class Sampler:
    def __init__(self, execution_mode: ExecutionMode, start_time: float, edge_servers_max: int):
        self.execution_mode = execution_mode
        self.start_time = start_time
        self.edge_servers_max = edge_servers_max
        self.timeelapsed_sampling_check = start_time
        self.samples_no = 0
        self.service_sampled = 0

    def sample(self, stats: Statistics, current_time: float, current_edge_servers: int, max_edge_servers: int, accsums,
               current_lambda: float, autoscaler: AutoScaler = None, from_start=False, is_last=False):
        sprint_verbose("Sampling... no." + str(self.samples_no) + "-" + seconds_to_hhmmss(current_time))

        start_time = stats.lastcurrent
        stats.times_sampling.append(current_time)

        rho = {t: [] for t in [StatsType.EDGE, StatsType.EDGE_E, StatsType.EDGE_C, StatsType.CLOUD]}
        service = {t: [] for t in [StatsType.EDGE, StatsType.EDGE_E, StatsType.EDGE_C, StatsType.CLOUD]}
        # stats for edge servers
        for s in range(1, max_edge_servers + 1):
            rho[StatsType.EDGE].append(
                accsums[s].service / (current_time - start_time) if (current_time - start_time) > 0 else 0)
            rho[StatsType.EDGE_E].append(
                accsums[s].service_catE / (current_time - start_time) if (current_time - start_time) > 0 else 0)
            rho[StatsType.EDGE_C].append(
                accsums[s].service_catC / (current_time - start_time) if (current_time - start_time) > 0 else 0)
            service[StatsType.EDGE].append(accsums[s].service / accsums[s].served if accsums[s].served > 0 else 0)
            service[StatsType.EDGE_E].append(
                accsums[s].service_catE / accsums[s].served if accsums[s].served > 0 else 0)
            service[StatsType.EDGE_C].append(
                accsums[s].service_catC / accsums[s].served if accsums[s].served > 0 else 0)

        # stats for cloud servers
        for s in range(max_edge_servers + 1, max_edge_servers + 1 + CLOUD_FICT):
            if accsums[s].service != 0:  # salta i vuoti
                service[StatsType.CLOUD].append(accsums[s].service / accsums[s].served if accsums[s].served > 0 else 0)
                stats.stats_cloud.numbers_node.append((stats.stats_cloud.area.node) / (current_time - start_time) if (
                                                                                                                             current_time - start_time) > 0 else 0)

        for nodestat in stats.get_nodestats():
            type = nodestat.stats_type
            if type is not StatsType.CLOUD:
                nodestat.rhos.append(rho[type])

            if len(service[type]) > 0:  # per il cloud
                nodestat.services.append(service[type])
            nodestat.waits.append(nodestat.area.node / nodestat.index if nodestat.index > 0 else 0)
            if type is not StatsType.CLOUD:
                nodestat.numbers_node.append(
                    nodestat.area.node / (current_time - start_time) if (current_time - start_time) > 0 else 0)

        stats.stats_edge.area.queue = stats.stats_edge.area.node
        stats.stats_edge_E.area.queue = stats.stats_edge_E.area.node
        stats.stats_edge_C.area.queue = stats.stats_edge_C.area.node
        for s in range(1, max_edge_servers + 1):
            if accsums[s].service != 0:  # salta i vuoti
                stats.stats_edge.area.queue -= accsums[s].service
                stats.stats_edge_E.area.queue -= accsums[s].service
                stats.stats_edge_C.area.queue -= accsums[s].service
        for s in range(max_edge_servers + 1, max_edge_servers + 1 + CLOUD_FICT):
            if accsums[s].service != 0:  # salta i vuoti
                stats.stats_cloud.area.queue -= accsums[s].service
        for nodestat in stats.get_nodestats():
            type = nodestat.stats_type
            if type is not StatsType.CLOUD:
                nodestat.delays.append((nodestat.area.queue) / nodestat.index if nodestat.index > 0 else 0)
                nodestat.numbers_queue.append(
                    (nodestat.area.queue) / (current_time - start_time) if (current_time - start_time) > 0 else 0)

        stats.pcs.append(stats.sys_index_catC / stats.sys_arrivals_count if stats.sys_arrivals_count > 0 else 0)

        if autoscaler is not None:
            stats.lambda_probed.append(current_lambda)
            stats.edge_autoscaled_servers.append(current_edge_servers)

        self.timeelapsed_sampling_check = current_time
        self.samples_no += 1
        return stats, accsums
