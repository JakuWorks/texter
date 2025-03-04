"""
This file contains functions regarding "Light Archives".

    "Light Archive"
    Is a custom format created for the purpose this program
    It aims to be much lighter than popular archive types (such as .tar) and "save every possible byte"
    It skips filesystem metadata (permissions, creation data, etc.). With the exception of the file size and file name
    Changing even a single byte may make the archive unreadable

    Legend:
    [] -> single byte
    () -> chain of bytes
    {} -> single reserved bit
    ... -> repeat previous byte as many times as necessary
    "<-" -> comment

    Format's structure looks this way for every element:

    If it's a file:
    ( NAME ) [ NAME TERMINATOR #1 ] ( [ LENGTH { IS ENDING } ] ... ) ( DATA )
    If it's a directory:
    ( NAME ) [ NAME TERMINATOR #0 ] ( [ GO_UPS { IS_ENDING } ] ... )

    IS_ENDING is a bit that marks the end of an unsigned integer bytes sequence
    LENGTH is the length of the DATA (in bytes)
    GO_UPS is specific to this light archive format and tells the unpacker how many directories to "go up"

    NAME TERMINATORS:
    - #0 - [ 0x00 ] - a file
    - #1 - [ 0x2F ] - a directory
    *[ 0x2F ] is an '/' utf-8 character). This is the only utf-8 character that cannot be used in both ext4 and NTFS filenames
    (having two different name terminators allows to store a single bit of information)

    The unpacker reads data from left to right. If it finds a folder => it automatically considers all next elements to be inside it
    ^(this is why GO_UPS is necessary)
    The archive has folders always sorted to be LAST

    *on the left is the GO_UPS value for each element (- means "missing")
    *on the right there are bytes 'representing' the file
    -  file         | ( NAME ) [ 0x00 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  folder       | ( NAME ) [ 0x2F ] [ 00000001 ]
    -  /   file     | ( NAME ) [ 0x00 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    -  /   file     | ( NAME ) [ 0x00 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  /   folder   | ( NAME ) [ 0x2F ] [ 00000001 ]
    -  /   /   file | ( NAME ) [ 0x00 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  /   folder   | ( NAME ) [ 0x2F ] [ 00000001 ]
    -  /   /   file | ( NAME ) [ 0x00 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    2  folder       | ( NAME ) [ 0x2F ] [ 00000101 ]
    -  /   file     | ( NAME ) [ 0x00 ] ( [ LENGTH { IS ENDING } ] ... ) ( FILE DATA )
    0  /   folder <- Imagine 700 folders inside each other here
    700/   folder   | ( NAME ) [ 0x2F ] [ 00001010 ] [ 01111001 ]
"""

# TODO: In the ROOT of the structure - the deepest directory should be last (this can save 1 byte when the depth exceeds >127)
#       ^ Also in all sub-directories the deepest element should be LAST
#       ^ everywhere else directories should be sorted as deepest-first (this has a possibility of saving 1 byte in deep nesting)
#       ^ I probably just want to make a function called optimize_dir_sorting_in_structure or something
#

# TODO Delete files in case the program exists early
# TODO for unpacking - make a system that first analyzes the entire file,
# then prepares coroutines for creating each file
# then runs it all
# TODO GREAT IDEA FOR PARALLELIZATION:
# - Make the write_light_archive_... functions return a tuple(length, write_coroutine)
# - Also add an argument for the beginning of the write to the file
# ^ I will also need to implement my own "offset" copy function that supports chunks
# ^ make a __SECOND__ function for actually creating the coroutines
# And a setting for the chunk size
# This should be EASIER than making the archive format handling itself

from typing import Collection
from io import BufferedWriter, BufferedReader
from enum import Enum
import copy
import math
import os
import shutil
from pathlib import Path
from settings import (
    LIGHT_ARCHIVE_UNPACK_EXPECTED_MAX_ENCODED_INT_BYTES,
    LIGHT_ARCHIVE_UNPACK_EXPECTED_MAX_NAME_BYTES,
    COPY_BLOCK_SIZE_BYTES,
    LOGS_ERROR_GENERIC_PREFIX,
    LOGS_ERROR_ASSERTION_PREFIX,
    LOGS_SEPARATOR as s,
    LOGS_LIGHT_ARCHIVE_UNKNOWN_NAME as unknown_name,
)
from Logger import get_paths_text, logger as l
from filesystem_helpers import (
    get_nonexistent_paths,
    get_non_children_paths,
    ensure_file_not_exist,
)
from number_base_helpers import as_base
from data_helpers import pad_list_from_left


