# Debugging an agentic system through a coding agent

"It doesn't work, fix it" gets you a random change. A good bug report gets you the right fix.

## Agents don't crash when they're wrong

Most bugs in an agent system don't raise an error. The run finishes, every code check passes,
and the output still contains an invented fact or a persona that doesn't match its audience.
You only see it by reading the output, or by asking a coding agent to review it for you.

## Debug with the coding agent (Exercise 2)

1. **Review.** Ask the coding agent to compare the run's `state.json` to the idea and to AGENTS.md,
   and to list the most serious problems with exact evidence. "Don't change any code yet."
2. **Check one claim yourself.** The reviewer is an LLM too. Open the file and confirm one piece of evidence.
3. **Choose one problem and set limits.** You decide what's worth fixing and what must not change.
   Don't accept every suggested fix: a rule that sounds smart may empty the output.
4. **Plan before change, and keep it small.** Commit first. Ask for the cause in 2 sentences and a plan,
   and wait. One file, no new LLM calls. Too big? "Smaller: the minimum change."
5. **Verify and compare.** Re-run only that step (`--research-only` / `--product-only <run_id>`).
   Is the problem gone? Did anything else get worse? Then: fixed, reverted, or logged.

## When to stop

A reviewer will always find another problem. Fix only what breaks a core rule ("never invent")
or changes a decision (what gets built, what gets promised). Everything else is a known issue.
Every new check also drops more output: tighten too far and the research comes back empty.
This is the same reason the QA loop in session 2 has a maximum number of rounds.

In practice: one problem, one fix, one re-run, then one of three results: **fixed**, **reverted**
or **logged**. A fix that makes the check pass can still make the output worse, so always compare
before and after. Commit before every fix so reverting is one command.

## The bug report format

```
Problem:    what is wrong, in one sentence
Evidence:   the exact output — a line from trace.jsonl, a field from state.json, an error
Expected:   what should have happened
Constraint: what must NOT change (schemas, other agents, the flow)
Ask:        explain the cause in 2 sentences before changing anything
```

## Where to look first

| Symptom | Look at | Usual cause |
|---|---|---|
| Crash / exception | the terminal error | missing key, wrong model name, schema mismatch |
| Agent output is generic | its input in state.json | the agent didn't get the context it needed |
| Agent ignores a rule | its instructions | the rule is buried, vague, or contradicts another rule |
| Two agents disagree | the hand-off field | the schema allows ambiguity (free text where a list was needed) |
| Very slow step | trace.jsonl `seconds` | rate-limit retries, or a tool called in a loop |
| QA never passes | qa_history | QA is too strict, or the Developer can't see the fixes |
| 0 sources | CrewAI verbose log | the search tool was never called |
| Fewer items than expected | the `dropped` list and `search_queries` in state.json | the search never looked for that topic, so the items had no source and were dropped |
| A field "has a source" but the source doesn't say it | the evidence next to that field | one evidence field shared by several claims |

## Three questions before every fix

1. **Instructions, input, or flow?** Is the agent badly instructed, missing information, or called at the wrong time?
2. **Can code check it?** If yes, add a check in code instead of another sentence in the prompt.
3. **Which level?** Is this a bug in the app (runtime agents), or did the coding agent misunderstand you (development-time)?

## Two levels, two kinds of bugs

- **Runtime bug:** the Product Agent invents features. Fix: the agent's instructions, its input, or a validation step.
- **Development-time bug:** the coding agent put routing logic inside an agent's prompt instead of the Flow.
  Fix: point it back to AGENTS.md rule 7 and ask it to refactor.
