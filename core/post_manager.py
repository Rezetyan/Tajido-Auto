import asyncio
import random
import os
from playwright.async_api import Page
from utils.logger import logger
from utils.config import CREATE_POST_URL
from utils.playwright_helpers import click_first, fill_first, first_visible_locator, safe_screenshot
from utils.selectors import POST_SELECTORS

class PostManager:
    def __init__(self, page: Page, dry_run: bool = False, create_post_url: str = CREATE_POST_URL):
        self.page = page
        self.dry_run = dry_run
        self.create_post_url = create_post_url

    async def delay(self, min_s=1.5, max_s=4.5):
        sleep_time = random.uniform(min_s, max_s)
        await asyncio.sleep(sleep_time)

    async def create_post(
        self,
        text_content: str,
        image_path: str = None,
        title: str = None,
        community: str = "异环",
        column: str = "「呗果」揭示板",
    ):
        logger.info("Starting create post flow...")
        result = {
            "ok": False,
            "dry_run": self.dry_run,
            "submitted": False,
            "image_uploaded": False,
            "category_selected": False,
        }

        try:
            if not text_content or not text_content.strip():
                raise ValueError("Post content cannot be empty.")

            if "#/create" not in self.page.url:
                logger.info("Opening create post page...")
                if "#/home" in self.page.url:
                    try:
                        await click_first(
                            self.page,
                            POST_SELECTORS.create_entry_links,
                            "open create post entry",
                            timeout=2500,
                        )
                    except Exception:
                        logger.debug("Create entry link was not visible; navigating directly.")
                        await self.page.goto(self.create_post_url)
                else:
                    await self.page.goto(self.create_post_url)
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    logger.debug("Create page did not reach networkidle before timeout.")
            await self.delay()

            post_title = title or self._build_title(text_content)
            logger.info("Filling post title...")
            await fill_first(self.page, POST_SELECTORS.title_inputs, post_title, "post title")

            logger.info("Filling text content...")
            await fill_first(self.page, POST_SELECTORS.text_editors, text_content, "post body")
            await self.delay()

            await self.select_category(community=community, column=column)
            result["category_selected"] = True
            await self.delay(0.5, 1.0)

            if image_path and self.dry_run:
                logger.info("Dry-run enabled; skipping image selection/upload.")
            elif image_path and os.path.exists(image_path):
                logger.info(f"Uploading image: {image_path}")
                file_input = await first_visible_locator(
                    self.page,
                    POST_SELECTORS.file_inputs,
                    "post image input",
                    timeout=2000,
                    state="attached",
                )
                await file_input.set_input_files(image_path)
                result["image_uploaded"] = True
                await self.delay(2.0, 5.0)
            elif image_path:
                logger.warning(f"Image path does not exist, sending text only: {image_path}")

            if self.dry_run:
                logger.info("Dry-run enabled; skipping post submission.")
                result["ok"] = True
                return result

            logger.info("Submitting post...")
            async with self.page.expect_response(
                lambda response: any(token in response.url.lower() for token in ("create", "publish", "post"))
                and response.status < 400,
                timeout=15000,
            ) as response_info:
                await click_first(self.page, POST_SELECTORS.submit_buttons, "submit post", timeout=3000)

            response = await response_info.value
            result["ok"] = True
            result["submitted"] = True
            result["response_status"] = response.status
            logger.info(f"Post created successfully! Response status: {response.status}")
            return result

        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            await safe_screenshot(self.page, "error_post")
            raise

    def _build_title(self, text_content: str) -> str:
        first_line = text_content.strip().splitlines()[0]
        return first_line[:50] or "自动发布"

    async def select_category(self, community: str = "异环", column: str = "「呗果」揭示板"):
        logger.info(f"Selecting post category: {community} / {column}")
        await click_first(
            self.page,
            POST_SELECTORS.category_fields,
            "category field",
            timeout=3000,
        )
        await self.delay(0.2, 0.5)
        await click_first(
            self.page,
            self._format_selectors(POST_SELECTORS.category_primary_options, community),
            f"category primary option {community}",
            timeout=3000,
        )
        await self.delay(0.2, 0.5)
        await click_first(
            self.page,
            self._format_selectors(POST_SELECTORS.category_leaf_options, column),
            f"category leaf option {column}",
            timeout=3000,
        )

    def _format_selectors(self, selectors: tuple[str, ...], text: str) -> tuple[str, ...]:
        escaped = text.replace('"', '\\"')
        return tuple(selector.format(text=escaped) for selector in selectors)
