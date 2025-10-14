# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import random
import sys
import time
from multiprocessing.dummy import Pool
from threading import Lock as ThreadLock

from fake_useragent import FakeUserAgent
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from px_defs import __DEBUG, ADDR_TYPE_HTTP, ADDR_TYPE_HTTPS, DEFAULT_HEADERS, EXTRA_ACCEPTED_CODES, STATUS_OK, Config, ProxyStruct
from px_utils import print_s

__all__ = ('check_proxies', 'result_lock', 'results')

us_generator = FakeUserAgent(fallback='Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.7 Firefox/102.0 PaleMoon/33.3.1')
result_lock = ThreadLock()
results: dict[str, ProxyStruct] = {}


def check_proxy(px: str) -> None:
    px = px if ' ' in px else f'[??] {px}'
    prefix, px = tuple(px.split(' ', 1))
    with Session() as cs:
        cs.keep_alive = True
        cs.adapters.clear()
        cs.mount(ADDR_TYPE_HTTP, HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.mount(ADDR_TYPE_HTTPS, HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.headers.update(DEFAULT_HEADERS.copy())
        cs.headers.update({'User-Agent': us_generator.ff})
        cs.proxies.update({'all': px})

        my_addrs = list(Config.targets)
        random.shuffle(my_addrs)
        del my_addrs[Config.tries_count:]
        cur_prox: ProxyStruct | None = None
        cur_time = time.time()
        for n in range(Config.tries_count):
            if n > 0:
                time.sleep(float(Config.delay))
            timer = time.time()
            try:
                with cs.request('GET', my_addrs[n % len(my_addrs)], timeout=float(Config.timeout)) as r:
                    if r.ok is False or r.status_code != STATUS_OK:
                        raise RequestException(response=r)
                    r.raise_for_status()
                    res_acc = STATUS_OK
                    suc = True
            except (KeyboardInterrupt, SystemExit):
                raise
            except RequestException as err:
                res_acc = -1
                suc = False
                if err.response and err.response.status_code in EXTRA_ACCEPTED_CODES:
                    res_acc = err.response.status_code
                    suc = True
                elif __DEBUG:
                    print_s(f'{px} - error {sys.exc_info()[0]!s}: {sys.exc_info()[1]!s}')
            except Exception:
                res_acc = -2
                suc = False
                if __DEBUG:
                    print_s(f'{px} - error {sys.exc_info()[0]!s}: {sys.exc_info()[1]!s}')
            finally:
                res_delay = time.time() - timer

            if cur_prox is not None:
                if suc:
                    cur_prox.delay.append(res_delay)
                cur_prox.accessibility.append(res_acc)
                cur_prox.suc_count += 1 if suc is True else 0
                if suc is False and n + 1 - cur_prox.suc_count >= Config.unsuccess_threshold:
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


def check_proxies(proxlist: set[str]) -> None:
    proxy_list = list(proxlist)
    random.shuffle(proxy_list)
    pool = Pool(Config.poolsize)
    pool.map_async(check_proxy, proxy_list, 1)
    pool.close()
    pool.join()

#
#
#########################################
