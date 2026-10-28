"""Search AWS icons.  Usage: python list_icons.py [keyword ...]
With no keyword, prints the short aliases the spec can use directly."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons

if len(sys.argv) == 1:
    print("Aliases:", ", ".join(sorted(icons.ALIASES)))
else:
    for p in icons.search(" ".join(sys.argv[1:])):
        print(p)
