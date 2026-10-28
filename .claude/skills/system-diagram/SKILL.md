---
name: system-diagram
description: Draw AWS architecture and flow diagrams as animated SVG from components and connections the user describes. Use when the user asks for a system design, architecture or data-flow diagram, or wants a flow animated step by step.
---

# system-diagram

Turns a description of components and connections into an animated AWS-style
SVG. You write a JSON spec; scripts do the layout, icons and animation, so the
output is repeatable.

## Steps

1. Convert the user's description into `spec.json` (schema and rules: `spec.md`).
   Ask a question only if a connection's direction is unclear.
   For many components, hand this step to the `diagram-architect` agent.
2. Find icons when unsure of a name:
   `python scripts/list_icons.py <keyword>` (no keyword lists the short aliases).
3. Validate: `python scripts/validate_spec.py spec.json`
   Fix every `error:` and re-run. A `warning:` about an icon means that node
   draws as a plain box.
4. Render: `python scripts/render_diagram.py spec.json out/diagram`
   writes `out/diagram.svg` (static, icons embedded).
5. Animate: `python scripts/animate_svg.py spec.json out/diagram.svg out/diagram.animated.svg`
6. Look at the result before delivering: open the SVG in a browser or
   screenshot it. Check for overlapping labels and that the step order reads
   correctly.
7. Send both files: `diagram.animated.svg` for screens, `diagram.svg` for docs
   and slides.

Run all scripts from this skill's folder, or use full paths to them.

## Rules for writing the spec

- Give every edge a `step` number. Edges with the same step animate together
  (use that for fan-out, such as an API writing to a database and a cache).
- Put VPCs, subnets and accounts in `groups`. A node can be in one group only.
- Label an edge only when the protocol or action adds meaning ("HTTPS", "SQL",
  "enqueue"). Leave obvious ones blank.
- Keep node labels short; use `\n` for a second line.
- More than about 15 nodes: make an overview diagram, then one diagram per
  flow, rather than one crowded picture.
- Use `direction` `LR` for request flows and `TB` for layered architectures.

## What the animation does

Each connection fades in at its step, dashes flow along it, a dot travels
source to target, and the target service pulses on arrival. The loop pauses
about 2.5 seconds before restarting. With reduced-motion enabled the viewer
sees the plain static diagram.

## Requirements

- Graphviz program (`dot`): `apt install graphviz`, `brew install graphviz`,
  or `winget install Graphviz.Graphviz`
- `pip install diagrams graphviz lxml` (the `diagrams` package supplies the
  AWS icon PNGs; its API is not used)

## If something fails

- `dot: command not found`: install Graphviz (above).
- `edge eN not found in SVG`: the SVG was not made by `render_diagram.py`;
  re-run step 4.
- Icon not found: run `list_icons.py` with a broader keyword, or set `icon` to a
  full path to your own PNG.

An example spec is in `examples/aws_web_app.json`.
