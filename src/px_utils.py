# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from threading import Lock as ThreadLock

print_lock = ThreadLock()


def print_s(msg: str) -> None:
    with print_lock:
        print(msg)


def module_name_short(module) -> str:
    return module.__name__[module.__name__.find('px_grab_') + 8:]

#
#
#########################################
