# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from os import path
from re import compile as re_compile

from px_defs import (
    UTF8, HELP_ARG_VERSION, HELP_ARG_TARGET, HELP_ARG_PROXIES, RANGE_MARKER_RE, RANGE_MARKER, RANGE_MAX, HELP_ARG_POOLSIZE,
    PROXY_CHECK_POOL_MAX, PROXY_AMOUNT_MAX, PROXY_AMOUNT_DEFAULT, HELP_ARG_DEST, ADDR_TYPE_HTTP, ADDR_TYPE_HTTPS, ADDR_TYPE_SOCKS5,
    PROXY_CHECK_TRIES_DEFAULT, PROXY_CHECK_UNSUCCESS_THRESHOLD_DEFAULT, HELP_ARG_TRIESCOUNT, HELP_ARG_UNSUCCESSTHRESHOLD,
    PROXY_CHECK_TRIES_MAX, PROXY_CHECK_TIMEOUT_MIN, PROXY_CHECK_TIMEOUT_DEFAULT, HELP_ARG_TIMEOUT, ORDER_ACCESSIBILITY, ORDER_ADDRESS,
    ORDER_DEFAULT, HELP_ARG_ORDER, PROXY_CHECK_DELAY_DEFAULT, PROXY_CHECK_DELAY_MIN, HELP_ARG_DELAY,
)
from px_utils import unquote, normalize_path
from px_version import APP_NAME, APP_VERSION

PARSER_TYPE_PARAM = 'zzzparser_type'
PARSER_TITLE_CMD = 'cmd'
EXISTING_PARSERS = {PARSER_TITLE_CMD}
"""'cmd'"""

ADDR_TYPES_ADDR = (ADDR_TYPE_HTTP, ADDR_TYPE_HTTPS)
ADDR_TYPES_PROX = (ADDR_TYPE_HTTP, ADDR_TYPE_SOCKS5)

ORDER_TYPES = (ORDER_ACCESSIBILITY, ORDER_ADDRESS)

re_expandable_range = re_compile(fr'^.+{RANGE_MARKER_RE}.*?$')


class HelpPrintExitException(Exception):
    pass


def is_addr(str_: str, *, proxy=False) -> bool:
    return str_.startswith(ADDR_TYPES_PROX) if proxy else str_.startswith(ADDR_TYPES_ADDR)


def expand_addr_template(addr: str) -> set[str]:
    addrs_ex = set()
    gs = re_expandable_range.findall(addr)
    if gs:
        for m in gs:
            n1, n2 = int(m[0]), int(m[1])
            q_count = (n2 + 1) - n1
            assert 2 <= q_count <= RANGE_MAX, f'Error: Invalid range in \'{addr}\': \'{q_count:d}\'. Must be 2-{RANGE_MAX:d}'
            for i in range(q_count):
                addrs_ex.update(expand_addr_template(addr.replace(RANGE_MARKER % (n1, n2), f'{n1 + i:d}')))
    else:
        addrs_ex.add(addr)
    return addrs_ex


def target_addr(url_or_file: str) -> set[str]:
    addrs = set()
    invalid_addrs = list()
    is_file = path.isfile(url_or_file)
    if is_file:
        with open(url_or_file, 'rt', encoding=UTF8) as addrsfile:
            for idx, line in enumerate(addrsfile.readlines()):
                line = line.strip(' \n\ufeff')
                if not line or line.startswith('#'):
                    continue
                if not is_addr(line):
                    invalid_addrs.append(f'at line {idx + 1:d}: {line}')
                    continue
                addrs.update(expand_addr_template(line))
    elif is_addr(url_or_file):
        addrs.update(expand_addr_template(url_or_file))
    else:
        invalid_addrs.append(f'\'{url_or_file}\'')
    if invalid_addrs:
        n = '\n - '
        print(f'Error: Invalid address(es) found{f" in file {url_or_file}" if is_file else ""}:\n - {n.join(invalid_addrs)}')
        raise ValueError
    return addrs


def target_prox(amount_or_url_or_file: str) -> int | set[str]:
    proxys = set()
    invalid_proxys = list()
    is_file = path.isfile(amount_or_url_or_file)
    if amount_or_url_or_file in [str(amount) for amount in range(PROXY_AMOUNT_DEFAULT, PROXY_AMOUNT_MAX + 1)]:
        return int(amount_or_url_or_file)
    elif is_file:
        with open(amount_or_url_or_file, 'rt', encoding=UTF8) as proxysfile:
            for idx, line in enumerate(proxysfile.readlines()):
                line = line.strip(' \n\ufeff')
                if not line or line.startswith('#'):
                    continue
                if not is_addr(line, proxy=True):
                    invalid_proxys.append(f'at line {idx + 1:d}: {line}')
                    continue
                proxys.update(expand_addr_template(line))
    elif is_addr(amount_or_url_or_file, proxy=True):
        proxys.update(expand_addr_template(amount_or_url_or_file))
    else:
        invalid_proxys.append(f'\'{amount_or_url_or_file}\'')
    if invalid_proxys:
        n = '\n - '
        print(f'Error: Invalid proxy(es){f" in file {amount_or_url_or_file}" if is_file else ""}:\n - {n.join(invalid_proxys)}')
        raise ValueError
    return proxys


