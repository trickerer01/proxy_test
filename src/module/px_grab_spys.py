# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import compile as re_compile, search as re_search, sub as re_sub
from typing import Dict

from requests import Session

from px_ua import random_useragent

ENABLED = True

my_result = ''

proxylist_addr = 'https://spys.one/proxys/US/'
default_headers = {'User-Agent': random_useragent(), 'Host': 'spys.one', 'Referer': proxylist_addr, 'Connection': 'keep-alive'}
ip_re = re_compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


# required format: {"export_address": ["3.210.193.173"], "port": 80}
def format_proxy(proxline: str) -> str:
    prox_ap = re_search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})', proxline)
    if prox_ap:
        addr, port = tuple(prox_ap.group(1).split(':', 1))
        prox_string = '{"export_address": ["' + addr + '"], "port": ' + port + '}\n'
        return prox_string
    return ''


def grab_proxies() -> None:
    global my_result

    with Session() as cs:
        cs.headers.update(default_headers.copy())
        try:
            for ptype in ('1', '2'):  # ptype 1 = http, 2 = socks5,
                preq = cs.request('POST', url=proxylist_addr, timeout=10,
                                  data={'xpp': '5', 'xf1': '0', 'xf2': '0', 'xf4': '0', 'xf5': ptype})  # xpp 4 = 300, 5 = 500 (max)
                preq.raise_for_status()
                content_str = preq.content.decode()
                preq.close()
                p, x = tuple(re_search(r'}\((\'[^.]+)', content_str).group(1).split(',60,60,'))
                p_exec, symbols = p[1:-2], x[1:-1].split('^')
                chr_arr = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX'  # const
                chars_to_symbols = {chr_arr[i]: symbols[i] or chr_arr[i] for i in range(len(chr_arr))}  # type: Dict[str, str]
                p_exec = re_sub(r'\b(\w+)\b', lambda w: chars_to_symbols.get(w.group(1)) or '0', p_exec)
                vals = dict()  # type: Dict[str, str]
                for s in p_exec.split(';'):
                    k, v = tuple(s.split('=', 1))
                    val = 0
                    for vs in v.split('^'):
                        if vs.isnumeric():
                            val ^= int(vs)
                        else:
                            assert vs in vals.keys()
                            val ^= int(vals.get(vs))
                    v = str(val)
                    vals[k] = vals.get(v) or v
                rows_raw = (re_sub(r'\)</script></font></td>.+', '',
                                   content_str.replace('<td colspan=1><font class=spy14>', '\n')
                                   .replace(r'<script type="text/javascript">document.write("<font class=spy2>:<\/font>"+', ':'))
                            ).split('\n')
                rows = [row for row in rows_raw if ip_re.match(row)]
                for ri, row in enumerate(rows):
                    ip, expr = tuple(row.split(':', 1))
                    exprs = re_sub(r'[()]', '', re_sub(r'(\w+)', lambda w: vals.get(w.group(1)), expr)).split('+')
                    for ei in range(len(exprs)):
                        evs = exprs[ei].split('^')
                        assert len(evs) == 2
                        exprs[ei] = str(int(evs[0]) ^ int(evs[1]))
                    port = ''.join(exprs)
                    rows[ri] = f'{ip}:{port}'

                my_result += ''.join(format_proxy(s) for s in rows)
        except Exception:
            pass

#
#
#########################################
