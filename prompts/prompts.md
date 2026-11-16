# Workshop prompts (same text as the slides and the workbook)

## Exercise 0 — warm-up
```
Read AGENTS.md. Don't write any code yet.
In 5 lines, explain back to me:
1. the difference between you and the runtime agents in this app,
2. the data flow between the agents,
3. the three architecture rules you think are most important.
```

## Prompt 01 — Research Agent
```
Build a Research Agent using Gemini with Google Search grounding.
Input: a startup idea.
Research competitors, target audiences, user pain points and market signals.
Produce typed structured output with evidence and source URLs.
Sources must come from the search tool's grounding metadata, never from the model's text.
Implement a runnable CLI, environment-variable API configuration,
clear execution logs and error handling (retry on rate limits).
Save each run to a state file that other agents will read later.
Explain your proposed architecture before implementation. Wait for my approval.
```

## Prompt 02 — Product Agent
```
Add a Product Agent that consumes the Research Agent structured output.
It reads only the research from the shared state. It never calls search.
Generate two personas, core user pain points, value proposition,
MVP features grouped into Must/Should/Later, and testable acceptance criteria.
Every feature must say which research pain point it solves. At most 3 Must features.
Use typed shared state. Preserve research citations.
Never invent market facts; explicitly label assumptions.
Add a flag --product-only <run_id> that re-runs only this agent on saved research.
Show me the plan first.
```

## Exercise 2 — debug with the coding agent

Step 1: the coding agent reviews the run.
```
Look at the last run in runs/. Compare state.json to the idea and to
the rules in AGENTS.md. List the 3 most serious quality problems, with
exact evidence for each, and say which agent caused each one.
Don't change any code yet.
```

Before step 2, save a restore point: `git add -A && git commit -m "before fix"`.

Step 2: you choose ONE problem. Copy this as is; change only the number.
```
Fix problem #<n> only. Don't touch the other agents and don't weaken any
existing check. Keep it small: one file if you can, and no new LLM calls.
Explain the cause in 2 sentences, show me your plan, and wait for my OK.
```

Step 3: read the plan. Too big (a new model call, many files, a rewrite)? Reply:
"Smaller: the minimum change that fixes problem #<n>." Then approve.

Step 4: re-run only that step (`--research-only` / `--product-only <run_id>`).
Compare before and after: did the problem go away, and did anything else get worse
(fewer items, generic names, another language)?

Step 5: stop. Every exercise ends in one of three results, and all three count:
- **Fixed**: the problem is gone and nothing got worse. Commit.
- **Reverted**: the fix made something else worse. Say "Revert your last change" (or `git checkout .`).
- **Logged**: write it as a known issue in one line and move on.

A reviewer will always find another problem. Don't ask it to review again in this exercise.

No run of your own (key not working)? Use `exercises/broken_state.json` in step 1:
"Review exercises/broken_state.json against AGENTS.md ..."

## Bug report template (when you found the problem yourself)
```
Problem:    <what is wrong, in one sentence>
Evidence:   <exact quote from the state file, the log or the error>
Expected:   <what should have happened>
Constraint: <what must NOT change: schemas, other agents, the flow>
Ask:        Explain the cause in 2 sentences before changing anything.
```

## Prompt 03 — the five-agent team
```
Refactor our project into a five-agent startup team
(Orchestrator, Research, Product, Developer, QA).
Use CrewAI or plain Python, your choice.
The order of steps lives in code (a Flow or a plain function), never in an agent's prompt.
Use typed shared state, explicit tasks and tool boundaries.
Preserve research citations and product specifications.
Include observable logs and saved artifacts.
Show the architecture and implementation plan before coding.
```

## Prompt 04 — Developer Agent
```
Add a Developer Agent.
Input: the brief and the product spec, plus QA feedback and the previous
version on later rounds.
Output: ONE complete index.html with inline CSS, no npm and no build step.
Follow landing_page_sections in order, exactly one <h1>, show every Must
feature by its exact name, a CTA in the hero and at the bottom, mobile friendly.
Save each version as landing_vN.html.
Show me the plan first.
```

## Prompt 05 — bounded QA loop
```
Add a bounded QA process for the generated landing page.
Evaluate the page against the product specification.
Check clear value proposition, functioning CTA, required sections,
basic responsiveness and unsupported claims.
Use deterministic checks where possible (one <h1>, every Must feature on the page,
a CTA exists); if code finds a major issue, the page fails even if the LLM says it passed.
Return structured, actionable feedback to the Developer on failure.
Maximum two revisions. Save QA results and final status.
```

## Exercise 6 — diagnose from a trace
```
Here is my trace:
<paste trace.jsonl>
And the last QA report:
<paste the last QA result>
Diagnose: which agent is the weakest link, and why? Is the problem in the agent's
instructions, in its input, or in the flow? Propose ONE change, explain the
trade-off, and wait for my approval.
```
