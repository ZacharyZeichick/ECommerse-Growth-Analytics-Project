# Claude Code Instructions — E-Commerce Growth Analytics

These instructions apply to all Claude Code sessions in this project. Follow them exactly.

---

## First Step for Every Session

Before doing anything else:
1. Read `PROJECT_STATE.md` to understand current phase and status
2. Read `PROJECT_PLAN.md` if you need phase details, decision rules, or scope boundaries
3. Confirm what the user is asking you to do before acting

---

## Core Rules

**Scope**
- Follow PROJECT_PLAN.md and PROJECT_STATE.md. Do not deviate from the defined scope without explicit user instruction.
- Do not add analysis areas, deliverables, or features not listed in the project plan.
- If an idea seems interesting but is out of scope, log it in IDEAS_BACKLOG.md — do not pursue it.

**File and folder discipline**
- Edit only the files explicitly requested unless told otherwise.
- Do not create new notebooks, scripts, SQL files, folders, or dependencies unless explicitly instructed.
- Do not rename, reorganize, or restructure existing files unless instructed.

**Implementation approach**
- Use scoped, specific implementation prompts — one task at a time.
- Prefer small, testable changes over large rewrites.
- Do not refactor working code unless explicitly asked.
- Do not add error handling, abstractions, or features beyond what the task requires.

**When stuck**
- If you cannot complete a task after 3 genuine attempts, stop.
- Summarize the blocker clearly: what you tried, what failed, and what information you need.
- Do not make increasingly speculative changes hoping one will work.

**Ideas and speculation**
- Put speculative ideas, tangential questions, and possible extensions in IDEAS_BACKLOG.md.
- Do not act on ideas not explicitly requested by the user.

---

## File Ownership Rules

| File | Rule |
|------|------|
| `README.md` | Keep public-facing and polished. Only update when asked. |
| `PROJECT_STATE.md` | Update when explicitly asked. Keep concise and current. |
| `PROJECT_PLAN.md` | Do not modify unless user explicitly requests a plan change. |
| `IDEAS_BACKLOG.md` | Append freely when appropriate. Never delete entries. |
| `CLAUDE.md` | Do not modify. |
| `sql/` | Create files only when explicitly instructed. |
| `notebooks/` | Create notebooks only when explicitly instructed. |
| `src/` | Create scripts only when explicitly instructed. |
| `outputs/` | Write outputs only when explicitly instructed. |

---

## Analytical Standards

- Every finding should be backed by a number (%, $, ratio, or trend).
- Document data quality issues and decisions when encountered.
- The final narrative follows the data — do not force the starting hypothesis.
- If a question cannot be answered by the dataset, document the limitation and move on.

---

## Tool Split

- **This tool (Claude Code):** Implementation — writing SQL, Python, notebooks; executing code; saving outputs; managing files.
- **ChatGPT:** Framing — hypothesis generation, narrative structure, business interpretation.
- Do not make major analytical or narrative decisions without prior direction from the user or ChatGPT framing.
