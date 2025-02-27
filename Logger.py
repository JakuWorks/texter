from typing import Collection
from pathlib import Path
from settings import IS_DEBUG, LOGS_DEBUG_PREFIX, LOGS_WARNING_PREFIX, LOGS_SEPARATOR as s


class Logger:
    is_debug: bool

    def __init__(self, is_debug: bool):
        self.is_debug = is_debug

    def log(self, message: str):
        print(message)

    def debug(self, message: str):
        if self.is_debug:
            self.log(f"{LOGS_DEBUG_PREFIX}{s}{message}")

    def warn(self, message: str):
        self.log(f"{LOGS_WARNING_PREFIX}{s}{message}")


def get_paths_text(paths: Collection[Path]):
    return s.join({str(path) for path in paths})


# Variable name shortened for convenience's sake. Full name should be "logger"
logger: Logger = Logger(is_debug=IS_DEBUG)
