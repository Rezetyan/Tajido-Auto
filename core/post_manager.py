import asyncio
import random
import os
from playwright.async_api import Page
from utils.logger import logger

class PostManager:
    def __init__(self, page: Page):
        self.page = page

    async def delay(self, min_s=1.5, max_s=4.5):
        sleep_time = random.uniform(min_s, max_s)
        await asyncio.sleep(sleep_time)

    async def create_post(self, text_content: str, image_path: str = None):
        logger.info("Starting create post flow...")
        try:
            # 1. Click "New Post" button (Selector needs adjustment based on actual site)
            logger.info("Clicking new post button...")
            await self.page.click('button.new-post-btn', timeout=10000)
            await self.delay()

            # 2. Fill text content
            logger.info("Filling text content...")
            await self.page.locator('textarea.post-editor').fill(text_content)
            await self.delay()

            # 3. Upload image if provided
            if image_path and os.path.exists(image_path):
                logger.info(f"Uploading image: {image_path}")
                # Playwright's set_input_files automatically intercepts the file chooser dialog
                await self.page.locator('input[type="file"]').set_input_files(image_path)
                await self.delay(2.0, 5.0) # Wait a bit longer for upload to complete

            # 4. Submit
            logger.info("Submitting post...")
            # We wait for the post creation API response to confirm it went through
            async with self.page.expect_response(lambda response: "create" in response.url and response.status == 200, timeout=15000) as response_info:
                await self.page.click('button.submit-post-btn')
            
            response = await response_info.value
            logger.info(f"Post created successfully! Response status: {response.status}")

        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            await self.page.screenshot(path="error_post.png")
            # We raise the exception to allow main loop to handle it, or we could just swallow it
            raise e
