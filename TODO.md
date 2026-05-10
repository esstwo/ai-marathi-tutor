# MarathiMitra — TODO

## Auth
- [ ] Switch from localStorage tokens to httpOnly cookies (more secure, simpler frontend — eliminates interceptor/refresh logic, but needs CORS `credentials: true` + cookie domain config for Vercel/Render cross-origin)

## Capstone Review Fixes (Remaining)
- [ ] Fix 4 (Section 3.2): Compute `marathi_ratio` — calculate Devanagari character ratio in child messages, write to `conversations` table in `end_conversation`
- [ ] Fix 5 (Section 3.5): Prompt engineering — add few-shot examples, Romanized Marathi handling, conversation flow control to `skills/conversation.md`

## Plugin Architecture
- [x] Phase 1: Extract skill definitions as Markdown files with YAML frontmatter (`skills/conversation.md`, `lessons.md`, `progress.md`) + skill loader
- [x] Phase 2: Split MCP tools into domain-grouped connectors (`connectors/supabase/`, `connectors/tts/`) + connector registry
- [x] Phase 3: Generic agentic loop in `core/llm.py` — `run_skill(skill, messages, connectors)` works with any skill
- [x] Phase 4: Thin HTTP gateway (`gateway/api.py`) replacing 5 router files
- [x] Phase 5: MCP server (`mcp_server.py`) exposing skills + connectors for Claude Desktop
- [x] Phase 6: Cleanup — wired gateway into main.py, deleted old modules (routers/, mcp/, dependencies/, models/, prompts/)
- [ ] Optional: Deploy MCP server as separate Render service with SSE transport for external MCP clients

## MCP App (Interactive UI inside Claude)
- [x] Scaffold TypeScript MCP App server in `mcp-app/` with `@modelcontextprotocol/sdk`
- [x] Add service key auth bypass to FastAPI gateway for server-to-server calls
- [x] Create API client (`api-client.ts`) proxying to FastAPI with `X-Service-Key` header
- [x] Build MCP server (`server.ts`) with 3 primary tools + 7 inner tools + 3 HTML resources
- [x] Create shared CSS design system (`styles/shared.css`) with Devanagari fonts
- [x] Build progress app (`mcp-app/apps/progress.html`) — XP, streak, level dashboard with roadmap
- [ ] Build conversation app (`mcp-app/apps/conversation.html`) — chat UI with Mitra, TTS playback, message history
- [ ] Build lessons app (`mcp-app/apps/lessons.html`) — lesson browser, vocabulary cards, quiz interface
- [ ] Bundle with Vite + vite-plugin-singlefile for sandboxed iframe delivery
- [ ] Deploy as remote MCP server with SSE transport + cloudflared or Render
- [ ] Register as Claude custom connector for testing
