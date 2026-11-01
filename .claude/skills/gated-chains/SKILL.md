---
name: gated-chains
description: Build or review a prompt chain with gates between steps (script, rule, judge and human gates), retry budgets and an audit log. Use when designing any multi-step agent workflow where a bad step must not flow into the next one.
---

# gated-chains

A chain runs steps in order. A gate sits between two steps and decides whether
the next step may run. Use this skill to design the gates, and
`scripts/gate_runner.py` to run them safely.

## Gate types (cheapest first)

| Gate | Checks | Implement as |
|---|---|---|
| Script | Format, schema, arithmetic, build, tests | Python or shell, exit code |
| Rule | Business limits: amount, environment, severity | Python with a policy file |
| Judge | Faithfulness of wording to its source | A separate read-only agent |
| Human | Irreversible or customer-facing actions | Stop and wait for approval |

Put cheap gates before expensive ones. Never use a judge for something a
script can check.

## The exit-code contract

Every gate script follows this, so the chain logic stays the same everywhere:

- exit 0: pass, continue
- exit 1: retry, redo the previous step using the `reasons`
- exit 2: escalate, a human must decide; never retry
- stdout: optional JSON such as `{"reasons": ["..."], "route": "deny"}`

## Running a gate

```
python scripts/gate_runner.py --name tf-plan --max-retries 2 -- \
    python ../terraform-change-gates/scripts/check_plan.py plan.json --env prod
```

The runner returns one JSON line (`verdict`, `attempt`, `reasons`) and the same
exit code. It also enforces three things the model should not be trusted with:

1. A retry budget: after `max-retries` failed retries a retry becomes an escalation.
2. Fail closed: a crash, timeout or unknown exit code is an escalation.
3. An audit log: every run is appended to `gates.jsonl`.

Run it from the folder where the chain keeps its working files, so
`gates_state.json` and `gates.jsonl` land next to them.

## How a skill should use the verdict

```markdown
Gate: run gate_runner.py for <name>.
- pass      → continue to the next step
- retry     → redo the previous step, giving it the gate's reasons verbatim
- escalate  → stop. Post the reasons and the artifacts to the ticket or channel
              and wait for a human. Do not continue on your own.
```

## Advanced patterns

- Conditional human gate: a rule gate escalates only the risky cases (large
  refund, production, major version bump), so most runs flow through unattended.
- Gate inside each parallel worker: when fanning out per repo, every worker runs
  its own gates. One repo escalating must not stop the others.
- Deterministic gate before a judge: check citations or schema with a script
  first, and call the judge only if that passes.
- Route, don't just pass: a gate can pass with a `route` field (for example
  `auto_refund` or `deny`), so one gate both checks and branches.
- No-op detection: a gate that retries when the edit changed nothing catches
  silent failures that a "build passed" check would miss.
- Audit trail: summarise `gates.jsonl` in the final report so reviewers see
  which gates fired, how often, and why.

## Scenarios in this repo

- `incident-summary`: alert and logs to an on-call summary, with citation gates
  (judge agent: `summary-checker`)
- `terraform-change-gates`: plan gates for destroys, blast radius and open
  security groups (judge agent: `pr-reviewer`)

Not built yet: a refund-triage skill (policy gate that routes, plus a
conditional human gate) and a Snyk-fix skill (version-bump, diff-scope and
secret gates). Each skill's `examples/` folder has sample data to try its gates on.
