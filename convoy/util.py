# Copyright (c) Microsoft Corporation
#
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# compat imports
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
from builtins import (  # noqa
    bytes, dict, int, list, object, range, str, ascii, chr, hex, input,
    next, oct, open, pow, round, super, filter, map, zip)
# stdlib imports
import base64
import copy
import hashlib
import logging
import logging.handlers
import os
import subprocess
try:
    from os import scandir as scandir
except ImportError:
    from scandir import scandir as scandir
import platform
import sys
import time
# function remaps
try:
    raw_input
except NameError:
    raw_input = input


# create logger
logger = logging.getLogger(__name__)
# global defines
_PY2 = sys.version_info.major == 2
_ON_WINDOWS = platform.system() == 'Windows'


def on_python2():
    # type: (None) -> bool
    """Execution on python2
    :rtype: bool
    :return: if on Python2
    """
    return _PY2


def on_windows():
    # type: (None) -> bool
    """Execution on Windows
    :rtype: bool
    :return: if on Windows
    """
    return _ON_WINDOWS


def setup_logger(logger):
    # type: (logger) -> None
    """Set up logger"""
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)sZ %(levelname)s %(name)s:%(funcName)s:%(lineno)d '
        '%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# set up util logger
setup_logger(logger)


def decode_string(string, encoding=None):
    # type: (str, str) -> str
    """Decode a string with specified encoding
    :type string: str or bytes
    :param string: string to decode
    :param str encoding: encoding of string to decode
    :rtype: str
    :return: decoded string
    """
    if isinstance(string, bytes):
        if encoding is None:
            encoding = 'utf8'
        return string.decode(encoding)
    if isinstance(string, str):
        return string
    raise ValueError('invalid string type: {}'.format(type(string)))


def encode_string(string, encoding=None):
    # type: (str, str) -> str
    """Encode a string with specified encoding
    :type string: str or bytes
    :param string: string to decode
    :param str encoding: encoding of string to decode
    :rtype: str
    :return: decoded string
    """
    if isinstance(string, bytes):
        return string
    if isinstance(string, str):
        if encoding is None:
            encoding = 'utf8'
        return string.encode(encoding)
    raise ValueError('invalid string type: {}'.format(type(string)))


def is_none_or_empty(obj):
    # type: (any) -> bool
    """Determine if object is None or empty
    :type any obj: object
    :rtype: bool
    :return: if object is None or empty
    """
    if obj is None or len(obj) == 0:
        return True
    return False


def is_not_empty(obj):
    # type: (any) -> bool
    """Determine if object is not None and is length is > 0
    :type any obj: object
    :rtype: bool
    :return: if object is not None and length is > 0
    """
    if obj is not None and len(obj) > 0:
        return True
    return False


def get_input(prompt):
    # type: (str) -> str
    """Get user input from keyboard
    :param str prompt: prompt text
    :rtype: str
    :return: user input
    """
    return raw_input(prompt)


def confirm_action(config, msg=None, allow_auto=True):
    # type: (dict, str, bool) -> bool
    """Confirm action with user before proceeding
    :param dict config: configuration dict
    :param msg str: confirmation message
    :param bool allow_auto: allow auto confirmation
    :rtype: bool
    :return: if user confirmed or not
    """
    if allow_auto and config['_auto_confirm']:
        return True
    if msg is None:
        msg = 'action'
    while True:
        user = get_input('Confirm {} [y/n]: '.format(msg)).lower()
        if user in ('y', 'yes', 'n', 'no'):
            break
    if user in ('y', 'yes'):
        return True
    return False


def merge_dict(dict1, dict2):
    # type: (dict, dict) -> dict
    """Recursively merge dictionaries: dict2 on to dict1. This differs
    from dict.update() in that values that are dicts are recursively merged.
    Note that only dict value types are merged, not lists, etc.

    :param dict dict1: dictionary to merge to
    :param dict dict2: dictionary to merge with
    :rtype: dict
    :return: merged dictionary
    """
    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        raise ValueError('dict1 or dict2 is not a dictionary')
    result = copy.deepcopy(dict1)
    for k, v in dict2.items():
        if k in result and isinstance(result[k], dict):
            result[k] = merge_dict(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def scantree(path):
    # type: (str) -> os.DirEntry
    """Recursively scan a directory tree
    :param str path: path to scan
    :rtype: DirEntry
    :return: DirEntry via generator
    """
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=True):
            # due to python2 compat, cannot use yield from here
            for t in scantree(entry.path):
                yield t
        else:
            yield entry


def wrap_commands_in_shell(commands, wait=True):
    # type: (List[str], bool) -> str
    """Wrap commands in a shell
    :param list commands: list of commands to wrap
    :param bool wait: add wait for background processes
    :rtype: str
    :return: wrapped commands
    """
    return '/bin/bash -c \'set -e; set -o pipefail; {}{}\''.format(
        '; '.join(commands), '; wait' if wait else '')


