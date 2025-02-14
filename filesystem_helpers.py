"""This file contains functions that interact with the filesystem"""
import os


def get_children() -> list[str]:
    cwd: str = os.getcwd()
    children: list[str] = os.listdir(cwd)
    return children