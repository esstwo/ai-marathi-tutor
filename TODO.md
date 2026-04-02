# MarathiMitra — TODO

## Auth
- [ ] Switch from localStorage tokens to httpOnly cookies (more secure, simpler frontend — eliminates interceptor/refresh logic, but needs CORS `credentials: true` + cookie domain config for Vercel/Render cross-origin)

## Capstone Review Fixes (Remaining)
- [ ] Fix 4 (Section 3.2): Compute `marathi_ratio` — calculate Devanagari character ratio in child messages, write to `conversations` table in `end_conversation`
- [ ] Fix 5 (Section 3.5): Prompt engineering — add few-shot examples, Romanized Marathi handling, conversation flow control to `mitra_system.py`

## Plugin Architecture (Phases 2-4)
- [ ] Phase 2: Deploy MCP servers as separate Render services (supabase-mcp, tts-mcp) with Python MCP SDK
- [ ] Phase 3: LLM-as-Orchestrator — pass MCP tool definitions to Groq, let LLM call tools directly
- [ ] Phase 4 (deferred): Thin gateway — replace FastAPI with minimal auth proxy
