# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import compile as re_compile, search as re_search, sub as re_sub

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
            for ptype in ['1', '2']:  # ptype 1 = http, 2 = socks5,
                preq = cs.request('POST', url=proxylist_addr, timeout=10,
                                  data={'xpp': '5', 'xf1': '0', 'xf2': '0', 'xf4': '0', 'xf5': ptype})  # xpp 4 = 300, 5 = 500 (max)
                preq.raise_for_status()
                content_str = preq.content.decode()
                preq.close()
                p, x = tuple(re_search(r'}\((\'[^.]+)', content_str).group(1).split(',60,60,'))
                p, x = p[1:-1], x[1:-1].split('^')
                chr_arr = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX'
                s = {chr_arr[i]: x[i] or chr_arr[i] for i in range(len(chr_arr))}
                p1 = re_sub(r'\b(\w+)\b', lambda w: s.get(w.group(1)) or '\'\'', p)
                assert p1.find('(') == -1  # nothing callable here, only assignments, ex Zero=0
                exec(p1)
                locs = locals()  # required to pass to eval()
                rows_raw = (re_sub(r'\)</script></font></td>.+', '',
                                   content_str.replace('<td colspan=1><font class=spy14>', '\n')
                                   .replace(r'<script type="text/javascript">document.write("<font class=spy2>:<\/font>"+', ':'))
                            ).split('\n')
                rows = [row for row in rows_raw if ip_re.match(row)]
                for ri, row in enumerate(rows):
                    ip, expr = tuple(row.split(':', 1))
                    port = ''.join(str(eval(e, locs)) for e in expr.split('+'))
                    rows[ri] = f'{ip}:{port}'

                my_result += ''.join([format_proxy(s) for s in rows])
        except Exception:
            pass

#
#
#########################################
