src_dir := quickfund
test_dir := tests
deps_file := requirements/install.txt

run:
    python -m quickfund 样例基金代码2.txt

test:
    pytest {{test_dir}}

release:
    scripts/release.py

format:
    # autopep8 --in-place --recursive --aggressive --aggressive --select E501 --max-line-length 88 .
    isort .
    black .

type-check:
    mypy .
    pyright
    # TODO pytype, pyre-check

lint:
    find . -type f -name "*.py" | xargs pylint

unused-imports:
    pycln --diff {{src_dir}} {{test_dir}}

reqs:
    pipreqs --use-local --encoding utf-8 {{src_dir}} --savepath {{deps_file}}
    sort {{deps_file}} -o {{deps_file}}

todo:
    rg "# TODO|# FIXME" --glob !justfile

clean:
    echo "No clean job"
