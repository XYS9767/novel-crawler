"""
番茄小说爬虫 GUI 界面
基于 tkinter 实现
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import sys

# 添加项目路径（父目录）
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from crawler.fanqie_crawler import FanqieCrawler
from utils.config import Config


class NovelCrawlerGUI:
    """小说爬虫 GUI 主窗口"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("番茄小说爬虫")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
        # 爬虫相关变量
        self.crawler = None
        self.is_running = False
        
        # 创建界面
        self.create_widgets()
        
        # 设置样式
        self.setup_styles()
    
    def setup_styles(self):
        """设置界面样式"""
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 标题样式
        style.configure('Title.TLabel', font=('微软雅黑', 16, 'bold'))
        
        # 标签样式
        style.configure('Label.TLabel', font=('微软雅黑', 10))
        
        # 按钮样式
        style.configure('Start.TButton', font=('微软雅黑', 11, 'bold'))
        style.configure('Stop.TButton', font=('微软雅黑', 11, 'bold'))
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📚 番茄小说爬虫", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 小说名称输入
        input_frame = ttk.LabelFrame(main_frame, text="小说信息", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # 小说名称
        ttk.Label(input_frame, text="小说名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.novel_name_var = tk.StringVar()
        self.novel_name_entry = ttk.Entry(input_frame, textvariable=self.novel_name_var, width=50)
        self.novel_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ttk.Label(input_frame, text="（或通过下方 URL 直接爬取）", foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # 小说 URL（可选）
        ttk.Label(input_frame, text="小说 URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.novel_url_var = tk.StringVar()
        self.novel_url_entry = ttk.Entry(input_frame, textvariable=self.novel_url_var, width=50)
        self.novel_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ttk.Label(input_frame, text="（可选，优先级高于小说名称）", foreground="gray").grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # 作者名称（可选）
        ttk.Label(input_frame, text="作者名称:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.author_var = tk.StringVar()
        self.author_entry = ttk.Entry(input_frame, textvariable=self.author_var, width=50)
        self.author_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ttk.Label(input_frame, text="（可选，用于过滤搜索结果）", foreground="gray").grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # 最大章节数
        ttk.Label(input_frame, text="最大章节数:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_chapters_var = tk.StringVar(value="100")
        self.max_chapters_entry = ttk.Entry(input_frame, textvariable=self.max_chapters_var, width=20)
        self.max_chapters_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Label(input_frame, text="（默认 100 章，防止过度爬取）", foreground="gray").grid(row=3, column=2, sticky=tk.W, padx=(5, 0))
        
        # 最小章节数（新增）
        ttk.Label(input_frame, text="最小章节数:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.min_chapters_var = tk.StringVar(value="1")
        self.min_chapters_entry = ttk.Entry(input_frame, textvariable=self.min_chapters_var, width=20)
        self.min_chapters_entry.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Label(input_frame, text="（默认 1，可设置从第几章开始）", foreground="gray").grid(row=4, column=2, sticky=tk.W, padx=(5, 0))
        
        # 保存路径
        ttk.Label(input_frame, text="保存路径:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.save_path_var = tk.StringVar(value="./novels/")
        self.save_path_entry = ttk.Entry(input_frame, textvariable=self.save_path_var, width=50)
        self.save_path_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ttk.Button(input_frame, text="浏览...", command=self.browse_save_path).grid(row=5, column=2, sticky=tk.W, padx=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="▶ 开始爬取", style='Start.TButton', 
                                       command=self.start_crawling, width=15)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="⏸ 停止爬取", style='Stop.TButton', 
                                      command=self.stop_crawling, width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1)
        
        # 进度条
        progress_frame = ttk.LabelFrame(main_frame, text="爬取进度", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 进度信息
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, 
                                style='Label.TLabel')
        status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 统计信息
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        self.found_var = tk.StringVar(value="找到小说：0 部")
        ttk.Label(stats_frame, textvariable=self.found_var).grid(row=0, column=0, padx=(0, 20))
        
        self.downloaded_var = tk.StringVar(value="已下载：0 部")
        ttk.Label(stats_frame, textvariable=self.downloaded_var).grid(row=0, column=1)
        
        # 日志窗口
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, 
                                                  wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置日志文本颜色
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        
        # 底部信息
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(info_frame, text="提示：支持爬取番茄小说网站的所有公开小说", 
                 foreground="gray").pack(side=tk.LEFT)
    
    def browse_save_path(self):
        """浏览保存路径"""
        current_path = self.save_path_var.get()
        if not os.path.exists(current_path):
            current_path = os.path.dirname(os.path.abspath(__file__))
        
        selected_dir = filedialog.askdirectory(initialdir=current_path, 
                                               title="选择保存目录")
        if selected_dir:
            # 转换为相对路径
            base_dir = os.path.dirname(os.path.abspath(__file__))
            try:
                rel_path = os.path.relpath(selected_dir, base_dir)
                self.save_path_var.set(rel_path)
            except ValueError:
                # 如果不在同一驱动器，使用绝对路径
                self.save_path_var.set(selected_dir)
    
    def log(self, message, level="info"):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n", level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, progress, message, current_task, novels_found, novels_downloaded):
        """更新进度回调"""
        self.progress_var.set(progress)
        self.status_var.set(message)
        self.found_var.set(f"找到小说：{novels_found} 部")
        self.downloaded_var.set(f"已下载：{novels_downloaded} 部")
        self.log(f"[{progress:.1f}%] {message} - {current_task}")
        self.root.update_idletasks()
    
    def start_crawling(self):
        """开始爬取"""
        # 验证输入
        novel_name = self.novel_name_var.get().strip()
        novel_url = self.novel_url_var.get().strip()
        
        if not novel_name and not novel_url:
            messagebox.showerror("错误", "请输入小说名称或小说 URL！")
            return
        
        # 创建配置
        try:
            author = self.author_var.get().strip() if self.author_var.get().strip() else None
            
            # 获取最大章节数
            try:
                max_chapters = int(self.max_chapters_var.get().strip())
                if max_chapters <= 0:
                    raise ValueError("必须大于 0")
            except ValueError:
                max_chapters = 100  # 默认值
            
            # 获取最小章节数
            try:
                min_chapters = int(self.min_chapters_var.get().strip())
                if min_chapters <= 0:
                    raise ValueError("必须大于 0")
            except ValueError:
                min_chapters = 1  # 默认值
            
            config = Config(
                novel_name=novel_name,
                novel_url=novel_url,
                author=author,
                save_path=self.save_path_var.get(),
                max_chapters=max_chapters,
                min_chapters=min_chapters,
            )
        except Exception as e:
            messagebox.showerror("错误", f"配置创建失败：{str(e)}")
            return
        
        # 创建爬虫
        self.crawler = FanqieCrawler(config)
        self.crawler.set_progress_callback(self.update_progress)
        
        # 更新 UI 状态
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.novel_name_entry.config(state=tk.DISABLED)
        self.author_entry.config(state=tk.DISABLED)
        self.save_path_entry.config(state=tk.DISABLED)
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        if novel_url:
            self.log(f"开始爬取：URL={novel_url}" + (f" 作者：{author}" if author else ""), "info")
        else:
            self.log(f"开始爬取：《{novel_name}》" + (f" 作者：{author}" if author else ""), "info")
        
        # 在新线程中运行爬虫
        def run_crawler():
            try:
                success = self.crawler.start()
                self.root.after(0, lambda: self.crawling_finished(success))
            except Exception as e:
                self.root.after(0, lambda: self.crawling_error(str(e)))
        
        thread = threading.Thread(target=run_crawler, daemon=True)
        thread.start()
    
    def stop_crawling(self):
        """停止爬取"""
        if self.crawler and self.is_running:
            self.log("正在停止爬取...", "warning")
            self.crawler.stop()
            self.is_running = False
    
    def crawling_finished(self, success):
        """爬取完成"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.novel_name_entry.config(state=tk.NORMAL)
        self.author_entry.config(state=tk.NORMAL)
        self.save_path_entry.config(state=tk.NORMAL)
        
        if success:
            self.log("✅ 爬取完成！", "success")
            messagebox.showinfo("成功", "小说爬取成功！\n请查看保存目录。")
        else:
            self.log("❌ 爬取失败或已取消", "error")
            messagebox.showwarning("提示", "爬取失败或已取消")
        
        self.progress_var.set(100)
        self.status_var.set("爬取完成")
    
    def crawling_error(self, error_msg):
        """爬取出错"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.novel_name_entry.config(state=tk.NORMAL)
        self.author_entry.config(state=tk.NORMAL)
        self.save_path_entry.config(state=tk.NORMAL)
        
        self.log(f"❌ 错误：{error_msg}", "error")
        messagebox.showerror("错误", f"爬取过程中发生错误：\n{error_msg}")
        self.progress_var.set(0)
        self.status_var.set("发生错误")


def main():
    """主函数"""
    root = tk.Tk()
    app = NovelCrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
