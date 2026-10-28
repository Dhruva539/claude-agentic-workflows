"""Add flow animation to a rendered diagram.

Usage: python animate_svg.py spec.json in.svg out.svg

Effects (all loop together; a pause at the end lets viewers read it):
  1. Step reveal    - each edge fades in at its step number
  2. Flowing dashes - dashes move along the edge to show direction
  3. Moving dot     - a packet travels source -> target
  4. Node pulse     - the target node pulses when the packet arrives
Reduced-motion users get the plain static diagram.
"""
import json
import sys

from lxml import etree

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
STEP = 1.0      # seconds per flow step
PAUSE = 2.5     # seconds of rest before the loop restarts
DOT = "#D85A30"


def q(tag):
    return f"{{{SVG}}}{tag}"


def pct(t, total):
    return round(100 * t / total, 3)


def frac(t, total):
    return round(t / total, 4)


def main():
    spec = json.load(open(sys.argv[1]))
    tree = etree.parse(sys.argv[2])
    root = tree.getroot()
    edges = spec["edges"]

    steps = [e.get("step", i + 1) for i, e in enumerate(edges)]
    total = max(steps) * STEP + PAUSE
    fade_out = total - 0.6

    css = [
        ".edge path{stroke-dasharray:6 4;animation:dash 1s linear infinite}",
        "@keyframes dash{to{stroke-dashoffset:-20}}",
        ".edge text{paint-order:stroke;stroke:#fff;stroke-width:4px;"
        "stroke-linejoin:round}",
    ]

    # Reveal keyframes, one per distinct step.
    for s in sorted(set(steps)):
        t0 = (s - 1) * STEP
        css.append(
            f"@keyframes r{s}{{0%,{pct(t0, total)}%{{opacity:0}}"
            f"{pct(t0 + 0.35 * STEP, total)}%,{pct(fade_out, total)}%{{opacity:1}}"
            f"100%{{opacity:0}}}}")

    # Pulse keyframes, one per distinct arrival step.
    for s in sorted(set(steps)):
        arrive = s * STEP
        css.append(
            f"@keyframes p{s}{{0%,{pct(arrive - 0.05, total)}%{{transform:scale(1)}}"
            f"{pct(arrive + 0.15 * STEP, total)}%{{transform:scale(1.12)}}"
            f"{pct(arrive + 0.45 * STEP, total)}%,100%{{transform:scale(1)}}}}")

    graph = next(g for g in root.iter(q("g")) if g.get("class") == "graph")
    by_id = {el.get("id"): el for el in root.iter(q("g")) if el.get("id")}

    pulsed = set()
    for i, e in enumerate(edges):
        s = steps[i]
        eid = f"e{i}"
        grp = by_id.get(eid)
        if grp is None:
            sys.exit(f"edge {eid} not found in SVG; render with render_diagram.py")
        path = grp.find(q("path"))
        path.set("id", f"p{i}")
        css.append(f"#{eid}{{animation:r{s} {total}s linear infinite}}")

        # Pulse the target node once per arrival step.
        key = (e["to"], s)
        if key not in pulsed:
            pulsed.add(key)
            css.append(
                f"#n_{e['to']}{{transform-box:fill-box;transform-origin:center;"
                f"animation:p{s} {total}s ease-in-out infinite}}")

        # Moving dot on the same path.
        a = frac((s - 1) * STEP + 0.2 * STEP, total)
        b = frac(s * STEP, total)
        dot = etree.SubElement(graph, q("circle"), r="5", fill=DOT,
                               opacity="0")
        dot.set("class", "dot")
        mo = etree.SubElement(dot, q("animateMotion"), dur=f"{total}s",
                              repeatCount="indefinite", calcMode="linear",
                              keyPoints="0;0;1;1", keyTimes=f"0;{a};{b};1")
        mp = etree.SubElement(mo, q("mpath"))
        mp.set(f"{{{XLINK}}}href", f"#p{i}")
        etree.SubElement(dot, q("animate"), attributeName="opacity",
                         values="0;1;0", keyTimes=f"0;{a};{b}",
                         calcMode="discrete", dur=f"{total}s",
                         repeatCount="indefinite")

    css.append("@media (prefers-reduced-motion:reduce){"
               ".edge,.node,.edge path{animation:none!important}"
               ".edge path{stroke-dasharray:none!important}"
               ".dot{display:none}}")

    style = etree.Element(q("style"))
    style.text = "\n".join(css)
    root.insert(0, style)
    tree.write(sys.argv[3], xml_declaration=True, encoding="UTF-8")
    print(sys.argv[3])


if __name__ == "__main__":
    main()
