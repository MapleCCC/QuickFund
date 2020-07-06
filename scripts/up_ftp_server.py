#!/usr/bin/env python3

import os
import subprocess
import sys

sys.path.append(os.getcwd())
from scripts.zip import ZIPAPP_DISTPATH

subprocess.run(
    ["python", "-m", "http.server", "--directory", ZIPAPP_DISTPATH]
).check_returncode()
