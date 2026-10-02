#!/usr/bin/env python3
"""Put the LunarCrush referral in front of anyone about to need an API key.

Every project here needs a key to run, so a project README is the highest
intent moment there is: somebody has read the method, wants to reproduce it,
and needs a key in the next five minutes. Before this, the code appeared in
exactly one of 34 READMEs and otherwise only in Instagram carousel footers,
which are images, where links do not work.

The block is idempotent, so re-running after adding a project is safe. If a
tracked referral URL ever replaces the bare code, change LINK and re-run.

Usage:
    python3 tools/affiliate_pass.py          # show what would change
    python3 tools/affiliate_pass.py --write
"""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = "https://lunarcrush.com/"   # swap for a tracked URL if one exists
CODE = "NICKI"
MARKER = "<!-- lunarcrush-referral -->"

BLOCK = f"""
{MARKER}
---

Needs a [LunarCrush]({LINK}) API key. Code `{CODE}` takes 15% off a
subscription, and pays me a commission. It costs you less, not more, and
nothing here changes based on it.
"""

ROOT_OLD = ("All projects authenticate with a LunarCrush API key passed as a Bearer token. "
            "Sign up and grab a key at [lunarcrush.com](https://lunarcrush.com/) under Settings > API.")
ROOT_NEW = (f"All projects authenticate with a LunarCrush API key passed as a Bearer token. "
            f"Sign up at [lunarcrush.com]({LINK}) and grab a key under Settings > API.\n\n"
            f"Code `{CODE}` takes 15% off a subscription, and pays me a commission. It costs you "
            f"less, not more. Every finding in this repo, including the ones that say the data is "
            f"wrong or that a signal does not exist, was published the same way before and after "
            f"that arrangement existed.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    targets = sorted((ROOT / "projects").glob("*/README.md"))
    added, already = [], []
    for p in targets:
        text = p.read_text()
        if MARKER in text:
            already.append(p)
            continue
        added.append(p)
        if args.write:
            p.write_text(text.rstrip() + "\n" + BLOCK)

    root = ROOT / "README.md"
    rtext = root.read_text()
    # Check for something only the new text has. Both versions open with the
    # same sentence, so a prefix match reports "already done" on the old one.
    root_done = f"Code `{CODE}` takes 15% off" in rtext
    if ROOT_OLD in rtext and not root_done:
        if args.write:
            root.write_text(rtext.replace(ROOT_OLD, ROOT_NEW))
        root_change = True
    else:
        root_change = False

    verb = "added to" if args.write else "would add to"
    print(f"{verb} {len(added)} project READMEs")
    for p in added:
        print(f"  {p.relative_to(ROOT)}")
    if already:
        print(f"\nalready had the block: {len(already)}")
    print(f"\nroot README: {'updated' if (root_change and args.write) else 'would update' if root_change else 'unchanged'}")
    if not args.write:
        print("\nnothing written. re-run with --write")


if __name__ == "__main__":
    main()
