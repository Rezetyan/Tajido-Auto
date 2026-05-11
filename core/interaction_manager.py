import asyncio
import random
import time
import re
from playwright.async_api import Page, APIRequestContext
from utils.logger import logger
from utils.config import POST_URL_TEMPLATE, REPLY_URL
from utils.playwright_helpers import click_first, fill_first, first_visible_locator, safe_screenshot
from utils.selectors import LIKE_SELECTORS, REPLY_SELECTORS

class InteractionManager:
    def __init__(
        self,
        page: Page,
        api_context: APIRequestContext = None,
        dry_run: bool = False,
        reply_url: str = REPLY_URL,
        post_url_template: str = POST_URL_TEMPLATE,
    ):
        self.page = page
        self.api_context = api_context
        self.dry_run = dry_run
        self.reply_url = reply_url
        self.post_url_template = post_url_template
        self.auth_headers = {}
        self.is_running = False
        self.discovered_post_ids = set()
        
        # Intercept network requests to dynamically capture Authorization headers
        self.page.on("request", self._capture_headers)
        # 核心：拦截响应，从底层 API 直接抓取所有帖子 ID，绕过 DOM 渲染难题
        self.page.on("response", self._capture_post_ids_from_response)

    def _capture_headers(self, request):
        if "authorization" in request.headers:
            self.auth_headers["authorization"] = request.headers["authorization"]
            
    async def _capture_post_ids_from_response(self, response):
        """隐式拦截 API 响应，提取所有的帖子 ID"""
        try:
            url = response.url.lower()
            if "/api/" in url or "/v1/" in url or "/wapi/" in url or "/bbs" in url:
                if any(ext in url for ext in [".png", ".jpg", ".jpeg", ".gif", ".mp4", ".css", ".js"]):
                    return
                    
                body = await response.text()

                post_ids = self.extract_post_ids(body)
                if post_ids:
                    self.discovered_post_ids.update(post_ids)
                    logger.debug(f"API intercept: captured {len(post_ids)} post IDs from {url}")
        except Exception as e:
            logger.debug(f"Unable to inspect response for post IDs: {e}")

    @staticmethod
    def extract_post_ids(body: str) -> set[str]:
        return set(re.findall(r'"postId"\s*:\s*"?(\d{4,12})', body))

    async def delay(self, min_s=1.5, max_s=4.5):
        sleep_time = random.uniform(min_s, max_s)
        await asyncio.sleep(sleep_time)

    def stop(self):
        """外部调用，用于安全中断正在执行的循环任务"""
        self.is_running = False
        logger.info("收到停止指令，正在安全中断任务...")

    async def reply_to_comments(self):
        logger.info("Checking for new comments to reply...")
        result = {
            "ok": False,
            "dry_run": self.dry_run,
            "replied_count": 0,
            "would_reply_count": 0,
        }
        try:
            await self.page.goto(self.reply_url)
            try:
                await self.page.wait_for_load_state('networkidle', timeout=8000)
            except Exception:
                logger.debug("Reply page did not reach networkidle before timeout.")
            await self.delay()

            reply_buttons = []
            for selector in REPLY_SELECTORS.unread_reply_buttons:
                buttons = await self.page.locator(selector).all()
                if buttons:
                    reply_buttons = buttons
                    logger.debug(f"Reply buttons matched selector: {selector}")
                    break

            logger.info(f"Found {len(reply_buttons)} unread comments.")
            
            for btn in reply_buttons:
                if self.dry_run:
                    result["would_reply_count"] += 1
                    logger.info("Dry-run enabled; skipping reply open/fill/send.")
                else:
                    await btn.click()
                    await self.delay(0.5, 1.5)
                    await fill_first(self.page, REPLY_SELECTORS.reply_editors, "感谢您的支持！", "reply editor")
                    await self.delay(0.5, 1.0)
                    await click_first(self.page, REPLY_SELECTORS.send_buttons, "send reply")
                    result["replied_count"] += 1
                    logger.info("Replied to a comment successfully.")
                await self.delay()

            result["ok"] = True
            return result

        except Exception as e:
            logger.error(f"Error while replying to comments: {e}")
            await safe_screenshot(self.page, "error_reply")
            raise

    async def browse_and_like(self, target_url: str, max_likes: int = 5, max_time_minutes: float = 10.0):
        self.is_running = True
        self.discovered_post_ids.clear()
        processed_post_ids = set()
        liked_count = 0
        would_like_count = 0
        
        logger.info(f"开始自动浏览: {target_url}")
        logger.info(f"目标设置 -> 点赞数: {max_likes}, 最大运行时间: {max_time_minutes} 分钟")
        
        start_time = time.time()
        result = {
            "ok": False,
            "dry_run": self.dry_run,
            "liked_count": 0,
            "would_like_count": 0,
            "processed_post_ids": [],
            "stopped": False,
        }
        
        try:
            if max_likes <= 0:
                logger.info("点赞数为 0，自动浏览任务直接结束。")
                result["ok"] = True
                return result

            # 强制重载页面，确保重新触发 API 拦截，清空残留状态
            if self.page.url.split('#')[0] == target_url.split('#')[0]:
                logger.info("重载页面以抓取最新帖子数据...")
                await self.page.goto(target_url, wait_until='networkidle')
                await self.page.reload(wait_until='networkidle')
            else:
                await self.page.goto(target_url, wait_until='networkidle')
            
            scroll_attempts = 0
            
            while self.is_running and liked_count < max_likes and (time.time() - start_time) < max_time_minutes * 60:
                # 1. 提取当前页面上可见的常规帖子链接 (DOM Fallback)
                try:
                    await self._capture_post_ids_from_dom()
                except Exception as exc:
                    logger.debug(f"DOM post ID capture failed: {exc}")
                
                # 2. 结算待处理的全新帖子
                pending_ids = list(self.discovered_post_ids - processed_post_ids)
                
                if not pending_ids:
                    logger.info("未发现新的帖子，尝试向下滚动加载更多...")
                    try:
                        # 确保鼠标在屏幕中央点击以激活滚动容器
                        viewport = self.page.viewport_size
                        if viewport:
                            await self.page.mouse.click(viewport['width'] / 2, viewport['height'] / 2)
                        
                        # 模拟真实的键盘向下翻页，比模拟鼠标滚轮更能稳定穿透局部 overflow:auto 的 div
                        await self.page.keyboard.press('PageDown')
                        await asyncio.sleep(0.5)
                        await self.page.keyboard.press('PageDown')
                        await self.page.wait_for_load_state('networkidle', timeout=5000)
                    except Exception as exc:
                        logger.debug(f"Scrolling list failed: {exc}")
                        
                    await self.delay(2.0, 4.0)
                    scroll_attempts += 1
                    
                    if scroll_attempts > 15:
                        logger.warning("连续多次未找到新帖子，可能已到达页面底部。")
                        break
                    continue
                    
                scroll_attempts = 0 # 找到了新帖子，重置空滚计数
                
                # 增加随机化：打乱当前待处理的帖子顺序，不再固定按 ID 顺序访问
                random.shuffle(pending_ids)
                
                for pid in pending_ids:
                    if not self.is_running or liked_count >= max_likes or (time.time() - start_time) >= max_time_minutes * 60:
                        break
                        
                    processed_post_ids.add(pid)
                    
                    logger.info(f"---- 正在进入帖子 (ID: {pid}) ----")
                    # 采用新标签页打开帖子，避免主列表页面的无限滚动状态丢失
                    new_page = await self.page.context.new_page()
                    try:
                        post_full_url = self.post_url_template.format(post_id=pid)
                        await new_page.goto(post_full_url)
                        # 避免 networkidle 超时导致抛出异常中断整个流程，使用 try-except 包裹
                        try:
                            await new_page.wait_for_load_state('networkidle', timeout=5000)
                        except Exception:
                            pass
                        
                        if not self.is_running:
                            break
                            
                        logger.info("页面加载完毕，开始向下滚动寻找点赞按钮...")
                        found_like_btn = False
                        
                        # 3. 在新页面中滚动寻找通用的点赞按钮
                        for step in range(15): # 增加滚动深度，最多向下翻 15 页
                            if not self.is_running:
                                break
                                
                            try:
                                like_btn = await self.find_like_button(new_page, timeout=1500)
                                found_like_btn = True
                                await like_btn.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.5, 1.0))
                                
                                if await self.is_already_liked(like_btn):
                                    logger.info("检测到该帖子已点赞过，直接跳过并退出该帖子。")
                                    break
                                
                                if self.dry_run:
                                    would_like_count += 1
                                    liked_count += 1
                                    logger.info(f"Dry-run: 将会点赞该帖子。进度: {liked_count} / {max_likes}")
                                else:
                                    logger.info("找到未点赞按钮，执行点赞点击...")
                                    await like_btn.click()
                                    liked_count += 1
                                    logger.info(f"点赞成功！进度: {liked_count} / {max_likes}")
                                
                                await asyncio.sleep(random.uniform(1.0, 2.0))
                                break # 点赞完毕，跳出当前帖子的滚动寻找循环
                            except Exception as exc:
                                logger.debug(f"Like button not found on scroll step {step + 1}: {exc}")
                                # 没找到按钮，说明在屏幕下方，控制焦点并向下滚动一页
                                try:
                                    viewport = new_page.viewport_size
                                    if viewport:
                                        await new_page.mouse.move(viewport['width'] / 2, viewport['height'] / 2)
                                    await new_page.keyboard.press('PageDown')
                                    await asyncio.sleep(0.8) # 给长帖子图片渲染留点时间
                                except Exception as scroll_exc:
                                    logger.debug(f"Scrolling post failed: {scroll_exc}")
                                
                        if not found_like_btn and self.is_running:
                            logger.info("长达15页滚动后仍未发现点赞按钮，跳过。")
                            
                    except Exception as e:
                        logger.warning(f"处理帖子时出现异常: {e}")
                    finally:
                        # 4. 关闭帖子标签页，返回主页的循环
                        logger.info("关闭帖子，返回主列表。")
                        await new_page.close()
                        await self.delay(1.5, 3.0)
                        
                # 处理完当前视图内的一批帖子后，主页面向下滚动加载下一批
                if self.is_running:
                    logger.info("当前队列帖子处理完毕，主列表向下滚动更新数据...")
                    try:
                        viewport = self.page.viewport_size
                        if viewport:
                            await self.page.mouse.click(viewport['width'] / 2, viewport['height'] / 2)
                        await self.page.keyboard.press('PageDown')
                        await self.delay(2.0, 4.0)
                    except Exception as exc:
                        logger.debug(f"Scrolling main list after queue failed: {exc}")

            # 循环退出后的汇总播报
            if not self.is_running:
                logger.info("=== 自动浏览任务已被用户手动停止 ===")
            elif liked_count >= max_likes:
                logger.info(f"=== 自动浏览任务完成！已达到设定的点赞数: {liked_count} ===")
            else:
                logger.info(f"=== 自动浏览任务结束！因达到时间上限或浏览到底部。共点赞: {liked_count} ===")

            result.update(
                {
                    "ok": True,
                    "liked_count": 0 if self.dry_run else liked_count,
                    "would_like_count": would_like_count,
                    "processed_post_ids": sorted(processed_post_ids),
                    "stopped": not self.is_running,
                }
            )
            return result

        except Exception as e:
            logger.error(f"浏览过程中发生致命错误: {e}")
            await safe_screenshot(self.page, "error_browse")
            raise
        finally:
            self.is_running = False

    async def _capture_post_ids_from_dom(self):
        for selector in LIKE_SELECTORS.post_links:
            link_locators = await self.page.locator(selector).all()
            for loc in link_locators:
                href = await loc.get_attribute("href")
                post_id = self.extract_post_id_from_href(href or "")
                if post_id:
                    self.discovered_post_ids.add(post_id)

    @staticmethod
    def extract_post_id_from_href(href: str) -> str | None:
        match = re.search(r'(?:postId=|/post/)(\d+)', href)
        return match.group(1) if match else None

    async def find_like_button(self, page: Page, timeout: int = 1500):
        return await first_visible_locator(page, LIKE_SELECTORS.like_buttons, "like button", timeout=timeout)

    async def is_already_liked(self, locator) -> bool:
        class_attr = await locator.get_attribute("class") or ""
        html = await locator.evaluate("(el) => el.outerHTML")

        if any(marker in class_attr or marker in html for marker in LIKE_SELECTORS.unliked_markers):
            return False
        return any(marker in class_attr or marker in html for marker in LIKE_SELECTORS.liked_markers)
