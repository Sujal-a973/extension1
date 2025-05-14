
from playwright.async_api import Page
import openai
from bs4 import BeautifulSoup

# ---- STEP 1: Open email by subject ----
async def open_email_by_subject(page: Page, subject_text: str) -> bool:
    await page.wait_for_selector("table[role=grid] tr")
    rows = await page.query_selector_all("table[role=grid] tr")

    for row in rows:
        subject_el = await row.query_selector("span.bog")
        if subject_el:
            subject = await subject_el.inner_text()
            if subject_text.lower() in subject.lower():
                await row.click()
                await page.wait_for_timeout(1000)
                return True
    return False


# ---- STEP 2: Read opened email content ----
async def read_opened_email_content(page: Page) -> dict:
    await page.wait_for_selector("h2.hP")
    subject = await page.inner_text("h2.hP")
    sender = await page.inner_text("span.gD")
    date = await page.inner_text("span.g3")

    body_el = await page.query_selector("div.a3s.aXjCH")
    body_html = await body_el.inner_html() if body_el else ""
    body_text = await body_el.inner_text() if body_el else ""

    if not body_text.strip():
        body_text = extract_clean_text_from_html(body_html)

    return {
        "subject": subject.strip(),
        "sender": sender.strip(),
        "date": date.strip(),
        "body_text": body_text,
        "body_html": body_html
    }


# ---- STEP 3: Fallback for HTML-to-text ----
def extract_clean_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n").strip()


# ---- STEP 4: GPT-4 summarization ----
async def summarize_email_with_openai(text: str) -> str:
    prompt = f"Summarize this email in 2-3 lines:\n\n{text.strip()}"
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes emails."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] OpenAI summarization failed: {str(e)}"


# ---- STEP 5: Extract thread of messages ----
async def extract_email_thread(page: Page) -> list[dict]:
    await page.wait_for_selector("div.adn")
    thread_blocks = await page.query_selector_all("div.adn")
    thread_data = []

    for block in thread_blocks:
        try:
            sender = await block.query_selector_eval("span.gD", "el => el?.innerText || ''")
            timestamp = await block.query_selector_eval("span.g3", "el => el?.innerText || ''")
            body_el = await block.query_selector("div.a3s")
            body_text = await body_el.inner_text() if body_el else ""
        except:
            sender, timestamp, body_text = None, None, None

        thread_data.append({
            "sender": sender.strip() if sender else None,
            "timestamp": timestamp.strip() if timestamp else None,
            "body": body_text.strip() if body_text else None
        })

    return thread_data
