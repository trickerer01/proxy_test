# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from os import path, remove as remove_file
from sys import argv
from threading import Thread
from time import time as ltime, sleep as thread_sleep
from urllib.parse import urlparse

from requests import Session
from requests.exceptions import HTTPError, ConnectionError

from px_builder import build_proxy_list
from px_grabber import fetch_all, MODULES
from px_tester import (
    check_proxies, get_target_addrs, set_target_addr, result_lock, results, PROXY_CHECK_UNSUCCESS_THRESHOLD, PROXY_CHECK_TIMEOUT,
    PROXY_CHECK_RECHECK_TIME, PROXY_CHECK_POOL, PROXY_CHECK_TRIES, RANGE_MARKER,
)
from px_utils import print_s, module_name_short

__all__ = ()

out_file = '!px_list_results.txt'

exiting = False


def _exit(msg: str, code: int) -> None:
    print_s(f'{msg} (code: {code:d})')
    input('\nPress <Enter> to quit...')
    raise SystemExit


def parse_target() -> None:
    if len(argv) > 2:
        _exit('\nError. Usage: px_test TARGET_ADDRESS', -2)
    elif len(argv) < 2:
        set_target_addr(input('\nEnter web address to test: '))
    else:
        set_target_addr(argv[1])

    if len(get_target_addrs()) < 4:
        _exit('\nError. Usage: px_test TARGET_ADDRESS', -3)

    try:
        urlparse(get_target_addrs()[0])
    except Exception:
        print(f'\nInvalid address \'{get_target_addrs()}\'!')
        raise

    print('\n'.join(get_target_addrs()) if get_target_addrs()[0] != get_target_addrs()[1] else get_target_addrs()[0])

    with Session() as s:
        try:
            r = s.request('HEAD', get_target_addrs()[0], timeout=5)
            r.raise_for_status()
            r.close()
        except HTTPError as err:
            if err.response.status_code == 404:
                _exit('\nError. Not found', -4)
        except ConnectionError as err:
            if str(err).find('getaddrinfo failed') >= 0:
                _exit('\nError. Unable to get address info', -5)
        except Exception as err:
            print(f'\nAddress test result: {str(err)}')


def cycle_results() -> None:
    try:
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
                        print(str(res))

    except Exception as err:
        raise err


def run_main() -> None:
    global exiting

    print(f'\nEnabled modules: {" ".join(module_name_short(modul) for modul in MODULES)}')
    print(f'Range marker: \'{RANGE_MARKER}\', {PROXY_CHECK_TRIES} queries. Example: \'https://example.com/$2-6$\'')

    parse_target()

    start_time = ltime()

    print('\nFetching proxy lists...')
    all_prox_str = fetch_all()

    if len(all_prox_str) <= 1:
        print('\nNo proxies found, aborting...')
        return

    print('\nBuilding checklist...')
    all_prox_set = build_proxy_list(all_prox_str)

    proxy_check_time = (PROXY_CHECK_TIMEOUT + PROXY_CHECK_RECHECK_TIME) * (len(all_prox_set) // PROXY_CHECK_POOL + 1) * PROXY_CHECK_TRIES
    print(f'\nChecking {len(all_prox_set):d} proxies ({PROXY_CHECK_TRIES:d} queries). This may take {proxy_check_time:d}+ seconds')

    print('\nTimed List:')
    res_display_queue = Thread(target=cycle_results, daemon=True)
    res_display_queue.start()

    check_proxies(all_prox_set)

    end_time = ltime()

    exiting = True
    res_display_queue.join()

    print('\nCompleted. Filtering out useless entries...')
    proxy_finals = list(reversed(sorted(reversed(sorted(results.values(), key=lambda ures: ures.addr)), key=lambda ures: ures.suc_count)))
    oldlen = len(proxy_finals)
    for i in reversed(range(len(proxy_finals))):  # type: int
        res = proxy_finals[i]
        if sum(res.accessibility) == 0 or res.suc_count <= (PROXY_CHECK_TRIES - PROXY_CHECK_UNSUCCESS_THRESHOLD):
            del proxy_finals[i]
            continue
        if not res.finalized:
            res.finalize()

    print(f'Filtered {oldlen - len(proxy_finals):d} / {oldlen:d} entries.')
    print(f'\nAll checked ({end_time - start_time:.3f}s). Sorted List ({len(proxy_finals):d}):')
    print(' ' + '\n '.join(str(res) for res in proxy_finals))

    if len(proxy_finals) > 0:
        if path.isfile(out_file):
            remove_file(out_file)
        with open(out_file, 'wt', encoding='utf8') as ofile:
            ofile.writelines('px_test results:\n' + '\n'.join(str(res) for res in proxy_finals))


if __name__ == '__main__':
    run_main()
    input('\nPress <Enter> to quit...')

#
#
#########################################
