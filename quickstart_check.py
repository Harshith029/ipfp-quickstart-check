"""Run the three quick-start options from the xKDR india-public-finance-portal README and compare
each result with the portal's own canonical figure.

    python3 -I quickstart_check.py /path/to/india-public-finance-portal [--strict]

Steps
  1. Check that each embedded snippet still appears word for word in the repo's README.md.
     If the README has changed, the run stops, so it never reports on code the README no longer shows.
  2. Run each snippet with the repo root as the working directory, capture what it prints, and read
     the unrounded total from the snippet's own `total` variable.
  3. Compare the unrounded total (crore) with examples/data/processed/canonical_numbers.json
     (onboarding.spend_vs_budget.be, within tolerance_crore).
  4. Compare the figure each snippet prints with the "~" figure in the snippet's own comment.

Exit status: 0 when all three options are within tolerance and every snippet matches the README.
1 otherwise. A comment that disagrees with the printed figure is reported as a NOTE and only fails
the run with --strict.

Reads files only. The only code executed is the three snippets embedded below, after they have been
matched against the README. Standard library only.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The snippets, copied from the README of xKDR/india-public-finance-portal at commit
# 4f8c7b9b3ad661869affa4797eaed39e3f6e3f16. Step 1 refuses to run if the README no longer matches.
SNIPPETS = {
    "A": r'''import csv
total = 0
with open("state-finances/karnataka/KA_years/KA_2024-25/KA_csv/KA_budget_2024-25.csv") as f:
    for row in csv.DictReader(f):
        if (row["type_of_table"] == "object_head"
                and row["row_type"] == "Data"
                and row["row_level"] == "Object-Head"):
            v = row["budget_estimate_2024_25_amount"].replace(",", "").strip()
            if v and v != "-":
                total += float(v)
print(f"Total BE 2024-25: ₹{total/100:,.0f} crore")  # ~₹370,659 crore''',
    "B": r'''import json
total = 0
with open("state-finances/karnataka/KA_years/KA_2024-25/KA_json/KA_budget_leaves_2024-25.ndjson") as f:
    for line in f:
        for amt in json.loads(line)["amounts"]:
            if amt["measure"] == "budget_estimate" and amt["fiscal_year"] == "2024-25":
                total += amt["value"]
print(f"Total BE 2024-25: ₹{total/100:,.0f} crore")  # ~₹370,659 crore''',
    "C": r'''import csv
total = sum(
    float(r["amount_lakh"]) for r in
    csv.DictReader(open("examples/data/processed/karnataka_budget_tidy.csv"))
    if r["fiscal_year"] == "2024-25" and r["measure"] == "BE"
) / 100
print(f"Total BE 2024-25: ₹{total:,.0f} crore")  # ~₹370,658 crore''',
}
# `total` is in lakh for A and B, and already in crore for C.
TO_CRORE = {"A": 0.01, "B": 0.01, "C": 1.0}
CANONICAL = "examples/data/processed/canonical_numbers.json"


def run(snippet: str, root: Path) -> tuple[str, float]:
    """Run one snippet with root as the working directory. Returns (printed text, unrounded `total`)."""
    out = io.StringIO()
    ns: dict = {"__name__": "__readme_snippet__"}
    before = os.getcwd()
    os.chdir(root)
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(snippet, "<readme snippet>", "exec"), ns)
    finally:
        os.chdir(before)
    return out.getvalue().strip(), float(ns["total"])


def commit_of(root: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def number_after_rupee(text: str) -> int | None:
    m = re.search(r"₹([\d,]+) crore", text)
    return int(m.group(1).replace(",", "")) if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", help="path to a clone of xKDR/india-public-finance-portal")
    ap.add_argument("--strict", action="store_true",
                    help="also fail when a README comment disagrees with what its snippet prints")
    a = ap.parse_args()
    root = Path(a.repo).resolve()

    readme = root / "README.md"
    canon_path = root / CANONICAL
    for p in (readme, canon_path):
        if not p.is_file():
            print(f"missing {p}: is {root} a clone of india-public-finance-portal?")
            return 1

    text = readme.read_text(encoding="utf-8")
    drifted = [k for k, s in SNIPPETS.items() if s.strip() not in text]
    if drifted:
        print("README.md no longer shows Option(s) " + ", ".join(drifted) + " word for word as embedded in "
              "this script. Nothing was run. Compare the README with SNIPPETS and update the script.")
        return 1

    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    svb = canon["onboarding"]["spend_vs_budget"]
    if svb["fiscal_year"] != "2024-25":
        print(f"canonical figure is for {svb['fiscal_year']}, the snippets compute 2024-25. Nothing compared.")
        return 1
    want, tol = float(svb["be"]), float(canon["tolerance_crore"])

    print(f"repo       {a.repo}")
    print(f"commit     {commit_of(root)}")
    print(f"canonical  {want:,.2f} crore (budget estimate 2024-25, {CANONICAL}), tolerance {tol} crore")
    print()
    print(f"{'option':<7}{'unrounded (crore)':>20}{'diff':>11}  {'in tolerance':<13}{'prints':>9}{'comment says':>14}  comment matches print")

    failed = False
    notes = []
    for key, snippet in SNIPPETS.items():
        printed_text, total = run(snippet, root)
        crore = total * TO_CRORE[key]
        diff = crore - want
        ok = abs(diff) <= tol
        printed = number_after_rupee(printed_text)
        claimed = number_after_rupee(snippet.splitlines()[-1].split("#", 1)[1])
        same = printed == claimed
        failed |= not ok
        if not same:
            notes.append(f"Option {key}: the snippet prints {printed:,} but its comment says ~{claimed:,}.")
        print(f"{key:<7}{crore:>20.4f}{diff:>+11.4f}  {'yes' if ok else 'NO':<13}"
              f"{printed:>9,}{claimed:>14,}  {'yes' if same else 'NO'}")

    print()
    if failed:
        print("FAIL: at least one option is outside the canonical tolerance.")
    else:
        print("PASS: all three options agree with the canonical figure within tolerance.")
    for n in notes:
        print("NOTE: " + n)
    return 1 if failed or (notes and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
