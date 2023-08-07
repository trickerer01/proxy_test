# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from multiprocessing.dummy import Pool
from random import shuffle
from sys import exc_info
from threading import Lock as ThreadLock
from time import time as ltime, sleep as thread_sleep
from typing import Dict, Set, List

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, ProxyError, ConnectionError

from px_ua import random_useragent
from px_utils import print_s

__DEBUG = False

CHECKLIST_RESPONSE_THRESHOLD = 4.0
PROXY_CHECK_POOL = 20
PROXY_CHECK_TRIES = 5
PROXY_CHECK_UNSUCCESS_LIMIT = 3
PROXY_CHECK_RECHECK_TIME = 2
PROXY_CHECK_TIMEOUT = max(int(CHECKLIST_RESPONSE_THRESHOLD) + 2, 8)

PTYPE_SOCKS = 'socks5'
PTYPE_HTTP = 'http'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
}

RANGE_MARKER = f'$%d-%d$'
BL = '\\'
RANGE_MARKER_RE = RANGE_MARKER.replace("%d", f"({BL}d+)").replace("-", f"{BL}-").replace("$", f"{BL}$")

EXTRA_ACCEPTED_CODES = {403, 503, 509}

target_addr = ''
target_addrs = []  # type: List[str]
results = dict()  # type: Dict[str, _ProxyStruct]
result_lock = ThreadLock()


def set_target_addr(addr: str) -> None:
    from re import fullmatch
    global target_addr
    target_addr = addr
    # form queries if addr contains range
    gs = fullmatch(fr'^.+{RANGE_MARKER_RE}.*?$', target_addr)
    if gs:
        n1, n2 = int(gs.group(1)), int(gs.group(2))
        assert n1 + PROXY_CHECK_TRIES - 1 == n2
        for i in range(PROXY_CHECK_TRIES):
            target_addrs.append(target_addr.replace(RANGE_MARKER % (n1, n2), f'{n1 + i:d}'))
    else:
        for _ in range(PROXY_CHECK_TRIES):
            target_addrs.append(target_addr)
    assert len(target_addrs) == PROXY_CHECK_TRIES


def get_target_addrs() -> List[str]:
    return target_addrs


def prox_key(ptype: str, addr: str) -> str:
    return f'({ptype}) {addr}'


class _ProxyStruct():
    def __init__(self, ptype: str, addr: str, delay: float, accessibility: int, success: bool, start: float) -> None:
        self.ptype = ptype
        self.addr = addr
        self.delay = [delay]
        self.accessibility = [accessibility]
        self.suc_count = 0 if success is False else 1
        self.start = start
        self.done = self.finalized = False
        self.average_delay = self._total_time = 0.0
        with result_lock:
            results[prox_key(ptype, addr)] = self

    def finalize(self) -> None:
        if self.finalized:
            return

        # average delay should only be counted from valid delays
        while len(self.accessibility) < PROXY_CHECK_TRIES:
            self.accessibility.append(0)
        while len(self.delay) < PROXY_CHECK_TRIES:
            self.delay.append(self.delay[-1] if len(self.delay) > 0 else CHECKLIST_RESPONSE_THRESHOLD)

        average_delay = 0.0
        valid_delays = 0
        for val in self.delay:
            average_delay += max(val, 0.0)
            valid_delays += int(val >= 0.0)

        self.average_delay = average_delay / max(valid_delays, 1)
        self._total_time = (ltime() - self.start) - PROXY_CHECK_RECHECK_TIME * (PROXY_CHECK_TRIES - 1)
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
        cs.headers.update(HEADERS.copy())

        for is_socks in (False, True):
            if is_socks is True and cur_prox is not None and cur_prox.finalized is True and cur_prox.accessibility.index(200) >= 0:
                break  # do not check socks proxy if http one is valid

            ptype = PTYPE_SOCKS if is_socks is True else PTYPE_HTTP
            with result_lock:
                if prox_key(ptype, px) in results.keys():
                    continue

            cs.headers.update({'User-Agent': random_useragent()})
            cs.proxies.update({'http': f'{ptype}://{px}', 'https': f'{ptype}://{px}'})

            my_addrs = target_addrs.copy()
            shuffle(my_addrs)
            cur_prox = None
            cur_time = ltime()
            for n in range(PROXY_CHECK_TRIES):
                if n > 0:
                    thread_sleep(float(PROXY_CHECK_RECHECK_TIME))
                timer = ltime()
                try:
                    with cs.request('GET', my_addrs[n], timeout=PROXY_CHECK_TIMEOUT) as r:
                        res_delay = ltime() - timer
                        if r.ok is False or r.status_code != 200:
                            raise HTTPError(response=r)
                        r.raise_for_status()
                        res_acc = 200
                        suc = True
                except (KeyboardInterrupt, SystemExit):
                    raise
                except (HTTPError, ProxyError, ConnectionError) as err:
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
                    if suc is False and ((n + 1) - cur_prox.suc_count) >= PROXY_CHECK_UNSUCCESS_LIMIT:
                        cur_prox.finalize()
                        break
                else:
                    cur_prox = _ProxyStruct(ptype=ptype, addr=px, delay=res_delay, accessibility=res_acc, success=suc, start=cur_time)

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
