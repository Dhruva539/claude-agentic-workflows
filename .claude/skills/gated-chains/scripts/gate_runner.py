"""Run a gate script under a retry budget and log the result.

Usage:
  python gate_runner.py --name NAME [--max-retries 2] [--timeout 300]
                        [--state gates_state.json] [--log gates.jsonl]
                        -- <gate command ...>

Gate contract for the wrapped command:
  exit 0  pass      the chain continues
  exit 1  retry     fixable: redo the previous step with the reasons
  exit 2  escalate  needs a human decision: never retry, stop the chain
  stdout  optional JSON, e.g. {"reasons": ["..."], "route": "auto_refund"}

This runner prints one JSON line and exits with the same 0/1/2 meaning:
  {"gate", "verdict", "attempt", "max_retries", "reasons", ...extra fields}

Safety rules built in:
  - Retry budget: after max_retries failed retries the verdict becomes
    escalate, so a chain can never loop forever.
  - Fail closed: any other exit code, a crash or a timeout is escalate.
  - Every run is appended to the audit log (JSONL) for later review.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def parse_args(argv):
    if "--" not in argv:
        sys.exit("usage: gate_runner.py --name NAME [options] -- <command ...>")
    i = argv.index("--")
    opts, cmd = argv[:i], argv[i + 1:]
    cfg = {"name": None, "max_retries": 2, "timeout": 300,
           "state": "gates_state.json", "log": "gates.jsonl"}
    it = iter(opts)
    for flag in it:
        key = flag.lstrip("-").replace("-", "_")
        if key not in cfg:
            sys.exit(f"unknown option {flag}")
        val = next(it)
        cfg[key] = int(val) if key in ("max_retries", "timeout") else val
    if not cfg["name"] or not cmd:
        sys.exit("--name and a gate command are required")
    return cfg, cmd


def load_state(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def main():
    cfg, cmd = parse_args(sys.argv[1:])
    state = load_state(cfg["state"])
    attempt = state.get(cfg["name"], 0) + 1

    extra, reasons = {}, []
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=cfg["timeout"])
        code = p.returncode
        try:
            body = json.loads(p.stdout) if p.stdout.strip() else {}
            if isinstance(body, dict):
                reasons = list(body.pop("reasons", []))
                extra = body
        except ValueError:
            reasons = [p.stdout.strip()[:300]] if p.stdout.strip() else []
        if code not in (0, 1, 2):
            reasons.append(f"gate crashed (exit {code}): {p.stderr.strip()[-200:]}")
            code = 2
    except subprocess.TimeoutExpired:
        code, reasons = 2, [f"gate timed out after {cfg['timeout']}s"]
    except OSError as e:
        code, reasons = 2, [f"gate could not start: {e}"]

    verdict = {0: "pass", 1: "retry", 2: "escalate"}[code]
    if verdict == "retry" and attempt > cfg["max_retries"]:
        verdict = "escalate"
        reasons.append(f"retry budget exhausted after {attempt} attempts")

    state[cfg["name"]] = 0 if verdict == "pass" else attempt
    json.dump(state, open(cfg["state"], "w"))

    result = {"gate": cfg["name"], "verdict": verdict, "attempt": attempt,
              "max_retries": cfg["max_retries"], "reasons": reasons, **extra}
    with open(cfg["log"], "a") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                            "cmd": cmd, **result}) + "\n")
    print(json.dumps(result))
    sys.exit({"pass": 0, "retry": 1, "escalate": 2}[verdict])


if __name__ == "__main__":
    main()
