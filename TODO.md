- Add more error / corner case handling logic. Improve/enhance/increase robustness.
- Use optimization mode when packaging to executable file.
- Use executable compression utility to reduce executable size.
- Implement a non-tech-savvy-user-friendly GUI. Try the goose library.
- Add docstring to functions, for better maintenance
- requests library's response type's default encoding ? Is it UTF-8?
- Investigate whether click library is lightweight. Whether it contains C extension module. Whether it's more lightweight to use builtin argparse library.
- Use Rust to rewrite.
- Use color output in console.
- Add README
- Add LICENSE
- Leverage concurrent programming to accelerate network IO. Take inspiration from black and autopep8's code about concurrently formatting multiple files. Use asyncio, multiprocessing, concurrent.futures, threading library.
- Read the book "High Performance Python" and deploy some tricks fromt there. Especially the part about mitigating expensive network IO>
- Reduce overhead of network IO, which is expensive.
- Use line profiler to find performance hotspots.
- Inspect the dependency graph generated from PyInstaller and figure out which third-party library is the the heavy one that takes up most of the size of the generated executable file.
- Use timeit to profile which is more performant: re.fullmatch(r"\d{6}", s) or test numberness of all chars.


## Archive

- 考虑在输出文件名中添加时间戳后缀
