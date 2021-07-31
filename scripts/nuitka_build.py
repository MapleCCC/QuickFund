#!/usr/bin/env python3

import shlex
import subprocess


# WARNING: below code is not working. subprocess.run has different behaviour under
# POSIX and Windows system regarding whether the args argument is passed in as a
# sequence or a string and whether the shell argument is set to True. I am too
# busy to take care of the tedious cross-platform issue. Somebody has a look and fix
# it is welcome.


command_line = 'NUITKA_CLCACHE_BINARY="D:\\Program Files\\Python38\\Scripts\\clcache.exe"; python -m nuitka --show-progress --show-scons --mingw64 --windows-dependency-tool=pefile --follow-imports --standalone quickfund/__main__.py'
subprocess.run(shlex.split(command_line)).check_returncode()
