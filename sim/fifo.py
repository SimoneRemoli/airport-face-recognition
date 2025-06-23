import sim
from DES_Python.rngs import selectStream, random
from DES_Python.rvgs import Exponential, TruncatedNormal
from globs import VERBOSE, CLOUD_FICT
from misc.rngstreams import RngStreams
from misc.timeutils import seconds_to_hhmmss
from model.categories import RequestCategory
from model.events import generate_event_datastruct, NextEvent, FindOne, NodeType
from sim.autoscaler import AutoScaler
from sim.executor import ExecutionMode
from sim.stats_types import StatsType
from sim.utils import GetArrival, AccumSum, update_lambda
from simio.simprint import sprint, simprint_inst, sprint_verbose
from simio.statistics import Statistics, INIT_INV, Time, SAMPLING_TIME_FIN, Sampler


def GetService(type: StatsType, exec_mode: ExecutionMode):
    tolerance_intv = 0.05  # s
    stddev = 0.025  # 95%
    avg = INIT_INV

    if type == StatsType.EDGE_E:
        selectStream(RngStreams.SERVICE_EDGE_E.value[0])
        avg = 0.5
    elif type == StatsType.EDGE_C:
        selectStream(RngStreams.SERVICE_EDGE_C.value[0])
        avg = 0.1
    elif type == StatsType.CLOUD:
        selectStream(RngStreams.SERVICE_CLOUD.value[0])
        avg = 0.8
    else:
        raise RuntimeError("Node type not known for" + type.__str__())

    if avg == INIT_INV:
        raise ValueError("Node type not known for" + type.__str__())

    if exec_mode in [ExecutionMode.MODEL, ExecutionMode.VERIFY_FEEDBACK_CUT, ExecutionMode.INFINITE_SIMULATION_EXP]:
        return Exponential(avg)
    return TruncatedNormal(avg, stddev, avg - tolerance_intv, avg + tolerance_intv)


tprint_guard = INIT_INV


