"""
启动番茄小说爬虫 GUI 界面
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并启动 GUI
from gui.crawler_gui import main

if __name__ == "__main__":
    main()
