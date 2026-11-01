#!/usr/bin/env bash
# Script gate: format, validate, plan. Writes plan.json for check_plan.py.
# Usage: validate_terraform.sh <module-dir>
# Exit 0 pass, 1 retry (fixable error). Never runs apply.
set -uo pipefail
dir="${1:?module directory required}"
cd "$dir" || exit 1

fail() { printf '{"reasons": ["%s"]}\n' "$1"; exit 1; }

terraform fmt -check -recursive >/dev/null 2>&1 || fail "terraform fmt -check failed; run terraform fmt"
terraform init -backend=false -input=false >/dev/null 2>&1 || fail "terraform init failed"
out=$(terraform validate -no-color 2>&1) || fail "terraform validate failed: $(echo "$out" | head -3 | tr '\n"' '  ')"

if terraform plan -input=false -out=tfplan >/dev/null 2>plan.err; then
  terraform show -json tfplan > plan.json
  echo '{"reasons": []}'
else
  fail "terraform plan failed: $(head -3 plan.err | tr '\n"' '  ')"
fi
