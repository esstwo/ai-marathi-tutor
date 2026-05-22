"""Contact form — send a user-submitted message to the admin inbox via Resend."""

import html
import logging
import os

import resend

logger = logging.getLogger(__name__)

RESEND_FROM = os.environ.get("RESEND_FROM_EMAIL", "MarathiMitra <noreply@marathimitra.site>")
CONTACT_TO_EMAIL = os.environ.get("CONTACT_TO_EMAIL", "sumedhps@gmail.com")


def _format_body(name: str, email: str, message: str) -> str:
    safe_name = html.escape(name)
    safe_email = html.escape(email)
    safe_message = html.escape(message).replace("\n", "<br/>")
    return f"""
      <div style="font-family:system-ui,sans-serif;font-size:15px;line-height:1.6;color:#222;max-width:600px;">
        <p><strong>From:</strong> {safe_name} &lt;{safe_email}&gt;</p>
        <hr style="border:none;border-top:1px solid #eee;margin:16px 0;" />
        <p>{safe_message}</p>
      </div>
    """


def send_contact_email(name: str, email: str, message: str) -> bool:
    """Send the contact form submission to CONTACT_TO_EMAIL with reply-to set."""
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    if not resend.api_key:
        logger.error("RESEND_API_KEY not set — cannot send contact email from %s", email)
        return False

    try:
        resend.Emails.send({
            "from": RESEND_FROM,
            "to": [CONTACT_TO_EMAIL],
            "reply_to": email,
            "subject": f"MarathiMitra contact: {name}",
            "html": _format_body(name, email, message),
        })
        logger.info("Contact email forwarded from %s to %s", email, CONTACT_TO_EMAIL)
        return True
    except Exception as e:
        logger.error("Failed to send contact email from %s: %s", email, e)
        return False
