# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from threading import Lock as ThreadLock


append_lock = ThreadLock()
print_lock = ThreadLock()

useragent = 'Mozilla/5.0 (X11; Linux i686; rv:68.9) Gecko/20100101 Goanna/4.8 Firefox/68.9'


def s_print(msg) -> None:
    with print_lock:
        print(msg)


def module_name_short(module) -> str:
    return module.__name__[module.__name__.find('px_grab_') + 8:]

#
#
#########################################
