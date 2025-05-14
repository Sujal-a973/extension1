
from playwright.async_api import Page
import os

# ---- Compose and send email ----
async def compose_email(
    page: Page,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    send: bool = True,
    attachment_path: str = ""
) -> bool:
    await page.wait_for_selector("div.T-I.T-I-KE.L3", timeout=10000)
    await page.click("div.T-I.T-I-KE.L3")  # Compose button

    await page.wait_for_selector("textarea[name=to]", timeout=5000)
    await page.fill("textarea[name=to]", to)

    if cc:
        await page.click("span.aB.gQ.pE")  # CC toggle
        await page.fill("textarea[name=cc]", cc)

    if bcc:
        await page.click("span.aB.gQ.pB")  # BCC toggle
        await page.fill("textarea[name=bcc]", bcc)

    await page.fill("input[name=subjectbox]", subject)
    await page.fill("div[aria-label='Message Body']", body)

    if attachment_path and os.path.exists(attachment_path):
        file_input = await page.query_selector("input[type='file']")
        if file_input:
            await file_input.set_input_files(attachment_path)
            await page.wait_for_timeout(2000)  # wait for upload

    if send:
        await page.click("div[aria-label*='Send'][role=button]")
    else:
        await page.click("img[aria-label='Close']")  # Save as draft by closing
        await page.wait_for_timeout(1000)

    return True
