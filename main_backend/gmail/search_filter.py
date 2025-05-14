
from playwright.async_api import Page

async def search_gmail(page: Page, query: str) -> bool:
    await page.wait_for_selector("input[name='q']")
    await page.fill("input[name='q']", query)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(2000)
    return True
