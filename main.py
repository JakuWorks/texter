"""This file is the heart of the program. This file controls the flow of the entire program at a high level"""
import shutil
import sys
from cli_helpers import get_zip_target
from number_base_helpers import as_high_base
from settings import RECURSION_LIMIT


def main() -> None:
    sys.setrecursionlimit(RECURSION_LIMIT)

    zipping_target: str = get_zip_target()
    zip_basename: str = zipping_target
    zip_path: str = shutil.make_archive(base_name=zip_basename, format='zip', root_dir='.', base_dir=zipping_target,)

    with open(zip_path, 'rb') as f:
        file_bytes: bytes = f.read()

    file_int: int = int.from_bytes(file_bytes, byteorder='big')
    high_base: str = as_high_base(file_int)
    print(high_base)



def testanotherthing():
    # import random
    # random_code_point = random.randint(0x0000, 0xFFFF)
    random_code_point = 0x20
    # random_code_point = 0xFFFFF
    # random_code_point = 0x10FFFF
    # random_code_point = 0x10FFFF
    random_char = chr(random_code_point)
    print(random_char)



# testanotherthing()
# print(len(get_valid_unicode_signs()))
# print(as_base(1, 11))
# print(chr(n))
# print("TESTING up,down")
main()
