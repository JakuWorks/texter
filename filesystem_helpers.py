"""This file contains functions that interact with the filesystem"""

from typing import Collection
import os
from pathlib import Path
from settings import LOGS_ERROR_GENERIC_PREFIX, LOGS_SEPARATOR as s
from Logger import logger as l


def get_children() -> list[str]:
    cwd: str = os.getcwd()
    children: list[str] = os.listdir(cwd)
    return children


def get_selected_files_in_dir(dir: str, names: Collection[str]) -> set[Path]:
    logs_infix: str = f"{get_selected_files_in_dir.__name__}{s}"

    l.debug(f"{logs_infix}Selecting files in dir...{s}main dir: {dir}{s}names: {names}")
    main_dir: Path = Path(dir).resolve()

    main_dir_exists: bool = main_dir.exists(follow_symlinks=False)
    if not main_dir_exists:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{main_dir}{s}Main dir doesn't exist!"
        )
    l.debug(f"{logs_infix}{main_dir}{s}Main dir exists")

    paths: set[Path] = {(main_dir / Path(name)).resolve() for name in names}

    invalid_paths: set[Path] = get_nonexistent_paths(paths)
    if len(invalid_paths) > 0:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{invalid_paths}{s}Files don't exist!"
        )
    l.debug(f"{logs_infix}All files exist{s}")

    unrelated_paths: set[Path] = get_unrelated_paths(main_dir, paths)
    if len(unrelated_paths) > 0:
        raise RuntimeError(
            f"{LOGS_ERROR_GENERIC_PREFIX}{s}{logs_infix}{unrelated_paths}{s}Files aren't relative to main dir! ({main_dir.resolve()})"
        )
    l.debug(f"{logs_infix}All files are relative to main dir")

    paths_count: int = len(paths)
    l.debug(f"{logs_infix}Finished selecting files in dir - got {paths_count}")

    return paths


def get_unrelated_paths(ancestor: Path, paths: Collection[Path]) -> set[Path]:
    unrelated: set[Path] = set()
    for path in paths:
        is_relative_to_main_dir: bool = path.resolve().is_relative_to(ancestor)
        if not is_relative_to_main_dir:
            unrelated.add(path)
    return unrelated


def get_non_children_paths(parent: Path, paths: Collection[Path]) -> set[Path]:
    non_children: set[Path] = set()
    for path in paths:
        is_child: bool = path.parent == parent
        if not is_child:
            non_children.add(path)

    return non_children


# def ensure_children_paths(parent: Path, paths: Collection[Path]) -> None:
#     non_children: set[Path] = get_non_children_paths(parent, paths)


def ensure_file_not_exist(file: Path) -> None:
    if file.exists(follow_symlinks=True):
        l.runtime_error(f"A file already exists at the destination! {file}")


def get_nonexistent_paths(paths: Collection[Path]) -> set[Path]:
    invalid: set[Path] = set()
    for path in paths:
        exists: bool = path.resolve().exists(follow_symlinks=False)
        if not exists:
            invalid.add(path)
    return invalid