def base64_encode_string(string):
    # type: (str or bytes) -> str
    """Base64 encode a string
    :param str or bytes string: string to encode
    :rtype: str
    :return: base64-encoded string
    """
    if on_python2():
        return base64.b64encode(string)
    else:
        return str(base64.b64encode(string), 'ascii')


def base64_decode_string(string):
    # type: (str) -> str
    """Base64 decode a string
    :param str string: string to decode
    :rtype: str
    :return: decoded string
    """
    return base64.b64decode(string)


def compute_md5_for_file(file, as_base64, blocksize=65536):
    # type: (pathlib.Path, bool, int) -> str
    """Compute MD5 hash for file
    :param pathlib.Path file: file to compute md5 for
    :param bool as_base64: return as base64 encoded string
    :param int blocksize: block size in bytes
    :rtype: str
    :return: md5 for file
    """
    hasher = hashlib.md5()
    with file.open('rb') as filedesc:
        while True:
            buf = filedesc.read(blocksize)
            if not buf:
                break
            hasher.update(buf)
        if as_base64:
            return base64_encode_string(hasher.digest())
        else:
            return hasher.hexdigest()


def subprocess_with_output(cmd, shell=False, cwd=None, suppress_output=False):
    # type: (str, bool, str, bool) -> int
    """Subprocess command and print output
    :param str cmd: command line to execute
    :param bool shell: use shell in Popen
    :param str cwd: current working directory
    :param bool suppress_output: suppress output
    :rtype: int
    :return: return code of process
    """
    _devnull = None
    try:
        if suppress_output:
            _devnull = open(os.devnull, 'w')
            proc = subprocess.Popen(
                cmd, shell=shell, cwd=cwd, stdout=_devnull,
                stderr=subprocess.STDOUT)
        else:
            proc = subprocess.Popen(cmd, shell=shell, cwd=cwd)
        proc.wait()
    finally:
        if _devnull is not None:
            _devnull.close()
    return proc.returncode


def subprocess_nowait(cmd, shell=False, cwd=None, env=None):
    # type: (str, bool, str, dict) -> subprocess.Process
    """Subprocess command and do not wait for subprocess
    :param str cmd: command line to execute
    :param bool shell: use shell in Popen
    :param str cwd: current working directory
    :param dict env: env vars to use
    :rtype: subprocess.Process
    :return: subprocess process handle
    """
    return subprocess.Popen(cmd, shell=shell, cwd=cwd, env=env)


def subprocess_nowait_pipe_stdout(
        cmd, shell=False, cwd=None, env=None):
    # type: (str, bool, str, dict) -> subprocess.Process
    """Subprocess command and do not wait for subprocess
    :param str cmd: command line to execute
    :param bool shell: use shell in Popen
    :param str cwd: current working directory
    :param dict env: env vars to use
    :rtype: subprocess.Process
    :return: subprocess process handle
    """
    return subprocess.Popen(
        cmd, shell=shell, stdout=subprocess.PIPE, cwd=cwd, env=env)


def subprocess_attach_stdin(cmd, shell=False):
    # type: (str, bool) -> subprocess.Process
    """Subprocess command and attach stdin
    :param str cmd: command line to execute
    :param bool shell: use shell in Popen
    :rtype: subprocess.Process
    :return: subprocess process handle
    """
    return subprocess.Popen(cmd, shell=shell, stdin=subprocess.PIPE)


def subprocess_wait_all(procs):
    # type: (list) -> list
    """Wait for all processes in given list
    :param list procs: list of processes to wait on
    :rtype: list
    :return: list of return codes
    """
    if procs is None or len(procs) == 0:
        raise ValueError('procs is invalid')
    rcodes = [None] * len(procs)
    while True:
        for i in range(0, len(procs)):
            if rcodes[i] is None and procs[i].poll() == 0:
                rcodes[i] = procs[i].returncode
        if all(x is not None for x in rcodes):
            break
        time.sleep(0.03)
    return rcodes


def subprocess_wait_any(procs):
    # type: (list) -> list
    """Wait for any process in given list
    :param list procs: list of processes to wait on
    :rtype: tuple
    :return: (integral position in procs list, return code)
    """
    if procs is None or len(procs) == 0:
        raise ValueError('procs is invalid')
    while True:
        for i in range(0, len(procs)):
            if procs[i].poll() == 0:
                return i, procs[i].returncode
        time.sleep(0.03)


def subprocess_wait_multi(procs1, procs2):
    # type: (list) -> list
    """Wait for any process in given list
    :param list procs: list of processes to wait on
    :rtype: tuple
    :return: (integral position in procs list, return code)
    """
    if ((procs1 is None or len(procs1) == 0) and
            (procs2 is None or len(procs2) == 0)):
        raise ValueError('both procs1 and procs2 are invalid')
    while True:
        if procs1 is not None and len(procs1) > 0:
            for i in range(0, len(procs1)):
                if procs1[i].poll() == 0:
                    return procs1, i, procs1[i].returncode
        if procs2 is not None and len(procs2) > 0:
            for i in range(0, len(procs2)):
                if procs2[i].poll() == 0:
                    return procs2, i, procs2[i].returncode
        time.sleep(0.03)
