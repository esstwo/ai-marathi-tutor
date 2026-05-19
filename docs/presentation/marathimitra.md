<!--
MarathiMitra — 5–7 min presentation
Format: Marp markdown. To render:
  brew install marp-cli  # one-time
  marp marathimitra.md -o marathimitra.pdf      # PDF
  marp marathimitra.md -o marathimitra.pptx     # PowerPoint
  marp marathimitra.md --html -o marathimitra.html
Or install the "Marp for VS Code" extension and preview live.

Screenshot placeholders: drop PNGs into ./screenshots/ with the filenames
referenced in each slide and they'll pick up automatically.
-->

---
marp: true
theme: default
class: invert
paginate: true
size: 16:9
style: |
  section {
    background: linear-gradient(135deg, #0F1F1E 0%, #1F3A38 100%);
    color: #E8F4F2;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  h1, h2 { color: #5BAFA9; font-weight: 700; }
  h1 { font-size: 2.4em; }
  h2 { font-size: 1.8em; }
  strong { color: #5BAFA9; }
  blockquote { border-left: 4px solid #5BAFA9; color: #B8D4D0; }
  code { background: rgba(91,175,169,0.15); color: #B8E0DC; padding: 2px 6px; border-radius: 4px; }
  table { font-size: 0.85em; }
  th { background: rgba(91,175,169,0.2); }
  .placeholder {
    background: rgba(91,175,169,0.1);
    border: 2px dashed #5BAFA9;
    padding: 60px 40px;
    text-align: center;
    color: #5BAFA9;
    font-style: italic;
    border-radius: 12px;
  }
---

<!-- _class: invert lead -->

# MarathiMitra
## मराठीमित्र

**Your child's AI best friend for learning spoken Marathi**

<br>

marathimitra.site

---

## The problem

**Diaspora kids understand Marathi — but freeze when it's time to speak.**

- They hear it at home, but reply in English
- Lose confidence; the gap widens with age
- Traditional apps (Duolingo-style) are great for vocabulary, terrible for spoken practice
- 1:1 tutors cost ₹500–1500/hour, can't be on-demand at bedtime
- Parents juggle full-time work; they can't run Marathi lessons every evening

> Result: a whole generation of kids who can *understand* their mother tongue but can't comfortably *speak* it.

---

## How MarathiMitra helps

**A patient, always-available AI tutor — designed around how kids actually learn languages.**

| Feature | What it does |
|---|---|
| **Mitra** (AI chat) | Friendly Marathi conversation partner — never judgmental, code-switches naturally |
| **80 Lessons** | Bite-sized vocab + grammar + interactive quizzes across 4 levels |
| **Missions** | Scenario-based gameplay — "buy from a shopkeeper", "talk to आजी on a video call" |
| **Voice in & out** | Mic for the kid, Marathi TTS for Mitra — practice the *sounds*, not just text |
| **Weekly parent digest** | AI writes a personalised "here's how your child did this week" email every Sunday |

---

## See it in action

<!-- Replace these placeholders with real screenshots from marathimitra.site -->

<div class="placeholder">
  [Screenshot: ./screenshots/landing.png]<br>
  Landing page — bot logo, "Learn Marathi with your AI Best Friend"
</div>

<br>

<div class="placeholder">
  [Screenshot: ./screenshots/chat.png — Mitra mid-conversation]
  &nbsp;&nbsp;&nbsp;
  [Screenshot: ./screenshots/mission.png — Mission in progress]
</div>

---

## Architecture at a glance

<div class="placeholder">
  [Screenshot: ./screenshots/architecture-diagram.png]<br>
  Or sketch: React frontend → FastAPI gateway → Skills (.md) + Connectors (.py)<br>
  Backed by Supabase, Sarvam AI (LLM), Google Cloud TTS, Resend
</div>

**Stack:** React + Vite (Vercel) · FastAPI (Render) · Supabase · Sarvam AI · Google TTS · Resend

---

## The key idea: Skills + Connectors

<br>

**Old way:** business logic + AI prompts buried in Python service code

**New way:**
- **Skills** = portable Markdown files. Each one is a system prompt + YAML metadata (inputs, outputs, which connectors it needs). The skill *is* the intelligence.
- **Connectors** = tiny Python functions that touch external systems (Supabase, TTS). Zero business logic.
- **Gateway** = thin HTTP layer that loads a skill, hands it connectors, and runs a generic agentic loop.

> Adding a new capability = writing a new `.md` file. No Python plumbing.

The same skill files run in the web app, in Claude Desktop (via MCP), or in any future client.

---

## LLM as orchestrator

**Instead of the backend orchestrating the LLM…**

```python
# OLD: backend knows what context it needs
profile = fetch_profile(child_id)
lesson = fetch_lesson(level)
response = call_llm(prompt, profile, lesson)
```

**…the LLM orchestrates the backend.**

```python
# NEW: LLM gets connector tools and decides what it needs
result = run_skill(conversation_skill, messages, connectors={
    "get_child_profile": ...,
    "get_lesson_context": ...,
})
```

The LLM sees the connector list as OpenAI-style tool schemas (auto-generated from Python function signatures), calls what it needs, gets results back, and returns a final response. Backend logic shrinks; intelligence grows.

---

## Why we moved off Groq to Sarvam AI

**Was:** Groq Llama 3.3 70B (free-tier, rate-limited — became a launch blocker)

**Now:** Sarvam-105B — Marathi-native model, OpenAI-compatible API

| | Groq Llama 3.3 (paid) | Sarvam-105B |
|---|---|---|
| Input cost | $0.59/M tokens | **$0.048/M tokens** |
| Output cost | $0.79/M tokens | **$0.19/M tokens** |
| Marathi quality | Decent (multilingual) | **Native** |
| Hard rate cap | Tier-based | Pay-per-use |

**Estimated cost at 100 active kids, 20 messages/day each: ~$15–25/month**

Free ₹1000 credits cover the first 1–2 months entirely.

---

## Sarvam: three sharp design choices

**1. No vendor SDK lock-in.** Sarvam's API is OpenAI-compatible, so we use the `openai` Python SDK pointed at `https://api.sarvam.ai/v1`. Switching providers in future = changing one base URL.

**2. Three-layer JSON enforcement.** Sarvam doesn't support `response_format={"type":"json_object"}`. Solution:
- Each skill prompt has a strict "Output format" section at the top
- The gateway appends a `[Reply as JSON object: {...}]` reminder to every user turn (not saved to history, so the chat UI stays clean)
- `parse_json_response` is defensive: strips markdown fences, then extracts the first `{...}` substring, then falls back to plain text

**3. Pre-fetch context instead of tool-calling.** mission_guide previously asked the LLM to call `get_child_profile` + `get_mission_by_id` as tools. The gateway already had that data. We now inject it directly into the system prompt — **1 LLM round per turn instead of 3–4**, no possibility of empty responses from exhausted tool loops.

---

## Production-ready: cost & abuse hardening

Before opening signups publicly:

- **Per-child daily LLM cap** — persisted in Supabase via atomic Postgres RPC, defaults to 100 calls/day. One abusive account can't burn the global budget.
- **Per-IP signup rate limit** — persisted, X-Forwarded-For aware, blocks bots even before they touch Supabase Auth.
- **Cloudflare Turnstile** on both signup AND login — verified server-side by Supabase.
- **Email verification** before login (Supabase) + **branded Resend templates** for verification / reset / digest.
- **CORS that doesn't lie** — env parser tolerates whitespace, logs parsed allowlist at startup.
- 123 pytest cases covering every guardrail surface.

---

## What's next

- Per-child caps on heavy LLM endpoints: mission generation, Whisper STT, Google TTS
- Provider-side hard quotas: GCP TTS character/day quota, Sarvam spend alerts
- Deploy the MCP App as a remote MCP server → interactive Marathi practice **inside claude.ai**
- Sarvam Bulbul TTS — Marathi-native voice synthesis to replace Google TTS

<br>

## Try it

**🌐 marathimitra.site** · **📦 github.com/esstwo/ai-marathi-tutor**

---

<!-- _class: invert lead -->

# धन्यवाद!
## Thank you

**Questions?**
