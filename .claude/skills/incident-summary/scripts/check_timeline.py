"""Gate 1: validate timeline.json against the logs it was extracted from.

Usage: python check_timeline.py timeline.json logs.json

Catches the usual extraction failures before any summary is drafted:
missing fields, unparseable or out-of-order times, log ids that do not exist
(invented events) and times that disagree with the cited log line.

Exit 0 pass, 1 retry the extraction, 2 escalate (no logs to work from).
"""
import json
import sys
from datetime import datetime

REQUIRED = ("time", "service", "log_line_id", "what_happened")


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main():
    timeline = json.load(open(sys.argv[1]))
    logs = {l["id"]: l for l in json.load(open(sys.argv[2]))}

    if not logs:
        print(json.dumps({"reasons": ["no logs were fetched; nothing to summarise"]}))
        sys.exit(2)
    if not timeline:
        print(json.dumps({"reasons": ["timeline is empty although logs exist"]}))
        sys.exit(1)

    problems, prev = [], None
    for i, ev in enumerate(timeline):
        tag = f"event {i + 1}"
        missing = [k for k in REQUIRED if not ev.get(k)]
        if missing:
            problems.append(f"{tag}: missing {', '.join(missing)}")
            continue
        try:
            t = parse(ev["time"])
        except ValueError:
            problems.append(f"{tag}: time '{ev['time']}' is not ISO 8601")
            continue
        if prev and t < prev:
            problems.append(f"{tag}: out of order ({ev['time']} is before the previous event)")
        prev = t
        log = logs.get(ev["log_line_id"])
        if log is None:
            problems.append(f"{tag}: log_line_id {ev['log_line_id']} does not exist in logs.json")
        elif parse(log["time"]) != t:
            problems.append(
                f"{tag}: time {ev['time']} does not match {ev['log_line_id']} ({log['time']})")

    if problems:
        print(json.dumps({"reasons": problems}))
        sys.exit(1)
    print(json.dumps({"reasons": [], "events": len(timeline)}))


if __name__ == "__main__":
    main()
