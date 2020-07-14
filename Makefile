# MAKEFLAGS+=.silent

run:
	scripts/run.py

release:
	scripts/release.py

format:
	autopep8 --in-place --recursive --aggressive --aggressive --select E501 --max-line-length 88 .
	isort --apply
	black .

lint:
	find ${SRC_DIR} ${TEST_DIR} -type f -name "*.py" | xargs pylint

unused-imports:
	find ${SRC_DIR} ${TEST_DIR} -type f -name "*.py" | xargs pylint --disable=all --enable=W0611

todo:
	rg "# TODO" --glob !Makefile

clean:
	rm -rf build/ dist/ __pycache__/ *.spec .cache/

.PHONY: all run release format lint unused-imports todo clean
