# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from datetime import datetime
from os import path, makedirs
from threading import Thread
from time import sleep as thread_sleep
from typing import Sequence

from px_builder import build_proxy_list
from px_cmdargs import prepare_arglist, HelpPrintExitException
from px_defs import (
    Config, UTF8, PROXY_CHECK_POOL_DEFAULT, PROXY_CHECK_TRIES, PROXY_CHECK_UNSUCCESS_THRESHOLD, PROXY_CHECK_RE_TIME, PROXY_CHECK_TIMEOUT,
    OUTPUT_FILE_NAME,
)
from px_grabber import fetch_all, MODULES
from px_tester import check_proxies, result_lock, results
from px_utils import module_name_short, print_s

__all__ = ('main_sync',)

exiting = False


def cycle_results() -> None:
    while True:
        if exiting:
            break
        thread_sleep(0.25)
        with result_lock:
            for res in results.values():
                if res.finalized and not res.done:
                    res.done = True
                    if sum(res.accessibility) == 0 or res.suc_count < PROXY_CHECK_UNSUCCESS_THRESHOLD:
                        continue
                    print_s(str(res))


def run_main(args: Sequence[str]) -> None:
    global exiting

    try:
        arglist = prepare_arglist(args)
        Config.read(arglist)
    except HelpPrintExitException:
        return

    start_datetime = datetime.now()
    start_date = start_datetime.strftime("%d-%m-%Y %H:%M:%S")

    print(f'STARTED AT {start_date}')
    print(f'\n{len(Config.targets)} targets parsed')
    if isinstance(Config.proxies, int):
        print(f'\nFetching proxy lists. Enabled modules: {" ".join(module_name_short(modul) for modul in MODULES)}')
        all_prox_str = fetch_all(int(Config.proxies))
        if not all_prox_str:
            print('\nNo proxies found, aborting...')
            return
        print('\nBuilding checklist...')
        Config.proxies = build_proxy_list(all_prox_str)
    else:
        print(f'{len(Config.proxies)} proxies parsed')

    proxy_check_time = int((PROXY_CHECK_TIMEOUT + PROXY_CHECK_RE_TIME) * (len(Config.proxies) // Config.poolsize + 1) * PROXY_CHECK_TRIES)
    print(f'\nChecking {len(Config.proxies):d} proxies, {PROXY_CHECK_TRIES:d} queries each, {PROXY_CHECK_POOL_DEFAULT:d} threads. '
          f'This may take {proxy_check_time:d}+ seconds')

    print('\nTimed List:')
    timed_results_thread = Thread(target=cycle_results, daemon=True)
    timed_results_thread.start()

    check_proxies(Config.proxies)

    exiting = True
    timed_results_thread.join()

    end_datetime = datetime.now()
    end_date = end_datetime.strftime("%d-%m-%Y %H:%M:%S")

    print(f'\nFINISHED AT {end_date}')
    print('\nCompleted. Filtering out useless entries...')
    proxy_finals = list(reversed(sorted(reversed(sorted(results.values(), key=lambda ures: ures.addr)), key=lambda ures: ures.suc_count)))
    oldlen = len(proxy_finals)
    i: int
    for i in reversed(range(len(proxy_finals))):
        res = proxy_finals[i]
        if sum(res.accessibility) == 0 or res.suc_count <= (PROXY_CHECK_TRIES - PROXY_CHECK_UNSUCCESS_THRESHOLD):
            del proxy_finals[i]
            continue
        if not res.finalized:
            res.finalize()

    print(f'Filtered {oldlen - len(proxy_finals):d} / {oldlen:d} entries.')
    print(f'\nAll checked ({(end_datetime - start_datetime).total_seconds():.1f}s). Sorted List ({len(proxy_finals):d}):')
    print(' ' + '\n '.join(str(res) for res in proxy_finals))

    if len(proxy_finals) > 0:
        if not path.isdir(Config.dest):
            makedirs(Config.dest)
        with open(f'{Config.dest}{OUTPUT_FILE_NAME}', 'at', encoding=UTF8) as ofile:
            ofile.writelines(f'px_test results {start_date} - {end_date} ({next(iter(Config.targets), "")}...):\n'
                             + '\n'.join(str(res) for res in proxy_finals))


def main_sync(args: Sequence[str]) -> None:
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'

    try:
        run_main(args)
    except (KeyboardInterrupt, SystemExit):
        print('Warning: catched KeyboardInterrupt/SystemExit...')


if __name__ == '__main__':
    main_sync(sys.argv[1:])
    exit(0)

#
#
#########################################
