import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name='novel_crawler', log_level=logging.INFO):
    """设置日志配置"""
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, f'crawler_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器 - 滚动日志，最大10MB，保留5个备份
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024, 
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class ProgressLogger:
    """进度日志记录器"""
    def __init__(self, logger):
        self.logger = logger
        self.start_time = datetime.now()
        
    def log_progress(self, current, total, message):
        """记录进度日志"""
        if total > 0:
            progress = (current / total) * 100
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            if current > 0:
                remaining = (elapsed / current) * (total - current)
                eta = f"ETA: {remaining:.1f}s"
            else:
                eta = "ETA: Calculating..."
                
            self.logger.info(
                f"Progress: {progress:.1f}% ({current}/{total}) - {message} - {eta}"
            )
    
    def log_task_start(self, task_name):
        """记录任务开始"""
        self.logger.info(f"Starting task: {task_name}")
        
    def log_task_complete(self, task_name, result=None):
        """记录任务完成"""
        if result:
            self.logger.info(f"Completed task: {task_name} - Result: {result}")
        else:
            self.logger.info(f"Completed task: {task_name}")
    
    def log_error(self, task_name, error):
        """记录错误"""
        self.logger.error(f"Task failed: {task_name} - Error: {error}")