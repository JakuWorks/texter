"""This file contains functions that are helpful for manipulating and analyzing data"""
from typing import Any, TypeVar


K = TypeVar('K')
V = TypeVar('V')
def swap_dict_keys_values(dictionary: dict[K, V]) -> dict[V, K]:
    reversed_dict: dict[V, K] = {v: k for k, v in dictionary.items()}
    return reversed_dict


def dict_keys_contain_substring(dictionary: Any, substring: str) -> bool:
    keys_string: str = ''.join(dictionary.keys())
    keys_string = keys_string.lower()
    substring = substring.lower()
    contains_substring: bool = substring in keys_string
    return contains_substring