# The children are respectively: Files and Directories
type ArchiveChildren = tuple[Collection[Path], ArchiveStructure]
type ArchiveStructure = dict[Path, ArchiveChildren]
type UnpackedFile = tuple[str, int, int]
type UnpackedChildren = tuple[Collection[UnpackedFile], UnpackedStructure]
type UnpackedStructure = dict[str, UnpackedChildren]


class UnpackedType(Enum):
    FILE = "file"
    DIR = "dir"


STRUCTURE_ROOT_KEY: Path = Path("ROOT")
# DO NOT CHANGE!
_NAME_TERMINATOR_0: bytes = b"\x00"
_NAME_TERMINATOR_0_DECODED: str = _NAME_TERMINATOR_0.decode("utf-8")
_NAME_TERMINATOR_1: bytes = b"\x2F"  # Terminator 1 is an utf-8 ASCII '\' character
_NAME_TERMINATOR_1_DECODED: str = _NAME_TERMINATOR_1.decode("utf-8")


def make_light_archive(
    destination: Path,
    input_directory: Path,
    input_elements: Collection[Path],
    debug_archive_id: int | None = None,
) -> None:
    # Archive IDs are only used for debugging purposes
    archive_id: int
    if debug_archive_id is not None:
        archive_id = debug_archive_id
    else:
        archive_id = new_archive_id()
    logs_infix: str = f"{archive_id}{s}"
    l.debug(f"{logs_infix}Creating a light archive")

    ensure_file_not_exist(destination)
    with open(destination, "wb") as dest:
        structure: ArchiveStructure = get_structure(
            input_directory, input_elements, archive_id
        )
        write_archive_from_structure(dest, structure, archive_id)


def new_archive_id() -> int:
    highest_archive_id_name: str = "highest_archive_id"
    archive_id: int
    if not hasattr(make_light_archive, highest_archive_id_name):
        archive_id = 1
    else:
        highest_archive_id: int = getattr(make_light_archive, highest_archive_id_name)
        archive_id = highest_archive_id + 1
    setattr(make_light_archive, highest_archive_id_name, archive_id)
    assert archive_id > 0
    return archive_id


def get_structure(
    input_directory: Path, input_elements: Collection[Path], archive_id: int = 0
) -> ArchiveStructure:
    # TODO: TO BE REMADE
    logs_infix: str = f"{s}{archive_id}{s}"
    l.debug(
        f"{logs_infix}Making archive structure{s}input dir: {input_directory}"
        f"{s}Selected {len(input_elements)} elements"
    )

    all_paths: set[Path] = {input_directory, *input_elements}

    nonexistent_paths: set[Path] = get_nonexistent_paths(all_paths)
    if len(nonexistent_paths):
        nonexistent_paths_text: str = get_paths_text(nonexistent_paths)
        l.runtime_error(
            f"{logs_infix}Elements don't exist!"
            f"{s}Dir: {input_directory}{s}Nonexistent Elements:{s}{nonexistent_paths_text}"
        )

    non_children_paths: set[Path] = get_non_children_paths(
        input_directory, input_elements
    )
    if len(non_children_paths):
        non_children_paths_text: str = get_paths_text(non_children_paths)
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Elements aren't children of input directory!"
            f"{s}Dir: {input_directory}{s}Non-Child Elements:{s}{non_children_paths_text}"
        )

    files: set[Path] = set()
    sub_structures: list[ArchiveStructure] = []
    for child in input_elements:
        if child.is_file():
            files.add(child)
        elif child.is_dir():
            children: set[Path] = set(child.iterdir())
            sub_structure: ArchiveStructure = get_structure(child, children, archive_id)
            sub_structures.append(sub_structure)
        else:
            l.warn(f"{logs_infix}Unusual file! SKIPPING!{s}{str(child)}")

    directories: ArchiveStructure = {
        k: v for sub_structure in sub_structures for k, v in sub_structure.items()
    }
    structure: ArchiveStructure = {input_directory: (files, directories)}
    l.debug(f"{logs_infix}Finished making an element of archive structure")
    return structure


def write_archive_from_structure(
    dest: BufferedWriter, structure: ArchiveStructure, archive_id: int = 0
) -> None:
    logs_infix: str = f"{write_archive_from_structure.__name__}{s}{archive_id}{s}"
    l.debug(f"{logs_infix}Beginning writing to light archive...")

    assert check_structure_has_root(structure), (
        f"{LOGS_ERROR_ASSERTION_PREFIX}{s}{logs_infix}Keys: {structure.keys()}{s}"
        f'Light archive structure must have a "{STRUCTURE_ROOT_KEY}" key at root level!'
    )

    assert check_structure_roots_count(structure), (
        f"{LOGS_ERROR_ASSERTION_PREFIX}{s}{logs_infix}Keys: {structure.keys()}{s}"
        f"Light archive structure has too many keys at root level!"
    )

    root_children: ArchiveChildren = structure[STRUCTURE_ROOT_KEY]
    write_encoded_children_bytes(dest, root_children, archive_id)
    l.debug(f"{logs_infix}Finished writing to light archive...")


