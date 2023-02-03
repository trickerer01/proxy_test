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

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, ProxyError

from px_utils import s_print, useragent

__DEBUG = False

CHECKLIST_RESPONSE_THRESHOLD = 4.0

PROXY_CHECK_POOL = 100
PROXY_CHECK_TRIES = 5
PROXY_CHECK_UNSUCCESS_LIMIT = 3
PROXY_CHECK_RECHECK_TIME = 2
PROXY_CHECK_TIMEOUT = max(int(CHECKLIST_RESPONSE_THRESHOLD) + 2, 5)

PTYPE_SOCKS = 'socks'
PTYPE_HTTP = 'http'

default_headers = {'User-Agent': useragent}

target_addr = ''

results = {}

result_lock = ThreadLock()


class _ProxyStruct():
    def __init__(self, ptype: str, addr: str, delay: float, accessibility: int, success: bool) -> None:
        global results

        self.ptype = ptype
        self._addr = addr
        self.delay = [delay]
        self.accessibility = [accessibility]
        self.suc_count = 0 if success is False else 1

        self.done = False
        self.finalized = False

        self.average_delay = 0.0

        self.start_time = 0.0
        self._total_time = 0.0

        results[f'({ptype}) {addr}'] = self

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
        return (f'({self.ptype}) {self._addr} ({self.average_delay:.3f}s) - {self.suc_count:d}/'
                f'{PROXY_CHECK_TRIES:d} in {self._total_time:.2f}s [{", ".join([str(a) for a in self.accessibility])}]')


def check_proxy(px: str) -> None:
    global results

    if px in results.keys():
        return

    cur_prox = None
    with Session() as cs:
        for is_socks in [False, True]:
            if is_socks and cur_prox is not None and cur_prox.finalized is True and cur_prox.accessibility.index(200) >= 0:
                break  # do not check socks proxy if http one is valid

            ptype = PTYPE_SOCKS if is_socks is True else PTYPE_HTTP
            cs.keep_alive = True
            cs.adapters.clear()
            cs.mount('http://', HTTPAdapter(pool_maxsize=1, max_retries=0))
            cs.mount('https://', HTTPAdapter(pool_maxsize=1, max_retries=0))
            cs.headers.update(default_headers.copy())
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
                    if err.response.status_code == 503:
                        # res_delay = -1.0
                        res_acc = 503
                        suc = True
                        pass
                    elif err.response.status_code == 509:
                        # res_delay = -1.0
                        res_acc = 509
                        suc = True
                        pass
                    elif __DEBUG:
                        s_print(f'{px} - error {str(exc_info()[0])}: {str(exc_info()[1])}')
                except Exception:
                    res_delay = -1.0
                    res_acc = 0
                    suc = False
                    if __DEBUG:
                        s_print(f'{px} - error {str(exc_info()[0])}: {str(exc_info()[1])}')

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
                    with result_lock:
                        cur_prox = _ProxyStruct(ptype=ptype, addr=px, delay=res_delay, accessibility=res_acc, success=suc)
                        cur_prox.start_time = total_timer

            if cur_prox:
                cur_prox.finalize()
            else:
                s_print(f'error214 - proxy {px} not found - not finalized')


def check_proxies(proxlist: set) -> None:

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
