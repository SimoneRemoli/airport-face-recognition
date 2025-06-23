import json
from enum import Enum
from pathlib import Path
from typing import List

from DES_Python.rngs import plantSeeds, getSeed
from simio.json_handler import json_encoder_default
from simio.simprint import sprint


class SchedulingPolicy(Enum):
    PS = 0
    FIFO = 1

    def __repr__(self): return self.name


class ExecutionMode(Enum):
    MODEL = 0,
    VERIFY_FEEDBACK_CUT = 1,
    TRANSIENT_ANALYSIS = 2,
    FINITE_BATCH = 3,
    INFINITE_SIMULATION = 4
    FINITE = 5
    INFINITE_SIMULATION_EXP = 6
    INFINITE_SIMULATION_BATCH=7

    def __repr__(self): return self.name


# individua una singola simulazione, for persistence purposes mainly
class SimulationId:
    def __init__(self,
                 description: str,
                 scheduling_policy: SchedulingPolicy,
                 execution_mode: ExecutionMode,
                 scalability: bool,
                 seed: int,
                 replication_no: int,
                 start_time: float,
                 stop_time: float,
                 infsim_B: int,
                 infsim_K: int,
                 edge_servers_init: int,
                 edge_servers_max: int,
                 lambda_value: float,
                 pc: float
                 ):
        self.description = description
        self.scheduling_policy = scheduling_policy
        self.execution_mode = execution_mode
        self.scalability = scalability,
        self.seed = seed
        self.replication_no = replication_no
        self.start_time = start_time
        self.stop_time = stop_time
        self.infsim_B = infsim_B
        self.infsim_K = infsim_K
        self.edge_servers_init = edge_servers_init
        self.edge_servers_max = edge_servers_max
        self.lambda_value = lambda_value
        self.pc = pc

    def dict_filtered(self):
        return {"repl": self.replication_no}


class Experiment:
    def __init__(self,
                 description: str,
                 scheduling_policies: List,
                 execution_modes: List,
                 scalability: bool,
                 initial_seed: int,
                 replications: int,
                 start_time: float,
                 stop_time: float,
                 edge_servers_init: int,
                 edge_servers_max: int,
                 lambda_values: List,
                 pc_values: List,
                 infsim_B: int,
                 infsim_K: int
                 ):
        self.description = description
        self.scheduling_policies = scheduling_policies
        self.execution_modes = execution_modes
        self.scalability = scalability
        self.initial_seed = initial_seed
        self.replications = replications
        self.start_time = start_time
        self.stop_time = stop_time
        self.edge_servers_init = edge_servers_init
        self.edge_servers_max = edge_servers_max
        self.pc_values = pc_values
        self.lambda_values = lambda_values
        self.infsim_B = infsim_B
        self.infsim_K = infsim_K

        self.results = {}

    def run(self, override_results: bool = False, persist: bool = True, need_return: bool = False) -> dict:
        results = {}
        sim_id = None
        for schedpol in self.scheduling_policies:
            for exec_mode in self.execution_modes:
                for lambda_val in self.lambda_values:
                    for pc_val in self.pc_values:
                        replications_data_for_output = {}
                        # check if all the replications statistics are already run
                        # (in that case, load them from file instead of execute simulations)
                        sim_id_last_replica = SimulationId(self.description, schedpol, exec_mode, self.scalability,
                                                           None, self.replications, self.start_time, self.stop_time,
                                                           self.infsim_B, self.infsim_K, self.edge_servers_init,
                                                           self.edge_servers_max,
                                                           lambda_val, pc_val
                                                           )
                        stats_last = self.load(sim_id_last_replica)
                        are_all_replications_present = stats_last != False

                        seed = self.initial_seed
                        plantSeeds(seed)
                        for replication in range(self.replications):
                            sprint("======================")
                            sprint("*** Running simulation with the following parameters:")
                            sprint("Experiment         :", self.description)
                            sprint("Scheduling policy  :", schedpol)
                            sprint("Execution mode     :", exec_mode)
                            sprint("Lambda             =", str(lambda_val))
                            sprint("pc                 =", str(pc_val))
                            sprint("Replication no.    :", str(replication + 1), "of", self.replications)
                            sim_id = SimulationId(self.description, schedpol, exec_mode, self.scalability,
                                                  seed, replication + 1, self.start_time, self.stop_time,
                                                  self.infsim_B, self.infsim_K, self.edge_servers_init,
                                                  self.edge_servers_max,
                                                  lambda_val, pc_val
                                                  )
                            if not override_results and are_all_replications_present:

                                if need_return:
                                    stats = self.load(sim_id)
                                    self.results[sim_id] = stats
                                    sprint(
                                        "*** Results already found, loading statistics from file and skipping the simulation.")

                                else:
                                    sprint("*** Results already found and return not needed, skipping the simulation.")


                            else:
                                if replication > 0: seed = getSeed()
                                sprint("seed               =", str(seed))
                                stats = None
                                if schedpol is SchedulingPolicy.PS:
                                    from sim.ps import run_sim_core_PS
                                    stats = (
                                        run_sim_core_PS(
                                            seed,
                                            self.start_time,
                                            self.edge_servers_init,
                                            self.edge_servers_max,
                                            exec_mode,
                                            pc_val,
                                            lambda_val,
                                            self.infsim_B,
                                            self.infsim_K,
                                            self.stop_time,
                                            self.scalability
                                        )
                                    )
                                elif schedpol is SchedulingPolicy.FIFO:
                                    from sim.fifo import run_sim_core_FIFO
                                    stats = (
                                        run_sim_core_FIFO(
                                            seed,
                                            self.start_time,
                                            self.edge_servers_init,
                                            self.edge_servers_max,
                                            exec_mode,
                                            pc_val,
                                            lambda_val,
                                            self.infsim_B,
                                            self.infsim_K,
                                            self.stop_time,
                                            self.scalability
                                        )
                                    )
                                else:
                                    raise ValueError("Unknown scheduling policy for", schedpol)
                                replications_data_for_output[replication + 1] = stats
                                self.results[sim_id] = stats.dict_filtered()
                                if persist and replications_data_for_output != {}:
                                    DIR = "OUTPUT/" + self.description
                                    Path(DIR).mkdir(parents=True, exist_ok=True)
                                    path = DIR + "/lambda" + str(sim_id.lambda_value) + "-pc" + str(sim_id.pc) + ".json"
                                    with open(path, 'w+') as json_file:
                                        json.dump([v.dict_filtered() for _, v in replications_data_for_output.items()],
                                                  json_file, indent=4, default=json_encoder_default)
                                    json_file.close()
        return self.results

    def load(self, sim_id: SimulationId):
        checked = False
        DIR = "OUTPUT/" + self.description
        path = DIR + "/lambda" + str(sim_id.lambda_value) + "-pc" + str(sim_id.pc) + ".json"
        if Path.exists(Path(path)):
            with open(path) as f:
                d = json.load(f)
                if len(d) < sim_id.replication_no: return checked
                checked = d[sim_id.replication_no - 1]
        return checked
