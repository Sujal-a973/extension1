
from playwright.async_api import Page

async def parse_inbox(page: Page) -> list[dict]:
    await page.wait_for_selector("table[role=grid] tr")
    rows = await page.query_selector_all("table[role=grid] tr")
    emails = []
    for row in rows:
        sender = await row.query_selector_eval("span[email]", "el => el?.textContent")
        subject = await row.query_selector_eval("span.bog", "el => el?.textContent")
        snippet = await row.query_selector_eval("span.y2", "el => el?.textContent")
        is_unread = await row.get_attribute("class")
        unread = "zE" in is_unread if is_unread else False
        emails.append({
            "sender": sender.strip() if sender else None,
            "subject": subject.strip() if subject else None,
            "snippet": snippet.strip() if snippet else None,
            "unread": unread
        })
    return emails

async def click_load_more_if_exists(page: Page) -> bool:
    try:
        next_button = await page.query_selector("div[aria-label='Older']")
        if next_button:
            await next_button.click()
            await page.wait_for_timeout(1000)
            return True
    except:
        pass
    return False

async def parse_full_inbox(page: Page, max_pages: int = 3) -> list[dict]:
    all_emails = []
    for _ in range(max_pages):
        emails = await parse_inbox(page)
        all_emails.extend(emails)
        has_more = await click_load_more_if_exists(page)
        if not has_more:
            break
    return all_emails

async def get_active_inbox_tab(page: Page) -> str:
    tabs = await page.query_selector_all("div.aKz")
    for tab in tabs:
        class_attr = await tab.get_attribute("class")
        if "aKS" in class_attr:
            label = await tab.inner_text()
            return label.strip()
    return "Unknown"
