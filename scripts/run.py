#!/usr/bin/env python3

import subprocess

# TODO install package locally so that we can run the console script.

subprocess.run(["python", "-m", "fetcher", "样例基金代码2.txt", "-y"]).check_returncode()
