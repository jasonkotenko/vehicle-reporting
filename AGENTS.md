# Agent Instructions

Guidance for AI agents working in this repository.

## Validate before handing off

Do not mark work complete or ask the user to try something until you have verified it yourself.

Before reporting a task as done:

1. **Run the stack** — `make up` (or the relevant subset of services).
2. **Exercise the change** — hit API endpoints with `curl` or tests; for UI work, open the app in the browser and confirm the expected behavior.
3. **Debug failures** — fix issues found during validation; do not leave known broken states for the user to discover.
4. **Report honestly** — if something could not be tested (missing credentials, environment constraint), say what was tested and what was not.

## Project context

- Product requirements: product/PRD.md
- Technical plan: technical/README.md



## Conventions

- Follow existing code style and keep diffs focused.
- Do not commit `.env` or secrets.
- Do not create git commits unless the user asks.
- Implementation follows the numbered steps in `technical/`; confirm the relevant step doc with the user before large new phases if they requested a review gate.



## Commit and push

After completing a unit of work:

1. **Validate** — follow the checks above; fix any failures first.
2. **User approval** — wait for the user to approve the result before committing, unless they explicitly asked you to commit as part of the task.
3. **Commit** — stage relevant files (never `.env`), write a descriptive message focused on *why*, then commit.
4. **Push** — only when the user asks; use `git push` to `origin` (no force push to `main`).

If validation or approval is still pending, report status to the user instead of committing.