def run_sim_core_FIFO(seed: int, start_time: float, edge_servers_init: int, edge_servers_max: int,
                      execution_mode: ExecutionMode, pc: float = 0.4, lambda_base: float = 1.5, infsim_B: int = None,
                      infsim_K: int = None, STOP: float = None, scalability: bool = False) -> Statistics:
    # some sanity checks before starting the simulation
    if start_time is None or edge_servers_init is None or edge_servers_max is None:
        raise ValueError("some simulation parameter is null!")
    infinite_Ecompletions = 0
    if execution_mode is ExecutionMode.INFINITE_SIMULATION:
        infsim_N = infsim_K * infsim_B
        STOP = infsim_N * SAMPLING_TIME_FIN  # just to be printed, not considered as halt condition
        sprint(
            f"Simulating for {infsim_N} completions, that is circa {infsim_N / lambda_base} s ({seconds_to_hhmmss(infsim_N / lambda_base)})")
        if infsim_N is None:
            raise ValueError("invalid infsim_N provided")
        if scalability:
            raise ValueError("scalability with INFHOR simulation!")
    else:
        if STOP is None:
            raise ValueError("stop_time is none!")
        if STOP <= start_time:
            raise ValueError("invalid start/stop simulation times")

    sim.utils.arrivalTemp = start_time

    t = Time()

    global CLOUD_FICT
    if execution_mode in [ExecutionMode.MODEL, ExecutionMode.VERIFY_FEEDBACK_CUT]:
        edge_servers_max = edge_servers_init

    current_edge_servers = edge_servers_init

    events = generate_event_datastruct(edge_servers_max)  # , CLOUD_SERVERS_MAX)

    e = None
    s = None
    stats = Statistics()
    stats.reset(start_time, edge_servers_max)
    stats.seed = seed
    sampler = Sampler(execution_mode, start_time, edge_servers_max)

    accum_sums = [AccumSum() for i in range(0, edge_servers_max + CLOUD_FICT + 1)]

    lambda_current = INIT_INV
    if scalability:
        lambda_current = update_lambda(lambda_base, t.current)
        autoscaler = AutoScaler(start_time, edge_servers_init, edge_servers_max, pc)
    else:
        lambda_current = lambda_base
    events[0].t = GetArrival(lambda_current)
    events[0].x = 1

    for s in range(1, edge_servers_max + CLOUD_FICT + 1):
        events[s].t = start_time
        events[s].x = 0

        accum_sums[s].service = 0.0
        accum_sums[s].service_catE = 0.0
        accum_sums[s].service_catC = 0.0

        accum_sums[s].served = 0
        accum_sums[s].served_catE = 0
        accum_sums[s].served_catC = 0

    timeelapsed_print_check = 0

    sprint("Starting simulation...")

    if VERBOSE:
        sprint("The VERBOSE flag is set to True. Please set it to False if you want some less detailed output.")
    else:
        sprint("The VERBOSE flag is set to False. Please set it to True if you want some more detailed output.")
    simprint_inst.set_sim_prints(start_time, STOP)
    simprint_inst.print_header()

    def should_simulation_continue():
        if execution_mode is ExecutionMode.INFINITE_SIMULATION:
            continue_condition = (sampler.samples_no != infsim_K)
            if sampler.samples_no > infsim_K:
                raise RuntimeError("More samples than needed!", infsim_K)
        else:
            continue_condition = ((events[0].x != 0) or (stats.stats_edge.number + stats.stats_cloud.number != 0))
        return continue_condition

    while should_simulation_continue():
        # progress indicator - just a fancy CLI printout
        if execution_mode is ExecutionMode.INFINITE_SIMULATION:
            if t.current == start_time or (sampler.samples_no) - timeelapsed_print_check >= int(infsim_K / 10):
                sprint(
                    f"{int(100 * (sampler.samples_no / infsim_K))}% elapsed ({sampler.samples_no}/{infsim_K} observations)")
                timeelapsed_print_check = sampler.samples_no

        else:
            if t.current == start_time or 100 * (t.current / (STOP - start_time)) - timeelapsed_print_check >= 10:
                sprint(
                    f"{int(100 * ((t.current - start_time) / (STOP - start_time)))}% elapsed ")
                timeelapsed_print_check = int(100 * (t.current / (STOP - start_time)))

        # pick the NE and update the next event clock
        e = NextEvent(events, edge_servers_max)
        t.next = events[e].t

        # sanity check
        if t.next <= t.current:
            raise RuntimeError(
                f"Error in the next event time ({t.next}), cannot be previous than t.current ({t.current})")

        stats.update_integrals(t)

        # progress the clock
        t.current = t.next

        if scalability:
            lambda_current = update_lambda(lambda_base, t.current)

        simprint_inst.tprint_clock = t.current
        sprint_verbose("--------------")

        if e < 0 or e >= len(events):
            raise IndexError("Invalid NE index for", e)
        if 1 + current_edge_servers < e < len(events) - CLOUD_FICT:
            raise RuntimeError(
                f"next event ({e}) into a forbidden region (i.e., an inactive, non-scaled, EDGE server). "
                f"Limit values are ({1 + current_edge_servers}, {len(events) - CLOUD_FICT})")

        # --------------------------------------------------------------------------
        # process a (system) ARRIVAL
        if e == 0:
            sprint_verbose("EDGE (system) ARRIVAL")

            if scalability:
                current_edge_servers = autoscaler.autoscale(lambda_current, current_edge_servers)

            # update the counts
            stats.sys_arrivals_count += 1
            stats.stats_edge.number += 1
            stats.stats_edge_E.number += 1
            stats.sys_number_catE += 1

            # by default, every job entering the sistem è di categoria E (sezione 6.1.2)
            stats.edge_jobs_queuetrack.append(RequestCategory.E)

            # update next arrival time, and check if it is beyond the stop time
            events[0].t = GetArrival(lambda_current)
            if events[0].t > STOP and execution_mode is not ExecutionMode.INFINITE_SIMULATION:
                # prepare the simulation halting
                sprint("STOP time reached! Halting the arrivals process...")
                events[0].x = 0
                t.last = t.current

            # se ci sono server liberi (nel nodo <= num. serventi)
            if stats.stats_edge.number <= current_edge_servers:
                if not stats.edge_jobs_queuetrack[0] == RequestCategory.E:
                    raise RuntimeError("Processing a system arrival (catE), but the first job in queue is not catE!")
                service = GetService(StatsType.EDGE_E, execution_mode)
                s = FindOne(events, NodeType.EDGE, current_edge_servers, edge_servers_max)
                sprint_verbose("> schedulo completamento EDGE per " + str(t.current + service) + " presso " + str(s))
                accum_sums[s].service += service
                accum_sums[s].served += 1
                accum_sums[s].served_catE += 1
                events[s].t = t.current + service
                events[s].x = 1
                events[s].category_served = RequestCategory.E
                stats.edge_jobs_queuetrack.pop(0)
            else:
                sprint_verbose("> all the EDGE servers are busy, keeping in the queue")


        # --------------------------------------------------------------------------
        # process an EDGE COMPLETION
        elif 1 <= e <= edge_servers_max:

            # anzitutto gestisco la richiesta (processo il completamento)
            sprint_verbose("EDGE COMPLETION")

            # update counts
            stats.stats_edge.index += 1
            stats.stats_edge.number -= 1

            category = events[e].category_served
            sprint_verbose("serving a cat. " + str(category) + " job")

            if category is RequestCategory.E:
                stats.stats_edge_E.index += 1
                stats.stats_edge_E.number -= 1

            elif category is RequestCategory.C:
                stats.stats_edge_C.number -= 1
                stats.stats_edge_C.index += 1

            else:
                raise ValueError("Job category invalid in EDGE completion for", category)

            if execution_mode is ExecutionMode.INFINITE_SIMULATION:
                if infinite_Ecompletions == infsim_B:

                    stats, accum_sums = sampler.sample(stats, t.current, current_edge_servers,
                                                       edge_servers_max,
                                                       accum_sums, lambda_current, None)
                    start_time = stats.reset_infinite(t.current)
                    infinite_Ecompletions = 0
                else:
                    infinite_Ecompletions += 1

            # only cat-E can/cannot be forwarded to cloud, based on probability
            if category is RequestCategory.E:
                selectStream(RngStreams.PC.value)
                if random() <= pc:
                    sprint_verbose("> sending to CLOUD node")

                    # update the counts
                    stats.stats_cloud.number += 1
                    stats.sys_number_catC += 1
                    stats.sys_number_catE -= 1  # cambio di categoria

                    if stats.stats_cloud.number <= CLOUD_FICT:
                        service = GetService(StatsType.CLOUD, execution_mode)
                        s = FindOne(events, NodeType.CLOUD, current_edge_servers, edge_servers_max)
                        sprint_verbose(
                            "> schedulo completamento CLOUD per " + str(t.current + service) + " presso " + str(s))
                        accum_sums[s].service += service
                        accum_sums[s].served += 1
                        accum_sums[s].served_catC += 1
                        events[s].t = t.current + service
                        events[s].x = 1
                        events[s].category_served = RequestCategory.C
                    else:
                        raise RuntimeError("Cannot find a fictitious CLOUD free server - please increase.")

                else:
                    # ... otherwise, just put it outside the sistem
                    sprint_verbose("> esce dal sistema come cat. E")
                    stats.sys_index_catE += 1
                    stats.sys_number_catE -= 1

                    if execution_mode in [ExecutionMode.INFINITE_SIMULATION, ExecutionMode.INFINITE_SIMULATION_BATCH]:
                        if infinite_Ecompletions == infsim_B:

                            stats, accum_sums = sampler.sample(stats, t.current, current_edge_servers,
                                                               edge_servers_max,
                                                               accum_sums, lambda_current, None)
                            if execution_mode is ExecutionMode.INFINITE_SIMULATION_BATCH: start_time = stats.reset_infinite(
                                t.current)
                            infinite_Ecompletions = 0
                        else:
                            infinite_Ecompletions += 1


            elif category is RequestCategory.C:
                if execution_mode is ExecutionMode.VERIFY_FEEDBACK_CUT:
                    raise RuntimeError("Verify mode - feedback is cut, should not have catC jobs into EDGE node!")
                # put also this outside the system, but count it as cat_C
                sprint_verbose("> esce dal sistema come cat. C")
                stats.sys_index_catC += 1
                stats.sys_number_catC -= 1
                if execution_mode is ExecutionMode.INFINITE_SIMULATION:
                    if infinite_Ecompletions == infsim_B:

                        stats, accum_sums = sampler.sample(stats, t.current, current_edge_servers, edge_servers_max,
                                                           accum_sums, lambda_current, None)

                        stats.reset_infinite(t.current)
                        infinite_Ecompletions = 0
                    else:
                        infinite_Ecompletions += 1
            else:
                raise ValueError("Invalid category for", category)

            s = e
            if stats.stats_edge.number >= current_edge_servers:
                sprint_verbose("> Progress the EDGE queue")

                updated_category = stats.edge_jobs_queuetrack[0]
                service = GetService(updated_category.toEdgeStatsType(), execution_mode)

                # update areas and counts
                accum_sums[s].service += service
                accum_sums[s].served += 1

                if updated_category is RequestCategory.E:
                    accum_sums[s].service_catE += service
                    accum_sums[s].served_catE += 1

                elif updated_category is RequestCategory.C:
                    accum_sums[s].service_catC += service
                    accum_sums[s].served_catC += 1

                else:
                    raise ValueError("Job updated_category invalid in EDGE queue advancing for", updated_category)

                sprint_verbose("> schedulo completamento EDGE per " + str(t.current + service) + " presso " + str(s))

                events[s].t = t.current + service
                events[s].category_served = updated_category
                stats.edge_jobs_queuetrack.pop(0)
            else:
                # the node (and the queue) is empty, free the server
                sprint_verbose("> No need to progress the (empty) EDGE queue")
                events[s].x = 0



        # --------------------------------------------------------------------------
        # process a CLOUD completion
        elif 1 + edge_servers_max <= e <= edge_servers_max + CLOUD_FICT:
            sprint_verbose("CLOUD COMPL")
            stats.stats_cloud.index += 1
            stats.stats_cloud.number -= 1
            if events[e].category_served is not RequestCategory.C:
                raise RuntimeError("Invalid category processed at cloud for", events[e].category_served,
                                   "for server no.", e)

            events[e].x = 0
            if execution_mode is ExecutionMode.VERIFY_FEEDBACK_CUT:
                sprint_verbose("> esce dal sistema come cat. C, senza feedback (verifica)")
                events[e].x = 0

                # in this case, update also the global (sys) counts
                stats.sys_number_catC -= 1
                stats.sys_index_catC += 1
            else:
                sprint_verbose("> lo mando a EDGE")
                stats.stats_edge.number += 1
                stats.stats_edge_C.number += 1

                stats.edge_jobs_queuetrack.append(RequestCategory.C)

                if stats.stats_edge.number <= current_edge_servers:
                    if not stats.edge_jobs_queuetrack[0] == RequestCategory.C:
                        raise RuntimeError(
                            "Processing a cloud feedback (catC), but the first job in queue is not catC!")
                    service = GetService(StatsType.EDGE_C, execution_mode)
                    sprint_verbose("> schedulo completamento per " + str(t.current + service))
                    s = FindOne(events, NodeType.EDGE, current_edge_servers, edge_servers_max)
                    accum_sums[s].service += service
                    accum_sums[s].served += 1
                    accum_sums[s].served_catC += 1
                    events[s].t = t.current + service
                    events[s].x = 1
                    events[s].category_served = RequestCategory.C
                    stats.edge_jobs_queuetrack.pop(0)
                else:
                    sprint_verbose("> all the EDGE servers are busy, keeping in the queue")

        else:
            raise ValueError("Invalid event for id =", e)

        stats.sanity_checks()
        sprint_verbose("FINE CICLO EVENTO")

        if execution_mode is not ExecutionMode.INFINITE_SIMULATION and (
                t.current == start_time or t.current - sampler.timeelapsed_sampling_check >= SAMPLING_TIME_FIN):
            stats, accum_sums = sampler.sample(stats, t.current, current_edge_servers, edge_servers_max, accum_sums,
                                               lambda_current, None)

    simprint_inst.terminate_sim()

    # ASSERTIONS
    if execution_mode is not ExecutionMode.INFINITE_SIMULATION:
        # global balance
        sprint_verbose(stats.sys_arrivals_count, stats.sys_index_catE, stats.sys_index_catC)
        assert (stats.sys_arrivals_count == stats.sys_index_catE + stats.sys_index_catC)

        # sistema vuoto
        assert (stats.sys_number_catE == 0)
        for stat in [stats.stats_edge, stats.stats_edge_E, stats.stats_edge_C, stats.stats_cloud]:
            assert (stat.number == 0)

    if execution_mode is not ExecutionMode.INFINITE_SIMULATION: stats.finalize(sampler, edge_servers_max, accum_sums,
                                                                               start_time, t.current, execution_mode)
    return stats
