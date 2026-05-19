# Screenshots for the presentation

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

After dropping screenshots in, find the `<div class="placeholder">` blocks in `marathimitra.md` and replace them with markdown image tags:

```markdown
![landing](screenshots/landing.png)
```
