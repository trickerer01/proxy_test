# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from os import path, remove as remove_file
from re import search as re_search
from sys import argv
from threading import Thread
from time import time as ltime, sleep as thread_sleep

from requests import Session
from requests.exceptions import HTTPError, ConnectionError

import px_builder
import px_grabber
import px_tester
import px_utils

out_file_raw = '!px_list_raw.txt'
out_file = '!px_list_results.txt'

exiting = False


def _exit(msg: str, code: int):
    px_utils.s_print(msg + (' (code: %d)' % code))
    input('\nPress <Enter> to quit...')
    raise SystemExit


def parse_target():
    global out_file

    if len(argv) > 2:
        _exit('\nError. Usage: px_test TARGET_ADDRESS', code=-2)
    elif len(argv) < 2:
        px_tester.target_addr = input('\nEnter web address to test: ')
    else:
        px_tester.target_addr = argv[1]

    if len(px_tester.target_addr) < 4:
        _exit('\nError. Usage: px_test TARGET_ADDRESS', code=-3)

    sitename = str(re_search(r'(?:https?://)?([^/]+)/?', px_tester.target_addr).group(1))
    print(sitename)

    px_tester.target_addr = 'http://' + px_tester.target_addr + '/'

    with Session() as s:
        try:
            r = s.request('HEAD', px_tester.target_addr, timeout=5)
            r.raise_for_status()
            r.close()
        except HTTPError as err:
            if err.response.status_code == 404:
                _exit('\nError. Not found', -4)
        except ConnectionError as err:
            if str(err).find('getaddrinfo failed') >= 0:
                _exit('\nError. Unable to get address info', -5)
        except Exception as err:
            print('\nAddress test result: %s' % str(err))


def cycle_results():

    try:
        while True:
            if exiting:
                break

            thread_sleep(0.25)

            with px_tester.result_lock:
                for res in px_tester.results.values():
                    if res.finalized and not res.done:
                        res.done = True
                        if sum(res.accessibility) == 0 or res.suc_count < px_tester.PROXY_CHECK_UNSUCCESS_LIMIT:
                            continue
                        print(str(res))

    except Exception as err:
        raise err


def run_main():
    global exiting

    print('\nEnabled modules:')
    print(''.join([px_utils.module_name_short(modul) + ' ' for modul in px_grabber.MODULES]))

    parse_target()

    start_time = ltime()

    print('\nFetching proxy lists...')
    all_prox_str = px_grabber.fetch_all()

    if len(all_prox_str) <= 1:
        print('\nNo proxies found, aborting...')
        return

    # print('\nSaving proxy list...')
    # px_utils.storefile(out_file_raw, all_prox_str)

    print('\nBuilding checklist...')
    all_prox_set = px_builder.build_proxy_list(all_prox_str)

    proxy_check_time = \
        (px_tester.PROXY_CHECK_TIMEOUT + px_tester.PROXY_CHECK_RECHECK_TIME) * (int(len(all_prox_set) / px_tester.PROXY_CHECK_POOL) + 1)
    print(('\nChecking %d proxies (%d queries). This may take more than %d seconds' %
           (len(all_prox_set), px_tester.PROXY_CHECK_TRIES, proxy_check_time * px_tester.PROXY_CHECK_TRIES * 2)))

    print('\nTimed List:')
    res_display_queue = Thread(target=cycle_results, daemon=True)
    res_display_queue.start()

    px_tester.check_proxies(all_prox_set)

    end_time = ltime()

    exiting = True
    res_display_queue.join()

    print('\nCompleted. Filtering out useless entries...')

    results = list(px_tester.results.values())

    oldlen = len(results)
    i = 0
    while i < len(results):
        res = results[i]
        if sum(res.accessibility) == 0:
            results.pop(i)
            continue
        if res.average_access == 0 and not res.finalized:
            res.finalize()
        i += 1
    print(('Filtered %d / %d entries.\n\nSorting...' % (oldlen - len(results), oldlen)))

    t_results = []
    while True:
        suc_max = -1
        suc_idx = -1
        i = 0
        while i < len(results):
            res_str = str(results[i])
            if results[i] not in t_results:
                suc_count = int(str(re_search(r'(\d+)/', res_str).group(1)))
                if suc_count > suc_max:
                    suc_max = suc_count
                    suc_idx = i
            i += 1
        if suc_max < (px_tester.PROXY_CHECK_TRIES - px_tester.PROXY_CHECK_UNSUCCESS_LIMIT):
            break
        t_results.append(results[suc_idx])
    results = t_results

    print(('\nAll checked (%.fs). Sorted List (%d):' % (end_time - start_time, len(results))))
    for res in results:
        print((' ' * 4 + str(res)))

    if path.isfile(out_file):
        remove_file(out_file)

    if len(results) > 0:
        with open(out_file, 'w') as ofile:
            ofile.write('px_test results:\n')
            for res in results:
                ofile.write(str(res) + '\n')


if __name__ == '__main__':
    run_main()
    input('\nPress <Enter> to quit...')

#
#
#########################################
