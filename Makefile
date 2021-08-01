# MAKEFLAGS+=.silent

SRC_DIR=quickfund
TEST_DIR=tests


run:
	scripts/run.py

test:
	pytest ${TEST_DIR}

release:
	scripts/release.py

format:
	autopep8 --in-place --recursive --aggressive --aggressive --select E501 --max-line-length 88 .
	isort .
	black .

type-check:
	mypy .
	pyright
	# TODO pytype, pyre-check

lint:
	find . -type f -name "*.py" | xargs pylint

unused-imports:
	find . -type f -name "*.py" | xargs pylint --disable=all --enable=W0611

todo:
	rg "# TODO|# FIXME" --glob !Makefile

clean:
	rm -rf build/ dist/ __pycache__/ *.spec .cache/

.PHONY: run test release format type-check lint unused-imports todo clean
