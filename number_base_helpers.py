"""This file contains functions that are helpful for interacting with number bases"""


# from typing import Collection
from unicode_helpers import ALLOWED_UNICODE_SIGNS


def as_base(number: int, base: int) -> list[int]:
    if number == 0:
        return [number]

    digits: list[int] = []
    while number != 0:
        digit = number % base
        number = number // base
        digits.append(digit)
    return list(reversed(digits))


# def from_base(number: Collection[int], base: int) -> int:
#     return 0


def as_high_base(number: int) -> str:
    valid_unicode_signs: tuple[str, ...] = ALLOWED_UNICODE_SIGNS

    base: int = len(valid_unicode_signs)
    number_as_base_abstract: list[int] = as_base(number, base)

    number_as_base_list: list[str] = []
    for n in number_as_base_abstract:
        sign: str = valid_unicode_signs[n]
        number_as_base_list.append(sign)

    number_as_base: str = "".join(number_as_base_list)
    return number_as_base


# def from_high_base(number: str) -> int:
#     valid_unicode_signs: tuple[str, ...] = VALID_unicode_signs
#     lookup

#     result: int = 0
#     for digit in number:
