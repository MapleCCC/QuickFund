#!/usr/bin/env python3

import subprocess

subprocess.run(["python", "main.py", "样例基金代码.txt", "-y"]).check_returncode()
