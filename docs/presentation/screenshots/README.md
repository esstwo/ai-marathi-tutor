# Screenshots for the presentation

Used by both `marathimitra.md` (Marp) and `marathimitra.html` (reveal.js).

Drop PNGs here with these filenames and the deck will pick them up:

| Filename | Slide | What to capture |
|---|---|---|
| `landing.png` | "See it in action" | Homepage hero at marathimitra.site |
| `chat.png` | "See it in action" | A chat with Mitra mid-conversation, with Marathi visible |
| `mission.png` | "See it in action" | A mission in progress — scenario + step indicator + reply |
| `architecture-diagram.png` | "Architecture at a glance" | Either crop ARCHITECTURE.md's ASCII diagram into an image, or draw a fresh one in tldraw / Excalidraw |

Optional extras you could add by editing the Marp file:
- `parent-digest-email.png` — the weekly email rendered in Gmail/Apple Mail
- `lesson-quiz.png` — the quiz screen of a lesson

After dropping screenshots in:

**For the HTML deck (`marathimitra.html`)** — find each `<div class="placeholder">…</div>` block and replace with:
```html
<img src="screenshots/landing.png" alt="Landing page" />
```

**For the Marp deck (`marathimitra.md`)** — replace `<div class="placeholder">…</div>` blocks with:
```markdown
![landing](screenshots/landing.png)
```
