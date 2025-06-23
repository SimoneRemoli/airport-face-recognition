from enum import Enum
from typing import List

from model.categories import RequestCategory
from globs import CLOUD_FICT

ARRIVALS_EVENT_INDEX = 0


# modeled as per Leemis-Park, ch. 5.2
class Event:
    def __init__(self):
        self.t = None  # next scheduled occurrence
        self.x = None  # "activity status" of the event (0/1)
        self.category_served = RequestCategory.NOT_DEFINED  # event (request) category

    # just a sanity check (exception raised elsewhere)
    def check_validity(self) -> bool:
        return self.t >= 0 and self.x in [0, 1]


# generate event list, modeled as per Leemis-Park, ch. 5.2
# cardinality:
#   1   +               (system arrivals)
#   N_e +               (Edge servers)
#   N_c                 (Cloud servers)
def generate_event_datastruct(cardinality_edge: int) -> List:
    # sanity check
    if cardinality_edge is None:  # or cardinality_cloud is None:
        raise ValueError("Edge or Cloud cardinality is None!")

    if cardinality_edge < 1:  # or cardinality_cloud<1:
        raise ValueError("No Edge/Cloud nodes specified!")
    cardinality_total = 1 + cardinality_edge + CLOUD_FICT

    list = [Event() for i in range(cardinality_total)]

    # initialize values
    # except for the item of index 0 (system arrivals),
    # that we will initialize at the first arrival
    for item in range(1, cardinality_total):
        list[item].t = -99999
        list[item].x = 0
    return list


def is_arrival_process_active(event_datastruct: List) -> bool:
    return event_datastruct[ARRIVALS_EVENT_INDEX].x != 0


def halt_arrival_process(event_datastuct: List):
    event_datastuct[ARRIVALS_EVENT_INDEX].x = 0


def NextEvent(events: List, edge_servers_max: int) -> int:
    i = 0
    while events[i].x == 0:
        i += 1
    e = i
    while i < edge_servers_max + CLOUD_FICT:
        i += 1
        if (events[i].x == 1) and (events[i].t < events[e].t):
            e = i
    return e


class NodeType(Enum):
    EDGE = 0,
    CLOUD = 1

    def __repr__(self):
        return self.name


def FindOne_modA(events, node_type: NodeType, edge_servers_max):
    # sanity check:
    if events is None or node_type is None:
        raise ValueError("events or node_type or current_edge_servers is NULL!")

    if node_type not in [NodeType.EDGE, NodeType.CLOUD]: raise ValueError("Unknown node type for", node_type)

    current_edge_servers = 1

    if node_type is NodeType.EDGE:
        s = 1
    elif node_type is NodeType.CLOUD:
        servers_no = CLOUD_FICT
        i = 1 + edge_servers_max

        # -----------------------------------------------------
        # * return the index of the available server idle longest
        # * -----------------------------------------------------
        # */

        while (events[i].x == 1):  # find the index of the first available */
            i += 1  # (idle) server                         */
        # EndWhile
        s = i
        while (i < servers_no):  # now, check the others to find which   */
            i += 1  # has been idle longest                 */
            if ((events[i].x == 0) and (events[i].t < events[s].t)):
                s = i
        # EndWhile
    else:
        raise RuntimeError("invalid Node_type")
    # check correctness
    if s < 0 or s > len(events): raise IndexError("out of range! for node_type", node_type, ", s =", s)

    # MEMO server 0 is the arrival process, 1 is OK for edge!
    if node_type is NodeType.EDGE and not (1 <= s <= current_edge_servers):
        raise RuntimeError("assigned server", s,
                           f"for nodetype EDGE, which should instead be in [{1},{current_edge_servers}]")

    if 1 + current_edge_servers < s < len(events) - CLOUD_FICT:
        raise RuntimeError("assigned server", s,
                           " into a forbidden region (i.e., an inactive, non-scaled, EDGE server). Nodetype =",
                           node_type, "."
                                      f"Should instead be OUTSIDE [{1 + current_edge_servers}, {len(events) - CLOUD_FICT}]")

    if node_type is NodeType.CLOUD and not (1 + edge_servers_max <= s <= 1 + edge_servers_max + CLOUD_FICT):
        raise RuntimeError("assigned server", s,
                           f"for nodetype CLOUD, which should instead be in [{1 + edge_servers_max},{1 + edge_servers_max + CLOUD_FICT}]")
    return (s)


def FindOne(events, node_type: NodeType, current_edge_servers: int, edge_servers_max: int):
    # sanity check:
    if events is None or node_type is None or current_edge_servers is None:
        raise ValueError("events or node_type or current_edge_servers is NULL!")

    if node_type not in [NodeType.EDGE, NodeType.CLOUD]: raise ValueError("Unknown node type for", node_type)

    if node_type is NodeType.EDGE:
        servers_no = current_edge_servers
        i = 1
    elif node_type is NodeType.CLOUD:
        servers_no = CLOUD_FICT
        i = 1 + edge_servers_max
    else:
        raise RuntimeError("invalid Node_type")

    # -----------------------------------------------------
    # * return the index of the available server idle longest
    # * -----------------------------------------------------
    # */

    while (events[i].x == 1):  # find the index of the first available */
        i += 1  # (idle) server                         */
    # EndWhile
    s = i
    while (i < servers_no):  # now, check the others to find which   */
        i += 1  # has been idle longest                 */
        if ((events[i].x == 0) and (events[i].t < events[s].t)):
            s = i
    # EndWhile

    # check correctness
    if s < 0 or s > len(events): raise IndexError("out of range! for node_type", node_type, ", s =", s)

    # MEMO server 0 is the arrival process, 1 is OK for edge!
    if node_type is NodeType.EDGE and not (1 <= s <= current_edge_servers):
        raise RuntimeError("assigned server", s,
                           f"for nodetype EDGE, which should instead be in [{1},{current_edge_servers}]")

    if 1 + current_edge_servers < s < len(events) - CLOUD_FICT:
        raise RuntimeError("assigned server", s,
                           " into a forbidden region (i.e., an inactive, non-scaled, EDGE server). Nodetype =",
                           node_type, "."
                                      f"Should instead be OUTSIDE [{1 + current_edge_servers}, {len(events) - CLOUD_FICT}]")

    if node_type is NodeType.CLOUD and not (1 + edge_servers_max <= s <= 1 + edge_servers_max + CLOUD_FICT):
        raise RuntimeError("assigned server", s,
                           f"for nodetype CLOUD, which should instead be in [{1 + edge_servers_max},{1 + edge_servers_max + CLOUD_FICT}]")
    return (s)
