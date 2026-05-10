/**
 * Lessons app — browse, learn, and quiz inside MCP App iframe.
 *
 * States: browsing → learning (flashcards) → quiz → results
 * Communicates with MCP server via postMessage / callServerTool.
 */

// ── Types ────────────────────────────────────────────────────────────

interface VocabWord {
  marathi: string;
  english: string;
  pronunciation: string;
}

interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
}

interface Lesson {
  id: string;
  level: number;
  sequence: number;
  title: string;
  theme: string;
  vocabulary: VocabWord[];
  quiz_questions: QuizQuestion[];
}

interface LessonCompleteResult {
  score: number;
  xp_earned: number;
  xp_total: number;
  streak_days: number;
}

interface InitData {
  child_id: string;
  level: number;
  lessons: Lesson[];
}

// ── State ────────────────────────────────────────────────────────────

type Phase = "browsing" | "learning" | "quiz" | "results";

let childId = "";
let currentLevel = 1;
let lessons: Lesson[] = [];
let activeLesson: Lesson | null = null;
let phase: Phase = "browsing";

// Learning state
let wordIndex = 0;

// Quiz state
let quizIndex = 0;
let selectedAnswer: number | null = null;
let answered = false;
let score = 0;

// Results state
let xpEarned: number | null = null;

let ttsPlaying = false;

// ── Tool call helper ─────────────────────────────────────────────────

let callId = 0;
const pendingCalls = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

function callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const id = ++callId;
    pendingCalls.set(id, { resolve, reject });
    window.parent.postMessage(
      { type: "tool-call", id, tool: name, arguments: args },
      "*"
    );
    setTimeout(() => {
      if (pendingCalls.has(id)) {
        pendingCalls.delete(id);
        reject(new Error("Tool call timed out"));
      }
    }, 30000);
  });
}

window.addEventListener("message", (event: MessageEvent) => {
  try {
    const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;

    // Tool call response
    if (data?.type === "tool-result" && data.id != null) {
      const pending = pendingCalls.get(data.id);
      if (pending) {
        pendingCalls.delete(data.id);
        if (data.error) {
          pending.reject(new Error(data.error));
        } else {
          const content = typeof data.content === "string" ? JSON.parse(data.content) : data.content;
          pending.resolve(content);
        }
      }
      return;
    }

    // Initial data from primary tool
    if (data && Array.isArray(data.lessons) && typeof data.child_id === "string") {
      handleInit(data as InitData);
      return;
    }
  } catch {
    // Ignore
  }
});

// ── Handlers ─────────────────────────────────────────────────────────

function handleInit(data: InitData): void {
  childId = data.child_id;
  currentLevel = data.level;
  lessons = data.lessons;
  phase = "browsing";
  render();
}

async function handleLevelChange(level: number): Promise<void> {
  currentLevel = level;
  const app = document.getElementById("app")!;
  app.innerHTML = '<div class="loading-center"><div class="spinner"></div><span>Loading lessons...</span></div>';

  try {
    const result = (await callTool("list-lessons", { level })) as Lesson[];
    lessons = result;
  } catch {
    lessons = [];
  }
  render();
}

async function handleSelectLesson(lessonId: string): Promise<void> {
  const app = document.getElementById("app")!;
  app.innerHTML = '<div class="loading-center"><div class="spinner"></div><span>Loading lesson...</span></div>';

  try {
    const result = (await callTool("get-lesson", { lesson_id: lessonId })) as Lesson;
    activeLesson = result;
    phase = "learning";
    wordIndex = 0;
    quizIndex = 0;
    score = 0;
    selectedAnswer = null;
    answered = false;
    xpEarned = null;
  } catch {
    activeLesson = null;
    phase = "browsing";
  }
  render();
}

function handleBackToBrowse(): void {
  activeLesson = null;
  phase = "browsing";
  render();
}

