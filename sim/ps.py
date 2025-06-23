import sim.utils
from DES_Python.rngs import getSeed, selectStream, random
from DES_Python.rvgs import TruncatedNormal
from globs import VERBOSE, CLOUD_FICT
from misc.rngstreams import RngStreams
from misc.timeutils import seconds_to_hhmmss
from model.categories import RequestCategory
from model.events import generate_event_datastruct, NextEvent, NodeType, FindOne_modA
from sim.autoscaler import AutoScaler
from sim.executor import ExecutionMode
from sim.stats_types import StatsType
from sim.utils import GetArrival, AccumSum, update_lambda
from simio.simprint import sprint, simprint_inst, sprint_verbose, sprint_warning
from simio.statistics import Statistics, INIT_INV, Time, SAMPLING_TIME_FIN, Sampler

PS_TOLERANCE = 1e-9


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

    return TruncatedNormal(avg, stddev, avg - tolerance_intv, avg + tolerance_intv)


class AccumSum:
    service = 0
    service_catE = 0
    service_catC = 0

    served = 0
    served_catE = 0
    served_catC = 0


tprint_guard = INIT_INV


def run_sim_core_PS(seed: int, start_time: float, edge_servers_init: int, edge_servers_max: int,
                    execution_mode: ExecutionMode, pc: float = 0.4, lambda_base: float = 1.5, infsim_B: int = None,
                    infsim_K: int = None, STOP: float = None, scalability: bool = False) -> Statistics:
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
    t.last_edgequeue_modify = start_time

    global CLOUD_FICT
    current_edge_servers = edge_servers_init

    events = generate_event_datastruct(edge_servers_max)

    e = None  # next event index                   */
    s = None  # server index                       */
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
        autoscaler = None

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
            continue_condition = (sampler.samples_no != infsim_K)  # infsim_N
            if sampler.samples_no > infsim_K:
                raise RuntimeError("More samples than needed!", infsim_K)
        else:
            continue_condition = ((events[0].x != 0) or (stats.stats_edge.number + stats.stats_cloud.number != 0))
        return continue_condition

    while should_simulation_continue():
        # progress indicator - just a fancy CLI printout
        if execution_mode is ExecutionMode.INFINITE_SIMULATION:
            if (sampler.samples_no) - timeelapsed_print_check >= int(infsim_K / 10):
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
        if t.next == t.current: sprint_warning("More completion at once! It is normal if lambda is high")
        if t.next < t.current:
            raise RuntimeError(
                f"Error in the next event time ({t.next}), cannot be previous than t.current ({t.current})")

        stats.update_integrals(t)

        # progress the clock
        t.current = t.next

        if scalability:
            lambda_current = update_lambda(lambda_base, t.current)

        simprint_inst.tprint_clock = t.current
        sprint_verbose("--------------")

        delta_t = t.current - t.last_edgequeue_modify
        t.last_edgequeue_modify = t.current
        num_servers_actually_used = min(current_edge_servers, stats.stats_edge.number)
        for s in range(1, num_servers_actually_used + 1):
            if len(stats.edge_jobs_queuetrack) > 0:
                accum_sums[s].service += delta_t

        for i in stats.edge_jobs_queuetrack:
            i[1] -= min(current_edge_servers, len(stats.edge_jobs_queuetrack)) * delta_t / len(
                stats.edge_jobs_queuetrack)
            i[2] += min(current_edge_servers, len(stats.edge_jobs_queuetrack)) * delta_t / len(
                stats.edge_jobs_queuetrack)
            if i[1] < - PS_TOLERANCE: raise RuntimeError("Missed a completion! Reached remtime=", i[1])

        # some sanity checks for the next event index
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
                updated_current_edge_servers = autoscaler.autoscale(lambda_current, current_edge_servers)
                stats.stats_edge.current_servers_no = current_edge_servers
                current_edge_servers = updated_current_edge_servers

            # update the counts
            stats.sys_arrivals_count += 1
            stats.stats_edge.number += 1
            stats.stats_edge_E.number += 1
            stats.sys_number_catE += 1

            # update next arrival time, and check if it is beyond the stop time
            events[0].t = GetArrival(lambda_current)
            if events[0].t > STOP and execution_mode is not ExecutionMode.INFINITE_SIMULATION:
                # prepare the simulation halting
                sprint("STOP time reached! Halting the arrivals process...")
                events[0].x = 0
                t.last = t.current

            service = GetService(StatsType.EDGE_E, execution_mode)

            stats.edge_jobs_queuetrack.append([RequestCategory.E, service, 0])

            completions = [i[1] for i in stats.edge_jobs_queuetrack]

            if len(stats.edge_jobs_queuetrack) < 0: raise RuntimeError("Empty queuetrack!")
            if len(stats.edge_jobs_queuetrack) > 0:
                s = FindOne_modA(events, NodeType.EDGE, edge_servers_max)
                if s != 1: raise IndexError("PS and edgenode!=1")
                sprint_verbose("> schedulo completamento EDGE per il minimo in coda, a " + str(
                    t.current + min(completions) * len(stats.edge_jobs_queuetrack)) + ", presso " + str(s))
                events[s].t = t.current + min(completions) * (len(stats.edge_jobs_queuetrack) / (
                    min(len(stats.edge_jobs_queuetrack), current_edge_servers)))
                events[s].x = 1
                events[s].category_served = RequestCategory.NOT_DEFINED
            else:
                sprint_verbose("nodo edge vuoto")
                events[e].x = 0

        # --------------------------------------------------------------------------
        # process an EDGE COMPLETION
        elif 1 <= e <= edge_servers_max:

            sprint_verbose("EDGE COMPLETION")

            # update counts
            stats.stats_edge.index += 1
            accum_sums[e].served += 1
            stats.stats_edge.number -= 1

            found = False
            tolerance = PS_TOLERANCE
            while not found:
                jobs_to_depart = []
                for i in stats.edge_jobs_queuetrack:
                    if abs(i[1]) <= tolerance: jobs_to_depart.append(i)
                if len(jobs_to_depart) == 0:
                    tolerance *= 10
                    sprint_warning("Increasing tolerance to" + tolerance)
                    if tolerance >= 1e-3:
                        raise RuntimeError("cannot find the job to depart!")
                else:
                    found = True

            for j in jobs_to_depart:
                category = j[0]
                stats.edge_jobs_queuetrack.remove(j)

                completions = [i[1] for i in stats.edge_jobs_queuetrack]

                if len(stats.edge_jobs_queuetrack) < 0: raise RuntimeError("empty queuetrack")

                if category is RequestCategory.E:
                    stats.stats_edge_E.index += 1
                    stats.stats_edge_E.number -= 1

                elif category is RequestCategory.C:
                    stats.stats_edge_C.number -= 1
                    stats.stats_edge_C.index += 1

                else:
                    raise ValueError("Job category invalid in EDGE completion for", category)
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
                            s = FindOne_modA(events, NodeType.CLOUD, edge_servers_max)
                            sprint_verbose(
                                "> schedulo completamento CLOUD per " + str(t.current + service) + " presso " + str(s))
                            accum_sums[s].service += service
                            accum_sums[s].served += 1
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


                elif category is RequestCategory.C:
                    if execution_mode is ExecutionMode.VERIFY_FEEDBACK_CUT:
                        raise RuntimeError("Verify mode - feedback is cut, should not have catC jobs into EDGE node!")
                    # put also this outside the system, but count it as cat_C
                    sprint_verbose("> esce dal sistema come cat. C")
                    stats.sys_index_catC += 1
                    stats.sys_number_catC -= 1
                else:
                    raise ValueError("Invalid category for", category)

            # now adjust the queue
            s = e
            if len(stats.edge_jobs_queuetrack) > 0:
                s = FindOne_modA(events, NodeType.EDGE, edge_servers_max)
                if s != 1: raise IndexError("ps and s!=1")
                sprint_verbose("MIN_COMPLETIONS=" + str(min(completions)) + "; LEN=" + str(
                    len(stats.edge_jobs_queuetrack)) + "> schedulo completamento EDGE per il minimo in coda, a " + str(
                    t.current + min(completions) * len(stats.edge_jobs_queuetrack)) + ", presso " + str(s))
                accum_sums[s].served_catE += 1
                events[s].t = t.current + min(completions) * (len(stats.edge_jobs_queuetrack) / (
                    min(len(stats.edge_jobs_queuetrack), current_edge_servers)))
                events[s].x = 1
                events[s].category_served = RequestCategory.NOT_DEFINED
            else:
                sprint_verbose("nodo edge vuoto")
                events[e].x = 0

            if execution_mode in [ExecutionMode.INFINITE_SIMULATION, ExecutionMode.INFINITE_SIMULATION_BATCH]:
                if infinite_Ecompletions == infsim_B:

                    stats, accum_sums = sampler.sample(stats, t.current, current_edge_servers,
                                                       edge_servers_max,
                                                       accum_sums, lambda_current, None)
                    if execution_mode is ExecutionMode.INFINITE_SIMULATION_BATCH: start_time=stats.reset_infinite(t.current)
                    infinite_Ecompletions = 0
                else:
                    infinite_Ecompletions += 1

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

                # in this case, update also the global (sys) counts
                stats.sys_number_catC -= 1
                stats.sys_index_catC += 1
            else:
                sprint_verbose("> lo mando a EDGE")
                stats.stats_edge.number += 1
                stats.stats_edge_C.number += 1
                service = GetService(StatsType.EDGE_C, execution_mode)

                stats.edge_jobs_queuetrack.append([RequestCategory.C, service, 0])

                completions = [i[1] for i in stats.edge_jobs_queuetrack]

                s = FindOne_modA(events, NodeType.EDGE, edge_servers_max)
                if s != 1: raise IndexError("PS and s!=1")
                sprint_verbose("> schedulo completamento EDGE per il minimo in coda, a " + str(
                    t.current + min(completions) * len(stats.edge_jobs_queuetrack)) + ", presso " + str(s))
                events[s].t = t.current + min(completions) * (len(stats.edge_jobs_queuetrack) / (
                    min(len(stats.edge_jobs_queuetrack), current_edge_servers)))
                events[s].x = 1
                events[s].category_served = RequestCategory.NOT_DEFINED
        else:
            raise ValueError("Invalid event for id =", e)

        # some sanity checks on stats values
        stats.sanity_checks()
        sprint_verbose("FINE CICLO EVENTO")

        if execution_mode is not ExecutionMode.INFINITE_SIMULATION and (
                t.current == start_time or t.current - sampler.timeelapsed_sampling_check >= SAMPLING_TIME_FIN):
            stats, accum_sums = sampler.sample(stats, t.current, current_edge_servers, edge_servers_max, accum_sums,
                                               lambda_current, autoscaler)

    simprint_inst.terminate_sim()

    if execution_mode is not ExecutionMode.INFINITE_SIMULATION:
        # global balance
        sprint_verbose(stats.sys_arrivals_count, stats.sys_index_catE, stats.sys_index_catC)
        assert (stats.sys_arrivals_count == stats.sys_index_catE + stats.sys_index_catC)

        # sistema vuoto
        assert (stats.sys_number_catE == 0)
        for stat in [stats.stats_edge, stats.stats_edge_E, stats.stats_edge_C, stats.stats_cloud]:
            sprint_verbose(stat.stats_type)
            assert (stat.number == 0)

    if execution_mode is not ExecutionMode.INFINITE_SIMULATION: stats.finalize(sampler, edge_servers_max, accum_sums,
                                                                               start_time, t.current, execution_mode)

    return stats
