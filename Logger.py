from typing import Collection
from pathlib import Path
from settings import IS_DEBUG, LOGS_DEBUG_PREFIX, LOGS_WARNING_PREFIX, LOGS_ERROR_GENERIC_PREFIX, LOGS_SEPARATOR as s
from python_helpers import get_caller, UNKNOWN_CALLER_NAME


class Logger:
    is_debug: bool

    def __init__(self, is_debug: bool) -> None:
        self.is_debug = is_debug

    def log(self, message: str) -> None:
        print(message)

    def debug(self, message: str) -> None:
        if self.is_debug:
            caller_infix: str = f'{get_caller()}{s}'
            text: str = f"{LOGS_DEBUG_PREFIX}{caller_infix}{s}{message}"
            self.log(text)

    def warn(self, message: str) -> None:
        caller_infix: str = f'{get_caller()}{s}'
        text: str = f"{LOGS_WARNING_PREFIX}{caller_infix}{s}{message}"
        self.log(text)

    def runtime_error(self, message: str) -> None:
        caller_infix: str
        try:
            caller_infix = f'{get_caller()}{s}'
        except:
            caller_infix = f'{UNKNOWN_CALLER_NAME}{s}'

        text: str
        try:
            text = f"{LOGS_ERROR_GENERIC_PREFIX}{s}{caller_infix}{message}"
        except:
            text = message

        raise RuntimeError(text)


def get_paths_text(paths: Collection[Path]) -> str:
    text: str = s.join({str(path) for path in paths})
    return text


# Variable name shortened for convenience's sake. Full name should be "logger"
logger: Logger = Logger(is_debug=IS_DEBUG)
