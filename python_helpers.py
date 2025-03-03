from types import FrameType
import inspect


UNKNOWN_CALLER_NAME: str = "Unknown Function"


def get_caller() -> str:
    frame: FrameType | None = inspect.currentframe()
    if frame is None:
        return UNKNOWN_CALLER_NAME
    this: FrameType | None = frame.f_back
    if this is None:
        return UNKNOWN_CALLER_NAME
    previous: FrameType | None = this.f_back
    if previous is None:
        return UNKNOWN_CALLER_NAME
    name: str = previous.f_code.co_name
    return name
