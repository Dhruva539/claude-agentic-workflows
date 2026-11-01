"""Rule gate for a Terraform plan.

Usage: python check_plan.py plan.json --env prod|staging|dev

Produce plan.json with:
  terraform plan -out=tfplan && terraform show -json tfplan > plan.json

Escalates (exit 2, a human must decide, never retry) when the plan:
  - deletes or replaces any resource
  - deletes or replaces a stateful resource (flagged separately)
  - opens an ingress rule to 0.0.0.0/0 or ::/0 on a port other than 80/443
  - changes more resources than the environment allows (blast radius)
Retries (exit 1) when the plan contains no changes at all, because the edit
probably did nothing.

Exit 0 pass.
"""
import argparse
import json
import sys

STATEFUL = {"aws_db_instance", "aws_rds_cluster", "aws_s3_bucket",
            "aws_dynamodb_table", "aws_kms_key", "aws_efs_file_system",
            "aws_elasticache_replication_group", "aws_ebs_volume"}
MAX_CHANGES = {"prod": 10, "staging": 25, "dev": 50}
WORLD = {"0.0.0.0/0", "::/0"}
SAFE_PORTS = {80, 443}


def open_world_ports(rc):
    """Yield (from_port, to_port) of any world-open ingress in this change."""
    after = (rc.get("change") or {}).get("after") or {}
    if rc.get("type") == "aws_security_group":
        for rule in after.get("ingress") or []:
            cidrs = set(rule.get("cidr_blocks") or []) | set(rule.get("ipv6_cidr_blocks") or [])
            if cidrs & WORLD:
                yield rule.get("from_port"), rule.get("to_port")
    elif rc.get("type") == "aws_security_group_rule" and after.get("type") == "ingress":
        cidrs = set(after.get("cidr_blocks") or []) | set(after.get("ipv6_cidr_blocks") or [])
        if cidrs & WORLD:
            yield after.get("from_port"), after.get("to_port")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--env", default="prod", choices=sorted(MAX_CHANGES))
    a = ap.parse_args()

    plan = json.load(open(a.plan))
    changes = [rc for rc in plan.get("resource_changes", [])
               if rc["change"]["actions"] != ["no-op"] and rc["change"]["actions"] != ["read"]]

    if not changes:
        print(json.dumps({"reasons": ["plan has no changes; the edit may not have taken effect"]}))
        sys.exit(1)

    escalate = []
    for rc in changes:
        actions = rc["change"]["actions"]
        if "delete" in actions:
            verb = "REPLACE" if "create" in actions else "DELETE"
            kind = "stateful " if rc["type"] in STATEFUL else ""
            escalate.append(f"{verb} {kind}resource {rc['address']}")
        for lo, hi in open_world_ports(rc):
            if not (lo == hi and lo in SAFE_PORTS):
                escalate.append(
                    f"{rc['address']} opens ports {lo}-{hi} to the whole internet")

    limit = MAX_CHANGES[a.env]
    if len(changes) > limit:
        escalate.append(f"{len(changes)} resources change; {a.env} allows {limit}")

    summary = {"env": a.env, "changes": len(changes)}
    if escalate:
        print(json.dumps({"reasons": escalate, **summary}))
        sys.exit(2)
    print(json.dumps({"reasons": [], **summary}))


if __name__ == "__main__":
    main()