function handleNextWord(): void {
  if (!activeLesson) return;
  if (wordIndex < activeLesson.vocabulary.length - 1) {
    wordIndex++;
  } else {
    phase = "quiz";
    quizIndex = 0;
    score = 0;
    selectedAnswer = null;
    answered = false;
  }
  render();
}

function handlePrevWord(): void {
  if (wordIndex > 0) {
    wordIndex--;
    render();
  }
}

function handleAnswer(index: number): void {
  if (answered || !activeLesson) return;
  selectedAnswer = index;
  answered = true;
  if (index === activeLesson.quiz_questions[quizIndex].correct_index) {
    score++;
  }
  render();
}

async function handleNextQuiz(): Promise<void> {
  if (!activeLesson) return;
  if (quizIndex < activeLesson.quiz_questions.length - 1) {
    quizIndex++;
    selectedAnswer = null;
    answered = false;
    render();
  } else {
    // Quiz done — submit results
    phase = "results";
    render();

    try {
      const result = (await callTool("complete-lesson", {
        lesson_id: activeLesson.id,
        child_id: childId,
        score: Math.round((score / activeLesson.quiz_questions.length) * 100),
      })) as LessonCompleteResult;
      xpEarned = result.xp_earned;
    } catch {
      xpEarned = 10; // Fallback
    }
    render();
  }
}

function handleRetry(): void {
  if (!activeLesson) return;
  phase = "learning";
  wordIndex = 0;
  quizIndex = 0;
  score = 0;
  selectedAnswer = null;
  answered = false;
  xpEarned = null;
  render();
}

async function handleTTS(text: string, button: HTMLButtonElement): Promise<void> {
  if (ttsPlaying) return;
  ttsPlaying = true;
  button.classList.add("playing");

  try {
    const result = (await callTool("speak-marathi", { text })) as { audio_base64: string };
    const audio = new Audio(`data:audio/mpeg;base64,${result.audio_base64}`);
    audio.onended = () => { ttsPlaying = false; button.classList.remove("playing"); };
    audio.onerror = () => { ttsPlaying = false; button.classList.remove("playing"); };
    await audio.play();
  } catch {
    ttsPlaying = false;
    button.classList.remove("playing");
  }
}

// ── Render ───────────────────────────────────────────────────────────

function render(): void {
  const app = document.getElementById("app")!;

  switch (phase) {
    case "browsing":
      renderBrowse(app);
      break;
    case "learning":
      renderLearning(app);
      break;
    case "quiz":
      renderQuiz(app);
      break;
    case "results":
      renderResults(app);
      break;
  }
}

function renderBrowse(app: HTMLElement): void {
  app.innerHTML = `
    <header class="app-header">
      <h1>\u{1F4DA} Marathi Lessons</h1>
      <p class="text-muted text-small mt-8">Choose a topic and start learning!</p>
    </header>

    <div class="level-tabs mb-16">
      ${[1, 2, 3, 4].map((l) => `
        <button class="level-tab ${l === currentLevel ? "active" : ""}" data-level="${l}">
          Level ${l}
        </button>
      `).join("")}
    </div>

    <div class="app-body">
      ${lessons.length === 0
        ? `<div class="empty-state">
            <div class="empty-state-icon">\u{1F4AD}</div>
            <p>No lessons available for this level yet.</p>
          </div>`
        : `<div class="lesson-grid">
            ${lessons.map((lesson) => `
              <div class="lesson-card" data-lesson-id="${lesson.id}">
                <div class="lesson-card-title">${escapeHtml(lesson.title)}</div>
                <div class="lesson-card-theme">${escapeHtml(lesson.theme)} \u2022 ${lesson.vocabulary?.length || "?"} words</div>
              </div>
            `).join("")}
          </div>`
      }
    </div>
  `;

  // Bind level tabs
  document.querySelectorAll<HTMLButtonElement>("[data-level]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const level = parseInt(btn.dataset.level!, 10);
      handleLevelChange(level);
    });
  });

  // Bind lesson cards
  document.querySelectorAll<HTMLElement>("[data-lesson-id]").forEach((card) => {
    card.addEventListener("click", () => {
      handleSelectLesson(card.dataset.lessonId!);
    });
  });
}

