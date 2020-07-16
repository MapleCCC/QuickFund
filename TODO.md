## Priority High

- Add docstring to functions, for better maintenance
  - Also add docstring to classes and modules.
- Try to use more modernized python project dependency management tools, like poetry, pyenv, pip-tools, requirements.in, Pipfile, Pipfile.lock, pipenv, pyproject, etc. Instead of using the naive requirements.txt method.
- Add pre-commit hook script. Lint, reformat, bump version.
- Deploy pre-commit hook using the famous "pre-commit" repository.
  - Reformat staged Python code with `isort` and `black`
  - Linting
- Append content of TODO.md and CHANGELOG.md to README.md
- Generate TOC for README in pre-commit hook script.
- Bump to first major release v1.0.0
- Try release candidate version.
- Search on the internet about existing project that make async possible with requests library.
- Polish the `--help` generated message.


## Priority Medium

- Use Go to rewrite. Leverage Go language's builtin concurrency support.
- Use color output in console. Use library like colorama, colored, termcolor, blessings.
- Read the book "High Performance Python" and deploy some tricks from there. Especially the part about mitigating expensive network IO.
- Reduce overhead of network IO, which is expensive.
- Use line profiler to find performance hotspots.
- Any compression algorithm targeted at binary file instead of text? Try to do some literature review on this research topic.
- Use lightweight utlity tool to preview content Excel document. So that we don't have to wait for the heavyweight Excel program to startup everytime we want to test on our program.
- Read semver.org. Understand thoroughly how to choose proper version number.
- Use advanced feature from click. Take inspiration from black library.
  - click.Path
  - click.version_option()
  - click.context
- Learn and master Vim movement, jumping, jump back, mark.
- exit() vs sys.exit() vs quit(). What's the difference? Which should we use?
  - atexit module
- See content of `rg TODO`
- See content of `rg FIXME`
- Specify minimal supported Python version.
- Add unit test suite/framework. Tox, pytest, nose.
- Play with atexit hook to reason about its behaviour.
  - When program successfully finishes.
  - When program terminates due to uncaught exception.
  - When program terminates due to call to exit()/sys.exit()/quit().
- Adopt `conventional commit` conventions.
- Find way to quick unit test, integrate test, regression test. No need to stand up with the startup time overhead of the super heavyweight Excel program anymore.
- Use requests session feature to leverage connection pool.
- Use requests body content flow stream. So we can display progress bar when downloading or uploading large files.
  - Incorporate with tqdm.
- Install to context menu, so that the user only needs to open the context menu of a file and then click our program. The UX is more intuitive and straightforward.
- Implement a non-tech-savvy-user-friendly GUI. Try the goose library.
- Too many issues and feature requests. Consider using GitHub's issue system.
- Try PyPy to accelerate the script.
- See content of snippets.py
- Issue: tqdm progress bar is not displayed correctly in some console environment.
- Issue: color code output is not displayed correctly in some console environment.
- Try some easy-to-use GUI library.
- Pin the dependencies' versions. Use exact version for max robustness and compatibility.
  - Use some utility tool to help automatically find all third-party library used in the repository.
  - Inspect pipreq library's source code. Figure out how it identifies an import as third-party import.
  - How to identify an import as third-party import, and not standard import?
  - Append to project idea
  - Look into isort library source code. Figure out how isort identifies an import as third-party import.
  - Look into mypy library source code. Figure out how mypy identifies an import as third-party import.
  - Look into pyright library source code. Figure out how isort identifies an import as third-party import.
- Consider use "WARN:" to replace "WARNING:" in comments.
- 调整输出的 Excel 文档的各列列宽
- Add badges to README.
  - build passing
  - lint passing
  - test coverage
  - license
  - code format style
  - we adopt semantic version
  - lines of code
  - release version number
  - code quality
  - pylint rating
  - commits since latest version/release
  - contribution is welcome
- Add scripts to update dependencies and bump their version in requirements*.txt files.
- Some TODO should be FIXME. Change to proper names.


## Priority Low

- Investigate whether click library is lightweight. Whether it contains C extension module. Whether it's more lightweight to use builtin argparse library.
- Use Rust to rewrite.
- When swtiching to client/server architecture, use xlsxwriter's advanced in-memory server feature.
- Setup autonomous workflow to auto build executable and publish to GitHub release page. Perhaps use CI pipeline setup or GitHub Actions.
- Open a feature branch to try on Gooey.
- Try Git workflow model like trunk-based, GitFlow.
- Auto workflow to calculate SHA256 hash signature of the released zip file and the released executable file.
- Script to auto check update daily.
- Try to search on the internet and find some other fund APIs.
- One way to overcome the difficulty of distribution and lengthy executable startup time, is to use client/server model. By client/server model, user doesn't need to know anything about the change of the underlying implmentation. The burden of updating to latest version is now off the shoulder of user.
- Open a feature branch to work on client/server architecture.
- After switching to client/server architecture, we don't need to embed the auto update detection logic any more. Remove the additional network IO overhead.
- Try to use Nuikta to compile into performant standalone executable.
- Try to use Django to build a server backend.
- Open issue: Pylance doesn't signal error when a non-existent method is called from a dataclass instance.


## Keep Doing

- Add more error / corner case handling logic. Improve/enhance/increase robustness.
- Make it a good habit to add elaborte comments and docstring and docs. This is important and has long-lasting benefits for other people to read my code, including the the guy called "future me".
- Make it a good habit to insert blank lines between groups of code to make code more visually readable.


## Yet to be classified

- Understand below code taken from attrs library:
  ```
  class _Nothing(object):
      """
      Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

      ``_Nothing`` is a singleton. There is only ever one of it.
      """

      _singleton = None

      def __new__(cls):
          if _Nothing._singleton is None:
              _Nothing._singleton = super(_Nothing, cls).__new__(cls)
          return _Nothing._singleton

      def __repr__(self):
          return "NOTHING"


  NOTHING = _Nothing()
  """
  Sentinel to indicate the lack of a value when ``None`` is ambiguous.
  """
  ```
- If we decide to use release candidate version, this complicates the version parsing. There is BNF grammar in semver.org. We can write a parser ourselves. Or we can use a dedicated library.
- What happens when yield keyword is used alone without the following yeild_expression?
- Consider moving colorama.init/deinit pair to every colored output. Prevent polluting global space. Also prevent forgetting to colorama.init in different places across the code repository. What's the overhead if we do so?


## Archive

- 考虑在输出文件名中添加时间戳后缀
- requests library's response type's default encoding ? Is it UTF-8?
  - From requests document, it try to make smart guess of the response's text encoding.
- Figure out why using pyinstaller with upx will lead to erroneous executable.
- Try some other executable compression utility tools. Turn out that UPX doesn't give us meaningful compression ratio.


## TIL

- User experience design: when doing long time processing, create some animated UI to let user understand that something is going on and the process is not dead.
