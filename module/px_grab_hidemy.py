# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from multiprocessing.dummy import Pool
from re import compile as re_compile, findall as re_findall
from threading import Lock as ThreadLock
from time import sleep as thread_sleep

from bs4 import BeautifulSoup
from iteration_utilities import unique_everseen
from requests import Session

from px_utils import useragent

ENABLED = True

my_result = ''

default_headers = {'User-Agent': useragent, 'Host': 'hidemy.name'}

proxylist_addr = 'https://hidemy.name/en/proxy-list/?start='
per_page = 64
add_port_re = re_compile(r'<tr><td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d{2,5})</td>')
ptype_re = re_compile(r'<td>(SOCKS|HTTP)[^<]*<')
myres_lock = ThreadLock()


# required format: {"export_address": ["3.210.193.173"], "port": 80}
def format_prox(proxline: str) -> str:
    prox_addr = proxline[:proxline.find(':')]
    prox_port = proxline[proxline.find(':') + 1:]
    prox_string = '{"export_address": ["' + prox_addr + '"], "port": ' + prox_port + '}'
    return prox_string + '\n'


def grab_proxies() -> None:

    def proc_page(raw):
        global my_result
        try:
            content = str(raw)
            ptype_results = re_findall(ptype_re, content)
            addr_port_results = re_findall(add_port_re, content)

            if len(addr_port_results) != len(ptype_results):
                raise KeyError('Assertion error: wrong results array length')

            idx = 0
            while idx < len(addr_port_results):
                with myres_lock:
                    my_result += format_prox(addr_port_results[idx][0] + ':' + addr_port_results[idx][1])
                idx += 1

        except Exception as err:
            raise err

    def get_and_proc_page(pagenum: int):
        try:
            if pagenum > 0:
                page_s = str(pagenum * per_page)
                r = cs.request('GET', url=(proxylist_addr + page_s), headers=default_headers, timeout=10)
                r.raise_for_status()
                raw = BeautifulSoup(r.content, 'html.parser')
                r.close()
            else:
                raw = res_raw

            # proc
            proc_page(raw)

        except Exception:
            pass

    with Session() as cs:
        try:
            preq = cs.request('GET', url=(proxylist_addr + '0'), headers=default_headers, timeout=10)
            preq.raise_for_status()
            res_raw = BeautifulSoup(preq.content, 'html.parser')
            preq.close()

            # <a href="/en/proxy-list/?start=2688#list">43</a>
            pages = res_raw.find_all('a', attrs={'href': re_compile(r'^/en/proxy-list/\?start=\d+#list$')})
            pages_u = list(unique_everseen(list(pages)))
            i = 0
            while i < len(pages_u):
                pages_u[i] = int(pages_u[i].contents[0] if len(pages_u[i].contents) > 0 else 0)
                i += 1
            num_pages = max(pages_u)

            pool = Pool(5)
            ress = []
            for i in range(num_pages):
                ress.append(pool.apply_async(get_and_proc_page, args=(i,)))
            pool.close()

            while len(ress) > 0:
                if ress[0].ready():
                    ress.pop(0)
                    thread_sleep(0.1)
                    continue
                thread_sleep(0.2)

            pool.terminate()

        except Exception:
            pass

#
#
#########################################
