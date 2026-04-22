import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import asyncio
import os
import sys

from core.auth_manager import AuthManager
from core.post_manager import PostManager
from core.interaction_manager import InteractionManager
from utils.logger import logger
import logging

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

class TajidoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("塔吉多 (Tajido) 自动化助手")
        self.root.geometry("650x580")
        
        # 居中显示
        self.root.eval('tk::PlaceWindow . center')
        
        # Setup async loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, args=(self.loop,), daemon=True)
        self.thread.start()
        
        # Managers
        self.auth_manager = AuthManager()
        self.context = None
        self.page = None
        self.api_context = None
        
        self.post_manager = None
        self.interaction_manager = None

        self.setup_ui()

    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
        
    def setup_ui(self):
        # 1. 顶部控制面板
        control_frame = tk.LabelFrame(self.root, text="控制面板", padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.btn_init = tk.Button(control_frame, text="1. 初始化 / 登录浏览器", command=self.run_init, bg="#d9edf7", font=('微软雅黑', 10, 'bold'))
        self.btn_init.grid(row=0, column=0, columnspan=3, pady=10, sticky="we", ipady=5)

        # 发帖区域
        tk.Label(control_frame, text="发帖内容:").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_post_text = tk.Entry(control_frame, width=40)
        self.entry_post_text.insert(0, "这是一个自动发布的测试帖子！")
        self.entry_post_text.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        self.btn_post = tk.Button(control_frame, text="2. 自动发帖", command=self.run_post, state=tk.DISABLED, width=15)
        self.btn_post.grid(row=1, column=2, padx=5, pady=5)

        # 互动区域
        tk.Label(control_frame, text="自动回复:").grid(row=2, column=0, sticky="e", pady=5)
        tk.Label(control_frame, text="检查我的帖子下的新评论并回复", fg="gray").grid(row=2, column=1, sticky="w", padx=5)
        self.btn_reply = tk.Button(control_frame, text="3. 自动回复新评论", command=self.run_reply, state=tk.DISABLED, width=15)
        self.btn_reply.grid(row=2, column=2, padx=5, pady=5)

        # 浏览区域设置
        tk.Label(control_frame, text="目标链接:").grid(row=3, column=0, sticky="e", pady=5)
        self.entry_url = tk.Entry(control_frame, width=40)
        self.entry_url.insert(0, "https://www.tajiduo.com/bbs/index.html#/home?id=2") # 默认主页
        self.entry_url.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        settings_frame = tk.Frame(control_frame)
        settings_frame.grid(row=4, column=1, sticky="w")
        
        tk.Label(settings_frame, text="点赞数:").pack(side=tk.LEFT)
        self.entry_likes = tk.Entry(settings_frame, width=5)
        self.entry_likes.insert(0, "5")
        self.entry_likes.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(settings_frame, text="最长运行(分钟):").pack(side=tk.LEFT)
        self.entry_time = tk.Entry(settings_frame, width=5)
        self.entry_time.insert(0, "10")
        self.entry_time.pack(side=tk.LEFT)
        
        # 浏览按钮组
        browse_btn_frame = tk.Frame(control_frame)
        browse_btn_frame.grid(row=3, column=2, rowspan=2, padx=5, pady=5)
        
        self.btn_like = tk.Button(browse_btn_frame, text="4. 自动浏览点赞", command=self.run_like, state=tk.DISABLED, width=15)
        self.btn_like.pack(side=tk.TOP, pady=(0, 5))
        
        self.btn_stop = tk.Button(browse_btn_frame, text="停止当前任务", command=self.stop_task, state=tk.DISABLED, width=15, bg="#f2dede")
        self.btn_stop.pack(side=tk.TOP)

        # 2. 日志输出面板
        log_frame = tk.LabelFrame(self.root, text="实时运行日志", padx=10, pady=10)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=12, bg="#f4f4f4", font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 重定向 logger 到 GUI
        text_handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)
        
        logger.info("GUI 初始化完成，等待连接浏览器...")

    def run_coroutine(self, coro):
        """将异步任务投递到后台事件循环中执行"""
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def run_init(self):
        self.btn_init.config(state=tk.DISABLED, text="正在启动浏览器...")
        self.run_coroutine(self._async_init())

    async def _async_init(self):
        try:
            logger.info("正在启动浏览器内核，请稍候...")
            self.context = await self.auth_manager.get_context()
            
            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()
            self.api_context = self.context.request
            
            # 初始化Managers
            self.post_manager = PostManager(self.page)
            self.interaction_manager = InteractionManager(self.page, self.api_context)
            
            # 监听浏览器上下文关闭事件
            self.context.on("close", lambda _: self.root.after(0, self.on_browser_closed))
            
            logger.info("浏览器初始化成功！")
            logger.info("若未登录，请在弹出的浏览器窗口中完成手动登录。")
            logger.info("登录完成后，您可以点击下方按钮开始自动化任务。")
            
            # 在主线程更新UI状态，激活其余按钮
            self.root.after(0, lambda: self.btn_init.config(text="浏览器已连接，运行中...", bg="#dff0d8"))
            self.root.after(0, lambda: self.btn_post.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_reply.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_like.config(state=tk.NORMAL))
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            self.root.after(0, lambda: self.btn_init.config(state=tk.NORMAL, text="1. 初始化 / 登录浏览器"))

    def on_browser_closed(self):
        # 避免重复触发
        if self.btn_init['state'] == tk.NORMAL:
            return
            
        logger.warning("检测到浏览器已被主动关闭！")
        self.btn_init.config(state=tk.NORMAL, text="1. 初始化 / 登录浏览器", bg="#d9edf7")
        self.btn_post.config(state=tk.DISABLED)
        self.btn_reply.config(state=tk.DISABLED)
        self.btn_like.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        
        # Cleanup
        self.context = None
        self.page = None
        self.api_context = None
        self.post_manager = None
        self.interaction_manager = None
        self.auth_manager.context = None

    def stop_task(self):
        if self.interaction_manager:
            self.interaction_manager.stop()
        self.btn_stop.config(state=tk.DISABLED)

    def run_post(self):
        text = self.entry_post_text.get()
        if not text:
            logger.warning("发帖内容不能为空！")
            return
            
        # 尝试读取 assets/sample.png 如果不存在则忽略
        image_path = os.path.join("assets", "sample.png")
        if not os.path.exists(image_path):
            image_path = None
            
        self.btn_post.config(state=tk.DISABLED)
        self.run_coroutine(self._async_post(text, image_path))

    async def _async_post(self, text, image_path):
        try:
            if self.post_manager:
                await self.post_manager.create_post(text, image_path)
        except Exception as e:
            logger.error(f"自动发帖任务异常: {e}")
        finally:
            self.root.after(0, lambda: self.btn_post.config(state=tk.NORMAL))

    def run_reply(self):
        self.btn_reply.config(state=tk.DISABLED)
        self.run_coroutine(self._async_reply())

    async def _async_reply(self):
        try:
            if self.interaction_manager:
                await self.interaction_manager.reply_to_comments()
        except Exception as e:
            logger.error(f"自动回复任务异常: {e}")
        finally:
            self.root.after(0, lambda: self.btn_reply.config(state=tk.NORMAL))

    def run_like(self):
        target_url = self.entry_url.get()
        if not target_url:
            logger.warning("目标链接不能为空！")
            return
            
        try:
            max_likes = int(self.entry_likes.get())
            max_time = float(self.entry_time.get())
        except ValueError:
            logger.error("点赞数和最长运行时间必须是有效的数字！")
            return
            
        self.btn_like.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.run_coroutine(self._async_like(target_url, max_likes, max_time))

    async def _async_like(self, target_url, max_likes, max_time):
        try:
            if self.interaction_manager:
                await self.interaction_manager.browse_and_like(
                    target_url=target_url, 
                    max_likes=max_likes, 
                    max_time_minutes=max_time
                )
        except Exception as e:
            logger.error(f"自动浏览任务异常: {e}")
        finally:
            self.root.after(0, lambda: self.btn_like.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))
        
    def on_closing(self):
        logger.info("正在关闭程序...")
        self.root.after(0, lambda: self.btn_init.config(state=tk.DISABLED))
        
        # Ensure we stop any running task
        if self.interaction_manager:
            self.interaction_manager.stop()
            
        if self.auth_manager and self.auth_manager.context:
            self.run_coroutine(self._async_close())
        else:
            self.root.destroy()
            sys.exit(0)

    async def _async_close(self):
        try:
            await self.auth_manager.close()
        except Exception as e:
            logger.error(f"关闭浏览器时出现异常: {e}")
        finally:
            self.root.after(0, self.root.destroy)
            os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = TajidoGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