def check_structure_has_root(structure: ArchiveStructure) -> bool:
    return STRUCTURE_ROOT_KEY in structure.keys()


def check_structure_roots_count(structure: ArchiveStructure) -> bool:
    return len(structure.keys()) == 1


def write_encoded_children_bytes(
    dest: BufferedWriter, children: ArchiveChildren, archive_id: int
) -> int:  # -> created_depth
    # Careful! This function is recursive
    logs_infix: str = f"{write_encoded_children_bytes.__name__}{s}{archive_id}{s}"

    files: Collection[Path] = children[0]
    for file in files:
        l.debug(f"{logs_infix}Encoding and writing bytes of file {file}")
        write_encoded_file_bytes(dest, file, archive_id)

    created_depth: int = 0

    dirs: ArchiveStructure = children[1]
    for dir, children in dirs.items():
        l.debug(f"{logs_infix}Encoding and writing bytes of dir {dir}")
        write_encoded_dir_bytes(dest, dir, created_depth, archive_id)
        created_depth = write_encoded_children_bytes(dest, children, archive_id)
        # The created depth from one call goes to the go ups of the next call

    created_depth = created_depth + 1
    return created_depth


def write_encoded_file_bytes(dest: BufferedWriter, path: Path, archive_id: int):
    # Note: Files don't need going up due to how the archive works
    logs_infix: str = f"{write_encoded_file_bytes.__name__}{s}{archive_id}{s}"
    l.debug(f"{logs_infix}Getting file bytes")
    expected_max_bytes: int = LIGHT_ARCHIVE_UNPACK_EXPECTED_MAX_NAME_BYTES

    name: str = path.name
    if not len(name):
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Filename cannot be empty!"
        )
    if _NAME_TERMINATOR_0_DECODED in name:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Filename cannot contain Terminator #0: {_NAME_TERMINATOR_0_DECODED}"
        )
    if _NAME_TERMINATOR_1_DECODED in name:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Filename cannot contain Terminator #1: {_NAME_TERMINATOR_1_DECODED}"
        )

    size: int = os.path.getsize(path)
    size_encoded: bytes = get_encoded_int(size)

    name_bytes: bytes = name.encode("utf-8")
    name_bytes_len: int = len(name_bytes)
    if name_bytes_len > expected_max_bytes:
        l.warn(
            f"{logs_infix}{name}{s}This name was encoded into {name_bytes_len} bytes"
            f"{s}But this exceeds your expected max name length setting for unpacking! ({expected_max_bytes})"
            f"{s}This archive may be unpackable for you now. Adjust your setting to at least {name_bytes_len}!"
        )

    dest.write(name_bytes + _NAME_TERMINATOR_0 + size_encoded)

    with open(path, "rb") as f:
        shutil.copyfileobj(f, dest, length=COPY_BLOCK_SIZE_BYTES)


def write_encoded_dir_bytes(
    dest: BufferedWriter, name: str, go_up: int, archive_id: int
) -> None:
    logs_infix: str = f"{write_encoded_dir_bytes.__name__}{s}{archive_id}{s}"

    if not len(name):
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Filename cannot be empty!"
        )
    if _NAME_TERMINATOR_0_DECODED in name:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{name}{s}Filename cannot contain Terminator #0: {_NAME_TERMINATOR_0_DECODED}"
        )
    if _NAME_TERMINATOR_1_DECODED in name:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{name}{s}Filename cannot contain Terminator #1: {_NAME_TERMINATOR_1_DECODED}"
        )
    go_up_bytes: bytes = get_encoded_int(go_up)
    dest.write(name.encode("utf-8") + _NAME_TERMINATOR_1 + go_up_bytes)
    l.debug(f"{logs_infix}Getting dir bytes")


