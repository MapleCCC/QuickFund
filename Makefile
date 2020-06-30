# MAKEFLAGS+=.silent

PYINSTALLER_FLAGS=--name "基金信息生成器" --upx-dir "D:\Apps\upx-3.96-win64\upx.exe" --onefile

all:
	pyinstaller ${PYINSTALLER_FLAGS} main.py

release:
	./release.py

format:
	isort --apply
	black .

clean:
	rm -rf build/ dist/ __pycache__/

.PHONY: all release format clean
