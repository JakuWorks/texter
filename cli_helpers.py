"""This file contains helper functions for managing the CLI of the program"""
from filesystem_helpers import get_children


def get_zip_target() -> str:
    while True:
        children: list[str] = get_children()
        prepended_children: list[str] = [f'  {child}' for child in children]
        children_text: str = '\n'.join(prepended_children)
        print(f'Choose a target. Possible options:' +
              f'\n{children_text}')
        target: str = input('Target: ')
        if target in children:
            break
    return target