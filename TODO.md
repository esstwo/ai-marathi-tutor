# MarathiMitra — TODO

## Auth
- [ ] Switch from localStorage tokens to httpOnly cookies (more secure, simpler frontend — eliminates interceptor/refresh logic, but needs CORS `credentials: true` + cookie domain config for Vercel/Render cross-origin)

## Capstone Review Fixes (Remaining)
- [ ] Fix 4 (Section 3.2): Compute `marathi_ratio` — calculate Devanagari character ratio in child messages, write to `conversations` table in `end_conversation`
- [ ] Fix 5 (Section 3.5): Prompt engineering — add few-shot examples, Romanized Marathi handling, conversation flow control to `mitra_system.py`

## Plugin Architecture (Remaining Phases)
- [x] Phase 1: Internal refactor — consolidated all Supabase operations into `backend/mcp/supabase_tools.py`, extracted LLM logic into `backend/skills/mitra_conversation.py`
- [x] Phase 2: In-process MCP servers — wired up FastMCP servers (supabase-mcp with 19 tools, tts-mcp with 1 tool), async MCP client calls throughout, token refresh endpoint
- [ ] Phase 2b (optional): Deploy MCP servers as separate Render services with SSE/HTTP transport
- [x] Phase 3: LLM-as-Orchestrator — pass MCP tool definitions to Groq, let LLM call tools directly (agentic loop in `call_llm`, JSON structured output, LLM fetches its own context via tools)
- [ ] Phase 4 (deferred): Thin gateway — replace FastAPI with minimal auth proxy
