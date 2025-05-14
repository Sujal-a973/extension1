
from playwright.async_api import Page

async def star_email(page: Page, subject_text: str) -> bool:
    rows = await page.query_selector_all("table[role=grid] tr")
    for row in rows:
        subject_el = await row.query_selector("span.bog")
        if subject_el:
            text = await subject_el.inner_text()
            if subject_text.lower() in text.lower():
                star_icon = await row.query_selector("div[role=checkbox] ~ div[role=link] img[aria-label*='Not starred']")
                if star_icon:
                    await star_icon.click()
                    return True
    return False
