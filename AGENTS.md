# AI Startup Team — project context for coding agents

You are the **development-time agent** (Claude Code, Gemini CLI, Antigravity, or similar).
You write and change the code of this project. You are NOT one of the agents inside it.

The application you are building contains **runtime agents**: Gemini-powered agents that
collaborate to turn a startup idea into research, a product spec and a landing page.
Keep the two levels separate: never use your own subagents or tools as part of the app.

## What the app does

```
startup idea -> Orchestrator -> Research -> Product -> Developer -> QA -> landing page
                                                          ^          |
                                                          +-revise---+  (bounded)
```

| Runtime agent | Job | Reads | Writes |
|---|---|---|---|
| Orchestrator | Brief at the start, sign-off at the end | idea, final QA | `brief`, `launch_note.md` |
| Research | Market research with live Google Search | idea, brief | `research` (ResearchReport) |
| Product | MVP spec from the research | brief, research | `product_spec` (ProductSpec) |
| Developer | Single-file HTML landing page | brief, product_spec, QA feedback | `landing_vN.html` |
| QA | Checks the page, gives concrete fixes | product_spec, brief, HTML | `qa_history` (QAReport) |

## Architecture rules (do not break these)

1. **Structured hand-offs.** Agents exchange Pydantic models, never free text. Schemas live in `schemas.py`.
2. **Shared state on disk.** Each run gets `runs/<run_id>/` with `state.json`, `trace.jsonl` and outputs.
   An agent reads its inputs from the state and writes its result back.
3. **Trace everything.** Every agent step appends `{at, agent, step, seconds, note}` to the trace.
4. **Sources come from the tool, not the model.** Research sources are taken from Gemini's
   grounding metadata. Never let the model write source URLs itself.
5. **Bounded loops.** Any feedback loop has a maximum number of rounds (default 2).
6. **Code checks facts, models judge quality.** If something can be checked with code
   (an `<h1>` exists, a feature name appears), check it with code before asking an LLM.
   When code drops or rejects an item, record what was dropped and why (in the state and the log).
   A silent drop hides bugs.
7. **Control flow in code, judgment in agents.** The order of steps is defined in code
   (plain Python, or a CrewAI Flow if you chose CrewAI). Agents decide content, not routing.

## Stack

- Run everything inside the project's virtual environment (`.venv`). If it doesn't exist,
  create it and install `requirements.txt` before running anything. Don't use the global Python.
- Python 3.11+, `google-genai` SDK, `pydantic`, `python-dotenv`. Session 2 may add `crewai[google-genai]` (optional).
- Models (free tier of the Gemini API):
  - Research search calls: `gemini-2.5-flash` with the Google Search tool
    (Search grounding is free only on the 2.5 Flash family).
  - All other agents: `gemini-3.5-flash`.
  - Model names come from `.env` (`RESEARCH_MODEL`, `AGENT_MODEL`), never hard-coded in agent logic.
- On the free tier, Google Search grounding and a JSON response schema don't work in the same call.
  Search first, then structure the result in a second call.
- API key in `.env` as `GEMINI_API_KEY`. Never print it, never commit it.
- Retry on HTTP 429/503 with backoff (free tier rate limits are low).
- Set `CREWAI_TRACING_ENABLED=false`, otherwise CrewAI pauses 20 seconds asking about traces.

## How to work with me (the architect)

- Before writing code for a new feature, show a short plan: files, data flow, schemas. Wait for approval.
- Keep files small and named after their job (`agents/research.py`, not `utils2.py`).
- After a change, tell me the exact command to run and what I should expect to see.
- When something fails, explain the cause in one or two sentences before fixing it.
- Do not add frameworks, databases or UIs I didn't ask for.
- The `exercises/` folder is for me, not for you. Don't open it unless I paste something from it.
- When I ask you to review a run, report problems with exact evidence and don't change code
  until I choose what to fix.
