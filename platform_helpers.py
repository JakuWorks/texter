from typing import Any, Callable
import os
import platform
import subprocess
import pyperclip # type: ignore # missing stubs
import functools
from data_helpers import dict_keys_contain_substring
from settings import ANDROID_CLIPBOARD_TIMEOUT_SECONDS, LOGS_SEPARATOR as s
from Logger import logger as l


def get_is_android() -> bool:
    is_android: bool = dict_keys_contain_substring(os.environ, "android")
    return is_android


def _get_os() -> str:
    os: str = platform.system()
    if os == "Linux" and get_is_android():
        os = "Android"
    return os
get_os: Callable[[], str] = functools.lru_cache(maxsize=1, typed=True)(_get_os)


def get_android_clipboard() -> str:
    # THIS WILL SILENTLY FAIL IF TERMUX-API IS IMPROPERLY INSTALLED
    # I am not aware of any way to circumvent this
    timeout: int = ANDROID_CLIPBOARD_TIMEOUT_SECONDS
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["termux-clipboard-get"], capture_output=True, text=True, timeout=timeout
    )
    clipboard: str = result.stdout
    clipboard = clipboard.lower()
    return clipboard


def set_android_clipboard(text: str) -> None:
    # THIS WILL SILENTLY FAIL IF TERMUX-API IS IMPROPERLY INSTALLED
    subprocess.run([f"termux-clipboard-set"], input=text, text=True)


def safely_set_android_clipboard(text: str) -> bool:
    "The return is if the set was a success"
    set_android_clipboard(text)
    current_clipboard: str = get_android_clipboard()
    return current_clipboard == text


def get_clipboard() -> str:
    clipboard: Any = pyperclip.paste()
    if type(clipboard) != str:
        raise RuntimeError("Failed to retrieve clipboard!")
    return clipboard


def set_clipboard(text: str) -> None:
    pyperclip.copy(text)  # type: ignore


OS: str = get_os()
l.debug(f"{OS}{s}Determined OS")