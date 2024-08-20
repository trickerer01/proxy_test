# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from threading import Lock as ThreadLock

from px_defs import SLASH, BL

__all__ = ('print_s', 'unquote', 'normalize_path', 'module_name_short')

print_lock = ThreadLock()


def print_s(msg: str) -> None:
    with print_lock:
        print(msg)


def unquote(tag: str) -> str:
    return tag.strip('"\'')


def normalize_path(basepath: str, append_slash=True) -> str:
    normalized_path = basepath.replace(BL, SLASH)
    need_slash = append_slash is True and len(normalized_path) != 0 and normalized_path[-1] != SLASH
    return f'{normalized_path}{SLASH}' if need_slash else normalized_path


def module_name_short(module) -> str:
    return module.__name__[module.__name__.find('px_grab_') + 8:]

#
#
#########################################
