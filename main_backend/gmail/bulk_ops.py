
from playwright.async_api import Page

async def bulk_select_emails(page: Page, count: int = 5) -> bool:
    checkboxes = await page.query_selector_all("div.oZ-jc input[type='checkbox']")
    for i in range(min(count, len(checkboxes))):
        await checkboxes[i].click()
    return True

async def bulk_delete(page: Page) -> bool:
    await page.click("div[aria-label='Delete']")
    await page.wait_for_timeout(1000)
    return True
