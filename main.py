import numpy as np

from globs import INITIAL_SEED
from misc.timeutils import hours_to_secs
from sim.executor import ExecutionMode, Experiment, SchedulingPolicy
from simio.plots import plot_inf_seq, plot_TA, plot_scaling, plot_finito
from simio.text_output import print_verify_output


def verify():
    pc_values = [0, 0.4]

    exp = Experiment("verify-PS-single", [SchedulingPolicy.PS], [ExecutionMode.MODEL],
                     False, INITIAL_SEED, 64, hours_to_secs(0), hours_to_secs(24), 1, 1,
                     [1.4], pc_values, None, None)
    exp.run(need_return=True)
    print_verify_output(exp, pc_values)

    exp = Experiment("verify-FIFO-multi", [SchedulingPolicy.FIFO], [ExecutionMode.MODEL],
                     False, INITIAL_SEED, 64, hours_to_secs(0), hours_to_secs(24), 2, 2,
                     [1.4], pc_values, None, None)
    exp.run(need_return=True)
    print_verify_output(exp, pc_values)


def transient():
    exp = Experiment("transient-single", [SchedulingPolicy.PS], [ExecutionMode.TRANSIENT_ANALYSIS],
                     False, INITIAL_SEED, 5, 0, hours_to_secs(48), 1, 1,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    plot_TA(1.4, stats, name="transient-single")

    exp = Experiment("transient-multi", [SchedulingPolicy.PS], [ExecutionMode.TRANSIENT_ANALYSIS],
                     False, INITIAL_SEED, 5, 0, hours_to_secs(48), 2, 2,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    plot_TA(1.4, stats, name="transient-multi")


def finhor_single():
    exp = Experiment("finite-PS", [SchedulingPolicy.PS], [ExecutionMode.FINITE],
                     False, INITIAL_SEED, 64, 0, hours_to_secs(24), 1, 1,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    plot_finito(1.4, stats, name="finito-single")


def infhor_single():
    exp = Experiment("infinite", [SchedulingPolicy.PS], [ExecutionMode.INFINITE_SIMULATION],
                     False, INITIAL_SEED, 1, 0, None, 1, 1,
                     [round(k, 1) for k in np.arange(0.1, 1.8, 0.1).tolist()], [0.4], 2048, 128)

    stats = exp.run(need_return=True)
    plot_inf_seq(stats, qos=True, name="inf-lambda")

    exp = Experiment("infinite", [SchedulingPolicy.PS], [ExecutionMode.INFINITE_SIMULATION],
                     False, INITIAL_SEED, 1, 0, None, 1, 1,
                     [1.4], [round(k, 1) for k in np.arange(0, 1.1, 0.1).tolist()], 2048, 128)

    stats = exp.run(need_return=True)
    plot_inf_seq(stats, True, qos=True, name="inf-pc")


def validation_single():
    exp = Experiment("infinite", [SchedulingPolicy.PS], [ExecutionMode.INFINITE_SIMULATION],
                     False, INITIAL_SEED, 1, 0, None, 1, 1,
                     [1.2, 1.4, 1.6], [0.4], 2048, 128)
    stats = exp.run(need_return=True)
    plot_inf_seq(stats, name="validazione-single-lambda")
    exp = Experiment("infinite", [SchedulingPolicy.PS], [ExecutionMode.INFINITE_SIMULATION],
                     False, INITIAL_SEED, 1, 0, None, 1, 1,
                     [1.4], [0.1, 0.4, 0.7], 2048, 128)
    stats = exp.run(need_return=True)
    plot_inf_seq(stats, True, name="validazione-single-pc")


def validazione_multiserver():
    exp = Experiment("infinite-multi2", [SchedulingPolicy.PS], [ExecutionMode.INFINITE_SIMULATION],
                     False, INITIAL_SEED, 1, 0, None, 2, 2,
                     [1.1, 1.4, 1.7], [0.4], 2048, 128)
    stats = exp.run(need_return=True)
    plot_inf_seq(stats, name="valida-multi-lambda")
    exp = Experiment("infinite-multi2", [SchedulingPolicy.PS], [ExecutionMode.INFINITE_SIMULATION],
                     False, INITIAL_SEED, 1, 0, None, 2, 2,
                     [1.4], [0.2, 0.4, 0.6], 2048, 128)
    stats = exp.run(need_return=True)
    plot_inf_seq(stats, True, name="valida-multi-pc")


def finhor_multi_scaling():
    exp = Experiment("provascaling-new-pc1", [SchedulingPolicy.PS], [ExecutionMode.FINITE],
                     True, INITIAL_SEED, 64, hours_to_secs(0), hours_to_secs(24), 1, 4,
                     [1.4], [0.4], None, None)
    stats = exp.run(need_return=True)
    plot_finito(1.4, stats, qos=False, fasce=True, name="scaling-fin")
    plot_scaling(stats)

    exp = Experiment("provascaling-new-pc1", [SchedulingPolicy.PS], [ExecutionMode.FINITE],
                     True, INITIAL_SEED, 64, hours_to_secs(0), hours_to_secs(24), 1, 4,
                     [1.4], [1], None, None)
    stats = exp.run(need_return=True)
    plot_finito(1.4, stats, qos=False, fasce=True, name="scaling-fin-pc1")
    plot_scaling(stats, name="pc1")


def display_menu():
    print("***** PMCSN project *****")
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


def main():
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
        display_menu()
        choice = input("Enter your choice: ")

        if choice == '0':
            print("Quitting...")
            break
        elif choice in functions:
            functions[choice]()
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
