# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent
from requests import Session

from px_defs import PTYPE_HTTP, PTYPE_HTTPS, PTYPE_SOCKS5

ENABLED = True

my_result = ''

proxylist_addr = 'https://ipspeed.info/free-proxy.php'
ua_generator = FakeUserAgent()
default_headers = {'User-Agent': ua_generator.ff, 'Host': 'ipspeed.info', 'Referer': proxylist_addr, 'Connection': 'keep-alive'}


class ProxTable:
    def __init__(self) -> None:
        self.type_ = self.addr = self.port = ''

    @property
    def valid(self) -> bool:
        return all(bool(_) for _ in (self.type_, self.addr, self.port))


def format_proxy(prox_table: ProxTable) -> str:
    if prox_table.valid:
        prox_string = '[??] {"export_address": ["' + prox_table.type_ + '://' + prox_table.addr + '"], "port": ' + prox_table.port + '}\n'
        return prox_string
    return ''


def grab_proxies(*_) -> None:
    global my_result

    with Session() as cs:
        cs.headers.update(default_headers.copy())
        try:
            preq = cs.request('GET', url=f'{proxylist_addr}', timeout=10)
            preq.raise_for_status()
            res_raw = BeautifulSoup(preq.content, 'html.parser')
            preq.close()

            # res_raw.find_all('tbody')[0].find_all('tr')[0].get_text('\n', strip=True).split('\n')[1:]
            for table in res_raw.find_all('tbody'):
                for tr in table.find_all('tr'):
                    tvals = tr.get_text('\n', strip=True).split('\n')[1:]
                    prox = ProxTable()
                    for tval in tvals:
                        if prox.valid:
                            break
                        for prox_type in (PTYPE_SOCKS5, PTYPE_HTTP, PTYPE_HTTPS):
                            if prox_type in tval.lower():
                                prox.type_ = prox_type
                                break
                        if tval.isnumeric() and 80 <= int(tval) < 2**16:
                            prox.port = tval
                        if tval.count('.') == 3 and all(_.isnumeric() for _ in tval.split('.')):
                            prox.addr = tval
                    my_result += format_proxy(prox)

        except Exception:
            pass

#
#
#########################################
