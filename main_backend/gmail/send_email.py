from playwright.async_api import Page
from main_backend.gmail.compose_email import compose_email

async def send_email(
    page: Page,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    attachment_path: str = ""
) -> bool:
    return await compose_email(
        page=page,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        send=True,
        attachment_path=attachment_path
    )
