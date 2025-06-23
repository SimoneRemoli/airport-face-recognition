import numpy as np

from simio.simprint import sprint

RHO_THRESHOLD_BASE = 0.7559
AUTOSCALER_THRESHOLDS = []  # j/s


class AutoScaler:

    def __init__(self, start_time: float, init_edge_servers: int, max_edge_servers: int, pc: float):
        super().__init__()
        global AUTOSCALER_THRESHOLDS
        S = (1 / (1 + pc)) * 0.5 + (pc / (1 + pc)) * 0.1  # 0.38571
        AUTOSCALER_THRESHOLDS = [(RHO_THRESHOLD_BASE * m / (S * (1 + pc))) for m in range(max_edge_servers + 1)]
        sprint("Lambda thresholds:", AUTOSCALER_THRESHOLDS)
        self.last_current = start_time
        self.interarrivals_for_guard = []
        self.max_edge_servers = max_edge_servers
        sprint("*** Autoscaler ON, starting with", init_edge_servers, "servers, up to", max_edge_servers)

    def get_thresholds(self):
        return AUTOSCALER_THRESHOLDS

    def reset_lambda_samplings(self) -> float:
        avg = 1 / np.average([i[1] for i in self.interarrivals_for_guard])
        return avg

    def autoscale(self, current_lambda: float, current_edge_servers: int) -> int:
        scaled_servers_no = None
        for i in range(self.max_edge_servers):
            if AUTOSCALER_THRESHOLDS[i] < current_lambda < AUTOSCALER_THRESHOLDS[i + 1]:
                scaled_servers_no = i + 1
                break

        if scaled_servers_no > current_edge_servers:
            sprint("*** Autoscaler: scaling UP to", scaled_servers_no, "servers")
        if scaled_servers_no < current_edge_servers:
            sprint("*** Autoscaler: scaling DOWN to", scaled_servers_no, "servers")

        if scaled_servers_no is None:
            raise RuntimeError("Cannot find server lambda range!")
        return scaled_servers_no
