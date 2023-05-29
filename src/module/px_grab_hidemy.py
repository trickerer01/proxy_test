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
from requests import Session

from px_ua import random_useragent

ENABLED = True

my_result = ''

proxylist_addr = 'https://hidemy.name/en/proxy-list/'
default_headers = {'User-Agent': random_useragent(), 'Host': 'hidemy.name', 'Referer': proxylist_addr, 'Connection': 'keep-alive'}
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

    def proc_page(raw: BeautifulSoup) -> None:
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
                start = pagenum * per_page
                r = cs.request('POST', url=f'{proxylist_addr}?start={start:d}', timeout=10, data={'start': f'{start:d}'})
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
        cs.headers.update(default_headers.copy())
        try:
            preq = cs.request('GET', url=f'{proxylist_addr}', timeout=10)
            preq.raise_for_status()
            res_raw = BeautifulSoup(preq.content, 'html.parser')
            preq.close()

            # <a href="/en/proxy-list/?start=2688#list">43</a>
            # pages = res_raw.find_all('a', attrs={'href': re_compile(r'^/en/proxy-list/\?start=\d+#list$')})
            num_pages = 1  # list(sorted(list(int(p.contents[0] if len(p.contents) > 0 else 0) for p in pages)))[-1]

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
