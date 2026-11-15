"""Write strategies/sNNN.py (self-contained) and strategies/index.csv from the specs.

    python research/build.py
"""
import csv
import inspect
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import helpers
import reg
import specs_a  # noqa: F401  (registers specs)
import specs_b  # noqa: F401

HELPERS = {n: f for n, f in vars(helpers).items() if inspect.isfunction(f) and f.__module__ == "helpers"}
ORDER = list(HELPERS)


def needed(src, acc=None):
    acc = set() if acc is None else acc
    for name, fn in HELPERS.items():
        if name not in acc and re.search(rf"(?<![\w.]){name}\(", src):
            acc.add(name)
            needed(inspect.getsource(fn), acc)
    return acc


def main():
    out_dir = os.path.join(ROOT, "strategies")
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if re.fullmatch(r"s\d+\.py", f):
            os.remove(os.path.join(out_dir, f))
    rows = []
    fams = {}
    for i, sp in enumerate(reg.SPECS, 1):
        sid = f"s{i:03d}"
        src = inspect.getsource(sp["fn"])
        src = src[src.index("def "):]
        body = re.sub(r"^def \w+\(", "def signal(", src, count=1)
        args = list(inspect.signature(sp["fn"]).parameters)[1:]
        assert args == list(sp["params"]), (sid, args, list(sp["params"]))
        use = [h for h in ORDER if h in needed(body)]
        parts = [
            f'"""{sid}: {sp["name"]} ({sp["family"]})\n\n{sp["idea"]}\n"""',
            "import numpy as np\nimport pandas as pd",
            f'NAME = {sp["name"]!r}\nFAMILY = {sp["family"]!r}\nIDEA = {sp["idea"]!r}\nPARAMS = {sp["params"]!r}',
        ]
        parts += [inspect.getsource(HELPERS[h]).rstrip() for h in use]
        parts.append(body.rstrip())
        with open(os.path.join(out_dir, sid + ".py"), "w") as fh:
            fh.write("\n\n\n".join(parts[:3]) + "\n\n\n" + "\n\n\n".join(parts[3:]) + "\n")
        rows.append([sid, sp["name"], sp["family"], sp["idea"]])
        fams[sp["family"]] = fams.get(sp["family"], 0) + 1
    with open(os.path.join(out_dir, "index.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "family", "idea"])
        w.writerows(rows)
    names = [r[1] for r in rows]
    assert len(set(names)) == len(names), "duplicate names"
    print(len(rows), "strategies;", fams)


if __name__ == "__main__":
    main()
