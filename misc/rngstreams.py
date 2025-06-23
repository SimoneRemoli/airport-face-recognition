from enum import Enum


class RngStreams(Enum):
    SEEDS = 0,
    ARRIVALS = 1,
    SERVICE_EDGE_E = 2,
    SERVICE_EDGE_C = 3,
    SERVICE_CLOUD = 4,
    PC = 5
