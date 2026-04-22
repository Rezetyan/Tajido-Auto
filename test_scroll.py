import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://www.tajiduo.com/bbs/index.html#/home?id=2', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        async def get_scroll():
            return await page.evaluate('''() => {
                let el = document.querySelector(".flex-1.w-full.pb-\\\\[30px\\\\].overflow-y-auto") || document.scrollingElement;
                return el ? el.scrollTop : -1;
            }''')
        
        print('Before scroll:', await get_scroll())
        
        viewport = page.viewport_size
        await page.mouse.click(viewport['width'] / 2, viewport['height'] / 2)
        await page.keyboard.press('PageDown')
        await page.wait_for_timeout(1000)
        
        print('After PageDown:', await get_scroll())
        
        await page.mouse.move(viewport['width'] / 2, viewport['height'] / 2)
        await page.mouse.wheel(0, 1500)
        await page.wait_for_timeout(1000)
        
        print('After Wheel:', await get_scroll())
        
        await browser.close()

asyncio.run(main())
