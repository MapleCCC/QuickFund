#!/usr/bin/env python3

import zipapp
# import os

zipapp.create_archive("fetcher", "基金信息生成器.pyz", "/usr/bin/env python3", compressed=True)

# zipapp.create_archive(
#     os.getcwd(),
#     "基金信息生成器.pyz",
#     "/usr/bin/env python3",
#     main="fetcher.__main__:main",
#     filter=lambda x: os.path.splitext(x)[1] == "py",
#     compressed=True,
# )
