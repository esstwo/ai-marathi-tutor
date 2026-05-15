"""Weekly parent digest — gather stats, generate AI summary, send email."""

import logging
import math
import os
from datetime import datetime, timedelta, timezone

import resend

from backend.connectors.supabase.children import get_children_by_parent
from backend.connectors.supabase.digest import (
    get_all_parents,
    get_weekly_conversations,
    get_weekly_lesson_completions,
)
from backend.core.llm import run_skill_raw
from backend.core.skill_loader import load_skills

logger = logging.getLogger(__name__)

_digest_skill = load_skills()["parent_digest"]

RESEND_FROM = os.environ.get("RESEND_FROM_EMAIL", "MarathiMitra <digest@marathimitra.com>")


# ── Data gathering ────────────────────────────────────────────────────

def _child_weekly_stats(child: dict, since: datetime) -> dict:
    child_id = child["id"]

    lessons = get_weekly_lesson_completions(child_id, since)
    conversations = get_weekly_conversations(child_id, since)

    # Derive XP from this week's activity
    xp_from_lessons = len(lessons) * 10
    xp_from_convos = sum(
        math.ceil(
            max(
                (
                    datetime.fromisoformat(c["ended_at"]) -
                    datetime.fromisoformat(c["started_at"])
                ).total_seconds(), 0
            ) / 60
        ) * 5
        for c in conversations
        if c.get("ended_at")
    )

    avg_score = (
        round(sum(l["score"] for l in lessons) / len(lessons))
        if lessons else None
    )

    return {
        "name": child["name"],
        "age": child["age"],
        "level": child["current_level"],
        "streak_days": child["streak_days"],
        "total_xp": child["xp_total"],
        "xp_this_week": xp_from_lessons + xp_from_convos,
        "lessons": lessons,
        "avg_score": avg_score,
        "conversations_count": len(conversations),
    }


# ── LLM digest generation ─────────────────────────────────────────────

def _build_prompt(parent_name: str, children_stats: list[dict]) -> str:
    lines = [
        f"Write a warm, friendly weekly Marathi learning digest email for {parent_name}.",
        "Be specific, encouraging, and personal. Use the child's name naturally.",
        "Keep it to 3-4 short paragraphs. No subject line — just the email body.",
        "End with a small tip or encouragement for next week.",
        "",
        "--- WEEKLY DATA ---",
    ]

    for c in children_stats:
        lines.append(f"\nChild: {c['name']}, age {c['age']}, Level {c['level']}")
        lines.append(f"Streak: {c['streak_days']} days | Total XP: {c['total_xp']} | XP this week: {c['xp_this_week']}")
        lines.append(f"Conversations with Mitra this week: {c['conversations_count']}")

        if c["lessons"]:
            lines.append(f"Lessons completed this week ({len(c['lessons'])}):")
            for l in c["lessons"]:
                score_str = f" — scored {l['score']}%" if l["score"] is not None else ""
                lines.append(f"  • {l['title']}{score_str}")
            if c["avg_score"] is not None:
                lines.append(f"Average quiz score: {c['avg_score']}%")
        else:
            lines.append("No lessons completed this week.")

    return "\n".join(lines)


def generate_digest_text(parent_name: str, children_stats: list[dict]) -> str:
    messages = [
        {"role": "system", "content": _digest_skill.system_prompt},
        {"role": "user", "content": _build_prompt(parent_name, children_stats)},
    ]
    return run_skill_raw(messages, connectors={}, max_tokens=_digest_skill.max_tokens)


# ── Email sending ─────────────────────────────────────────────────────

def _text_to_html(text: str) -> str:
    """Convert plain-text digest into a simple styled HTML email."""
    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    body = "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: system-ui, sans-serif; background: #fdf8f3; margin: 0; padding: 0; }}
  .wrap {{ max-width: 560px; margin: 32px auto; background: #fff; border-radius: 12px;
           padding: 32px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
  .logo {{ font-size: 1.5rem; font-weight: 700; color: #f97316; margin-bottom: 4px; }}
  .sub {{ color: #888; font-size: 0.875rem; margin-bottom: 24px; }}
  p {{ color: #333; line-height: 1.65; margin: 0 0 16px; }}
  .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee;
             font-size: 0.8rem; color: #aaa; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="logo">🇮🇳 MarathiMitra</div>
  <div class="sub">Your weekly learning digest</div>
  {body}
  <div class="footer">
    You're receiving this because you have an account on MarathiMitra.
  </div>
</div>
</body>
</html>"""


def send_digest_email(parent_email: str, parent_name: str, digest_text: str) -> bool:
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    if not resend.api_key:
        logger.error("RESEND_API_KEY not set — skipping email to %s", parent_email)
        return False

    child_names = []
    for line in digest_text.splitlines():
        pass  # name extracted by subject line below

    first_name = parent_name.split()[0] if parent_name else "there"

    try:
        resend.Emails.send({
            "from": RESEND_FROM,
            "to": [parent_email],
            "subject": f"🌟 This week's Marathi progress, {first_name}!",
            "html": _text_to_html(digest_text),
        })
        logger.info("Digest sent to %s", parent_email)
        return True
    except Exception as e:
        logger.error("Failed to send digest to %s: %s", parent_email, e)
        return False


# ── Orchestration ─────────────────────────────────────────────────────

def build_parent_digest(parent_id: str) -> dict | None:
    """Gather weekly stats and generate digest text for one parent. Returns preview dict."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    children = get_children_by_parent(parent_id)
    if not children:
        return None

    children_stats = [_child_weekly_stats(c, since) for c in children]
    return {"children_stats": children_stats}


def send_all_digests() -> dict:
    """Generate and send weekly digests to all parents. Returns a result summary."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    parents = get_all_parents()
    sent, skipped, failed = 0, 0, 0

    for parent in parents:
        try:
            children = get_children_by_parent(parent["id"])
            if not children:
                skipped += 1
                continue

            children_stats = [_child_weekly_stats(c, since) for c in children]
            digest_text = generate_digest_text(parent["name"] or "there", children_stats)
            ok = send_digest_email(parent["email"], parent["name"] or "", digest_text)
            if ok:
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.error("Digest failed for parent %s: %s", parent["id"], e)
            failed += 1

    return {"sent": sent, "skipped": skipped, "failed": failed}
