# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import search as re_search

from iteration_utilities import unique_everseen

from px_tester import __DEBUG


def build_proxy_list(proxlist_str: str):

    checklist = set()
    res_raw = proxlist_str.split('\n')

    idx = 0
    idx_max = len(res_raw) - 1
    while idx <= idx_max:
        drop = False
        addr = '0.0.0.0'
        port = '80'
        if len(res_raw[idx]) <= 1:
            drop = True
        if not drop:
            addr_re = re_search(r'\"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\"\]', res_raw[idx])
            port_re = re_search(r'\"port\": (\d+)', res_raw[idx])
            if addr_re is None:  # "export_address": [],
                drop = True
            else:
                assert port_re is not None
                addr = str(addr_re.group(1))
                port = str(port_re.group(1))

        if not drop:
            checklist.add(addr + ':' + port)
        elif __DEBUG:
            print('dropped %s...' % res_raw[idx])

        idx += 1

    return set(unique_everseen(checklist))

#
#
#########################################
