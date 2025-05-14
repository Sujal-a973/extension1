import asyncio

from main_backend.browser.browser import Browser
from main_backend.gmail import (compose_email, extract_email_thread,
                                parse_full_inbox, read_opened_email_content,
                                search_gmail, star_email,
                                summarize_email_with_openai)


async def run():
    # Step 1: Boot persistent Chrome
    browser = Browser()
    playwright_browser = await browser.get_playwright_browser()
    context = await playwright_browser.new_context()
    page = await context.new_page()
    
    await page.goto("https://mail.google.com", timeout=60000)
    print("[+] Opened Gmail... waiting for manual login if needed.")
    await page.wait_for_timeout(10000)

    # Step 2: Gmail Tasks
    print("[+] Parsing Inbox...")
    emails = await parse_full_inbox(page)
    for email in emails[:5]:
        print(email)

    # Step 3: Search
    await search_gmail(page, "project update")

    # Step 4: Read + Summarize
    await page.wait_for_timeout(2000)
    await page.click("table[role=grid] tr")
    content = await read_opened_email_content(page)
    print("[+] Subject:", content["subject"])
    print("[+] Summary:")
    print(await summarize_email_with_openai(content["body_text"]))

    # Step 5: Compose + Send
    await compose_email(
        page=page,
        to="someone@example.com",
        subject="Demo Mail",
        body="This is a test from our Gmail agent.",
        send=False  # Set to True to send
    )
    print("[+] Drafted email.")

    # Step 6: Star an email
    await star_email(page, subject_text="Demo")

    await page.wait_for_timeout(5000)
    await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
