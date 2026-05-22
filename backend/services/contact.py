"""Contact form — send a user-submitted message to the admin inbox via Resend."""

import html
import logging
import os
import re

import resend

logger = logging.getLogger(__name__)

RESEND_FROM = os.environ.get("RESEND_FROM_EMAIL", "MarathiMitra <noreply@marathimitra.site>")
CONTACT_TO_EMAIL = os.environ.get("CONTACT_TO_EMAIL", "sumedhps@gmail.com")

# Control chars (incl. CR/LF/NUL) — strip from any value that goes into an email
# header to neutralize header-injection attempts. Tab is allowed.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _header_safe(value: str) -> str:
    """Collapse CR/LF/NUL/other control chars so the value is safe in any header."""
    return _CONTROL_CHARS_RE.sub("", value.replace("\r", " ").replace("\n", " ")).strip()


def _format_body(name: str, email: str, message: str) -> str:
    # html.escape() neutralizes <, >, &, ", ' so user input can't break out of the HTML
    # context. Normalize \r\n → \n first so escaping + <br/> conversion is consistent.
    safe_name = html.escape(name)
    safe_email = html.escape(email)
    normalized = message.replace("\r\n", "\n").replace("\r", "\n")
    safe_message = html.escape(normalized).replace("\n", "<br/>")
    return f"""
      <div style="font-family:system-ui,sans-serif;font-size:15px;line-height:1.6;color:#222;max-width:600px;">
        <p><strong>From:</strong> {safe_name} &lt;{safe_email}&gt;</p>
        <hr style="border:none;border-top:1px solid #eee;margin:16px 0;" />
        <p>{safe_message}</p>
      </div>
    """


def send_contact_email(name: str, email: str, message: str) -> bool:
    """Send the contact form submission to CONTACT_TO_EMAIL with reply-to set.

    Sanitization layers:
    - Subject uses `_header_safe(name)` to neutralize CRLF header-injection.
    - reply_to uses `_header_safe(email)`; Pydantic EmailStr already validated
      the format, this is belt-and-suspenders against control chars.
    - HTML body fields are run through html.escape() so user input can't
      inject markup, scripts, or tracking pixels.
    """
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    if not resend.api_key:
        logger.error("RESEND_API_KEY not set — cannot send contact email from %s", email)
        return False

    safe_subject_name = _header_safe(name)[:80]  # cap to keep subjects readable
    safe_reply_to = _header_safe(email)

    try:
        resend.Emails.send({
            "from": RESEND_FROM,
            "to": [CONTACT_TO_EMAIL],
            "reply_to": safe_reply_to,
            "subject": f"MarathiMitra contact: {safe_subject_name}",
            "html": _format_body(name, email, message),
        })
        logger.info("Contact email forwarded from %s to %s", email, CONTACT_TO_EMAIL)
        return True
    except Exception as e:
        logger.error("Failed to send contact email from %s: %s", email, e)
        return False
