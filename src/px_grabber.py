# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from threading import Thread

from module import (
    px_grab_fate,
    px_grab_freeproxy,
    px_grab_freeproxylist,
    px_grab_hidemyna,
    px_grab_proxylist,
    px_grab_spys,
    px_grab_txt,
)
from px_utils import module_name_short

MODULES = (
    px_grab_fate,
    px_grab_freeproxy,
    px_grab_freeproxylist,
    px_grab_hidemyna,
    px_grab_proxylist,
    px_grab_spys,
    px_grab_txt,
)


def fetch_all(amount_factor: int) -> str:
    try:
        grab_threads: list[Thread] = []
        for modul in MODULES:
            if not modul.ENABLED:
                continue
            grab_threads.append(Thread(target=modul.grab_proxies, args=(amount_factor,)))
            grab_threads[-1].start()

        for thread in grab_threads:
            thread.join()

        checklist = ''
        for modul in MODULES:
            if len(modul.my_result) == 0:
                print(f'{module_name_short(modul)} returned empty result!')
            else:
                checklist += modul.my_result

        return checklist
    except Exception as err:
        raise err

#
#
#########################################
