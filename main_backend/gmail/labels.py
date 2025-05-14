
from playwright.async_api import Page
from main_backend.gmail import parse_full_inbox

# ---- Create a new label ----
async def create_label(page: Page, label_name: str) -> bool:
    await page.click("div[aria-label='Main menu']")
    await page.wait_for_selector("div[aria-label='More']", timeout=5000)
    await page.click("div[aria-label='More']")
    await page.wait_for_selector("div[role='button'][aria-label*='Create new label']", timeout=5000)
    await page.click("div[role='button'][aria-label*='Create new label']")
    await page.fill("input[name='newLabelName']", label_name)
    await page.click("button[name='ok']")
    await page.wait_for_timeout(1000)
    return True

# ---- Move email to a label ----
async def move_email_to_label(page: Page, email_subject: str, label_name: str) -> bool:
    await page.wait_for_selector("table[role=grid] tr")
    rows = await page.query_selector_all("table[role=grid] tr")
    for row in rows:
        subject_el = await row.query_selector("span.bog")
        if subject_el:
            subject_text = await subject_el.inner_text()
            if email_subject.lower() in subject_text.lower():
                await row.click()
                break
    else:
        return False

    await page.wait_for_selector("div[aria-label='Move to']")
    await page.click("div[aria-label='Move to']")
    await page.wait_for_selector("div.J-M.J-M-ayU[role='menu']")
    labels = await page.query_selector_all("div.J-M.J-M-ayU[role='menu'] div.J-N")
    for label in labels:
        label_text = await label.inner_text()
        if label_name.lower() in label_text.lower():
            await label.click()
            await page.wait_for_timeout(1000)
            return True
    return False

# ---- Apply multiple labels to an email ----
async def apply_labels_to_email(page, email_subject: str, labels_to_apply: list[str]) -> bool:
    await page.wait_for_selector("table[role=grid] tr")
    rows = await page.query_selector_all("table[role=grid] tr")
    for row in rows:
        subject_el = await row.query_selector("span.bog")
        if subject_el:
            subject_text = await subject_el.inner_text()
            if email_subject.lower() in subject_text.lower():
                await row.click()
                break
    else:
        return False

    await page.wait_for_selector("div[aria-label='Labels']")
    await page.click("div[aria-label='Labels']")
    await page.wait_for_selector("div.J-M.J-M-ayU[role='menu']")
    menu_items = await page.query_selector_all("div.J-M.J-M-ayU[role='menu'] div.J-N")
    for label in labels_to_apply:
        for item in menu_items:
            label_text = await item.inner_text()
            if label.lower() in label_text.lower():
                await item.click()
                await page.wait_for_timeout(200)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    return True

# ---- Remove a label from an email ----
async def remove_label_from_email(page, email_subject: str, label_name: str) -> bool:
    await page.wait_for_selector("table[role=grid] tr")
    rows = await page.query_selector_all("table[role=grid] tr")
    for row in rows:
        subject_el = await row.query_selector("span.bog")
        if subject_el:
            subject_text = await subject_el.inner_text()
            if email_subject.lower() in subject_text.lower():
                await row.click()
                break
    else:
        return False

    await page.wait_for_selector("div[aria-label='Labels']")
    await page.click("div[aria-label='Labels']")
    await page.wait_for_selector("div.J-M.J-M-ayU[role='menu']")
    labels = await page.query_selector_all("div.J-M.J-M-ayU[role='menu'] div.J-N")
    for label in labels:
        label_text = await label.inner_text()
        aria_checked = await label.get_attribute("aria-checked")
        if label_name.lower() in label_text.lower() and aria_checked == "true":
            await label.click()
            await page.wait_for_timeout(300)
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    return True

# ---- Organize by Gmail category tab ----
async def get_emails_by_category(page, category: str, max_pages: int = 1) -> list[dict]:
    tab_map = {"Primary": "Primary", "Promotions": "Promotions", "Social": "Social"}
    await page.wait_for_selector("div.aKz")
    tabs = await page.query_selector_all("div.aKz")
    for tab in tabs:
        text = await tab.inner_text()
        if tab_map[category].lower() in text.lower():
            await tab.click()
            await page.wait_for_timeout(1000)
            break
    return await parse_full_inbox(page, max_pages=max_pages)
