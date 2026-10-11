# ipfp-quickstart-check

Runs the three quick-start snippets (Option A, B and C) from the README of
[xKDR/india-public-finance-portal](https://github.com/xKDR/india-public-finance-portal) on a clone and
compares each answer with the portal's own canonical figure.

The question it answers: does the README's quick start produce the number the project says it should?
At commit `4f8c7b9b3ad661869affa4797eaed39e3f6e3f16` (2026-07-16), yes.

This is a third-party check. I did not write the portal or its data.

## Run

```bash
git clone https://github.com/xKDR/india-public-finance-portal
python3 -I quickstart_check.py ./india-public-finance-portal
```

Standard library only. Tested with Python 3.13 on Linux. Add `--strict` to also fail on the comment
mismatch described below.

## Result at the pinned commit

```
repo       ./india-public-finance-portal
commit     4f8c7b9b3ad661869affa4797eaed39e3f6e3f16
canonical  370,658.45 crore (budget estimate 2024-25, examples/data/processed/canonical_numbers.json), tolerance 0.01 crore

option    unrounded (crore)       diff  in tolerance    prints  comment says  comment matches print
A               370658.4489    -0.0011  yes            370,658       370,659  NO
B               370658.4489    -0.0011  yes            370,658       370,659  NO
C               370658.4489    -0.0011  yes            370,658       370,658  yes

PASS: all three options agree with the canonical figure within tolerance.
NOTE: Option A: the snippet prints 370,658 but its comment says ~370,659.
NOTE: Option B: the snippet prints 370,658 but its comment says ~370,659.
```

All three routes land within 0.0011 crore of `canonical_numbers.json`, against a stated tolerance of
0.01. The only finding is cosmetic: the comments on Options A and B say `~₹370,659 crore`, while the
code prints `₹370,658 crore` (the unrounded total is 370,658.4489, which rounds to 370,658). Option C's
comment is right.

## How it avoids checking the wrong thing

1. The three snippets are embedded in `quickstart_check.py`. Before running anything, the script checks
   that each one still appears word for word in the clone's `README.md`. If the README has changed, it
   stops and says so, instead of reporting on code the README no longer shows.
2. Only those embedded snippets are executed, never code read from the clone. Everything else the script
   touches (the README, `canonical_numbers.json`, the data files) is read as data.
3. The comparison uses the snippet's own unrounded `total`, not the rounded number it prints, so the
   0.01 tolerance means what it says.

## What this does not cover

- One figure: the Karnataka 2024-25 budget estimate total. Not Tamil Nadu, not other years or measures.
- Not the `examples/` compendium and its own reproduction targets.
- Not the quality of the data against the source budget PDFs. It checks that three routes through the
  published files agree with each other and with the project's recorded figure.
- Linux and Python 3.13 only. The snippets call `open()` without an encoding, so a result on Windows
  depends on the machine's default encoding. I have not tested that.

Exit status: 0 when all three options are within tolerance and every snippet matches the README, 1
otherwise.

MIT licensed (see `LICENSE`). Written by Krishna Harshith ([github.com/Harshith029](https://github.com/Harshith029)).
