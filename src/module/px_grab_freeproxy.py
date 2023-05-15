# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import compile as re_compile, search as re_search, findall as re_findall

from bs4 import BeautifulSoup
from iteration_utilities import unique_everseen
from requests import Session

from px_ua import random_useragent

ENABLED = True

my_result = ''

default_headers = {'User-Agent': random_useragent(), 'Host': 'free-proxy.cz'}

proxylist_addr = 'http://free-proxy.cz/en/proxylist/country/all/http/ping/level'
proxylist_lvls = ['1', '2']


# required format: {"export_address": ["3.210.193.173"], "port": 80}
def format_prox(proxline: str) -> str:
    prox_addr = re_search(r'^decode\(\"([\d\w=]+)\"\)$', proxline).group(1)  # Base64.decode("MTQ5LjI0OC41MC4yMDY=")
    prox_port = re_search(r'^fport\" style=\\\'\\\'>(\d+)<$', proxline).group(1)  # <span class="fport" style=\'\'>3128</span>
    prox_string = '{"export_address": ["' + prox_addr + '"], "port": ' + prox_port + '}'
    return prox_string + '\n'


def grab_proxies() -> None:

    def proc_page() -> None:
        global my_result
        try:
            prox_lines_matches = re_findall(r'^<tr><td style=.+</small></td></tr>$', str(res_raw))
            for match in prox_lines_matches:
                my_result += format_prox(match)
        except Exception as err:
            raise err

    with Session() as cs:
        for lvl in proxylist_lvls:
            try:
                preq = cs.request('GET', url=(proxylist_addr + lvl), headers=default_headers, timeout=10)
                preq.raise_for_status()
                res_raw = BeautifulSoup(preq.content, 'html.parser')
                preq.close()

                # <a href="/en/proxylist/country/all/all/ping/level1/5">
                pages = res_raw.find_all('a', href=re_compile(r'^/en/proxylist/country/all/http/uptime/level\d/\d$'))
                pages_u = list(unique_everseen(list(pages)))
                i = 0
                while i < len(pages_u):
                    # todo: extract page num, this code is not gonna work
                    pages_u[i] = int(pages_u[i])
                    i += 1
                num_pages = min(5, max(pages_u))  # pages 6+ require captcha

                for i in range(num_pages):
                    try:
                        if i > 0:
                            page_s = lvl + '/' + str(i + 1)
                            r = cs.request('GET', url=(proxylist_addr + page_s), headers=default_headers, timeout=10)
                            r.raise_for_status()
                            res_raw = BeautifulSoup(r.content, 'html.parser')
                            r.close()

                        # proc
                        proc_page()

                    except Exception:
                        continue

            except Exception:
                continue

#
#
#########################################
