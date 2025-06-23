import datetime


def hours_to_secs(hours: int, mins: int = 0):
    return hours * 60 * 60 + mins * 60


def seconds_to_hhmm(seconds: int) -> str:
    seconds = seconds % 86400
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)

    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def seconds_to_extract_h(seconds: int) -> int:
    seconds = seconds % 86400
    h = int(seconds // 3600)
    return h


def seconds_to_hhmmss(seconds: float) -> str:
    return str(datetime.timedelta(seconds=seconds))  # %hours_to_secs(24)))
