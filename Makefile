# MAKEFLAGS+=.silent

PYINSTALLER_FLAGS=--name "基金信息生成器" --upx-dir "D:\Apps\upx-3.96-win64\upx.exe" --onefile

all:
	pyinstaller ${PYINSTALLER_FLAGS} main.py

release:
	scripts/release.py

format:
	autopep8 --in-place --recursive --aggressive --aggressive --select E501 .
	isort --apply
	black .

clean:
	rm -rf build/ dist/ __pycache__/

.PHONY: all release format clean
