from DES_Python.rngs import selectStream
from DES_Python.rvgs import Exponential

from misc.rngstreams import RngStreams
from misc.timeutils import hours_to_secs

arrivalTemp = -99999


def GetArrival(current_lambda: float):
    global arrivalTemp
    selectStream(RngStreams.ARRIVALS.value[0])
    arrivalTemp += Exponential(1 / current_lambda)
    return arrivalTemp


class AccumSum:
    service = 0
    service_catE = 0
    service_catC = 0

    served = 0
    served_catE = 0
    served_catC = 0


def update_lambda(lambda_base: float, time: int):
    time = time % hours_to_secs(24)

    if hours_to_secs(0) <= time < hours_to_secs(6): return 0.28 * lambda_base
    if hours_to_secs(6) <= time < hours_to_secs(12): return 1.6 * lambda_base
    if hours_to_secs(12) <= time < hours_to_secs(18): return 0.8 * lambda_base
    if hours_to_secs(18) <= time < hours_to_secs(22): return 1.68 * lambda_base
    if hours_to_secs(22) <= time < hours_to_secs(24): return 0.6 * lambda_base

    raise ValueError(f"in update_lambda ({lambda_base}, {time})")