def get_encoded_int(num: int) -> bytes:
    # This function does not need to be fast. For every element in the archive there should be
    # one encoded int that's most likely going to be 1-10 bytes long (very short)

    # The result is referred to here as the "encoded"
    logs_infix: str = f"{get_encoded_int.__name__}{s}{num}{s}"
    expected_max_bytes: int = LIGHT_ARCHIVE_UNPACK_EXPECTED_MAX_ENCODED_INT_BYTES
    usable_bits_per_byte: int = 7

    as_base2: list[int] = as_base(num, 2)
    bytes_count: int = math.ceil(len(as_base2) / usable_bits_per_byte)

    reversed_as_base2: list[int] = list(reversed(as_base2))
    reversed_encoded_as_bytes: list[list[int]] = []
    for i in range(bytes_count):
        start: int = i * usable_bits_per_byte
        byte: list[int] = reversed_as_base2[start : start + usable_bits_per_byte]
        reversed_encoded_as_bytes.append(byte)

    encoded_as_bytes: list[list[int]] = list(reversed(reversed_encoded_as_bytes))
    encoded_as_bytes = [list(reversed(bytes)) for bytes in encoded_as_bytes]

    for byte in encoded_as_bytes[0:-1]:
        byte.append(0)
    encoded_as_bytes[-1].append(1)
    encoded_as_bytes[0] = pad_list_from_left(encoded_as_bytes[0], 0, 8)

    encoded_as_bytes_len: int = len(encoded_as_bytes)

    encoded_as_bits: list[int] = [bit for byte in encoded_as_bytes for bit in byte]
    encoded_as_int: int = int("".join(map(str, encoded_as_bits)), base=2)
    encoded: bytes = encoded_as_int.to_bytes(bytes_count, "big")

    l.debug(f"{logs_infix}Encoded into {encoded_as_bytes_len} bytes")

    if encoded_as_bytes_len > expected_max_bytes:
        l.warn(
            f"{logs_infix}This int was encoded into {encoded_as_bytes_len} bytes"
            f"{s}But this exceeds your expected max encoded int length setting for unpacking! ({expected_max_bytes})"
            f"{s}This archive may be unpackable for you now. Adjust your setting to at least {encoded_as_bytes_len}!"
        )
    return encoded


def unpack_light_archive(archive: Path, dest: Path) -> None:
    archive_name_infix: str = f"Name: {archive.name}{s}"
    logs_infix: str = f"{unpack_light_archive.__name__}{s}{archive_name_infix}"

    if not archive.exists():
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{archive}{s}File Doesn't Exist"
        )
    if not dest.exists():
        os.mkdir(dest)

    with open(archive, "rb") as f:
        # DEV
        print("-" * 50)
        print(unpack_structure(f, archive.name))
        pass


def unpack_structure(
    archive: BufferedReader, archive_name: str = unknown_name
) -> UnpackedStructure:
    archive_name_infix: str = f"Name: {archive_name}{s}"
    logs_infix: str = f"{unpack_structure.__name__}{s}{archive_name_infix}"
    tip_postfix: str = f"{s}Tip: Your archive may be invalid"
    l.debug(f"{logs_infix}Building structure")

    # This entire implementation works thanks to reference semantics
    structure: UnpackedStructure = {}
    # The scope is a list with handles of the "dictionaries" that belong to each element
    scope: list[UnpackedStructure] = [structure]  # This must never be empty
    curr_dir_name: str = STRUCTURE_ROOT_KEY
    curr_files: list[UnpackedFile] = []
    while True:
        name: str
        type: UnpackedType

        is_eof: bool = not archive.peek(1)
        if is_eof:
            scope[-1][curr_dir_name] = (curr_files, {})
            l.debug(f"{logs_infix}Finished building structure (EOF)")
            break

        name, type = unpack_identify_element(archive, archive_name)
        if type == UnpackedType.FILE:
            length: int = unpack_decode_next_int(archive, archive_name)
            start: int = archive.tell()
            file_info: UnpackedFile = (name, start, length)
            curr_files.append(file_info)
            l.debug(
                f"{logs_infix}Type: {UnpackedType.FILE.value}{s}Start: {start}{s}Length: {length}{s}Added element to structure"
            )
            archive.seek(length, 1)  # Skipping DATA and going to the next element
        elif type == UnpackedType.DIR:
            go_ups: int = unpack_decode_next_int(archive, archive_name)
            substructure: UnpackedStructure = {}
            files: list[UnpackedFile] = copy.copy(curr_files)
            scope[-1][curr_dir_name] = (files, substructure)
            l.debug(
                f"{logs_infix}Type: {UnpackedType.DIR.value}{s}Name: {name}{s}Go Ups: {go_ups}{s}Added element to structure"
            )

            # Preparing for next dir (enacting go ups, etc.)
            scope.append(substructure)
            curr_dir_name = name
            curr_files.clear()

            structure_scope_length: int = len(scope)
            if go_ups >= len(scope):
                raise RuntimeError(
                    f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Archive cannot have negative depth!"
                    f"{s}GO_UPS: {go_ups}{s}Scope Length: {structure_scope_length}{tip_postfix}"
                )
            if go_ups != 0:
                del scope[-go_ups:]
        else:
            raise RuntimeError(
                f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{type}{s}Unsupported element type!"
            )

    return structure


