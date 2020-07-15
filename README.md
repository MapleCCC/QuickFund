# 基金信息生成器

<!-- TODO add badge about code coverage -->
<!-- TODO add badge about requires.io -->
<!-- TODO add badge about pylint rating -->
[![License](https://img.shields.io/github/license/MapleCCC/Fund-Info-Fetcher?color=00BFFF)](LICENSE)
[![Build Status](https://travis-ci.com/MapleCCC/Fund-Info-Fetcher.svg?branch=master)](https://travis-ci.com/MapleCCC/Fund-Info-Fetcher)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/MapleCCC/Fund-Info-Fetcher)](https://github.com/MapleCCC/Fund-Info-Fetcher/releases/latest)
[![Semantic release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![LOC](https://sloc.xyz/github/MapleCCC/Fund-Info-Fetcher)](https://sloc.xyz/github/MapleCCC/Fund-Info-Fetcher)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub commits since latest release (by SemVer)](https://img.shields.io/github/commits-since/MapleCCC/Fund-Info-Fetcher/latest?sort=semver)](https://github.com/MapleCCC/Fund-Info-Fetcher/compare/v1.0.0...master)
<!-- TODO which diff method should we use? two dots or three dots? -->

## Overview

A script to fetch various fund information from `https://fund.eastmoney.com`, and structuralize into Excel document.

抓取天天基金信息，生成自定义表格。表头和样式可以在 `fetcher/schema.py` 自定义。

## Installation

Prerequisites: Python>=3.8, [Git](https://git-scm.com/), [pip](https://pip.pypa.io/en/stable/).

One-liner installation recipe:

```bash
$ python -m pip install git+https://github.com/MapleCCC/Fund-Info-Fetcher.git#egg=Fund-Info-Fetcher
```

If editable mode installation is preferred:

```bash
# You can optionally create a virtual environment for isolation purpose
$ python -m virtualenv .venv
$ source .venv/Scripts/activate

# Install in editable mode
$ python -m pip install -e git+https://github.com/MapleCCC/Fund-Info-Fetcher.git#egg=Fund-Info-Fetcher
```

## Usage

```bash
$ fund-info-fetch <list of fund codes>
```

### Example Output

![Example Output](assets/example_output.png)

## Download

Go to [Release](https://github.com/MapleCCC/Fund-Info-Fetcher/releases/latest) page.

## Development

Prerequisites: Git, Python3.8+, `pip`.

```bash
# Clone the repository to local environment
$ git clone https://github.com/MapleCCC/Fund-Info-Fetcher.git

$ cd Fund-Info-Fetcher

# You can optionally create a virtual environment for isolation purpose
$ python -m virtualenv .venv
$ source .venv/Scripts/activate

# Install basic build requirements
$ pip install -r requirements/install.txt

# Install dev requirements
$ pip install -r requirements/dev.txt
```

<!-- TODO: Pre-commit hook -->
<!-- Use black and isort to format staged codes. -->
<!-- Generate TOC for README. -->
<!-- Concatenate content of TODO.md and CHANGELOG.md to README. -->

### Test

The project uses pytest and hypothesis as test framework. Property-based testing is adopted in favor of its flexibility and conciseness.

```bash
# Install test requirements
$ python -m pip install -r requirements/test.txt

# unit tests
$ make test
```

### Release Strategy

We follow [semantic version convention](https://semver.org). Every tag pushed to GitHub triggers a Release event. Release workflow (a GitHub action) proceeds and publishes built assets (along with SHA256 hash digest for secure verification).

We follow [conventional commit message guideline](https://www.conventionalcommits.org/en/v1.0.0/).

## License

[MIT](./LICENSE)
