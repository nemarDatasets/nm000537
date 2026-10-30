#!/usr/bin/env python3
"""nm000537 fix-20261030: regenerate the BrainVision headers of the 7 runs whose SamplingFrequency was corrected in
version 1.0.1 (sub-369 runs 91/92: 2000 Hz; sub-515 runs 6/7/8/13/14: 16000 Hz) but whose .vhdr still said 125 us
(8000 Hz). Only the SamplingInterval line changes (plus one ';' comment line); the unit fields stay as released
(n/a), as in the sub-400 headers of the open pull request #3 (fix/sub-400-16khz). .eeg and .vmrk are unchanged.
Usage: fix-20261030_vhdr_rates.py <dataset root>  (reads each run's current header from the public NEMAR S3 copy by
its git-annex key on the parent commit, writes the new header as a plain file)."""
import json, re, subprocess, sys, urllib.request, os
root = sys.argv[1]
RUNS = ["sub-369/ieeg/sub-369_task-amygdalastim_run-91", "sub-369/ieeg/sub-369_task-amygdalastim_run-92"] + \
       [f"sub-515/ieeg/sub-515_task-amygdalastim_run-{r}" for r in (6, 7, 8, 13, 14)]
for run in RUNS:
    sf = json.load(open(os.path.join(root, run + "_ieeg.json")))["SamplingFrequency"]
    ptr = subprocess.run(["git", "-C", root, "show", "HEAD:" + run + "_ieeg.vhdr"], capture_output=True, text=True, check=True).stdout.strip()
    key = ptr.rsplit("/", 1)[1]
    txt = urllib.request.urlopen(f"https://nemar.s3.us-east-2.amazonaws.com/nm000537/objects/{key}", timeout=60).read().decode("utf-8")
    si_new = 1e6 / sf
    assert re.search(r"^SamplingInterval=125\.0\r?$", txt, re.M), run
    txt2 = re.sub(r"^SamplingInterval=125\.0", f"SamplingInterval={si_new:g}" if si_new != int(si_new) else f"SamplingInterval={si_new:.1f}", txt, count=1, flags=re.M)
    lines = txt2.split("\n")
    lines.insert(2, f"; sampling rate corrected to {sf:g} Hz Oct 2026 (see README)")
    open(os.path.join(root, run + "_ieeg.vhdr"), "w", newline="").write("\n".join(lines))
    print(run, sf, f"SamplingInterval 125.0 -> {1e6/sf}")
