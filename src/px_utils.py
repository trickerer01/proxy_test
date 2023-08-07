# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from threading import Lock as ThreadLock
from types import ModuleType

print_lock = ThreadLock()


def print_s(msg: str) -> None:
    with print_lock:
        print(msg)


def module_name_short(module: ModuleType) -> str:
    return module.__name__[module.__name__.find('px_grab_') + 8:]

#
#
#########################################
