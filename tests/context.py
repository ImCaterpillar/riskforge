"""把 src/ 加入 sys.path，使测试无需安装即可导入 riskforge。

用法：每个测试模块首行 ``import context  # noqa: F401``。
"""
import os
import sys

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)
