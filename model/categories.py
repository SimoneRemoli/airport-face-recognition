from enum import Enum

from sim.stats_types import StatsType


class RequestCategory(Enum):
    NOT_DEFINED = 0,
    E = 1
    C = 2

    def __repr__(self):
        return self.name

    def toEdgeStatsType(self) -> StatsType:
        if self is RequestCategory.E: return StatsType.EDGE_E
        if self is RequestCategory.C: return StatsType.EDGE_C
        raise ValueError("Invalid conversion for", self)