def proxy_pool_size(size_str: str) -> int:
    assert size_str.isnumeric()
    size = int(size_str)
    assert 1 <= size <= PROXY_CHECK_POOL_MAX, f'Invalid pool size {size:d}, Must be 1-{PROXY_CHECK_POOL_MAX:d}'
    return size


def dest_path(pathstr: str) -> tuple[str, str]:
    path_abs = path.abspath(path.expanduser(unquote(pathstr)))
    newpath = normalize_path(path_abs, append_slash=path.splitext(path_abs)[1] == '')
    dirpath, filename = path.split(newpath)
    assert path.isdir(dirpath), f'Error: Invalid path \'{pathstr}\' (folder doesn\'t exist)'
    return dirpath, filename


def valid_int(val: str, *, lb: int = None, ub: int = None) -> int:
    val = int(val)
    assert lb is None or val >= lb
    assert ub is None or val <= ub
    return val


def timeout_seconds(val: str) -> int:
    return valid_int(val, lb=PROXY_CHECK_TIMEOUT_MIN)


def tries_count(val: str) -> int:
    return valid_int(val, lb=1, ub=PROXY_CHECK_TRIES_MAX)


def delay_seconds(val: str) -> int:
    return valid_int(val, lb=PROXY_CHECK_DELAY_MIN)


def unsuccess_threshold(val: str) -> int:
    return valid_int(val, lb=1, ub=PROXY_CHECK_TRIES_MAX)


def validate_parsed(parser: ArgumentParser, default_sub: ArgumentParser, args: Sequence[str]) -> Namespace:
    parsed, _ = (parser if args[0] in EXISTING_PARSERS else default_sub).parse_known_args(args)
    assert parsed.unsuccess_threshold <= parsed.tries_count, (
        f'Fail threshold ({parsed.unsuccess_threshold:d}) is higher than tries count ({parsed.tries_count:d})!'
    )
    assert parsed.pool_size < 3 or len(parsed.target) >= 2 * parsed.pool_size, (
        f'Testing {parsed.pool_size:d} proxies simultaneously requires at least {2 * parsed.pool_size:d} targets, '
        f'got {len(parsed.target):d}!'
    )
    return parsed


def execute_parser(parser: ArgumentParser, default_sub: ArgumentParser, args: Sequence[str]) -> Namespace:
    try:
        parsed = validate_parsed(parser, default_sub, args)
        return parsed
    except SystemExit:
        raise HelpPrintExitException
    except Exception:
        from traceback import format_exc
        default_sub.print_help()
        print(format_exc())
        raise HelpPrintExitException


def create_parsers() -> tuple[ArgumentParser, ArgumentParser]:
    parser = ArgumentParser(add_help=False)
    subs = parser.add_subparsers()
    par_cmd = subs.add_parser(PARSER_TITLE_CMD, description='Run using normal cmdline', add_help=False)
    [p.add_argument('--help', action='help', help='Print this message') for p in (par_cmd,)]
    [p.add_argument('--version', action='version', help=HELP_ARG_VERSION, version=f'{APP_NAME} {APP_VERSION}') for p in (par_cmd,)]
    [p.set_defaults(**{PARSER_TYPE_PARAM: t}) for p, t in zip((par_cmd,), (PARSER_TITLE_CMD,))]
    return parser, par_cmd


def prepare_arglist(args: Sequence[str]) -> Namespace:
    parser, par_cmd = create_parsers()
    par_cmd.usage = 'px_main.py --target URL_OR_FILE --proxy URL_OR_FILE_OR_AMOUNT [options...]'
    par_cmd.add_argument('--target', '-t', metavar='URL_OR_FILE', required=True,
                         help=HELP_ARG_TARGET, type=target_addr)
    par_cmd.add_argument('--proxy', '-p', metavar=f'URL_OR_FILE_OR_AMOUNT=1..{PROXY_AMOUNT_MAX:d}', default=PROXY_AMOUNT_DEFAULT,
                         help=HELP_ARG_PROXIES, type=target_prox)
    par_cmd.add_argument('--pool-size', '-s', metavar=f'1..{PROXY_CHECK_POOL_MAX:d}', default=0,
                         help=HELP_ARG_POOLSIZE, type=proxy_pool_size)
    par_cmd.add_argument('--dest', '-d', metavar='PATH', default=dest_path(path.curdir),
                         help=HELP_ARG_DEST, type=dest_path)
    par_cmd.add_argument('--timeout', '-e', metavar='SECONDS', default=PROXY_CHECK_TIMEOUT_DEFAULT,
                         help=HELP_ARG_TIMEOUT, type=timeout_seconds)
    par_cmd.add_argument('--tries-count', '-c', metavar='COUNT', default=PROXY_CHECK_TRIES_DEFAULT,
                         help=HELP_ARG_TRIESCOUNT, type=tries_count)
    par_cmd.add_argument('--delay', '-l', metavar='SECONDS', default=PROXY_CHECK_DELAY_DEFAULT,
                         help=HELP_ARG_DELAY, type=delay_seconds)
    par_cmd.add_argument('--unsuccess-threshold', '-u', metavar='COUNT', default=PROXY_CHECK_UNSUCCESS_THRESHOLD_DEFAULT,
                         help=HELP_ARG_UNSUCCESSTHRESHOLD, type=unsuccess_threshold)
    par_cmd.add_argument('--order', '-o', default=ORDER_DEFAULT, help=HELP_ARG_ORDER, choices=ORDER_TYPES)
    return execute_parser(parser, par_cmd, args)

#
#
#########################################
