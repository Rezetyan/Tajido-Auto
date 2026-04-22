import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def intercept(res):
            if 'wapi' in res.url:
                try:
                    body = await res.text()
                    if 'postId' in body:
                        print('Found postId in', res.url)
                except Exception as e:
                    pass
                
        page.on('response', intercept)

        await page.goto('https://www.tajiduo.com/bbs/index.html#/home?id=2', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print('Scrolling to bottom...')
        await page.evaluate('''() => {
            let elements = document.querySelectorAll('*');
            for(let i=0; i<elements.length; i++) {
                let el = elements[i];
                let style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                    el.scrollTop += 5000;
                    console.log('Scrolled element:', el.className);
                }
            }
            window.scrollBy(0, 5000);
        }''')
        await page.wait_for_timeout(3000)
        
        await browser.close()

asyncio.run(main())
