# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import Namespace
from time import time as ltime
from typing import Set

__DEBUG = False

OUTPUT_FILE_NAME = '!px_test_results.txt'

UTF8 = 'utf-8'

ACTION_STORE_TRUE = 'store_true'

PTYPE_SOCKS5 = 'socks5'
PTYPE_HTTP = 'http'
PTYPE_HTTPS = 'https'

ADDR_TYPE_HTTP = f'{PTYPE_HTTP}://'
ADDR_TYPE_HTTPS = f'{PTYPE_HTTPS}://'
ADDR_TYPE_SOCKS5 = f'{PTYPE_SOCKS5}://'

BL = '\\'
SLASH = '/'
MARKER = '#'
RANGE_MARKER = f'{MARKER}%d-%d{MARKER}'
RANGE_MARKER_RE = RANGE_MARKER.replace("%d", f"({BL}d+)").replace("-", f"{BL}-").replace(MARKER, f"{BL}{MARKER}")
RANGE_MAX = 1000

STATUS_OK = 200
STATUS_FORBIDDEN = 403
STATUS_NOTFOUND = 404
STATUS_SERVICE_UNAVAILABLE = 503
STATUS_BANDWITH_EXCEEDED = 509
EXTRA_ACCEPTED_CODES = {STATUS_FORBIDDEN, STATUS_NOTFOUND, STATUS_SERVICE_UNAVAILABLE, STATUS_BANDWITH_EXCEEDED}

PROXY_AMOUNT_DEFAULT = 1
PROXY_AMOUNT_MAX = 9
PROXY_CHECK_POOL_DEFAULT = 1
PROXY_CHECK_POOL_MAX = 100
PROXY_CHECK_TRIES_DEFAULT = 5
PROXY_CHECK_TRIES_MAX = 20
PROXY_CHECK_UNSUCCESS_THRESHOLD_DEFAULT = PROXY_CHECK_TRIES_DEFAULT
PROXY_CHECK_TIMEOUT_MIN = 5
PROXY_CHECK_TIMEOUT_DEFAULT = 10
PROXY_CHECK_RE_TIME = 1.0

DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
}

HELP_ARG_VERSION = 'Show program\'s version number and exit'
HELP_ARG_TARGET = (
    f'Target address to test proxies on. Range format available: \'#MIN-MAX#\', up to {RANGE_MAX:d}, example:'
    f' \'http://example.com/5#101-500#/\' becomes 500 addresses ranging from \'http://example.com/5101/\' to \'http://example.com/5500/\'.'
    f' Alternatively it can be a path to a text file containing different addresses (range format still applies)'
)
HELP_ARG_PROXIES = (
    f'Proxy to test, format: {{http,socks5}}://[user@password]a.d.d.r:port. Range format available: \'#MIN-MAX#\', example:'
    f' \'http://127.0.0.#1-255#:3128\' becomes 255 addresses ranging from \'http://127.0.0.1:3128\' to \'http://127.0.0.255:3128\'.'
    f' Alternatively it can be a path to a text file containing different addresses (range format still applies).'
    f' Another alternative is to fetch random proxies from the web using relative amount {PROXY_AMOUNT_DEFAULT:d}..{PROXY_AMOUNT_MAX:d}.'
    f' This is the default mode (amount={PROXY_AMOUNT_DEFAULT:d}).'
    f' Warning: may fetch many thousands of proxies, testing which may take hours!'
)
HELP_ARG_POOLSIZE = (
    f'Number of proxies to test simultaneously. Increasing this number reduces total test time but may trigger anti-DDoS protection.'
    f' This number can\'t be greater than targets pool size or hard limit of {PROXY_CHECK_POOL_MAX:d}'
)
HELP_ARG_DEST = 'Path to directory to store results to. Default is current workdir'
HELP_ARG_TIMEOUT = (
    f'Proxy connection timeout (total) in seconds, {PROXY_CHECK_TIMEOUT_MIN:d}-inf. Defaults is {PROXY_CHECK_TIMEOUT_DEFAULT:d}'
)
HELP_ARG_TRIESCOUNT = f'Proxy connection tries count, 1-{PROXY_CHECK_TRIES_MAX:d}. Default is {PROXY_CHECK_TRIES_DEFAULT:d}'
HELP_ARG_UNSUCCESSTHRESHOLD = (
    f'Proxy unsuccessful connection tries count to consider proxy check failed. Defaults is {PROXY_CHECK_UNSUCCESS_THRESHOLD_DEFAULT:d}'
)


class BaseConfig:
    def __init__(self) -> None:
        self.targets: Set[str] = set()
        self.proxies: Set[str] = set()
        self.iproxies = 0
        self.poolsize = 0
        self.dest = ''
        self.timeout = 0
        self.tries_count = 0
        self.unsuccess_threshold = 0

    def read(self, params: Namespace) -> None:
        self.targets.update(params.target)
        self.proxies.update(params.proxy if isinstance(params.proxy, set) else self.proxies)
        self.iproxies = params.proxy if isinstance(params.proxy, int) else self.iproxies
        self.poolsize = min(params.pool_size or self.poolsize, len(self.targets), PROXY_CHECK_POOL_MAX)
        self.dest = str(params.dest)
        self.timeout = int(params.timeout)
        self.tries_count = int(params.tries_count)
        self.unsuccess_threshold = int(params.unsuccess_threshold)


Config = BaseConfig()


class ProxyStruct():
    def __init__(self, prefix: str, addr: str, delay: float, accessibility: int, success: bool, start: float) -> None:
        self.prefix = prefix
        self.addr = addr
        self.delay = [delay]
        self.accessibility = [accessibility]
        self.suc_count = int(success)
        self.done = False
        self.finalized = False
        self._start = start
        self._average_delay = 0.0
        self._total_time = 0.0

    def finalize(self) -> None:
        if self.finalized:
            return

        # average delay should only be counted from valid delays
        while len(self.accessibility) < Config.tries_count:
            self.accessibility.append(0)
        while len(self.delay) < Config.tries_count:
            self.delay.append(self.delay[-1] if len(self.delay) > 0 else float(PROXY_CHECK_TIMEOUT_DEFAULT))

        average_delay = 0.0
        valid_delays = 0
        for val in self.delay:
            average_delay += max(val, 0.0)
            valid_delays += int(val >= 0.0)

        self._average_delay = average_delay / max(valid_delays, 1)
        self._total_time = (ltime() - self._start) - PROXY_CHECK_RE_TIME * (Config.tries_count - 1)
        self.finalized = True

    def __str__(self) -> str:
        return (f'{self.prefix} {self.addr} ({self._average_delay:.3f}s) - {self.suc_count:d}/{Config.tries_count :d} '
                f'in {self._total_time:.2f}s [{",".join([str(a) for a in self.accessibility])}]')

#
#
#########################################
