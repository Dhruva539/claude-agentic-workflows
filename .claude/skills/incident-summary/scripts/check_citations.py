"""Gate 2: every claim in summary.md must cite a real log line.

Usage: python check_citations.py summary.md logs.json

Rules:
  - the sections Impact, Timeline and Suspected cause must exist
  - every bullet ("- ...") must carry at least one [L-<number>] citation
  - every citation must exist in logs.json

This is deterministic and cheap. Run it before the judge agent, which then only
has to judge wording and inference, not look for missing citations.

Exit 0 pass, 1 retry the draft.
"""
import json
import re
import sys

SECTIONS = ("impact", "timeline", "suspected cause")
CITE = re.compile(r"\[(L-\d+)\]")


def main():
    text = open(sys.argv[1]).read()
    known = {l["id"] for l in json.load(open(sys.argv[2]))}
    problems = []

    headings = {h.strip().lower() for h in re.findall(r"^##\s+(.+)$", text, re.M)}
    for s in SECTIONS:
        if s not in headings:
            problems.append(f"missing section '## {s.title()}'")

    for n, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("- "):
            continue
        cites = CITE.findall(line)
        if not cites:
            problems.append(f"line {n}: bullet has no [L-id] citation: {line.strip()[:70]}")
        for c in cites:
            if c not in known:
                problems.append(f"line {n}: cites {c}, which is not in logs.json")

    if problems:
        print(json.dumps({"reasons": problems}))
        sys.exit(1)
    print(json.dumps({"reasons": []}))


if __name__ == "__main__":
    main()
