import os
import time
from collections.abc import Iterable

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from utils.config import SCREENSHOT_DIR
from utils.logger import logger


class LocatorNotFoundError(RuntimeError):
    def __init__(self, action_name: str, selectors: Iterable[str]):
        self.action_name = action_name
        self.selectors = tuple(selectors)
        super().__init__(
            f"Unable to find locator for {action_name}. Tried: {', '.join(self.selectors)}"
        )


async def first_visible_locator(
    scope,
    selectors: Iterable[str],
    action_name: str,
    timeout: int = 1500,
    state: str = "visible",
):
    tried = []
    for selector in selectors:
        tried.append(selector)
        locator = scope.locator(selector).first
        try:
            await locator.wait_for(state=state, timeout=timeout)
            logger.debug(f"{action_name}: matched selector {selector}")
            return locator
        except PlaywrightTimeoutError:
            logger.debug(f"{action_name}: selector not visible: {selector}")
        except Exception as exc:
            logger.debug(f"{action_name}: selector failed {selector}: {exc}")
    raise LocatorNotFoundError(action_name, tried)


async def click_first(scope, selectors: Iterable[str], action_name: str, timeout: int = 1500):
    locator = await first_visible_locator(scope, selectors, action_name, timeout=timeout)
    await locator.click()
    return locator


async def fill_first(scope, selectors: Iterable[str], value: str, action_name: str, timeout: int = 1500):
    locator = await first_visible_locator(scope, selectors, action_name, timeout=timeout)
    try:
        await locator.fill(value)
    except Exception:
        await locator.click()
        await locator.press("Control+A")
        await locator.type(value)
    return locator


async def safe_screenshot(page: Page, name: str) -> str | None:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{timestamp}.png")
    try:
        await page.screenshot(path=path, full_page=True)
        return path
    except Exception as exc:
        logger.debug(f"Unable to write screenshot {path}: {exc}")
        return None
