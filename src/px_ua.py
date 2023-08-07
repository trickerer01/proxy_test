# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer)
"""
#########################################
#
#

from random import randint

FF_USERAGENTS = (
    'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.2 Firefox/102.0 PaleMoon/32.3.1',
    'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.2 Firefox/102.0 PaleMoon/32.2.0',
    'Mozilla/5.0 (X11; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0',
    'Mozilla/5.0 (X11; Linux i686; rv:101.0) Gecko/20100101 Firefox/101.0',
    'Mozilla/5.0 (Android 8.1.0; Mobile; rv:101.0) Gecko/101.0 Firefox/101.0',
    'Mozilla/5.0 (Windows NT 6.2; rv:101.0) Gecko/20100101 Firefox/101.0',
    'Mozilla/5.0 (X11; U; Linux x86_64; rv:101.0esr) Gecko/20102211 Firefox/101.0esr',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; WOW64; rv:41.0) Gecko/20100101 Firefox/106.0.5 (x64 de)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; WOW64; rv:41.0) Gecko/20100101 Firefox/106.0.1 (x64 de)',
    'Mozilla/5.0 (Android 10; Mobile; rv:106.0) Gecko/106.0 Firefox/106.0',
    'Mozilla/5.0 (Android 11; Mobile; rv:106.0) Gecko/106.0 Firefox/106.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/96.0',
    'Mozilla/5.0 (Android 8.0.0; Mobile; rv:96.0) Gecko/96.0 Firefox/96.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4; rv:96.0esr) Gecko/20100101 Firefox/96.0esr',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_10; rv:33.0) Gecko/20100101 Firefox/104.0',
    'Mozilla/5.0 (Android 6.0.1; Mobile; rv:104.0) Gecko/104.0 Firefox/104.0',
    'Mozilla/5.0 (Android 10; Mobile; rv:104.0) Gecko/104.0 Firefox/104.0',
    'Mozilla/5.0 (Android 6.0.1; Mobile; rv:104.0) Gecko/104.0 Firefox/104.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; x64; rv:107.0) Gecko/20100101 Firefox/108.0 WebExplorer/16.2.5248.0',
    'Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.8) Gecko/20051111 Firefox/108.0',
    'Mozilla/5.0 (Android 13; Mobile; rv:108.0) Gecko/108.0 Firefox/108.0',
    'Mozilla/5.0 (Android 10; Mobile; rv:109.0) Gecko/109.0 Firefox/109.0 QwantMobile/4.2',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; WOW64; rv:41.0) Gecko/20100101 Firefox/109.0.1 (x64 de)',
    'Mozilla/5.0 (Android 11; Tablet; rv:109.0) Gecko/109.0 Firefox/109.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (Android 11; Mobile; rv:109.0) Gecko/109.0 Firefox/109.0',
    'Mozilla/5.0 (Android 8.1.0; Mobile; rv:109.0) Gecko/109.0 Firefox/109.0',
)


def random_useragent() -> str:
    random_idx = randint(1, len(FF_USERAGENTS)) - 1
    return FF_USERAGENTS[random_idx]

#
#
#########################################
