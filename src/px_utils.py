# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from threading import Lock as ThreadLock

print_lock = ThreadLock()

useragent = 'Mozilla/5.0 (X11; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0'


def print_s(msg: str) -> None:
    with print_lock:
        print(msg)


def module_name_short(module) -> str:
    return module.__name__[module.__name__.find('px_grab_') + 8:]

#
#
#########################################
