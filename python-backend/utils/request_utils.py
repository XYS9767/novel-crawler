import requests
import time
import random
from urllib.parse import urljoin, urlparse
import logging

class RequestManager:
    """请求管理器，处理HTTP请求和反爬措施"""
    
    def __init__(self, timeout=10, max_retries=3, delay_range=(1, 3)):
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    def get(self, url, **kwargs):
        """发送GET请求，带有重试机制"""
        return self._request_with_retry('GET', url, **kwargs)
    
    def post(self, url, data=None, json=None, **kwargs):
        """发送POST请求，带有重试机制"""
        return self._request_with_retry('POST', url, data=data, json=json, **kwargs)
    
    def _request_with_retry(self, method, url, **kwargs):
        """带重试的请求方法"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                
                # 随机延迟，避免请求过快
                self._random_delay()
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    raise e
                    
                # 指数退避延迟
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
    
    def _random_delay(self):
        """随机延迟"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def set_proxies(self, proxies):
        """设置代理"""
        self.session.proxies.update(proxies)
    
    def update_headers(self, headers):
        """更新请求头"""
        self.session.headers.update(headers)
    
    def close(self):
        """关闭会话"""
        self.session.close()

def is_valid_url(url):
    """验证URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def build_absolute_url(base_url, relative_url):
    """构建绝对URL"""
    if is_valid_url(relative_url):
        return relative_url
    return urljoin(base_url, relative_url)