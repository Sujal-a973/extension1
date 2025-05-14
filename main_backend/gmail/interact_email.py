
from playwright.async_api import Page

async def reply_to_email(page: Page, reply_text: str, quote: bool = False) -> bool:
    await page.wait_for_selector("div[aria-label='Reply']")
    await page.click("div[aria-label='Reply']")
    await page.wait_for_selector("div[aria-label='Message Body']")
    await page.fill("div[aria-label='Message Body']", reply_text)
    await page.click("div[aria-label*='Send'][role=button]")
    await page.wait_for_timeout(1000)
    return True

async def forward_email(page: Page, forward_to: str, extra_note: str = "") -> bool:
    await page.wait_for_selector("div[aria-label='More']")
    await page.click("div[aria-label='More']")
    await page.click("div[role='menuitem']:has-text('Forward')")
    await page.wait_for_selector("textarea[name=to]")
    await page.fill("textarea[name=to]", forward_to)
    if extra_note:
        await page.fill("div[aria-label='Message Body']", extra_note)
    await page.click("div[aria-label*='Send'][role=button]")
    return True
