# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from multiprocessing.dummy import Pool
from sys import exc_info
from threading import Lock as ThreadLock
from time import time as ltime, sleep as thread_sleep
from typing import Dict, Set
from urllib.parse import urlparse

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, ProxyError

from px_ua import random_useragent
from px_utils import print_s

__DEBUG = False

CHECKLIST_RESPONSE_THRESHOLD = 4.0

PROXY_CHECK_POOL = 20
PROXY_CHECK_TRIES = 5
PROXY_CHECK_UNSUCCESS_LIMIT = 3
PROXY_CHECK_RECHECK_TIME = 2
PROXY_CHECK_TIMEOUT = max(int(CHECKLIST_RESPONSE_THRESHOLD) + 2, 5)

PTYPE_SOCKS = 'socks5'
PTYPE_HTTP = 'http'

EXTRA_ACCEPTED_CODES = {403, 503, 509}

target_addr = ''
target_host = ''

results = {}  # type: Dict[str, _ProxyStruct]

result_lock = ThreadLock()


def set_target_addr(addr: str) -> None:
    global target_addr
    global target_host
    target_addr = addr
    target_host = urlparse(addr).netloc


def get_target_addr() -> str:
    return target_addr


def prox_key(ptype: str, addr: str) -> str:
    return f'({ptype}) {addr}'


class _ProxyStruct():
    def __init__(self, ptype: str, addr: str, delay: float, accessibility: int, success: bool) -> None:
        global results

        self.ptype = ptype
        self.addr = addr
        self.delay = [delay]
        self.accessibility = [accessibility]
        self.suc_count = 0 if success is False else 1

        self.done = False
        self.finalized = False

        self.average_delay = 0.0

        self.start_time = 0.0
        self._total_time = 0.0

        with result_lock:
            results[prox_key(ptype, addr)] = self

    def finalize(self) -> None:
        # average delay should only be counted from valid delays
        average_delay = 0.0

        valid_delays = 0
        for val in self.delay:
            average_delay += max(val, 0.0)
            valid_delays += 1 if val >= 0.0 else 0

        average_delay = average_delay / max(valid_delays, 1)

        self.average_delay = average_delay

        self._total_time = ltime() - self.start_time

        self.finalized = True

    def __str__(self) -> str:
        return (f'({self.ptype}) {self.addr} ({self.average_delay:.3f}s) - {self.suc_count:d}/'
                f'{PROXY_CHECK_TRIES:d} in {self._total_time:.2f}s [{",".join([str(a) for a in self.accessibility])}]')


def check_proxy(px: str) -> None:
    cur_prox = None
    with Session() as cs:
        cs.keep_alive = True
        cs.adapters.clear()
        cs.mount('http://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.mount('https://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        headers = {'Host': target_host,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'DNT': '1',
                   'Connection': 'keep-alive'}
        cs.headers.update(headers.copy())
        for is_socks in [False, True]:
            if is_socks is True and cur_prox is not None and cur_prox.finalized is True and cur_prox.accessibility.index(200) >= 0:
                break  # do not check socks proxy if http one is valid

            ptype = PTYPE_SOCKS if is_socks is True else PTYPE_HTTP

            if prox_key(ptype, px) in results.keys():
                continue

            cs.headers.update({'User-Agent': random_useragent()})
            cs.proxies.update({'all': f'{ptype}://{px}'})

            cur_prox = None
            total_timer = ltime()
            for n in range(PROXY_CHECK_TRIES):
                if n > 0:
                    thread_sleep(float(PROXY_CHECK_RECHECK_TIME))
                timer = ltime()
                try:
                    with cs.request(method='GET', url=target_addr, timeout=PROXY_CHECK_TIMEOUT) as r:
                        res_delay = ltime() - timer
                        if r.ok is False:
                            raise HTTPError(response=r)
                        r.raise_for_status()
                        res_acc = 200
                        suc = True
                except (KeyboardInterrupt, SystemExit) as err:
                    raise err
                except (HTTPError, ProxyError) as err:
                    res_delay = ltime() - timer
                    res_acc = 0
                    suc = False
                    if err.response.status_code in EXTRA_ACCEPTED_CODES:
                        res_acc = err.response.status_code
                        suc = True
                    elif __DEBUG:
                        print_s(f'{px} - error {str(exc_info()[0])}: {str(exc_info()[1])}')
                except Exception:
                    res_acc = 0
                    suc = False
                    if __DEBUG:
                        print_s(f'{px} - error {str(exc_info()[0])}: {str(exc_info()[1])}')

                if cur_prox is not None:
                    cur_prox.delay.append(res_delay)
                    cur_prox.accessibility.append(res_acc)
                    cur_prox.suc_count += 1 if suc is True else 0
                    # will be filtered out anyways
                    if not suc and ((n + 1) - cur_prox.suc_count >= PROXY_CHECK_UNSUCCESS_LIMIT):
                        # s_print(('%s - unsuccess count reached!' % px))
                        cur_prox.finalize()
                        break
                else:
                    cur_prox = _ProxyStruct(ptype=ptype, addr=px, delay=res_delay, accessibility=res_acc, success=suc)
                    cur_prox.start_time = total_timer

            if cur_prox:
                cur_prox.finalize()
            else:
                print_s(f'error214 - proxy {px} not found - not finalized')


def check_proxies(proxlist: Set[str]) -> None:

    try:
        pool = Pool(PROXY_CHECK_POOL)
        pool.map_async(check_proxy, proxlist, 1)
        pool.close()
        pool.join()

    except Exception as err:
        raise err

#
#
#########################################
