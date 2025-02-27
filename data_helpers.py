"""This file contains functions that are helpful for manipulating and analyzing data"""

from typing import Any, TypeVar


A = TypeVar("A")
B = TypeVar("B")


def swap_dict_keys_values(dictionary: dict[A, B]) -> dict[B, A]:
    reversed_dict: dict[B, A] = {v: k for k, v in dictionary.items()}
    return reversed_dict


def dict_keys_contain_substring(dictionary: Any, substring: str) -> bool:
    keys_string: str = "".join(dictionary.keys())
    keys_string = keys_string.lower()
    substring = substring.lower()
    contains_substring: bool = substring in keys_string
    return contains_substring


def pad_list_from_left(list: list[A], padding: A, desired_length: int) -> list[A]:
    to_pad: int = desired_length - len(list)
    return [padding] * to_pad + list
