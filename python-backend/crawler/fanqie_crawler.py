"""
番茄小说爬虫 - 完整版本
支持搜索、下载、字体解码，保持原始格式
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from urllib.parse import quote
import random


class FanqieCrawler:
    """番茄小说爬虫类"""
    
    def __init__(self, config):
        """
        初始化爬虫
        
        Args:
            config: 配置对象，包含 novel_name, ranking, start_page, end_page, save_path 等
        """
        self.config = config
        self.is_running = False
        self.progress_callback = None
        
        # 爬虫配置
        # User-Agent 轮换列表（增强版：更多浏览器版本）
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        ]
        
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # 会话保持
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 统计信息
        self.novels_found = 0
        self.novels_downloaded = 0
        self.total_chapters = 0
        self.downloaded_chapters = 0
        
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
        
    def update_progress(self, progress, message, current_task=""):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(
                progress, 
                message, 
                current_task,
                self.novels_found,
                self.novels_downloaded
            )
    
    def _get_page(self, url, retries=5):
        """
        获取网页内容，带重试机制（增强版）
        
        Args:
            url: 目标 URL
            retries: 重试次数
            
        Returns:
            response 对象或 None
        """
        for i in range(retries):
            try:
                # 智能延迟：首次请求延迟短，重试时延迟递增
                if i == 0:
                    delay = random.uniform(1.0, 2.0)  # 首次 1-2 秒
                elif i == 1:
                    delay = random.uniform(2.0, 3.0)  # 第二次 2-3 秒
                else:
                    delay = random.uniform(3.0, 5.0)  # 后续 3-5 秒
                
                time.sleep(delay)
                
                # 每次重试更换 User-Agent
                if i > 0:
                    self.headers['User-Agent'] = random.choice(self.user_agents)
                
                response = self.session.get(url, timeout=15)  # 增加超时时间
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"    被反爬（403），等待后重试...")
                    time.sleep(5)  # 403 错误等待更久
                elif response.status_code == 404:
                    print(f"    页面不存在（404）")
                    return None
                elif response.status_code == 503:
                    print(f"    服务不可用（503），等待后重试...")
                    time.sleep(10)  # 503 错误等待很久
                else:
                    print(f"    请求失败，状态码：{response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"    请求超时 ({i+1}/{retries})")
                if i < retries - 1:
                    time.sleep(5)
            except requests.exceptions.ConnectionError:
                print(f"    连接错误 ({i+1}/{retries})")
                if i < retries - 1:
                    time.sleep(5)
            except Exception as e:
                print(f"    请求出错 ({i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(5)
        
        return None
    
    def search_novels(self):
        """
        搜索小说 - 支持搜索和直接 URL 两种方式
        Returns:
            小说列表，每个小说包含 title, author, url, description, book_id 等信息
        """
        novels = []
        
        # 检查是否是 URL 格式
        if hasattr(self.config, 'novel_url') and self.config.novel_url:
            return self._parse_novel_url(self.config.novel_url)
        
        # 构建搜索 URL
        search_url = f'https://fanqienovel.com/search/{quote(self.config.novel_name)}'
        
        print(f'正在搜索：{self.config.novel_name}')
        response = self._get_page(search_url)
        
        if not response:
            print('搜索失败')
            return novels
        
        # 解析页面
        if '__INITIAL_STATE__' in response.text:
            try:
                start = response.text.find('__INITIAL_STATE__=') + len('__INITIAL_STATE__=')
                end = response.text.find('</script>', start)
                state_json = response.text[start:end].strip().split(';')[0].strip()
                state = json.loads(state_json)
                
                # 获取搜索结果
                if 'search' in state:
                    search_data = state['search']
                    search_list = search_data.get('searchBookList', [])
                    
                    # 处理 search_list 为 None 的情况
                    if search_list is None:
                        print('搜索结果为空 (searchBookList is None)，尝试从 HTML 解析...')
                        search_list = []
                    
                    if search_list:
                        for book in search_list:
                            novel = {
                                'title': book.get('title', '未知'),
                                'author': book.get('author', '未知'),
                                'book_id': book.get('bookId', ''),
                                'url': f'https://fanqienovel.com/page/{book.get("bookId", "")}',
                                'description': book.get('abstract', ''),
                                'word_count': book.get('wordCount', 0),
                                'category': book.get('category', ''),
                            }
                            
                            # 如果指定了作者，过滤
                            if hasattr(self.config, 'author') and self.config.author:
                                if self.config.author.lower() in novel['author'].lower():
                                    novels.append(novel)
                            else:
                                novels.append(novel)
                        
                        print(f'找到 {len(novels)} 部小说')
                        
            except Exception as e:
                print(f'解析搜索结果失败：{e}')
                import traceback
                traceback.print_exc()
        
        # 如果通过 API 没找到，尝试从 HTML 中解析
        if not novels:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 查找小说项
            novel_items = soup.select('[class*="book"], [class*="novel"]')
            
            for item in novel_items[:20]:
                title_elem = item.select_one('.title, .name, h3, a')
                author_elem = item.select_one('.author, .writer')
                link_elem = item.select_one('a[href*="/page/"]')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    author = author_elem.get_text().strip() if author_elem else '未知作者'
                    url = link_elem.get('href')
                    
                    # 提取 book_id
                    book_id_match = re.search(r'/page/(\d+)', url)
                    book_id = book_id_match.group(1) if book_id_match else ''
                    
                    # 如果指定了作者，过滤
                    if hasattr(self.config, 'author') and self.config.author:
                        if self.config.author.lower() not in author.lower():
                            continue
                    
                    novel = {
                        'title': title,
                        'author': author,
                        'book_id': book_id,
                        'url': f'https://fanqienovel.com{url}' if url.startswith('/') else url,
                        'description': '',
                        'word_count': 0,
                        'category': '',
                    }
                    novels.append(novel)
            
            print(f'从 HTML 中找到 {len(novels)} 部小说')
        
        self.novels_found = len(novels)
        return novels
    
    def _parse_novel_url(self, url):
        """
        直接从小说 URL 解析小说信息
        
        Args:
            url: 小说页面 URL（支持 /page/ 和 /reader/ 格式）
            
        Returns:
            小说列表（通常只有一个）
        """
        novels = []
        
        # 提取 book_id（支持 /page/ 和 /reader/ 两种格式）
        book_id_match = re.search(r'/(?:page|reader)/(\d+)', url)
        if not book_id_match:
            print(f'无效的 URL 格式：{url}')
            print(f'期望格式：https://fanqienovel.com/page/xxxxxx 或 https://fanqienovel.com/reader/xxxxxx')
            return novels
        
        book_id = book_id_match.group(1)
        print(f'从 URL 提取 book_id: {book_id}')
        
        # 将 URL 转换为 /page/ 格式（/reader/ 是阅读页面，/page/ 是小说信息页面）
        page_url = f'https://fanqienovel.com/page/{book_id}'
        
        # 访问小说页面获取信息
        print(f'访问小说页面：{page_url}')
        response = self._get_page(page_url)
        
        # 如果 /page/ 页面不存在，尝试从 /reader/ 页面获取信息
        if not response or response.status_code == 404:
            print(f'/page/ 页面不存在，尝试从 /reader/ 页面获取信息')
            reader_url = f'https://fanqienovel.com/reader/{book_id}'
            print(f'访问阅读页面：{reader_url}')
            response = self._get_page(reader_url)
            
            if response:
                # 从 reader 页面提取信息
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取章节标题
                title_elem = soup.select_one('.muye-reader-title')
                chapter_title = title_elem.get_text().strip() if title_elem else '第 1 章'
                
                # 提取小说名（从页面标题）
                page_title_elem = soup.find('title')
                if page_title_elem:
                    page_title = page_title_elem.get_text().strip()
                    # 从标题中提取小说名，例如："我在大明那些年第 1 章 人在大明，长生不死在线免费阅读_番茄小说官网"
                    match = re.match(r'^(.+?) 第', page_title)
                    novel_name = match.group(1) if match else page_title.split('第')[0]
                else:
                    novel_name = '未知'
                
                novel = {
                    'title': novel_name,
                    'author': '未知',  # reader 页面没有作者信息
                    'book_id': book_id,
                    'url': reader_url,
                    'description': '',
                    'word_count': 0,
                    'category': '',
                    'first_chapter_title': chapter_title,  # 第一章节标题
                }
                
                novels.append(novel)
                print(f'从 reader 页面找到小说：《{novel_name}》')
                return novels
            else:
                print('获取 reader 页面也失败')
                return novels
        
        # 解析 INITIAL_STATE（从 page 页面）
        if '__INITIAL_STATE__' in response.text:
            try:
                start = response.text.find('__INITIAL_STATE__=') + len('__INITIAL_STATE__=')
                end = response.text.find('</script>', start)
                state_json = response.text[start:end].strip().split(';')[0].strip()
                state = json.loads(state_json)
                
                if 'page' in state:
                    page_data = state['page']
                    
                    novel = {
                        'title': page_data.get('bookName', '未知'),
                        'author': page_data.get('author', '未知'),
                        'book_id': book_id,
                        'url': url,
                        'description': page_data.get('abstract', ''),
                        'word_count': page_data.get('wordNumber', 0),
                        'category': page_data.get('category', ''),
                    }
                    
                    novels.append(novel)
                    print(f'找到小说：《{novel["title"]}》作者：{novel["author"]}')
                    
            except Exception as e:
                print(f'解析小说信息失败：{e}')
                import traceback
                traceback.print_exc()
        else:
            # 如果无法解析，至少返回 book_id
            novel = {
                'title': '未知',
                'author': '未知',
                'book_id': book_id,
                'url': url,
                'description': '',
                'word_count': 0,
                'category': '',
            }
            novels.append(novel)
            print(f'无法解析小说信息，使用 book_id: {book_id}')
        
        self.novels_found = len(novels)
        return novels
    
    def get_chapter_list(self, book_id):
        """
        获取小说章节列表
        
        Args:
            book_id: 小说 ID
            
        Returns:
            章节列表，每个章节包含 title, chapter_id
        """
        chapters = []
        
        url = f'https://fanqienovel.com/page/{book_id}'
        print(f'获取章节列表：{url}')
        
        response = self._get_page(url)
        if not response:
            return chapters
        
        # 解析 INITIAL_STATE
        if '__INITIAL_STATE__' in response.text:
            try:
                start = response.text.find('__INITIAL_STATE__=') + len('__INITIAL_STATE__=')
                end = response.text.find('</script>', start)
                state_json = response.text[start:end].strip().split(';')[0].strip()
                state = json.loads(state_json)
                
                if 'page' in state:
                    page_data = state['page']
                    
                    # 获取章节 ID 列表
                    item_ids = page_data.get('itemIds', [])
                    chapter_list = page_data.get('chapterListWithVolume', [])
                    
                    # 如果有 chapterListWithVolume
                    if chapter_list:
                        chapter_index = 0
                        for volume_chapters in chapter_list:
                            if isinstance(volume_chapters, list):
                                # 分卷的情况
                                for chapter in volume_chapters:
                                    chapters.append({
                                        'title': chapter.get('title', f'第{chapter_index+1}章'),
                                        'chapter_id': chapter.get('itemId', ''),
                                        'index': chapter_index,
                                    })
                                    chapter_index += 1
                            else:
                                # 不分卷的情况
                                chapter = volume_chapters
                                chapters.append({
                                    'title': chapter.get('title', f'第{chapter_index+1}章'),
                                    'chapter_id': chapter.get('itemId', ''),
                                    'index': chapter_index,
                                })
                                chapter_index += 1
                    
                    # 如果只有 itemIds
                    elif item_ids:
                        for i, item_id in enumerate(item_ids):
                            chapters.append({
                                'title': f'第{i+1}章',
                                'chapter_id': item_id,
                                'index': i,
                            })
                    
                    print(f'找到 {len(chapters)} 个章节')
                    
            except Exception as e:
                print(f'解析章节列表失败：{e}')
        
        return chapters
    
    def download_chapter(self, chapter_id):
        """
        下载单个章节（增强版）
        
        Args:
            chapter_id: 章节 ID
            
        Returns:
            (title, content) 元组，如果失败返回 (None, None)
        """
        url = f'https://fanqienovel.com/reader/{chapter_id}'
        
        # 增加重试次数
        response = self._get_page(url, retries=5)
        if not response:
            print(f'    ⚠️  下载失败，章节 ID: {chapter_id}')
            return None, None
        
        # 检查响应状态
        if response.status_code != 200:
            print(f'    ⚠️  状态码异常：{response.status_code}')
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取章节标题
        title_elem = soup.select_one('.muye-reader-title')
        chapter_title = title_elem.get_text().strip() if title_elem else '未知章节'
        
        if not chapter_title or chapter_title == '未知章节':
            print(f'    ⚠️  未找到章节标题')
        
        # 获取章节内容（增强版：多策略提取）
        content_parts = []
        prev_text = None
        
        # 策略 1：查找主要内容区域
        content_div = soup.select_one('.muye-reader-story-content')
        if content_div:
            # 在内容区域内查找 p 标签
            p_tags = content_div.select('p')
            print(f'    找到内容区域，{len(p_tags)} 个段落')
        else:
            # 策略 2：直接查找所有 p 标签
            p_tags = soup.select('p')
            print(f'    未找到内容区域，使用全部 p 标签，共{len(p_tags)}个')
        
        # 提取并解码内容
        valid_content_count = 0
        for i, p in enumerate(p_tags):
            text = p.get_text().strip()
            
            # 跳过空文本
            if not text or len(text) == 0:
                continue
            
            # 解码字体加密
            from utils.font_decoder import decode_text
            decoded_text = decode_text(text)
            
            # 验证解码后的内容
            if decoded_text and len(decoded_text.strip()) > 0:
                # 清理空白字符
                cleaned_text = ' '.join(decoded_text.split())
                
                # 检查是否与前一行重复
                if cleaned_text != prev_text:
                    # 检查内容质量（至少有一些中文字符或标点）
                    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in cleaned_text)
                    has_punctuation = any(c in '，。！？；：""''、' for c in cleaned_text)
                    
                    if has_chinese or has_punctuation or len(cleaned_text) > 10:
                        content_parts.append(cleaned_text)
                        prev_text = cleaned_text
                        valid_content_count += 1
        
        print(f'    有效内容：{valid_content_count} 段')
        
        if content_parts:
            # 保持原始段落格式
            content = '\n\n'.join(content_parts)
            
            # 验证内容质量
            total_chars = len(content.replace(' ', '').replace('\n', ''))
            if total_chars < 50:
                print(f'    ⚠️  内容过短（{total_chars}字），可能爬取失败')
                return None, None
            
            return chapter_title, content
        
        print(f'    ❌ 未提取到有效内容')
        return None, None
    
    def download_novel(self, novel):
        """
        下载整部小说
        Args:
            novel: 小说信息字典
        Returns:
            是否成功
        """
        print(f'\n开始下载：《{novel["title"]}》作者：{novel["author"]}')
        
        # 获取章节列表
        chapters = self.get_chapter_list(novel['book_id'])
        
        # 如果没有获取到章节列表，尝试从 reader 页面连续爬取
        if not chapters:
            print('无法获取章节列表，尝试从 reader 页面连续爬取...')
            return self._download_novel_from_reader(novel)
        
        # 获取章节范围配置
        min_chapters = self.config.min_chapters if hasattr(self.config, 'min_chapters') else 1
        max_chapters = self.config.max_chapters if hasattr(self.config, 'max_chapters') else 100
        
        # 跳过前面的章节
        if min_chapters > 1:
            print(f"正在跳过前 {min_chapters - 1} 章，从第 {min_chapters} 章开始爬取...")
            if min_chapters > len(chapters):
                print(f'❌ 小说总章节数不足 {min_chapters} 章（当前共{len(chapters)}章）')
                return False
            chapters = chapters[min_chapters - 1:]  # 跳过前 min_chapters-1 章
            print(f"✅ 已定位到第 {min_chapters} 章，共 {len(chapters)} 章待爬取\n")
        
        # 限制最大章节数
        if len(chapters) > (max_chapters - min_chapters + 1):
            chapters = chapters[:(max_chapters - min_chapters + 1)]
        
        self.total_chapters = len(chapters)
        self.downloaded_chapters = 0
        
        # 创建保存目录
        save_dir = self.config.save_path if hasattr(self.config, 'save_path') else './novels'
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名（包含章节范围）
        if min_chapters > 1 or max_chapters < 100:
            filename = f"{novel['title']} (第{min_chapters}-{min_chapters + len(chapters) - 1}章).txt"
        else:
            filename = f"{novel['title']}.txt"
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filepath = os.path.join(save_dir, filename)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            # 写入小说信息
            f.write(f"标题：{novel['title']}\n")
            f.write(f"作者：{novel['author']}\n")
            if novel.get('description'):
                f.write(f"简介：{novel['description']}\n")
            if novel.get('word_count'):
                f.write(f"字数：{novel['word_count']}\n")
            if novel.get('category'):
                f.write(f"分类：{novel['category']}\n")
            
            f.write("=" * 80 + "\n\n")
            
            # 下载所有章节
            for i, chapter in enumerate(chapters):
                if not self.is_running:
                    print('用户取消下载')
                    break
                
                print(f"下载章节 {i+1}/{len(chapters)}: {chapter['title']}")
                
                title, content = self.download_chapter(chapter['chapter_id'])
                
                if title and content:
                    # 保持原始格式写入
                    f.write(f"\n\n{title}\n\n")
                    f.write(content)
                    f.write("\n")
                    
                    self.downloaded_chapters += 1
                    
                    # 更新进度
                    progress = 50 + (self.downloaded_chapters / self.total_chapters) * 50
                    self.update_progress(
                        progress,
                        f"正在下载：{chapter['title']}",
                        f"章节 {self.downloaded_chapters}/{self.total_chapters}"
                    )
                    
                    # 每 10 章休息一下
                    if (i + 1) % 10 == 0:
                        time.sleep(random.uniform(2, 4))
                    
                    # 定期更换 User-Agent（每 20 章）
                    if (i + 1) % 20 == 0:
                        self.headers['User-Agent'] = random.choice(self.user_agents)
                        print(f"🔄 已更换 User-Agent")
                else:
                    print(f"下载失败：{chapter['title']}")
        
        print(f'\n✅ 下载完成！保存至：{filepath}')
        print(f'成功下载 {self.downloaded_chapters}/{self.total_chapters} 个章节')
        
        self.novels_downloaded += 1
        return True
    
    def _download_novel_from_reader(self, novel):
        """
        从 reader 页面连续爬取小说（当无法获取章节列表时使用）
        
        Args:
            novel: 小说信息字典
            
        Returns:
            是否成功
        """
        print(f'\n开始从 reader 页面爬取：《{novel["title"]}》')
        
        # 创建保存目录
        save_dir = self.config.save_path if hasattr(self.config, 'save_path') else './novels'
        os.makedirs(save_dir, exist_ok=True)
        
        # 获取章节范围配置
        min_chapters = self.config.min_chapters if hasattr(self.config, 'min_chapters') else 1
        max_chapters = self.config.max_chapters if hasattr(self.config, 'max_chapters') else 100
        
        # 生成文件名（包含章节范围）
        if min_chapters > 1 or max_chapters < 100:
            filename = f"{novel['title']} (第{min_chapters}-{max_chapters}章).txt"
        else:
            filename = f"{novel['title']}.txt"
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filepath = os.path.join(save_dir, filename)
        
        self.downloaded_chapters = 0
        current_chapter_id = novel['book_id']  # 从第一个章节开始
        
        # 如果需要跳过前面的章节
        if min_chapters > 1:
            print(f"正在跳过前 {min_chapters - 1} 章，从第 {min_chapters} 章开始爬取...")
            for i in range(min_chapters - 1):
                if not self.is_running:
                    print('用户取消爬取')
                    return False
                
                # 获取下一章 ID
                next_id = self._get_next_chapter_id(current_chapter_id)
                if next_id:
                    current_chapter_id = next_id
                    print(f"  已跳过第 {i+1} 章")
                else:
                    print(f'❌ 小说总章节数不足 {min_chapters} 章')
                    return False
            
            print(f"✅ 已定位到第 {min_chapters} 章，开始爬取\n")
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            # 写入小说信息
            f.write(f"标题：{novel['title']}\n")
            f.write(f"作者：{novel.get('author', '未知')}\n")
            f.write("=" * 80 + "\n\n")
            
            # 连续爬取章节
            while self.is_running and self.downloaded_chapters < max_chapters:
                print(f"\n下载章节 {self.downloaded_chapters + 1}: ID={current_chapter_id}")
                
                # 下载当前章节
                title, content = self.download_chapter(current_chapter_id)
                
                if title and content:
                    # 写入章节
                    f.write(f"\n\n{title}\n\n")
                    f.write(content)
                    f.write("\n")
                    
                    self.downloaded_chapters += 1
                    print(f"✅ 成功下载：{title}")
                    
                    # 更新进度
                    progress = (self.downloaded_chapters / max_chapters) * 100
                    self.update_progress(
                        progress,
                        f"正在下载：{title}",
                        f"已下载 {self.downloaded_chapters}/{max_chapters} 章"
                    )
                    
                    # 尝试获取下一章节 ID
                    next_chapter_id = self._get_next_chapter_id(current_chapter_id)
                    if next_chapter_id and next_chapter_id != current_chapter_id:
                        current_chapter_id = next_chapter_id
                    else:
                        print('没有更多章节了')
                        break
                    
                    # 每 10 章休息一下
                    if self.downloaded_chapters % 10 == 0:
                        time.sleep(random.uniform(2, 4))
                else:
                    print(f"❌ 下载失败")
                    break
        
        if self.downloaded_chapters > 0:
            print(f'\n✅ 爬取完成！保存至：{filepath}')
            print(f'成功下载 {self.downloaded_chapters} 个章节')
            self.novels_downloaded += 1
            return True
        else:
            print('\n❌ 未能下载任何章节')
            return False
    
    def _get_next_chapter_id(self, current_chapter_id):
        """
        从当前章节页面获取下一章节 ID
        
        Args:
            current_chapter_id: 当前章节 ID
            
        Returns:
            下一章节 ID，如果没有返回 None
        """
        url = f'https://fanqienovel.com/reader/{current_chapter_id}'
        response = self._get_page(url)
        
        if not response:
            return None
        
        # 尝试从 HTML 中提取 nextItemId
        next_id_match = re.search(r'"nextItemId"\s*:\s*"(\d+)"', response.text)
        if next_id_match:
            next_id = next_id_match.group(1)
            print(f'  找到下一章 ID: {next_id}')
            return next_id
        
        # 备用方案：查找下一章按钮
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找"下一章"按钮
        next_btn = soup.select_one('a.reader-toolbar-item-next, a[href*="/reader/"][title="下一章"], .muye-reader-btns a[href*="/reader/"]')
        
        if next_btn:
            href = next_btn.get('href', '')
            match = re.search(r'/reader/(\d+)', href)
            if match:
                next_id = match.group(1)
                print(f'  找到下一章 ID: {next_id}')
                return next_id
        
        # 尝试从页面底部查找下一章链接
        next_links = soup.select('a[href*="/reader/"]')
        for link in next_links:
            href = link.get('href', '')
            match = re.search(r'/reader/(\d+)', href)
            if match:
                potential_id = match.group(1)
                if potential_id != current_chapter_id:
                    # 检查是否是下一章（通过检查链接文本）
                    link_text = link.get_text().strip()
                    if '下一' in link_text or 'next' in link_text.lower():
                        print(f'  找到下一章 ID: {potential_id}')
                        return potential_id
        
        print('  未找到下一章')
        return None
    
    def start(self):
        """开始爬取"""
        self.is_running = True
        self.novels_found = 0
        self.novels_downloaded = 0
        
        try:
            # 搜索小说
            self.update_progress(0, "正在搜索小说...", "搜索中")
            novels = self.search_novels()
            
            if not novels:
                self.update_progress(100, "未找到匹配的小说", "搜索完成")
                return False
            
            # 下载小说（只下载第一部匹配的）
            if novels:
                novel = novels[0]  # 取第一部
                success = self.download_novel(novel)
                return success
            
            return False
            
        except Exception as e:
            self.update_progress(0, f"爬取失败：{str(e)}", "发生错误")
            print(f"错误：{e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.is_running = False
    
    def stop(self):
        """停止爬取"""
        self.is_running = False
