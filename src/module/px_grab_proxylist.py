# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import base64
import re

from requests import Session

ENABLED = True

my_result = ''

proxylist_addr = 'http://proxy-list.org/english/index.php?p='
proxylist_pages = 10


def format_proxy(proxline: str) -> str:
    prox_addr = proxline[:proxline.rfind(':')]
    prox_port = proxline[proxline.rfind(':') + 1:]
    prox_string = '[??] {"export_address": ["' + 'http://' + prox_addr + '"], "port": ' + prox_port + '}'
    return prox_string + '\n'


def grab_proxies(*_) -> None:
    global my_result

    with Session() as cs:
        for i in range(proxylist_pages):
            try:
                pnum = str(i + 1)
                preq = cs.request('GET', url=(proxylist_addr + pnum), timeout=10)
                preq.raise_for_status()
                contents = preq.content.decode()
                preq.close()

                prox_lines = re.findall(r'Proxy\(\'([\w\d=+]+)\'\)', contents)

                for prox_line in prox_lines:
                    my_result += format_proxy(base64.b64decode(prox_line).decode())

            except Exception:
                pass

#
#
#########################################
