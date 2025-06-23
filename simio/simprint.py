from enum import Enum

from globs import VERBOSE
from misc.timeutils import seconds_to_hhmmss


def format(num):
    s = f"{num:.3f}"

    if len(s) > 9:
        if 'e' not in s.lower():
            pass
        s = s[:9]
    elif len(s) < 9:
        s = f"{s:>9}"

    return s


class PrintType(Enum):
    ERROR = "[*ERROR*]"
    WARNING = "[WARNING]"
    INFO = "[info   ]"
    VERBOSE = "[verbose]"

    def __str__(self): return self.value


class SimPrint:
    def __init__(self):
        global simprint_inst
        simprint_inst = self
        self.tprint_clock = float('inf')
        self.tprint_guard = float('inf')
        self.tprint_start = float('inf')
        self.tprint_stop = float('inf')
        self.last_print_was_idle = False

    def get_instance(self):
        global simprint_inst
        if simprint_inst is None: simprint_inst = SimPrint()
        return simprint_inst

    def is_idle(self) -> bool:
        return self.tprint_clock == float('inf')

    def print_header(self):
        print(f"[  clock  | clock-RT| h24-RT ]{PrintType.INFO} ----------------------")
        self._print(PrintType.INFO, "SIMULATION STARTED")

    def print_footer(self):
        self._print(PrintType.INFO, "SIMULATION COMPLETED")
        self.reset()

    def terminate_sim(self):
        self.print_footer()

    def preamble(self) -> str:
        if self.is_idle():
            if self.last_print_was_idle:
                return f"[{' ' * 9 * 3}>]"
            else:
                self.last_print_was_idle = True
                return f"[ ---------------------- idle]"
        else:
            self.last_print_was_idle = False
            if self.tprint_clock == self.tprint_guard:
                return f"[{' ' * 9 * 3}>]"
            else:
                return (f"["
                        f"{format(self.tprint_clock - self.tprint_start)}"
                        f" "
                        f"{format(self.tprint_clock)}"
                        f" "
                        f"{seconds_to_hhmmss(self.tprint_clock).split('.')[0]:>8.8s}"
                        f"]")

    def _print(self, print_type, *args, **kwargs):
        print(f"{self.preamble()}{print_type}", *args, **kwargs)
        self.tprint_guard = self.tprint_clock
        self.check_update_sim_expiration()

    def set_sim_prints(self, start, stop):
        self.tprint_clock = start
        self.tprint_guard = float('inf')
        self.tprint_start = start
        self.tprint_stop = stop

    def reset(self):
        self.tprint_clock = float('inf')
        self.tprint_guard = float('inf')
        self.tprint_start = float('inf')
        self.tprint_stop = float('inf')

    def check_update_sim_expiration(self):
        if self.tprint_clock >= self.tprint_stop:
            self.reset()


simprint_inst = SimPrint()


def sprint(*args, **kwargs):
    global simprint_inst
    simprint_inst._print(PrintType.INFO, *args, **kwargs)


def sprint_error(*args, **kwargs):
    global simprint_inst
    simprint_inst._print(PrintType.ERROR, *args, **kwargs)


def sprint_warning(*args, **kwargs):
    global simprint_inst
    simprint_inst._print(PrintType.WARNING, *args, **kwargs)


def sprint_verbose(*args, **kwargs):
    if VERBOSE:
        global simprint_inst
        simprint_inst._print(PrintType.VERBOSE, *args, **kwargs)
