import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def intercept(res):
            if 'getRecommendPostList' in res.url:
                body = await res.text()
                with open('api_response.json', 'w', encoding='utf-8') as f:
                    f.write(body)
                print("Dumped API response")
                
        page.on('response', intercept)

        await page.goto('https://www.tajiduo.com/bbs/index.html#/home?id=2', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        await browser.close()

asyncio.run(main())
