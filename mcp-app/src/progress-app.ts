/**
 * Progress app — renders child's learning dashboard inside MCP App iframe.
 *
 * Receives progress data from the tool result via the MCP App protocol.
 * Renders: level card with XP bar, stats grid, next level tips, level roadmap.
 */

// ── Types ────────────────────────────────────────────────────────────

interface ChildProgress {
  xp_total: number;
  streak_days: number;
  current_level: number;
  lessons_completed: number;
  conversations_count: number;
}

interface Level {
  level: number;
  name: string;
  xpNeeded: number;
  emoji: string;
}

// ── Constants ────────────────────────────────────────────────────────

const LEVELS: Level[] = [
  { level: 1, name: "Beginner", xpNeeded: 0, emoji: "\u{1F331}" },
  { level: 2, name: "Explorer", xpNeeded: 100, emoji: "\u{1F50D}" },
  { level: 3, name: "Learner", xpNeeded: 300, emoji: "\u{1F4DA}" },
  { level: 4, name: "Speaker", xpNeeded: 600, emoji: "\u{1F5E3}\u{FE0F}" },
  { level: 5, name: "Fluent", xpNeeded: 1000, emoji: "\u{1F3C6}" },
];

// ── Helpers ──────────────────────────────────────────────────────────

function getCurrentLevel(xp: number): Level {
  let current = LEVELS[0];
  for (const l of LEVELS) {
    if (xp >= l.xpNeeded) current = l;
    else break;
  }
  return current;
}

function getNextLevel(xp: number): Level | null {
  for (const l of LEVELS) {
    if (xp < l.xpNeeded) return l;
  }
  return null;
}

// ── Render ───────────────────────────────────────────────────────────

function render(progress: ChildProgress): void {
  const app = document.getElementById("app")!;
  const xp = progress.xp_total;
  const current = getCurrentLevel(xp);
  const next = getNextLevel(xp);

  const xpInLevel = next ? xp - current.xpNeeded : 0;
  const xpForNext = next ? next.xpNeeded - current.xpNeeded : 1;
  const pct = next ? Math.round((xpInLevel / xpForNext) * 100) : 100;
  const xpRemaining = next ? next.xpNeeded - xp : 0;

  app.innerHTML = `
    <header class="app-header">
      <h1>\u{2728} Your Progress</h1>
    </header>

    <div class="app-body">
      <!-- Level Card -->
      <div class="card">
        <div class="flex items-center gap-12 mb-16">
          <div style="font-size:2.5rem">${current.emoji}</div>
          <div style="flex:1">
            <div class="text-small text-muted">Your Level</div>
            <h2>Level ${current.level} \u2014 ${current.name}</h2>
            <div class="text-small" style="color:var(--saffron);font-weight:700">${xp} XP earned!</div>
          </div>
        </div>

        ${next ? `
          <div class="flex justify-between text-small mb-8">
            <span class="text-muted">Next: Level ${next.level}</span>
            <span style="color:var(--primary);font-weight:700">${xpRemaining} XP to go!</span>
          </div>
          <div class="progress-bar progress-bar-saffron">
            <div class="progress-bar-fill" style="width:${pct}%"></div>
          </div>
          <div class="flex justify-between text-small mt-8 text-muted">
            <span>${current.name}</span>
            <span>${next.name}</span>
          </div>
        ` : `
          <div class="text-center" style="color:var(--primary);font-weight:700;font-size:1.125rem">
            \u{1F389} Max level reached! You're amazing!
          </div>
        `}
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card stat-streak">
          <div class="stat-value">${progress.streak_days}</div>
          <div class="stat-label">\u{1F525} Day Streak</div>
        </div>
        <div class="stat-card stat-lessons">
          <div class="stat-value">${progress.lessons_completed}</div>
          <div class="stat-label">\u{1F4D6} Lessons Done</div>
        </div>
        <div class="stat-card stat-chats">
          <div class="stat-value">${progress.conversations_count}</div>
          <div class="stat-label">\u{1F4AC} Chats</div>
        </div>
        <div class="stat-card stat-xp">
          <div class="stat-value">${xp}</div>
          <div class="stat-label">\u{26A1} Total XP</div>
        </div>
      </div>

      ${next ? `
      <!-- Next Level Tips -->
      <div class="card">
        <h3 class="mb-16">\u{1F680} Power Up to ${next.name}!</h3>
        <div class="flex-col gap-8" style="display:flex">
          <div class="flex items-center gap-12" style="padding:12px;border-radius:var(--radius-sm);background:var(--mint-light)">
            <span style="font-size:1.25rem">\u{1F4D6}</span>
            <span style="flex:1;font-weight:600;font-size:0.9rem">Complete more lessons</span>
            <span class="level-badge" style="background:var(--mint);font-size:0.75rem">+10 XP</span>
          </div>
          <div class="flex items-center gap-12" style="padding:12px;border-radius:var(--radius-sm);background:var(--sky-light)">
            <span style="font-size:1.25rem">\u{1F4AC}</span>
            <span style="flex:1;font-weight:600;font-size:0.9rem">Chat with Mitra</span>
            <span class="level-badge" style="background:var(--sky);font-size:0.75rem">+5 XP/min</span>
          </div>
          <div class="flex items-center gap-12" style="padding:12px;border-radius:var(--radius-sm);background:var(--saffron-light)">
            <span style="font-size:1.25rem">\u{1F3AF}</span>
            <span style="flex:1;font-weight:600;font-size:0.9rem">Perfect quiz score</span>
            <span class="level-badge" style="background:var(--saffron);font-size:0.75rem">Bonus XP</span>
          </div>
        </div>
      </div>
      ` : ""}

      <!-- Level Roadmap -->
      <div class="card">
        <h3 class="mb-16">\u{1F3C5} Your Journey</h3>
        <div class="level-roadmap">
          ${LEVELS.map((l) => {
            const isActive = l.level === current.level;
            const isCompleted = xp >= l.xpNeeded && l.level < current.level;
            const cls = isActive ? "active" : isCompleted ? "completed" : "";
            return `
              <div class="level-step ${cls}">
                <div class="level-dot">${l.level}</div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:0.9rem">${l.emoji} ${l.name}</div>
                  <div class="text-small text-muted">${l.xpNeeded} XP needed</div>
                </div>
                ${isActive ? '<span class="level-badge" style="font-size:0.75rem">You\'re here!</span>' : ""}
                ${isCompleted ? '<span style="color:var(--mint);font-size:1.25rem">\u2713</span>' : ""}
              </div>
            `;
          }).join("")}
        </div>
      </div>
    </div>
  `;
}

// ── MCP App init ─────────────────────────────────────────────────────

function init(): void {
  // Listen for tool result data from the MCP App host via postMessage
  window.addEventListener("message", (event: MessageEvent) => {
    try {
      const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;

      // The tool result content is passed as the initial data
      if (data && typeof data.xp_total === "number") {
        render(data as ChildProgress);
        return;
      }

      // Also handle wrapped formats
      if (data?.type === "tool-result" && data.content) {
        const parsed = typeof data.content === "string" ? JSON.parse(data.content) : data.content;
        render(parsed as ChildProgress);
        return;
      }
    } catch {
      // Ignore non-JSON messages
    }
  });

  // Also check if data was embedded in the URL hash (fallback)
  if (window.location.hash) {
    try {
      const data = JSON.parse(decodeURIComponent(window.location.hash.slice(1)));
      render(data as ChildProgress);
      return;
    } catch {
      // Ignore
    }
  }

  // Request data from parent (MCP App host)
  window.parent?.postMessage({ type: "ready", app: "progress" }, "*");
}

init();
