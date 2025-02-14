from typing import Any
import os
import subprocess
import pyperclip
from texter.data_helpers import dict_keys_contain_substring
from main import ANDROID_CLIPBOARD_TIMEOUT_SECONDS


def is_android() -> bool:
    is_android: bool = dict_keys_contain_substring(os.environ, 'android')
    return is_android

def get_android_clipboard() -> str:
    # THIS WILL SILENTLY FAIL IF TERMUX-API IS IMPROPERLY INSTALLED
    timeout: int = ANDROID_CLIPBOARD_TIMEOUT_SECONDS
    result: subprocess.CompletedProcess[str] = subprocess.run(['termux-clipboard-get'], capture_output=True, text=True, timeout=timeout)
    clipboard: str = result.stdout
    clipboard = clipboard.lower()
    return clipboard


def set_android_clipboard(text: str) -> None:
    # THIS WILL SILENTLY FAIL IF TERMUX-API IS IMPROPERLY INSTALLED
    subprocess.run([f'termux-clipboard-set'], input=text, text=True)


def get_clipboard() -> str:
    clipboard: Any = pyperclip.paste()
    if type(clipboard) != str:
        raise RuntimeError('Failed to retrive clipboard!') 
    return clipboard


def set_clipboard(text: str) -> None:
    pyperclip.copy(text)  # type: ignore


IS_ANDROID: bool = is_android()