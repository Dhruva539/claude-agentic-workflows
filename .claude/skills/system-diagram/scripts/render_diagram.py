"""spec.json -> static SVG using Graphviz layout and AWS icons.

Usage: python render_diagram.py spec.json out/diagram
Writes out/diagram.svg (icons embedded, so the file is self-contained).
Every node gets id n_<id> and every edge gets id e<index>, which
animate_svg.py relies on.
"""
import base64
import json
import os
import sys

from graphviz import Digraph
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons

XLINK = "http://www.w3.org/1999/xlink"

# Fallback fill for nodes with no icon, keyed by optional "type".
FILLS = {"client": "#E6F1FB", "network": "#EEEDFE", "compute": "#E1F5EE",
         "data": "#FAEEDA", "security": "#FAECE7"}


def build(spec):
    g = Digraph(
        format="svg",
        graph_attr={
            "rankdir": spec.get("direction", "LR"),
            "splines": "spline",
            "nodesep": "0.7",
            "ranksep": "1.1",
            "pad": "0.4",
            "fontname": "Helvetica",
            "fontsize": "16",
            "labelloc": "t",
            "label": spec.get("title", ""),
            "bgcolor": "white",
        },
        edge_attr={"fontname": "Helvetica", "fontsize": "11",
                   "color": "#5F5E5A", "fontcolor": "#444441",
                   "penwidth": "1.6", "arrowsize": "0.9"},
    )
    nodes = {n["id"]: n for n in spec["nodes"]}

    def add(graph, n):
        icon = icons.resolve(n.get("icon"))
        common = {"id": f"n_{n['id']}", "label": n["label"],
                  "fontname": "Helvetica", "fontsize": "12"}
        if icon:
            graph.node(n["id"], shape="none", image=icon, imagescale="true",
                       labelloc="b", imagepos="tc", width="1.4", height="1.95",
                       fixedsize="true", **common)
        else:
            graph.node(n["id"], shape="box", style="rounded,filled",
                       fillcolor=FILLS.get(n.get("type"), "#F1EFE8"),
                       color="#888780", **common)

    placed = set()
    for grp in spec.get("groups", []):
        with g.subgraph(name="cluster_" + grp["id"]) as c:
            c.attr(label=grp["label"], style="rounded,dashed", color="#7F77DD",
                   fontname="Helvetica", fontsize="13", fontcolor="#3C3489",
                   margin="20")
            for m in grp["members"]:
                add(c, nodes[m])
                placed.add(m)
    for nid, n in nodes.items():
        if nid not in placed:
            add(g, n)

    for i, e in enumerate(spec["edges"]):
        step = e.get("step")
        label = e.get("label", "")
        if step is not None:
            label = f"{step}. {label}" if label else str(step)
        g.edge(e["from"], e["to"], id=f"e{i}", label=label)
    return g


def embed_icons(svg_path):
    tree = etree.parse(svg_path)
    root = tree.getroot()
    # Scale to the window instead of a fixed pt size (viewBox keeps the ratio).
    root.set("width", "100%")
    if "height" in root.attrib:
        del root.attrib["height"]
    for img in tree.iter("{http://www.w3.org/2000/svg}image"):
        href = img.get(f"{{{XLINK}}}href")
        if href and os.path.isfile(href):
            data = base64.b64encode(open(href, "rb").read()).decode()
            img.set(f"{{{XLINK}}}href", f"data:image/png;base64,{data}")
    tree.write(svg_path, xml_declaration=True, encoding="UTF-8")


def main():
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    build(spec).render(out, cleanup=True)
    embed_icons(out + ".svg")
    print(out + ".svg")


if __name__ == "__main__":
    main()
