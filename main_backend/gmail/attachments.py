
from playwright.async_api import Page

async def list_attachments(page: Page) -> list[str]:
    await page.wait_for_selector("div.aQH span.aZo", timeout=5000)
    attachments = await page.query_selector_all("div.aQH span.aZo")
    return [await a.inner_text() for a in attachments]

async def download_attachments(page: Page, download_dir: str) -> bool:
    buttons = await page.query_selector_all("div.aQH span.aZo")
    for button in buttons:
        await button.click()
        await page.wait_for_timeout(1000)
    return True
