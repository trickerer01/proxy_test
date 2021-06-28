# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from re import findall as re_findall

from requests import Session

ENABLED = True

my_result = ''

proxylist_addr = 'https://free-proxy-list.net/'


def format_proxy(proxline):
    prox_addr = proxline[:proxline.find(':')]
    prox_port = proxline[proxline.find(':') + 1:]
    prox_string = '{"export_address": ["' + prox_addr + '"], "port": ' + prox_port + '}'
    return prox_string + '\n'


def grab_proxies():
    global my_result

    with Session() as cs:
        try:
            preq = cs.request('GET', url=proxylist_addr, timeout=10)
            preq.raise_for_status()
            contents = preq.content.decode()
            preq.close()

            prox_lines = re_findall(r'<tr><td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d{2,5})</td>', contents)

            for prox_line in prox_lines:
                my_result += format_proxy(prox_line[0] + ':' + prox_line[1])

        except Exception:
            pass

#
#
#########################################
