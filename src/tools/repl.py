#!/usr/bin/env python
"""
Serve a ptpython console using both telnet and ssh.

Thanks to Vincent Michel for this!
https://gist.github.com/vxgmichel/7685685b3e5ead04ada4a3ba75a48eef
"""

import asyncio
import inspect
import os
import threading
import time

from prompt_toolkit import print_formatted_text
from prompt_toolkit.contrib.telnet.server import TelnetServer
from ptpython.repl import embed


def interact(locals_, globals_):
    globals_["print"] = print_formatted_text
    embed(locals=locals_, globals=globals_, patch_stdout=True)


def run_repl():
    calling_scope = None
    current_scope = inspect.currentframe()
    if current_scope:
        calling_scope = current_scope.f_back

    locals_, globals_ = None, None
    if calling_scope:
        locals_ = calling_scope.f_locals
        globals_ = calling_scope.f_globals

    t = threading.Thread(target=interact, args=(locals_, globals_), daemon=True)
    t.start()
