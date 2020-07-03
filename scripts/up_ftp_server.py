#!/usr/bin/env python3

import os
import subprocess
import sys

sys.path.append(os.getcwd())
from scripts.build import PYINSTALLER_DISTPATH

subprocess.run(
    ["python", "-m", "http.server", "--directory", PYINSTALLER_DISTPATH]
).check_returncode()
