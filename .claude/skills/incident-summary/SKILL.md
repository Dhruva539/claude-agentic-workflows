---
name: incident-summary
description: Turn an alert and its logs into an on-call incident summary, with gates that block invented events and uncited claims. Use when an alert fires and a summary must be posted to an incident channel.
---

# incident-summary

Chain: fetch logs, extract a timeline, draft a summary, post. Gates stop
invented events and uncited claims. Gate behaviour and the exit-code contract
are in the `gated-chains` skill; run every gate through its `gate_runner.py`.

## Steps

1. Fetch the logs for the alert window into `logs.json` (a list of
   `{id, time, service, level, message}`). If you have no fetch script, use the
   logging connector or ask for an export.
2. Extract `timeline.json`: one event per log line that matters, with `time`,
   `service`, `log_line_id`, `what_happened`. Use only `logs.json`.
3. Gate 1 (script):
   `python ../gated-chains/scripts/gate_runner.py --name timeline --max-retries 1 -- python scripts/check_timeline.py timeline.json logs.json`
   - retry: redo step 2 using the reasons verbatim
   - escalate: stop and report, because there are no logs to work from
4. Draft `summary.md` with sections `## Impact`, `## Timeline`,
   `## Suspected cause`. Every bullet must end with `[L-id]` citations.
   Do not state numbers (customers affected, revenue) that are not in the logs.
5. Gate 2 (script): `check_citations.py summary.md logs.json` through the runner.
6. Gate 3 (judge): spawn the `summary-checker` agent with `summary.md` and
   `logs.json`. It returns `{"verdict", "unsupported_claims"}`. Any unsupported
   claim: redo step 4 once with the claims listed. Still failing: stop.
7. Gate 4 (human): show the summary and wait for approval. Never post without it.
8. Post to the incident channel. Attach the gate log (`gates.jsonl`) summary.

## Why these gates

- Gate 1 catches extraction errors cheaply: invented log ids, wrong times,
  out-of-order events.
- Gate 2 enforces the citation rule mechanically, so the judge never has to
  hunt for missing citations.
- The judge checks the one thing scripts cannot: whether a cited line really
  supports the sentence, and whether the suspected cause is an overreach.
- A person sees it last, because a wrong summary in an incident channel
  misleads people under pressure.

Sample data in `examples/`: `logs.json`, plus good and bad timelines and
summaries to try the gates on.
