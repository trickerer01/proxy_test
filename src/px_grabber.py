# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from threading import Thread

from module import (
    px_grab_fate as pg_fate,
    px_grab_freeproxy as pg_fp,
    px_grab_freeproxylist as pg_fpl,
    px_grab_hidemyna as pg_hid,
    px_grab_proxylist as pg_pl,
    px_grab_txt as pg_txt,
    px_grab_spys as pg_sps,
)
from px_utils import module_name_short

MODULES = (
    pg_fate,
    pg_fp,
    pg_fpl,
    pg_hid,
    pg_pl,
    pg_txt,
    pg_sps,
)


def fetch_all(amount_factor: int) -> str:
    try:
        grab_threads = list()
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
