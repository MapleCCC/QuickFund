# MAKEFLAGS+=.silent

SRC_DIR=quickfund
TEST_DIR=tests
DEPS_FILE=requirements/install.txt

run:
	# FIXME why chinese characters in Makefile passed to command in 乱码，fix it！
	python -m quickfund 样例基金代码2.txt

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

reqs:
	pipreqs --use-local --encoding utf-8 ${SRC_DIR} --savepath ${DEPS_FILE}
	sort ${DEPS_FILE} -o ${DEPS_FILE}

todo:
	rg "# TODO|# FIXME" --glob !Makefile

clean:
	rm -rf build/ dist/ __pycache__/ *.spec .cache/

.PHONY: run test release format type-check lint unused-imports todo clean
