import os
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """爬虫配置类"""
    novel_name: str = ""
    novel_url: str = ""  # 小说页面 URL（可选，如果提供则直接使用 URL）
    ranking: str = "热搜榜"
    start_page: int = 1
    end_page: int = 10
    save_path: str = "./novels/"
    max_workers: int = 3
    request_timeout: int = 10
    delay_range: tuple = (1, 3)
    author: Optional[str] = None  # 作者名（可选）
    max_chapters: Optional[int] = 100  # 单次最大爬取章节数（默认 100 章）
    min_chapters: Optional[int] = 1  # 最小爬取章节数（默认从第 1 章开始）
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保保存路径存在
        os.makedirs(self.save_path, exist_ok=True)
        
        # 验证页码范围
        if self.start_page < 1:
            raise ValueError("起始页必须大于 0")
        if self.end_page < self.start_page:
            raise ValueError("结束页必须大于等于起始页")
        
        # 验证至少有一个搜索条件
        if not self.novel_name and not self.novel_url:
            raise ValueError("必须提供小说名称或小说 URL")
        
        # 验证章节范围
        if self.min_chapters < 1:
            raise ValueError("最小章节数必须大于 0")
        if self.max_chapters < self.min_chapters:
            raise ValueError("最大章节数必须大于等于最小章节数")
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'Config':
        """从字典创建配置"""
        return cls(**config_dict)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'novel_name': self.novel_name,
            'novel_url': self.novel_url,
            'ranking': self.ranking,
            'start_page': self.start_page,
            'end_page': self.end_page,
            'save_path': self.save_path,
            'max_workers': self.max_workers,
            'request_timeout': self.request_timeout,
            'delay_range': self.delay_range
        }
    
    def save_to_file(self, filepath: str):
        """保存配置到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Config':
        """从文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "ranking_options": ["热搜榜", "飙升榜", "完结榜", "新书榜", "评分榜"],
            "default_save_path": "./novels/",
            "max_pages": 100,
            "max_workers_range": (1, 10),
            "api_timeout": 30
        }
    
    def load_user_config(self) -> Optional[dict]:
        """加载用户配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def save_user_config(self, config: dict):
        """保存用户配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_default_config(self) -> dict:
        """获取默认配置"""
        return self.default_config.copy()
