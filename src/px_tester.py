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
from typing import Dict, Set, List, Optional

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, ProxyError, ConnectionError

from px_ua import random_useragent
from px_utils import print_s

__all__ = (
    'check_proxies', 'get_target_addrs', 'get_proxies_amount_factor', 'set_proxies_amount_factor', 'set_target_addr', 'result_lock',
    'results', 'PROXY_CHECK_UNSUCCESS_THRESHOLD', 'PROXY_CHECK_TIMEOUT', 'PROXY_CHECK_RECHECK_TIME', 'PROXY_CHECK_POOL',
    'PROXY_CHECK_TRIES', 'RANGE_MARKER', '__DEBUG',
)

__DEBUG = False

CHECKLIST_RESPONSE_THRESHOLD = 4.0
PROXY_CHECK_POOL = 50
PROXY_CHECK_TRIES = 5
PROXY_CHECK_UNSUCCESS_THRESHOLD = 3
PROXY_CHECK_RECHECK_TIME = 5.0
PROXY_CHECK_TIMEOUT = max(int(CHECKLIST_RESPONSE_THRESHOLD) + 2, 10)

PTYPE_SOCKS = 'socks5'
PTYPE_HTTP = 'http'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
}

RANGE_MARKER = '$%d-%d$'
BL = '\\'
RANGE_MARKER_RE = RANGE_MARKER.replace("%d", f"({BL}d+)").replace("-", f"{BL}-").replace("$", f"{BL}$")

STATUS_OK = 200
STATUS_FORBIDDEN = 403
STATUS_SERVICE_UNAVAILABLE = 503
STATUS_BANDWITH_EXCEEDED = 509
EXTRA_ACCEPTED_CODES = {STATUS_FORBIDDEN, STATUS_SERVICE_UNAVAILABLE, STATUS_BANDWITH_EXCEEDED}

target_addr = ''
proxies_amount_factor = 1
target_addrs: List[str] = []
result_lock = ThreadLock()


class _ProxyStruct():
    def __init__(self, prefix: str, addr: str, delay: float, accessibility: int, success: bool, start: float) -> None:
        self.prefix = prefix
        self.addr = addr
        self.delay = [delay]
        self.accessibility = [accessibility]
        self.suc_count = 0 if success is False else 1
        self.start = start
        self.done = self.finalized = False
        self.average_delay = self._total_time = 0.0
        with result_lock:
            results[addr] = self

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
        return (f'{self.prefix} {self.addr} ({self.average_delay:.3f}s) - {self.suc_count:d}/'
                f'{PROXY_CHECK_TRIES:d} in {self._total_time:.2f}s [{",".join([str(a) for a in self.accessibility])}]')


results: Dict[str, _ProxyStruct] = dict()


def set_target_addr(addr: str) -> None:
    from re import fullmatch
    global target_addr
    target_addr = addr
    # form queries if addr contains range
    gs = fullmatch(fr'^.+{RANGE_MARKER_RE}.*?$', target_addr)
    if gs:
        n1, n2 = int(gs.group(1)), int(gs.group(2))
        q_count = (n2 + 1) - n1
        assert PROXY_CHECK_TRIES <= q_count <= 100
        for i in range(q_count):
            target_addrs.append(target_addr.replace(RANGE_MARKER % (n1, n2), f'{n1 + i:d}'))
    else:
        target_addrs.append(target_addr)


def set_proxies_amount_factor(amount: str) -> None:
    global proxies_amount_factor
    if not amount:
        return
    assert amount in '123456789', f'Invalid proxies amount factor value \'{amount}\'!'
    proxies_amount_factor = int(amount)


def get_target_addrs() -> List[str]:
    return target_addrs


def get_proxies_amount_factor() -> int:
    return proxies_amount_factor


def check_proxy(px: str) -> None:
    prefix, px = tuple(px.split(' ', 1))
    with Session() as cs:
        cs.keep_alive = True
        cs.adapters.clear()
        cs.mount('http://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.mount('https://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.headers.update(HEADERS.copy())
        cs.headers.update({'User-Agent': random_useragent()})
        cs.proxies.update({'all': px})

        my_addrs = target_addrs.copy()
        shuffle(my_addrs)
        del my_addrs[PROXY_CHECK_TRIES:]
        cur_prox: Optional[_ProxyStruct] = None
        cur_time = ltime()
        for n in range(PROXY_CHECK_TRIES):
            if n > 0:
                thread_sleep(PROXY_CHECK_RECHECK_TIME)
            timer = ltime()
            try:
                with cs.request('GET', my_addrs[n], timeout=PROXY_CHECK_TIMEOUT) as r:
                    res_delay = ltime() - timer
                    if r.ok is False or r.status_code != STATUS_OK:
                        raise HTTPError(response=r)
                    r.raise_for_status()
                    res_acc = STATUS_OK
                    suc = True
            except (KeyboardInterrupt, SystemExit):
                raise
            except (HTTPError, ProxyError, ConnectionError) as err:
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
                cur_prox = _ProxyStruct(prefix=prefix, addr=px, delay=res_delay, accessibility=res_acc, success=suc, start=cur_time)

        if cur_prox:
            if cur_prox.finalized is False:
                cur_prox.finalize()
        else:
            print_s(f'error214 - proxy {px} not found - not finalized')


def check_proxies(proxlist: Set[str]) -> None:
    pool = Pool(PROXY_CHECK_POOL)
    pool.map_async(check_proxy, proxlist, 1)
    pool.close()
    pool.join()

#
#
#########################################
