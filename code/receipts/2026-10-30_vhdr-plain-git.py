"""Plain-git BrainVision headers at the PR head vs the annexed ones: changed lines, agreement with channels.tsv and
_ieeg.json, and data files untouched.

Usage: python 2026-10-30_vhdr-plain-git.py <git clone> <PR head> <dir with the annexed headers of origin/main>
"""

import difflib
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REV = "origin/main"
POINTER = b"/annex/objects/SHA256E-"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", clone, *args], capture_output=True, text=True, check=True).stdout


def blob(rev: str, rel: str) -> bytes:
    return subprocess.run(["git", "-C", clone, "show", f"{rev}:{rel}"], capture_output=True, check=True).stdout


def parse(text: str) -> tuple[list[tuple[str, str]], float]:
    channels = [tuple(m.groups()) for m in re.finditer(r"^Ch\d+=([^,]*),[^,]*,[^,]*,(.*)$", text, re.M)]
    return channels, 1e6 / float(re.search(r"^SamplingInterval=(.*)$", text, re.M).group(1))


def changed_lines(old: str, new: str) -> Counter:
    """Changed header lines: unit field of a channel record, comment, SamplingInterval, other."""
    kinds = Counter()
    a, b = old.splitlines(), new.splitlines()
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op == "replace" and i2 - i1 == j2 - j1:
            for x, y in zip(a[i1:i2], b[j1:j2]):
                if x.startswith("Ch") and x.rsplit(",", 1)[0] == y.rsplit(",", 1)[0]:
                    kinds["unit"] += 1
                elif x.startswith(";") and y.startswith(";"):
                    kinds["comment"] += 1
                elif x.startswith("SamplingInterval=") and y.startswith("SamplingInterval="):
                    kinds["SamplingInterval"] += 1
                else:
                    kinds["other"] += 1
        else:  # lines removed or added
            kinds["comment"] += sum(line.startswith(";") for line in b[j1:j2])
            kinds["other"] += (i2 - i1) + sum(not line.startswith(";") for line in b[j1:j2])
    return +kinds  # drop zero counts


def norm(unit: str) -> str:
    return unit.replace("µ", "u").replace("μ", "u")


clone, head, base_dir = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
head_sha, rev_sha = git("rev-parse", head).strip(), git("rev-parse", REV).strip()
vhdrs = sorted(f for f in git("ls-tree", "-r", "--name-only", head).splitlines() if f.endswith("_ieeg.vhdr"))
print(f"PR head {head_sha}, {REV} {rev_sha}")
print("| recording | origin/main: annexed, sha256 = key | head | lines changed | channels | "
      "units header / channels.tsv | units agree | rate header / ieeg.json / channels.tsv (Hz) | rate agrees | "
      ".eeg and .vmrk as on origin/main |")
print("|---|---|---|---|---:|---|---:|---|---|---|")
totals = Counter()
for rel in vhdrs:
    stem = rel.removesuffix("_ieeg.vhdr")
    pointer, new = blob(REV, rel), blob(head, rel)
    annexed = pointer.startswith(POINTER)
    old = (base_dir / rel).read_bytes()
    key_ok = annexed and pointer.strip().rsplit(b"--", 1)[-1].startswith(hashlib.sha256(old).hexdigest().encode())
    plain = not new.startswith(POINTER) and git("ls-tree", head, "--", rel).split()[0] == "100644"
    if new == pointer:  # still annexed at the head, same key: its content is the origin/main file
        new = old
    kinds = changed_lines(old.decode("utf-8"), new.decode("utf-8"))
    channels, rate = parse(new.decode("utf-8"))
    tsv = pd.read_csv(io.BytesIO(blob(head, f"{stem}_channels.tsv")), sep="\t", dtype=str, keep_default_na=False)
    sidecar = json.loads(blob(head, f"{stem}_ieeg.json"))
    names_ok = [n for n, _ in channels] == list(tsv["name"])
    units_ok = sum(norm(u) == norm(t) for (_, u), t in zip(channels, tsv["units"])) if names_ok else 0
    tsv_rates = {float(x) for x in tsv["sampling_frequency"]}
    rate_ok = abs(rate - sidecar["SamplingFrequency"]) < 1e-6 and all(abs(rate - r) < 1e-6 for r in tsv_rates)
    data_same = all(blob(REV, f"{stem}{s}") == blob(head, f"{stem}{s}") for s in ("_ieeg.eeg", "_ieeg.vmrk"))
    units = f"{'/'.join(sorted({u for _, u in channels}))} / {'/'.join(sorted(set(tsv['units'])))}"
    rates = f"{rate:g} / {sidecar['SamplingFrequency']:g} / {'/'.join(f'{r:g}' for r in sorted(tsv_rates))}"
    lines = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "none"
    state = "plain git" if plain else ("annexed, unchanged" if new is old else "other")
    print(f"| {Path(stem).name} | {annexed} {key_ok} | {state} | {lines} | {len(channels)} | {units} | "
          f"{units_ok}/{len(channels)} | {rates} | {rate_ok} | {data_same} |")
    totals.update(headers=1, plain=plain, key_ok=key_ok, names_ok=names_ok, rate_ok=rate_ok, data_same=data_same,
                  channels=len(channels), units_ok=units_ok, changed=bool(kinds), **kinds)
print(f"\nTotals: {dict(totals)}")
diff = git("diff", "--name-only", f"{REV}...{head}").split()
print(f"Files changed by the PR ({REV}...head): {len(diff)}; by suffix: "
      f"{dict(Counter(Path(f).suffix or Path(f).name for f in diff))}")
