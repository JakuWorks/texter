"""This file contains functions that are helpful for interacting with number bases"""
from unicode_helpers import ALLOWED_UNICODES


def as_base(number: int, base: int) -> tuple[int, ...]:
    if number == 0:
        return tuple([number])

    digits: list[int] = []
    while number != 0:
        digit = number % base
        number = number // base
        digits.append(digit)
    digits_tuple = tuple(reversed(digits))
    return digits_tuple

def from_base(number: tuple[int, ...], base: int) -> int:
    return 0

def as_high_base(number: int) -> str:
    valid_unicodes: tuple[str, ...] = ALLOWED_UNICODES

    base: int = len(valid_unicodes)
    number_as_base_abstract: tuple[int, ...] = as_base(number, base)
    number_as_base_list: list[str] = []

    for n in number_as_base_abstract:
        sign: str = valid_unicodes[n]
        number_as_base_list.append(sign)

    number_as_base: str = ''.join(number_as_base_list)
    return number_as_base


# def from_high_base(number: str) -> int:
#     valid_unicodes: tuple[str, ...] = VALID_UNICODES
#     lookup

#     result: int = 0
#     for digit in number:

