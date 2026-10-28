# claude-agentic-workflows

Claude Code skills and agents for agentic workflows.

## system-diagram

Draws AWS architecture and flow diagrams as animated SVG from a JSON spec of
components and connections. Graphviz does the layout, the `diagrams` package
supplies AWS icons, and a script adds step-by-step flow animation (reveal,
flowing dashes, moving packet dot, node pulse).

- Skill: `.claude/skills/system-diagram/` (see `SKILL.md` and `spec.md`)
- Agent: `.claude/agents/diagram-architect.md` (description -> `spec.json`)
- Example: `.claude/skills/system-diagram/examples/aws_web_app.json`, with
  rendered `aws_web_app.svg` and `aws_web_app.animated.svg`

### Setup

    apt install graphviz        # or: brew install graphviz
    pip install diagrams graphviz lxml

### Usage

    python .claude/skills/system-diagram/scripts/validate_spec.py spec.json
    python .claude/skills/system-diagram/scripts/render_diagram.py spec.json out/diagram
    python .claude/skills/system-diagram/scripts/animate_svg.py spec.json out/diagram.svg out/diagram.animated.svg

Or ask Claude Code to draw an architecture and it follows `SKILL.md`.
