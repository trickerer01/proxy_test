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

from px_utils import s_print

__DEBUG = False

CHECKLIST_RESPONSE_THRESHOLD = 4.0

PROXY_CHECK_POOL = 100
PROXY_CHECK_TRIES = 5
PROXY_CHECK_UNSUCCESS_LIMIT = 2
PROXY_CHECK_RECHECK_TIME = 2
PROXY_CHECK_TIMEOUT = max(int(CHECKLIST_RESPONSE_THRESHOLD) + 2, 5)

useragent = 'Mozilla/5.0 (X11; Linux i686; rv:68.9) Gecko/20100101 Goanna/4.8 Firefox/68.9'
default_headers = {'User-Agent': useragent}

target_addr = ''

results = {}

result_lock = ThreadLock()


class _ProxyStruct():
    def __init__(self, addr='', delay=0.0, accessibility=0, success=False):
        global results

        self._addr = addr
        self.delay = [delay]
        self.accessibility = [accessibility]
        self.suc_count = 0 if success is False else 1

        self.done = False
        self.finalized = False

        self.average_delay = 0.0
        self.average_access = 0

        self.start_time = 0.0
        self._total_time = 0.0

        results[addr] = self

    def finalize(self):
        # average delay should only be counted from valid delays
        average_delay = 0.0
        average_access = 0

        valid_delays = 0
        for val in self.delay:
            average_delay += max(val, 0.0)
            valid_delays += 1 if val >= 0.0 else 0
        for val in self.accessibility:
            if val == 503:
                average_access = 503 * PROXY_CHECK_TRIES
                break
            elif val == 509:
                average_access = 509 * PROXY_CHECK_TRIES
                break
            else:
                average_access += val

        average_delay = average_delay / max(valid_delays, 1)
        average_access = int(average_access / PROXY_CHECK_TRIES)

        if 100 < average_access < 503:
            average_access = 503

        self.average_delay = average_delay
        self.average_access = average_access

        self._total_time = ltime() - self.start_time

        self.finalized = True

    def __str__(self):
        return '%s (%.3f ms) - %d%% (%d/%d) in %.2fs' % (self._addr, self.average_delay, self.average_access,
                                                         self.suc_count, PROXY_CHECK_TRIES, self._total_time)


def check_proxy(px: str):
    global results

    if px in results.keys():
        return

    with Session() as cs:
        cs.keep_alive = True
        cs.headers['User-Agent'] = useragent
        cs.adapters.clear()
        cs.mount('http://', HTTPAdapter(pool_maxsize=1, max_retries=0))
        cs.mount('https://', HTTPAdapter(pool_maxsize=1, max_retries=0))

        cur_prox = None
        total_timer = ltime()
        for n in range(0, PROXY_CHECK_TRIES):
            if n > 0:
                thread_sleep(PROXY_CHECK_RECHECK_TIME)
            timer = ltime()
            try:
                r = cs.request(method='GET', url=(target_addr), headers=default_headers,
                               cookies=None, proxies={'all': px}, timeout=PROXY_CHECK_TIMEOUT)
                res_delay = ltime() - timer
                res_acc = 100
                suc = True
                r.raise_for_status()
                r.close()
            except (KeyboardInterrupt, SystemExit) as err:
                raise err
            except (HTTPError, ProxyError) as err:
                res_delay = ltime() - timer
                res_acc = 0
                suc = False
                if err.response.status_code == 503:
                    res_delay = -1.0
                    res_acc = 503
                    suc = True
                elif err.response.status_code == 509:
                    res_delay = -1.0
                    res_acc = 509
                    suc = True
                elif __DEBUG:
                    s_print(('%s - error %s: %s' % (px, str(exc_info()[0]), str(exc_info()[1]))))
            except Exception:
                res_delay = -1.0
                res_acc = 0
                suc = False
                if __DEBUG:
                    s_print(('%s - error %s: %s' % (px, str(exc_info()[0]), str(exc_info()[1]))))

            with result_lock:
                if cur_prox:
                    cur_prox.delay.append(res_delay)
                    cur_prox.accessibility.append(res_acc)
                    cur_prox.suc_count += 1 if suc is True else 0
                    # will be filtered out anyways
                    if (not suc and (n + 1) - cur_prox.suc_count) >= PROXY_CHECK_UNSUCCESS_LIMIT:
                        # s_print(('%s - unsuccess count reached!' % px))
                        cur_prox.finalize()
                        return
                else:
                    cur_prox = _ProxyStruct(addr=px, delay=res_delay, accessibility=res_acc, success=suc)
                    cur_prox.start_time = total_timer

    if cur_prox:
        cur_prox.finalize()
    else:
        s_print('error214 - proxy %s not found - not finalized' % px)


def check_proxies(proxlist: set):

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
