# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import search as re_search
from typing import Set

from px_tester import __DEBUG


def build_proxy_list(proxlist_str: str) -> Set[str]:

    checklist = set()
    uchecklist = set()
    res_raw = proxlist_str.split('\n')

    idx = 0
    idx_max = len(res_raw) - 1
    while idx <= idx_max:
        drop = False
        addr = '0.0.0.0'
        port = '80'
        pref = '??'
        if len(res_raw[idx]) <= 1:
            drop = True
        if not drop:
            addr_re = re_search(r'\"((?:http|socks5)://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\"\]', res_raw[idx])
            port_re = re_search(r'\"port\": (\d+)', res_raw[idx])
            pref_re = re_search(r'(\[(?:[A-Z]{2,3}|\?{2})\])', res_raw[idx])
            if addr_re is None:  # "export_address": [],
                drop = True
            else:
                addr = str(addr_re.group(1))
                port = str(port_re.group(1))
                pref = str(pref_re.group(1))

        if not drop:
            if f'{addr}:{port}' not in uchecklist:
                uchecklist.add(f'{addr}:{port}')
                checklist.add(f'{pref} {addr}:{port}')
        elif __DEBUG:
            print(f'dropped {res_raw[idx]}...')

        idx += 1

    return checklist

#
#
#########################################