function renderLearning(app: HTMLElement): void {
  if (!activeLesson) return;
  const word = activeLesson.vocabulary[wordIndex];
  const total = activeLesson.vocabulary.length + activeLesson.quiz_questions.length;
  const current = wordIndex + 1;
  const pct = Math.round((current / total) * 100);

  app.innerHTML = `
    <div class="flex items-center gap-8 mb-16">
      <button class="btn btn-ghost btn-sm" id="back-btn">\u2190 Back</button>
      <div style="flex:1">
        <h3 style="margin:0">${escapeHtml(activeLesson.title)}</h3>
      </div>
      <span class="level-badge">${current}/${total}</span>
    </div>

    <div class="progress-bar mb-16">
      <div class="progress-bar-fill" style="width:${pct}%"></div>
    </div>

    <div class="flashcard">
      <div class="flex items-center justify-center gap-8 mb-8">
        <div class="flashcard-marathi">${escapeHtml(word.marathi)}</div>
        <button class="tts-btn" data-tts="${escapeAttr(word.marathi)}" title="Listen">\u{1F50A}</button>
      </div>
      <div class="flashcard-pronunciation">${escapeHtml(word.pronunciation)}</div>
      <div class="flashcard-english">${escapeHtml(word.english)}</div>
    </div>

    <div class="flashcard-nav mt-16">
      <button class="btn btn-secondary btn-sm" id="prev-btn" ${wordIndex === 0 ? "disabled" : ""}>\u2190 Back</button>
      <span class="flashcard-counter">${wordIndex + 1} / ${activeLesson.vocabulary.length}</span>
      <button class="btn btn-primary btn-sm" id="next-btn">
        ${wordIndex === activeLesson.vocabulary.length - 1 ? "\u{1F3AF} Quiz Time!" : "Next \u2192"}
      </button>
    </div>
  `;

  document.getElementById("back-btn")!.addEventListener("click", handleBackToBrowse);
  document.getElementById("prev-btn")!.addEventListener("click", handlePrevWord);
  document.getElementById("next-btn")!.addEventListener("click", handleNextWord);

  document.querySelectorAll<HTMLButtonElement>("[data-tts]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-tts");
      if (text) handleTTS(text, btn);
    });
  });
}

function renderQuiz(app: HTMLElement): void {
  if (!activeLesson) return;
  const question = activeLesson.quiz_questions[quizIndex];
  const total = activeLesson.vocabulary.length + activeLesson.quiz_questions.length;
  const current = activeLesson.vocabulary.length + quizIndex + 1;
  const pct = Math.round((current / total) * 100);

  app.innerHTML = `
    <div class="flex items-center gap-8 mb-16">
      <button class="btn btn-ghost btn-sm" id="back-btn">\u2190 Back</button>
      <div style="flex:1">
        <h3 style="margin:0">${escapeHtml(activeLesson.title)}</h3>
      </div>
      <span class="level-badge">${current}/${total}</span>
    </div>

    <div class="progress-bar mb-16">
      <div class="progress-bar-fill" style="width:${pct}%"></div>
    </div>

    <div style="text-align:center;margin-bottom:8px">
      <span class="level-badge" style="background:var(--saffron)">\u{1F3AF} Quiz Time!</span>
    </div>

    <div class="quiz-question">${escapeHtml(question.question)}</div>

    <div class="quiz-options">
      ${question.options.map((opt, i) => {
        let cls = "quiz-option";
        if (answered) {
          if (i === question.correct_index) cls += " correct";
          else if (i === selectedAnswer) cls += " incorrect";
        }
        return `
          <button class="${cls}" data-answer="${i}" ${answered ? "disabled" : ""}>
            <strong>${String.fromCharCode(65 + i)}.</strong> ${escapeHtml(opt)}
          </button>
        `;
      }).join("")}
    </div>

    ${answered ? `
      <div class="quiz-feedback ${selectedAnswer === question.correct_index ? "correct" : "incorrect"}">
        ${selectedAnswer === question.correct_index
          ? "\u{2728} Awesome! You got it right!"
          : "\u{1F914} The right answer is highlighted above."}
      </div>
      <div class="text-center mt-16">
        <button class="btn btn-primary" id="next-quiz-btn">
          ${quizIndex === activeLesson.quiz_questions.length - 1 ? "\u{2B50} See My Score" : "Next Question \u2192"}
        </button>
      </div>
    ` : ""}
  `;

  document.getElementById("back-btn")!.addEventListener("click", handleBackToBrowse);

  document.querySelectorAll<HTMLButtonElement>("[data-answer]").forEach((btn) => {
    btn.addEventListener("click", () => {
      handleAnswer(parseInt(btn.dataset.answer!, 10));
    });
  });

  const nextBtn = document.getElementById("next-quiz-btn");
  nextBtn?.addEventListener("click", handleNextQuiz);
}

