# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import findall as re_findall

from requests import Session

ENABLED = True

my_result = ''

proxylist_addrs = [
    'http://ab57.ru/downloads/proxylist.txt',
    'http://api.xicidaili.com/free2016.txt',
    'http://www.proxylists.net/http_highanon.txt',
    'http://www.proxylists.net/http.txt',
    'https://www.rmccurdy.com/scripts/proxy/good.txt',
]


def format_proxy(proxline: str) -> str:
    prox_addr = proxline[:proxline.find(':')]
    prox_port = proxline[proxline.find(':') + 1:]
    prox_string = '[??] {"export_address": ["' + prox_addr + '"], "port": ' + prox_port + '}'
    return prox_string + '\n'


def grab_proxies(*_) -> None:
    global my_result

    with Session() as cs:
        for proxylist_addr in proxylist_addrs:
            try:
                preq = cs.request('GET', url=proxylist_addr, timeout=10)
                preq.raise_for_status()
                contents = preq.content.decode()
                preq.close()

                prox_lines = re_findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', contents)

                for prox_line in prox_lines:
                    my_result += format_proxy(prox_line[0] + ':' + prox_line[1])

            except Exception:
                continue

#
#
#########################################
