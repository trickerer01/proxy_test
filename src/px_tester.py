# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from multiprocessing.dummy import Pool
from random import shuffle
from sys import exc_info
from threading import Lock as ThreadLock
from time import time as ltime, sleep as thread_sleep
from typing import Dict, Set, Optional

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from px_defs import (
    Config, ProxyStruct, __DEBUG, DEFAULT_HEADERS, STATUS_OK, EXTRA_ACCEPTED_CODES, PROXY_CHECK_TRIES, PROXY_CHECK_UNSUCCESS_THRESHOLD,
    PROXY_CHECK_RE_TIME, PROXY_CHECK_TIMEOUT,
)
from px_ua import random_useragent
from px_utils import print_s

__all__ = ('check_proxies', 'result_lock', 'results')

result_lock = ThreadLock()
results: Dict[str, ProxyStruct] = dict()


def check_proxy(px: str) -> None:
    prefix, px = tuple(px.split(' ', 1)) if ' ' in px else ('[??]', px)
    with Session() as cs:
        cs.keep_alive = True
        cs.adapters.clear()
        cs.mount('http://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.mount('https://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.headers.update(DEFAULT_HEADERS.copy())
        cs.headers.update({'User-Agent': random_useragent()})
        cs.proxies.update({'all': px})

        my_addrs = list(Config.targets)
        while len(my_addrs) < PROXY_CHECK_TRIES:
            my_addrs.append(my_addrs[len(my_addrs) - len(Config.targets)])
        shuffle(my_addrs)
        del my_addrs[PROXY_CHECK_TRIES:]
        cur_prox: Optional[ProxyStruct] = None
        cur_time = ltime()
        for n in range(PROXY_CHECK_TRIES):
            if n > 0:
                thread_sleep(PROXY_CHECK_RE_TIME)
            timer = ltime()
            try:
                with cs.request('GET', my_addrs[n], timeout=PROXY_CHECK_TIMEOUT) as r:
                    res_delay = ltime() - timer
                    if r.ok is False or r.status_code != STATUS_OK:
                        raise RequestException(response=r)
                    r.raise_for_status()
                    res_acc = STATUS_OK
                    suc = True
            except (KeyboardInterrupt, SystemExit):
                raise
            except RequestException as err:
                res_delay = ltime() - timer
                res_acc = -1
                suc = False
                if err.response and err.response.status_code in EXTRA_ACCEPTED_CODES:
                    res_acc = err.response.status_code
                    suc = True
                elif __DEBUG:
                    print_s(f'{px} - error {str(exc_info()[0])}: {str(exc_info()[1])}')
            except Exception:
                res_delay = ltime() - timer
                res_acc = -2
                suc = False
                if __DEBUG:
                    print_s(f'{px} - error {str(exc_info()[0])}: {str(exc_info()[1])}')

            if cur_prox is not None:
                cur_prox.delay.append(res_delay)
                cur_prox.accessibility.append(res_acc)
                cur_prox.suc_count += 1 if suc is True else 0
                if suc is False and n + 1 - cur_prox.suc_count >= PROXY_CHECK_UNSUCCESS_THRESHOLD:
                    cur_prox.finalize()
                    break
            else:
                cur_prox = ProxyStruct(prefix=prefix, addr=px, delay=res_delay, accessibility=res_acc, success=suc, start=cur_time)
                with result_lock:
                    results[px] = cur_prox

        if cur_prox:
            if cur_prox.finalized is False:
                cur_prox.finalize()
        else:
            print_s(f'error214 - proxy {px} not found - not finalized')


def check_proxies(proxlist: Set[str]) -> None:
    pool = Pool(Config.poolsize)
    pool.map_async(check_proxy, proxlist, 1)
    pool.close()
    pool.join()

#
#
#########################################
