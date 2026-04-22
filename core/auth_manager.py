import asyncio
from playwright.async_api import async_playwright, BrowserContext
import os
from utils.logger import logger
from utils.config import TARGET_URL

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "browser_data")

class AuthManager:
    def __init__(self):
        self.playwright = None
        self.context = None

    async def get_context(self) -> BrowserContext:
        if not self.playwright:
            self.playwright = await async_playwright().start()
            
        if self.context:
            return self.context
            
        logger.info("启动持久化浏览器上下文 (自动保存所有登录状态)...")
        # Launch persistent context to automatically save cookies and local storage
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            no_viewport=False, # Allow window sizing
            viewport={'width': 1280, 'height': 800},
            args=["--window-size=1280,800"] # Set a reasonable default window size instead of maximized
        )
        
        # In a persistent context, it usually comes with one empty page
        pages = self.context.pages
        page = pages[0] if pages else await self.context.new_page()
        
        logger.info(f"Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL)
        
        return self.context
            
    async def close(self):
        if self.context:
            await self.context.close()
            self.context = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
