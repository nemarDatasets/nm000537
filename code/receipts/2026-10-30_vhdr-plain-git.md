# Receipt: sub-400 runs 72/73 headers at 16000 Hz, committed as plain git text files

**Claim**: the `.vhdr` headers of sub-400 runs 72 and 73, annexed with `SamplingInterval=125.0` (8000 Hz) at
`origin/main`, are plain git text files at the PR head with `SamplingInterval=62.5` (16000 Hz), as in their `_ieeg.json`
and channels.tsv. Only that line and one added comment line differ from the annexed files; no `.eeg` or `.vmrk` file
changes, and the other 44 headers are unchanged.

**PR**: nemarDatasets/nm000537#3, header commit `3f48b391ffa2c25554cb95dcbf38e1f0b1991ea5` (the receipt commit adds
only this receipt's two files and a pointer line in `2026-10-22_sampling-rates.md`).

## Source
- NEMAR nm000537 `origin/main` `d46e41a6c50c42d36c8e7557d8f14691d866815b`: the 46 annexed `*_ieeg.vhdr`, fetched from the
  NEMAR annex (public S3 prefix `nemar/nm000537/objects/`); the sha256 of each equals its git-annex key (column 2).
- PR head: the 46 headers (2 git blobs, 44 annex pointers) and the channels.tsv and `_ieeg.json` of the 46 runs, read
  with `git show`.
- Mechanism and comment line as in nemarDatasets/nm000509 `432a7a42` (`; sampling rate corrected to ... Oct 2026 (see
  README)`): the annex pointer of the `.vhdr` is replaced by the header text, a plain git blob (mode 100644); no
  `.gitattributes` change. Here the files were added with `git -c annex.largefiles=nothing add`.

## Method
- Header text: the annexed file with `SamplingInterval=125.0` -> `SamplingInterval=62.5` and the comment line
  `; sampling rate corrected to 16000 Hz Oct 2026 (see README)` inserted after the converter comment.
- `2026-10-30_vhdr-plain-git.py <clone> <PR head> <dir with the origin/main headers>` (Python 3.12.15, pandas 3.1.0),
  per header: annexed at `origin/main` with sha256 = key; plain git blob with mode 100644 at the head (headers still
  annexed at the head have the `origin/main` key and are read from the fetched file); changed lines (difflib, classed as
  unit field, comment, SamplingInterval or other); header units vs channels.tsv units per channel (same names in the
  same order); header rate (1e6 / SamplingInterval) vs `_ieeg.json` SamplingFrequency and channels.tsv
  sampling_frequency; `.eeg` (annex pointer) and `.vmrk` (git text) blobs at the head equal to those at `origin/main`.

## Result (script output)

| recording | origin/main: annexed, sha256 = key | head | lines changed | channels | units header / channels.tsv | units agree | rate header / ieeg.json / channels.tsv (Hz) | rate agrees | .eeg and .vmrk as on origin/main |
|---|---|---|---|---:|---|---:|---|---|---|
| sub-369_task-amygdalastim_run-100 | True True | annexed, unchanged | none | 202 | n/a / uV | 0/202 | 8000 / 8000 / 8000 | True | True |
| sub-369_task-amygdalastim_run-91 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 2000 / 2000 | False | True |
| sub-369_task-amygdalastim_run-92 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 2000 / 2000 | False | True |
| sub-376_task-amygdalastim_run-108 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-384_task-amygdalastim_run-46 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-384_task-amygdalastim_run-47 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-384_task-amygdalastim_run-48 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-384_task-amygdalastim_run-49 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-399_task-amygdalastim_run-132 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-399_task-amygdalastim_run-133 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-400_task-amygdalastim_run-72 | True True | plain git | SamplingInterval 1, comment 1 | 256 | n/a / uV | 0/256 | 16000 / 16000 / 16000 | True | True |
| sub-400_task-amygdalastim_run-73 | True True | plain git | SamplingInterval 1, comment 1 | 256 | n/a / uV | 0/256 | 16000 / 16000 / 16000 | True | True |
| sub-404_task-amygdalastim_run-39 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-404_task-amygdalastim_run-40 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-405_task-amygdalastim_run-102 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-405_task-amygdalastim_run-103 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-405_task-amygdalastim_run-104 | True True | annexed, unchanged | none | 254 | n/a / uV | 0/254 | 8000 / 8000 / 8000 | True | True |
| sub-405_task-amygdalastim_run-105 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-405_task-amygdalastim_run-106 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-418_task-amygdalastim_run-77 | True True | annexed, unchanged | none | 191 | n/a / uV | 0/191 | 8000 / 8000 / 8000 | True | True |
| sub-466_task-amygdalastim_run-128 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-466_task-amygdalastim_run-129 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 8000 / 8000 | True | True |
| sub-466_task-amygdalastim_run-132 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-466_task-amygdalastim_run-133 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-466_task-amygdalastim_run-134 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-466_task-amygdalastim_run-135 | True True | annexed, unchanged | none | 256 | n/a / uV | 0/256 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-117 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-118 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-123 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-124 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-125 | True True | annexed, unchanged | none | 191 | n/a / uV | 0/191 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-127 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-89 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-90 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-91 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-92 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-93 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-94 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-95 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-96 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-511_task-amygdalastim_run-97 | True True | annexed, unchanged | none | 192 | n/a / uV | 0/192 | 8000 / 8000 / 8000 | True | True |
| sub-515_task-amygdalastim_run-13 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 16000 / 16000 | False | True |
| sub-515_task-amygdalastim_run-14 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 16000 / 16000 | False | True |
| sub-515_task-amygdalastim_run-6 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 16000 / 16000 | False | True |
| sub-515_task-amygdalastim_run-7 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 16000 / 16000 | False | True |
| sub-515_task-amygdalastim_run-8 | True True | annexed, unchanged | none | 255 | n/a / uV | 0/255 | 8000 / 16000 / 16000 | False | True |

Totals: {'headers': 46, 'plain': 2, 'key_ok': 46, 'names_ok': 46, 'rate_ok': 39, 'data_same': 46, 'channels': 10682, 'units_ok': 0, 'changed': 2, 'comment': 2, 'SamplingInterval': 2}

Files changed by the PR (origin/main...head): 13; by suffix: {'CHANGES': 1, '.md': 2, '.py': 1, '.json': 3, '.tsv': 4, '.vhdr': 2} (at the header commit; no `.eeg` or `.vmrk` among them.)

- sub-400 runs 72 and 73: plain git text at the head; header, `_ieeg.json` and channels.tsv all give 16000 Hz; the only
  changed lines are `SamplingInterval` and the added comment; `.eeg` and `.vmrk` unchanged.
- Not changed by this PR, as at `origin/main`: the headers of sub-369 runs 91/92 (2000 Hz in `_ieeg.json` and
  channels.tsv) and of the 5 sub-515 runs (16000 Hz) say 8000 Hz (CHANGES 1.0.1, README); every header gives unit
  `n/a` while channels.tsv gives `uV` (CHANGES 1.0.1).

## Coverage
46 of 46 headers (2 changed), 46 of 46 channels.tsv and `_ieeg.json`, 46 of 46 `.eeg` and `.vmrk`.

## Reproduce
```
uv run --no-project --python 3.12 --with pandas python code/receipts/2026-10-30_vhdr-plain-git.py \
  <nm000537 git clone> 3f48b391ffa2c25554cb95dcbf38e1f0b1991ea5 <dir with the 46 origin/main headers>
```
Run on 2026-10-30 (header text only, no signal data read); the table is verbatim from its output.
