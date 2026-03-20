"""
测试爬取指定章节范围 - 从第 11 章开始
"""

import sys
sys.path.insert(0, '.')

from crawler.fanqie_crawler import FanqieCrawler
from utils.config import Config

print("=" * 80)
print("爬取测试：《大明：开局剧透朱元璋》第 11-20 章")
print("=" * 80)
print()

try:
    # 创建配置 - 爬取第 11-20 章
    config = Config(
        novel_name="",
        novel_url="https://fanqienovel.com/page/7085534012160085000",
        author="青红",
        min_chapters=11,  # 从第 11 章开始
        max_chapters=20,  # 到第 20 章结束
        save_path="./test_novels/",
    )
    
    # 创建爬虫
    crawler = FanqieCrawler(config)
    
    def print_progress(progress, message, current_task, novels_found, novels_downloaded):
        print(f"[{progress:.1f}%] {message} - {current_task}")
        if novels_found > 0:
            print(f"  找到：{novels_found}部")
        if novels_downloaded > 0:
            print(f"  已下载：{novels_downloaded}部")
    
    crawler.set_progress_callback(print_progress)
    
    # 开始爬取
    success = crawler.start()
    
    if success:
        print("\n✅ 爬取成功！")
        print(f"保存位置：./test_novels/")
        print(f"文件名：大明：开局剧透朱元璋 (第 11-20 章).txt")
    else:
        print("\n❌ 爬取失败")
        
except Exception as e:
    print(f"\n❌ 错误：{e}")
    import traceback
    traceback.print_exc()
