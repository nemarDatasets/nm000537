[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.nm000537-blue)](https://doi.org/10.82901/nemar.nm000537)

# Mapping effective connectivity of human amygdala with intracranial stimulation - es-TT evoked potentials (OSF dngv5)

Evoked-potential epochs recorded with intracranial electrodes during single-pulse electrical stimulation of the amygdala
("electrical stimulation tract-tracing", es-TT) in neurosurgical patients, released on OSF by Hiroyuki Oya, LeiQi
(doi:10.17605/OSF.IO/DNGV5; licence on the OSF node: GNU General Public License (GPL) 3.0) for Sawada et al., Nature Communications 2022
(doi:10.1038/s41467-022-32644-y). OSF description: "esTT data converted in to MATLAB formatted matrix."

## Content
- 11 participants (`sub-<PT number>`, the numbers used in the article), 46 stimulation runs (`run-<release
  run folder>`), each the release's EP_data3D matrix (typically 60 epochs) written back to back (`RecordingType` epoched).
- Sampling rate: not stored in the release files. 8000 Hz (the article's rate) for 38 of the 46 runs, 2000 Hz for the 3
  sub-369 runs and 16000 Hz for sub-515 (all 5 runs). Basis: the authors' analysis code (github.com/hiroyukioya/Amygdala-Network,
  `New_Waveform_Comparison_N150_Brain.m`) treats every epoch as -1..1 s and takes the rate from the epoch length
  (`SR=(numel(EP_data(1,:))-2)/2`, then resamples to 8000 Hz), so epochs of 4001, 16001 and 32001 samples are 2, 8 and 16 kHz.
  This agrees with the 60 Hz mains harmonics in the baseline of sub-369 runs 91/92 (spectral check of 16 Oct 2026) and with
  FS 16k in the deposit's `515_experiment_list.ods`, and it sets sub-400 (16001 samples) at 8000 Hz.
  **Correction (1.0.1, 2026-10-16; 1.0.3, 2026-10-21 for sub-369 run 100):** version 1.0.0 gave 8000 Hz for all runs. The
  BrainVision headers (`_ieeg.vhdr`) of the 8 corrected runs (sub-369, sub-515) still say 8000 Hz (SamplingInterval 125 us)
  until they are re-generated: use `SamplingFrequency` in `_ieeg.json`.
- Epochs: each run is the release's EP_data3D matrix (25-62 epochs per run: 60 in 37 runs, 30 in the 5 sub-515 runs) written back to back. Epoch length is
  4001 samples in the 3 sub-369 runs (2.0005 s at 2 kHz), 32001 samples
  (2.0000625 s at 16 kHz) in the 5 sub-515 runs and 16001 samples in the other 38 runs (2.000125 s at 8 kHz). The stimulus artefact (sample index per run in code/conversion_report.json, usually the centre) is
  the epoch time zero and has an event in events.tsv. The stimulated amygdala contact pair is not identified in the release,
  except for sub-515 (stimulation channels per block in `515_experiment_list.ods`, copied into `ElectricalStimulationParameters`).
- Channels: only the release's channel slots that contain data, named `ch<slot>`; the contact label from the patient's
  spreadsheet (PT<n>.xlsx / Eleclocation.xlsx) is in the channel description. Typing rule actually applied: labels
  containing "depth" are SEEG, labels containing "strip" or "grid" are ECOG, and every other channel is also typed SEEG
  although its electrode type is not stated: channels with only an anatomical label (180-181 per run in sub-399 and
  sub-400, 11 in sub-376; e.g. "MTG", "Orbital g.") and channels with no spreadsheet label (all 255 of sub-515, 5-75 in
  each other subject).
  Units: microvolts (not stated in the release; baseline amplitudes of a few to a few hundred uV and clipping at about
  +/-1000 in many channels, counts per run in the conversion report; version 1.0.0 had `n/a`). Reference: subgaleal
  contact (article). Channels with NaN samples are marked bad.
- `sourcedata/osf_dngv5/`: per-patient spreadsheets, Coordinates.mat (space not stated, so not used for electrodes.tsv)
  and the few EPdata2.mat files whose layout ([254 x 16002]) is undocumented; MAT text-header dates set to day 01.
- Not included: es-fMRI folders (the fMRI data are on OpenNeuro ds002799) and the Granger-causality source data.

## Provenance
Converted by the ieeg-nemar-20261005 campaign (convert_20261014, slice 6) with `code/cv6_conv_lit165.py`.
