# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import compile as re_compile, search as re_search, sub as re_sub

from requests import Session

from px_ua import random_useragent
from px_utils import print_s

ENABLED = True

my_result = ''

proxylist_addr = 'https://spys.one/proxys/'
default_headers = {'User-Agent': random_useragent(), 'Host': 'spys.one', 'Referer': proxylist_addr, 'Connection': 'keep-alive'}
ip_re = re_compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


# required format: {"export_address": ["3.210.193.173"], "port": 80}
def format_proxy(proxline: str, ptype: str, prefix) -> str:
    prox_ap = re_search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})', proxline)
    if prox_ap:
        addr, port = tuple(prox_ap.group(1).split(':', 1))
        prox_string = '[' + prefix + '] {"export_address": ["' + ptype + '://' + addr + '"], "port": ' + port + '}\n'
        return prox_string
    return ''


def grab_proxies(amount_factor: int) -> None:
    global my_result

    chr_arr = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX'  # const
    prox_types = {'1': 'http', '2': 'socks5'}
    prox_prefs = ['US', 'SG', 'MX', 'DE', 'GB', 'BR', 'FR', 'HK', 'CO', 'TH', 'FI', 'JP', 'TR', 'ZA', 'EC', 'ID', 'KR', 'CN', 'PH',
                  'EG', 'IN', 'VN', 'BD', 'CL', 'IR', 'ES', 'VE', 'NL', 'DO', 'AR', 'PE', 'CA', 'PL', 'PK', 'KH', 'TW', 'AU', 'KE',
                  'IT', 'MY', 'SE', 'LY', 'IQ', 'HU', 'CZ', 'GT', 'HN']
    prox_prefs_a = prox_prefs[:int(5.25 * amount_factor)]

    with Session() as cs:
        cs.headers.update(default_headers.copy())
        for country in prox_prefs_a:
            for ptype in ('1', '2'):  # ptype 1 = http, 2 = socks5,
                try:
                    print_s(f'spys: {country} {ptype}...')
                    preq = cs.request('POST', url=f'{proxylist_addr}{country}/', timeout=10,
                                      data={'xpp': '5', 'xf1': '0', 'xf2': '0', 'xf4': '0', 'xf5': ptype})  # xpp 4 = 300, 5 = 500 (max)
                    preq.raise_for_status()
                    content_str = preq.content.decode()
                    preq.close()
                    p, x = tuple(re_search(r'}\((\'[^.]+)', content_str).group(1).split(',60,60,'))
                    p_exec, symbols = p[1:-2], x[1:-1].split('^')
                    chars_to_symbols: dict[str, str] = {chr_arr[i]: symbols[i] or chr_arr[i] for i in range(len(chr_arr))}
                    p_exec = re_sub(r'\b(\w+)\b', lambda w: chars_to_symbols.get(w.group(1), '0'), p_exec)
                    vals = dict()
                    for s in p_exec.split(';'):
                        k, v = tuple(s.split('=', 1))
                        val = 0
                        for vs in v.split('^'):
                            if vs.isnumeric():
                                val ^= int(vs)
                            else:
                                assert vs in vals
                                val ^= int(vals[vs])
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

                    my_result += ''.join(format_proxy(s, prox_types[ptype], country) for s in rows)
                except Exception:
                    pass

#
#
#########################################
