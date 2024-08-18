# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import search as re_search

from requests import Session

ENABLED = True

my_result = ''

proxylist_addr = 'https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list'


# required format: [PREFIX] {"export_address": ["type://3.210.193.173"], "port": 80}
def format_proxy(proxline: str) -> str:
    prox_addr_r = re_search(r'\"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\"\]', proxline)
    prox_port_r = re_search(r'\"port\": (\d+)', proxline)
    prox_string = '[??] {"export_address": ["' + 'http://' + prox_addr_r.group(1) + '"], "port": ' + prox_port_r.group(1) + '}\n' \
        if prox_addr_r and prox_port_r else ''
    return prox_string


def grab_proxies(*_) -> None:
    global my_result

    with Session() as cs:
        try:
            preq = cs.request('GET', url=proxylist_addr, timeout=10)
            preq.raise_for_status()
            my_result = ''.join([format_proxy(s) for s in preq.content.decode().split('\n')])
            preq.close()

        except Exception:
            pass

#
#
#########################################
