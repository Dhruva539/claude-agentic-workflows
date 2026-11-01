"""Write the real graph as Mermaid so the diagram always matches the code.
Usage: python draw_graph.py > ../docs/loan_graph.mmd
Render: mmdc -i ../docs/loan_graph.mmd -o ../docs/loan_graph.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loan_graph import g

print(g.compile().get_graph().draw_mermaid())
