import asyncio
import random
import time
import re
from playwright.async_api import Page, APIRequestContext
from utils.logger import logger

class InteractionManager:
    def __init__(self, page: Page, api_context: APIRequestContext = None):
        self.page = page
        self.api_context = api_context # For hybrid approach (API calls)
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
                # 过滤掉图片和多媒体请求，防止 body 读取异常
                if any(ext in url for ext in [".png", ".jpg", ".jpeg", ".gif", ".mp4"]):
                    return
                    
                body = await response.text()
                
                # 策略1: 明确寻找 "postId": 12345
                post_ids = re.findall(r'"postId"\s*:\s*"?(\d{4,9})', body)
                if post_ids:
                    self.discovered_post_ids.update(post_ids)
                    logger.debug(f"API 拦截: 从 {url} 抓取到 {len(post_ids)} 个 postId")
                    
                # 策略2: 如果是列表接口，直接抓取通用 "id" 字段
                if any(x in url for x in ['list', 'feed', 'recommend', 'home', 'post', 'topic']):
                    ids = re.findall(r'"id"\s*:\s*"?(\d{5,9})', body)
                    if ids:
                        self.discovered_post_ids.update(ids)
                        logger.debug(f"API 拦截: 从 {url} 抓取到 {len(ids)} 个 id")
        except Exception as e:
            # 静默处理由于页面跳转等原因导致的 read text 失败
            pass

    async def delay(self, min_s=1.5, max_s=4.5):
        sleep_time = random.uniform(min_s, max_s)
        await asyncio.sleep(sleep_time)

    def stop(self):
        """外部调用，用于安全中断正在执行的循环任务"""
        self.is_running = False
        logger.info("收到停止指令，正在安全中断任务...")

    async def reply_to_comments(self):
        logger.info("Checking for new comments to reply...")
        try:
            await self.page.goto("https://www.tajiduo.com/bbs/index.html#/notifications")
            await self.page.wait_for_load_state('networkidle')
            await self.delay()

            reply_buttons = await self.page.locator('button.reply-btn.unread').all()
            logger.info(f"Found {len(reply_buttons)} unread comments.")
            
            for btn in reply_buttons:
                await btn.click()
                await self.delay(0.5, 1.5)
                await self.page.locator('textarea.reply-editor').fill("感谢您的支持！")
                await self.delay(0.5, 1.0)
                await self.page.click('button.send-reply-btn')
                logger.info("Replied to a comment successfully.")
                await self.delay()

        except Exception as e:
            logger.error(f"Error while replying to comments: {e}")
            await self.page.screenshot(path="error_reply.png")

    async def browse_and_like(self, target_url: str, max_likes: int = 5, max_time_minutes: float = 10.0):
        self.is_running = True
        self.discovered_post_ids.clear()
        processed_post_ids = set()
        
        logger.info(f"开始自动浏览: {target_url}")
        logger.info(f"目标设置 -> 点赞数: {max_likes}, 最大运行时间: {max_time_minutes} 分钟")
        
        start_time = time.time()
        
        try:
            # 强制重载页面，确保重新触发 API 拦截，清空残留状态
            if self.page.url.split('#')[0] == target_url.split('#')[0]:
                logger.info("重载页面以抓取最新帖子数据...")
                await self.page.goto(target_url, wait_until='networkidle')
                await self.page.reload(wait_until='networkidle')
            else:
                await self.page.goto(target_url, wait_until='networkidle')
            
            liked_count = 0
            scroll_attempts = 0
            
            while self.is_running and liked_count < max_likes and (time.time() - start_time) < max_time_minutes * 60:
                # 1. 提取当前页面上可见的常规帖子链接 (DOM Fallback)
                try:
                    link_locators = await self.page.locator('a[href*="postId="], a[href*="/post/"]').all()
                    for loc in link_locators:
                        href = await loc.get_attribute("href")
                        if href:
                            match = re.search(r'(?:postId=|\/post\/)(\d+)', href)
                            if match:
                                self.discovered_post_ids.add(match.group(1))
                except Exception:
                    pass
                
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
                    except Exception:
                        pass
                        
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
                        post_full_url = f"https://www.tajiduo.com/bbs/index.html#/post?postId={pid}"
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
                                
                            # 使用包含 like 图标的 div 群组，不预先限定颜色，便于识别已点赞状态
                            like_btn = new_page.locator('div.group:has(div[class*="like"])').first
                            
                            try:
                                # 设置 1.5 秒超时，如果没看到就抛异常进入 except 块继续滚动
                                await like_btn.wait_for(state="visible", timeout=1500)
                                found_like_btn = True
                                await like_btn.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.5, 1.0))
                                
                                # 获取按钮的 class，判断是否已点赞
                                class_attr = await like_btn.get_attribute("class")
                                # 注意：未点赞的按钮类名中也包含 hover:text-secondary-color
                                # 因此，必须严格判断是否包含未点赞特有的灰色类名 text-tajido-gray-3
                                if class_attr and "text-tajido-gray-3" not in class_attr:
                                    logger.info("检测到该帖子已点赞过，直接跳过并退出该帖子。")
                                    break
                                
                                logger.info("✅ 找到未点赞按钮，执行点赞点击...")
                                await like_btn.click()
                                liked_count += 1
                                logger.info(f"点赞成功！进度: {liked_count} / {max_likes}")
                                
                                await asyncio.sleep(random.uniform(1.0, 2.0))
                                break # 点赞完毕，跳出当前帖子的滚动寻找循环
                            except Exception:
                                # 没找到按钮，说明在屏幕下方，控制焦点并向下滚动一页
                                try:
                                    viewport = new_page.viewport_size
                                    if viewport:
                                        await new_page.mouse.move(viewport['width'] / 2, viewport['height'] / 2)
                                    await new_page.keyboard.press('PageDown')
                                    await asyncio.sleep(0.8) # 给长帖子图片渲染留点时间
                                except Exception:
                                    pass
                                
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
                    except Exception:
                        pass

            # 循环退出后的汇总播报
            if not self.is_running:
                logger.info("=== 自动浏览任务已被用户手动停止 ===")
            elif liked_count >= max_likes:
                logger.info(f"=== 自动浏览任务完成！已达到设定的点赞数: {liked_count} ===")
            else:
                logger.info(f"=== 自动浏览任务结束！因达到时间上限或浏览到底部。共点赞: {liked_count} ===")

        except Exception as e:
            logger.error(f"浏览过程中发生致命错误: {e}")
            await self.page.screenshot(path="error_browse.png")
        finally:
            self.is_running = False