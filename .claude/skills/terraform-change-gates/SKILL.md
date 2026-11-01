---
name: terraform-change-gates
description: Make a Terraform change from a Jira ticket and open a PR, with gates for fmt/validate, destroys, open security groups and blast radius. Use for any automated Terraform edit. Never runs apply.
---

# terraform-change-gates

Chain: edit, validate, plan, check the plan, review, PR. Run each gate through
`../gated-chains/scripts/gate_runner.py` (see `gated-chains`).

## Steps

1. Create branch `fix/<jira-key>` in the repo's own working copy.
2. Edit the module or provider version named in the ticket. Change only what
   the ticket asks for.
3. Gate 1 (script): `scripts/validate_terraform.sh <module-dir>`
   - runs fmt check, init, validate and plan, and writes `plan.json`
   - retry: fix the error it names and run again (budget 2)
   - escalate: stop and comment the error on the ticket
4. Gate 2 (rule): `python scripts/check_plan.py plan.json --env <env>`
   - exit 2 means a human must decide. The commonest case is a replace or
     destroy on a stateful resource. Do not edit around it, do not retry.
     Comment the reasons and the plan summary on the ticket and stop.
   - exit 1 means the plan has no changes: the edit did nothing. Redo step 2.
5. Gate 3 (judge): spawn `pr-reviewer` with the diff, the ticket text and the
   plan summary. A reject goes back to step 2 once. A second reject stops.
6. Open the PR with the plan summary attached. Link the Jira key.
7. Gate 4 (human): a person reviews and merges. Nothing in this skill runs
   `terraform apply`.

## What the plan gate catches (real examples)

- An engine version bump on an RDS instance that Terraform plans as
  delete-and-create. A build check would pass; only the plan shows the data loss.
- A security group edit that adds SSH open to `0.0.0.0/0` next to a legitimate
  443 rule. Ports 80 and 443 are allowed to be public; everything else is not.
- A module upgrade that quietly touches 40 resources. Production allows 10
  changed resources per PR, staging 25, dev 50.

## Notes

- Run plan with read-only credentials where possible.
- Tune `STATEFUL` and `MAX_CHANGES` at the top of `check_plan.py` to your estate.
- Sample plans in `examples/`: `plan_safe`, `plan_replace_db`, `plan_open_sg`,
  `plan_noop`.