def unpack_flatten_structure(
    archive: BufferedReader,
    structure: UnpackedStructure,
    archive_name: str = unknown_name,
) -> tuple[list[Path], set[UnpackedFile]]:
    archive_name_infix: str = f"Name: {archive_name}{s}"
    logs_infix: str = f"{unpack_flatten_structure.__name__}{s}{archive_name_infix}"
    l.debug(f"{logs_infix}Flattening unpacked structure")

    roots_count: int = len(structure.keys())
    if roots_count > 1 or roots_count < 1:
        # Hardcoded because it's the nature of the format
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Got {roots_count} roots in unpacked light archive structure instead of 1!"
        )

    dirs: list[Path] = []
    files: list[Path] = []
    stack: list[tuple[Path, UnpackedChildren]] = []

    while stack:
        files

    return tuple([], {})


def unpack_identify_element(
    archive: BufferedReader, archive_name: str = unknown_name
) -> tuple[str, UnpackedType]:
    # This function also moves the pointer of the archive to the beginning of the DATA
    archive_name_infix: str = f"Name: {archive_name}{s}"
    initial_pointer_pos: int = archive.tell()
    logs_infix: str = (
        f"{unpack_identify_element.__name__}{s}{archive_name_infix}Pointer: {initial_pointer_pos}{s}"
    )
    tip_postfix: str = f"{s}Tip: Your archive may be invalid"
    l.debug(f"{logs_infix}Identifying element")

    max_len: int = LIGHT_ARCHIVE_UNPACK_EXPECTED_MAX_NAME_BYTES
    name_bytes: bytearray = bytearray()
    type: UnpackedType | None = None
    while True:
        byte: bytes = archive.read(1)

        if byte == _NAME_TERMINATOR_0:
            type = UnpackedType.FILE
            break
        elif byte == _NAME_TERMINATOR_1:
            type = UnpackedType.DIR
            break
        elif not byte:
            raise RuntimeError(
                # EOFs are handled elsewhere
                f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Reached EOF when trying to identify!{tip_postfix}"
            )
        else:
            name_bytes.extend(byte)

        if len(name_bytes) > max_len:
            raise RuntimeError(
                f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Reached max name bytes ({max_len}) when trying to identify!{tip_postfix}"
            )

    name_bytes_len: int = len(name_bytes)
    if not type or not len(name_bytes):
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Failed to identify element!{s}Type: {type}{s}Name Length: {name_bytes_len}"
        )

    # Decoding errors are raised by this function itself
    name: str = name_bytes.decode("utf-8")
    return (name, type)


def unpack_decode_next_int(
    archive: BufferedReader, archive_name: str = unknown_name
) -> int:
    # This function does not need to be fast. For every element in the archive there should be
    # one encoded int that's most likely going to be 1-10 bytes long (very short)
    archive_name_infix: str = f"Name: {archive_name}{s}"
    initial_pointer_pos: int = archive.tell()
    logs_infix: str = (
        f"{unpack_decode_next_int.__name__}{s}{archive_name_infix}Pointer: {initial_pointer_pos}{s}"
    )
    tip_postfix: str = f"{s}Tip: Your archive may be invalid"
    l.debug(f"{logs_infix}Decoding int")

    num_bytes: list[list[int]] = []
    max_len: int = LIGHT_ARCHIVE_UNPACK_EXPECTED_MAX_ENCODED_INT_BYTES
    while True:
        if len(num_bytes) >= max_len:
            raise RuntimeError(
                f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Reached max encoded int length ({max_len}) when trying to decode!{tip_postfix}"
            )

        byte: bytes = archive.read(1)
        if not byte:
            raise RuntimeError(
                f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Reached EOF when decoding int!{tip_postfix}"
            )
        byte_as_int: int = int.from_bytes(byte, byteorder="big", signed=False)
        base2: list[int] = as_base(byte_as_int, 2)
        bits: list[int] = pad_list_from_left(base2, 0, 8)
        bits_length: int = len(bits)
        if bits_length > 8:
            raise RuntimeError(
                f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}Incorrect bits length ({bits_length})"
            )

        usable_bits: list[int] = bits[:7]
        num_bytes.append(usable_bits)

        is_ending: bool = bool(bits[7])
        if is_ending:
            break

    num_binary: list[int] = [bit for b in num_bytes for bit in b]
    num_binary_text: str = "".join(map(str, num_binary))
    num: int = int(num_binary_text, base=2)
    return num
