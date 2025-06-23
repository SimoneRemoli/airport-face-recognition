from enum import Enum

def json_decoder_object_hook(d):
    if "__class__" in d:
        class_name = d.pop("__class__")
        if class_name == "NodeStats":
            from simio.statistics import NodeStats
            return NodeStats(**d)
        elif class_name == "Track":
            from simio.statistics import Track
            return Track(**d)
        elif class_name == "SimulationId":
            from simio import Statistics
            return Statistics(**d)

    if "__enum__" in d:
        enum_name = d["__enum__"]
        member_name = d["name"]

        from sim.executor import SchedulingPolicy
        enum_classes = {
            "SchedulingPolicy": SchedulingPolicy,
        }

        if enum_name in enum_classes:
            enum_class = enum_classes[enum_name]
            try:
                return getattr(enum_class, member_name)
            except AttributeError:
                pass

    return d


def json_encoder_default(obj):
    if isinstance(obj, Enum):
        return obj.name

    if isinstance(obj, NodeStats): return obj.__dict__
    if isinstance(obj, Track): return obj.__dict__
    if isinstance(obj, Statistics): return obj.__dict__

    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


