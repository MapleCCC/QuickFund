# MAKEFLAGS+=.silent

PYINSTALLER_FLAGS=--name "基金信息生成器" --upx-dir "D:\Apps\upx-3.96-win64\upx.exe" --onefile

all:
	pyinstaller ${PYINSTALLER_FLAGS} main.py

run:
	scripts/run.py

release:
	scripts/release.py

format:
	autopep8 --in-place --recursive --aggressive --aggressive --select E501 .
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
