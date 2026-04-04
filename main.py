import numpy as np

from realface.app import run_realface_menu


def _simulation_dependencies():
    from globs import INITIAL_SEED
    from misc.timeutils import hours_to_secs
    from sim.executor import ExecutionMode, Experiment, SchedulingPolicy
    from simio.plots import plot_inf_seq, plot_TA, plot_scaling, plot_finito
    from simio.text_output import print_verify_output

    return {
        "INITIAL_SEED": INITIAL_SEED,
        "hours_to_secs": hours_to_secs,
        "ExecutionMode": ExecutionMode,
        "Experiment": Experiment,
        "SchedulingPolicy": SchedulingPolicy,
        "plot_inf_seq": plot_inf_seq,
        "plot_TA": plot_TA,
        "plot_scaling": plot_scaling,
        "plot_finito": plot_finito,
        "print_verify_output": print_verify_output,
    }


def verify():
    deps = _simulation_dependencies()
    pc_values = [0, 0.4]

    exp = deps["Experiment"]("verify-PS-single", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].MODEL],
                     False, deps["INITIAL_SEED"], 64, deps["hours_to_secs"](0), deps["hours_to_secs"](24), 1, 1,
                     [1.4], pc_values, None, None)
    exp.run(need_return=True)
    deps["print_verify_output"](exp, pc_values)

    exp = deps["Experiment"]("verify-FIFO-multi", [deps["SchedulingPolicy"].FIFO], [deps["ExecutionMode"].MODEL],
                     False, deps["INITIAL_SEED"], 64, deps["hours_to_secs"](0), deps["hours_to_secs"](24), 2, 2,
                     [1.4], pc_values, None, None)
    exp.run(need_return=True)
    deps["print_verify_output"](exp, pc_values)


def transient():
    deps = _simulation_dependencies()
    exp = deps["Experiment"]("transient-single", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].TRANSIENT_ANALYSIS],
                     False, deps["INITIAL_SEED"], 5, 0, deps["hours_to_secs"](48), 1, 1,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    deps["plot_TA"](1.4, stats, name="transient-single")

    exp = deps["Experiment"]("transient-multi", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].TRANSIENT_ANALYSIS],
                     False, deps["INITIAL_SEED"], 5, 0, deps["hours_to_secs"](48), 2, 2,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    deps["plot_TA"](1.4, stats, name="transient-multi")


def finhor_single():
    deps = _simulation_dependencies()
    exp = deps["Experiment"]("finite-PS", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].FINITE],
                     False, deps["INITIAL_SEED"], 64, 0, deps["hours_to_secs"](24), 1, 1,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    deps["plot_finito"](1.4, stats, name="finito-single")


def infhor_single():
    deps = _simulation_dependencies()
    exp = deps["Experiment"]("infinite", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].INFINITE_SIMULATION],
                     False, deps["INITIAL_SEED"], 1, 0, None, 1, 1,
                     [round(k, 1) for k in np.arange(0.1, 1.8, 0.1).tolist()], [0.4], 2048, 128)

    stats = exp.run(need_return=True)
    deps["plot_inf_seq"](stats, qos=True, name="inf-lambda")

    exp = deps["Experiment"]("infinite", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].INFINITE_SIMULATION],
                     False, deps["INITIAL_SEED"], 1, 0, None, 1, 1,
                     [1.4], [round(k, 1) for k in np.arange(0, 1.1, 0.1).tolist()], 2048, 128)

    stats = exp.run(need_return=True)
    deps["plot_inf_seq"](stats, True, qos=True, name="inf-pc")


def validation_single():
    deps = _simulation_dependencies()
    exp = deps["Experiment"]("infinite", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].INFINITE_SIMULATION],
                     False, deps["INITIAL_SEED"], 1, 0, None, 1, 1,
                     [1.2, 1.4, 1.6], [0.4], 2048, 128)
    stats = exp.run(need_return=True)
    deps["plot_inf_seq"](stats, name="validazione-single-lambda")
    exp = deps["Experiment"]("infinite", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].INFINITE_SIMULATION],
                     False, deps["INITIAL_SEED"], 1, 0, None, 1, 1,
                     [1.4], [0.1, 0.4, 0.7], 2048, 128)
    stats = exp.run(need_return=True)
    deps["plot_inf_seq"](stats, True, name="validazione-single-pc")


def validazione_multiserver():
    deps = _simulation_dependencies()
    exp = deps["Experiment"]("infinite-multi2", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].INFINITE_SIMULATION],
                     False, deps["INITIAL_SEED"], 1, 0, None, 2, 2,
                     [1.1, 1.4, 1.7], [0.4], 2048, 128)
    stats = exp.run(need_return=True)
    deps["plot_inf_seq"](stats, name="valida-multi-lambda")
    exp = deps["Experiment"]("infinite-multi2", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].INFINITE_SIMULATION],
                     False, deps["INITIAL_SEED"], 1, 0, None, 2, 2,
                     [1.4], [0.2, 0.4, 0.6], 2048, 128)
    stats = exp.run(need_return=True)
    deps["plot_inf_seq"](stats, True, name="valida-multi-pc")


def finhor_multi_scaling():
    deps = _simulation_dependencies()
    exp = deps["Experiment"]("provascaling-new-pc1", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].FINITE],
                     True, deps["INITIAL_SEED"], 64, deps["hours_to_secs"](0), deps["hours_to_secs"](24), 1, 4,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    deps["plot_finito"](1.4, stats, qos=False, fasce=True, name="scaling-fin")
    deps["plot_scaling"](stats)

    exp = deps["Experiment"]("provascaling-new-pc1", [deps["SchedulingPolicy"].PS], [deps["ExecutionMode"].FINITE],
                     True, deps["INITIAL_SEED"], 64, deps["hours_to_secs"](0), deps["hours_to_secs"](24), 1, 4,
                     [1.4], [1], None, None)
    stats = exp.run(need_return=True)
    deps["plot_finito"](1.4, stats, qos=False, fasce=True, name="scaling-fin-pc1")
    deps["plot_scaling"](stats, name="pc1")


def display_simulation_menu():
    print("***** Legacy Simulation *****")
    print("--- Choose a Function ---")
    print("1. Verify (both base and scalable)")
    print("2. Validation (base)")
    print("3. Validation (scalable)")
    print("4. Transient analysis")
    print("5. Finite horizon (base)")
    print("6. Infinite horizon (base)")
    print("7. Finite horizon (scalable)")
    print("0. Exit")
    print("-------------------------\n")


def run_simulation_menu():
    functions = {
        '1': verify,
        '2': validation_single,
        '3': validazione_multiserver,
        '4': transient,
        '5': finhor_single,
        '6': infhor_single,
        '7': finhor_multi_scaling,
    }

    while True:
        display_simulation_menu()
        choice = input("Enter your choice: ")

        if choice == '0':
            return
        elif choice in functions:
            functions[choice]()
        else:
            print("Invalid choice. Please try again.")


def display_main_menu():
    print("***** Airport Face Recognition *****")
    print("--- Choose a Mode ---")
    print("1. Real face recognition")
    print("2. Legacy simulation")
    print("0. Exit")
    print("---------------------\n")


def main():
    while True:
        display_main_menu()
        choice = input("Enter your choice: ").strip()

        if choice == '0':
            print("Quitting...")
            break
        if choice == '1':
            run_realface_menu()
            continue
        if choice == '2':
            run_simulation_menu()
            continue
        print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