function renderResults(app: HTMLElement): void {
  if (!activeLesson) return;
  const total = activeLesson.quiz_questions.length;
  const pct = Math.round((score / total) * 100);
  const isPerfect = score === total;
  const isGood = score >= total / 2;

  const emoji = isPerfect ? "\u{1F31F}" : isGood ? "\u{1F44D}" : "\u{1F4AA}";
  const message = isPerfect
    ? "PERFECT SCORE!"
    : isGood
      ? "Great Job!"
      : "Keep Trying!";
  const sub = isPerfect
    ? "You're a Marathi superstar!"
    : isGood
      ? "You're doing amazing! Keep it up!"
      : "Practice makes perfect! Try again!";

  app.innerHTML = `
    <header class="app-header">
      <h1>\u{1F4DA} Lesson Complete</h1>
    </header>

    <div class="results-card">
      <div class="results-emoji">${emoji}</div>
      <div class="results-score">${score}/${total}</div>
      <div style="font-size:1.125rem;font-weight:700;color:var(--primary);margin-bottom:4px">${message}</div>
      <div class="text-muted">${sub}</div>
      ${xpEarned != null
        ? `<div style="margin-top:12px;display:inline-flex;align-items:center;gap:6px;background:var(--saffron-light);padding:8px 16px;border-radius:var(--radius-full);font-weight:700;color:var(--saffron)">
            \u{26A1} +${xpEarned} XP earned!
          </div>`
        : `<div class="loading-center" style="padding:12px 0"><div class="spinner"></div></div>`
      }
    </div>

    <div class="flex justify-center gap-12 mt-16">
      <button class="btn btn-secondary" id="all-lessons-btn">All Lessons</button>
      <button class="btn btn-primary" id="retry-btn">\u{1F680} Try Again</button>
    </div>
  `;

  document.getElementById("all-lessons-btn")!.addEventListener("click", handleBackToBrowse);
  document.getElementById("retry-btn")!.addEventListener("click", handleRetry);
}

// ── Utilities ────────────────────────────────────────────────────────

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function escapeAttr(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ── Init ─────────────────────────────────────────────────────────────

function init(): void {
  window.addEventListener("message", (event: MessageEvent) => {
    try {
      const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      if (data && Array.isArray(data.lessons) && typeof data.child_id === "string" && !childId) {
        handleInit(data as InitData);
      }
    } catch {
      // Ignore
    }
  });

  if (window.location.hash) {
    try {
      const data = JSON.parse(decodeURIComponent(window.location.hash.slice(1)));
      if (data.lessons && data.child_id) {
        handleInit(data as InitData);
        return;
      }
    } catch {
      // Ignore
    }
  }

  window.parent?.postMessage({ type: "ready", app: "lessons" }, "*");
}

init();
