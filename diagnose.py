"""Throwaway diagnostic: prints the ACTUAL first record inside following.json."""
import json
from pathlib import Path

matches = list(Path(".venv").rglob("following.json"))
if not matches:
    print("No following.json found under this folder.")

for path in matches:
    print(f"\nFile: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"  top-level type: {type(data).__name__}")

    # Drills down through any dict wrapping to the first list of records.
    node = data
    while isinstance(node, dict):
        list_values = [v for v in node.values() if isinstance(v, list)]
        if not list_values:
            break
        node = list_values[0]

    if isinstance(node, list) and node:
        print(f"  number of records: {len(node)}")
        print("  --- first record (pretty-printed) ---")
        print(json.dumps(node[0], indent=2)[:1000])
    else:
        print("  Couldn't locate a list of records. Raw top of file:")
        print(json.dumps(data, indent=2)[:1000])
