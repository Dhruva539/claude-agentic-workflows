"""Validate a diagram spec. Exit 1 with a readable message on any problem."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons

spec = json.load(open(sys.argv[1]))
errors, warnings = [], []

nodes = spec.get("nodes", [])
ids = [n.get("id") for n in nodes]
if not nodes:
    errors.append("spec has no nodes")
for i in {x for x in ids if ids.count(x) > 1}:
    errors.append(f"duplicate node id: {i}")
idset = set(ids)

for n in nodes:
    if not n.get("label"):
        errors.append(f"node {n.get('id')} has no label")
    icon = n.get("icon")
    if icon and not icons.resolve(icon):
        warnings.append(
            f"node {n['id']}: icon '{icon}' not found "
            f"(run: python scripts/list_icons.py <keyword>); drawn as plain box")

grouped = set()
for g in spec.get("groups", []):
    for m in g.get("members", []):
        if m not in idset:
            errors.append(f"group {g.get('id')}: unknown member {m}")
        if m in grouped:
            errors.append(f"node {m} is in more than one group")
        grouped.add(m)

for k, e in enumerate(spec.get("edges", [])):
    for end in ("from", "to"):
        if e.get(end) not in idset:
            errors.append(f"edge {k}: unknown node in '{end}': {e.get(end)}")
    if "step" in e and (not isinstance(e["step"], int) or e["step"] < 1):
        errors.append(f"edge {k}: step must be an integer >= 1")

if len(nodes) > 15:
    warnings.append(f"{len(nodes)} nodes: consider an overview plus one detail diagram per flow")

for w in warnings:
    print("warning:", w)
if errors:
    for e in errors:
        print("error:", e)
    sys.exit(1)
print("ok")
