"""convert_20261014 slice 6: src-literature-165 (OSF dngv5, 'MAPPING EFFECTIVE CONNECTIVITY OF HUMAN AMYGDALA WITH INTRACRANIAL
STIMULATION', GNU GPL 3.0 on the OSF node; Sawada et al., Nat Commun 2022, es-TT data) -> iEEG-BIDS (epoched).
Release: <PT>/<run>/EPdata3D.mat (EP_data3D [trials x samples x 256 channel slots], NaN for unused slots), a few
<PT>/<run>/EPdata2.mat (EP_data [254 x 16002], layout undocumented), <PT>/PT<PT>.xlsx or Eleclocation.xlsx (channel number
-> contact label), <PT>/Coordinates.mat ([n x 4], space not stated), es-fMRI and Granger-causality result folders.
Sampling rate and epoch window are not in the files. Evidence used here: the article states iEEG was recorded at 8 kHz, and
the single-trial baseline spectra of the EP matrices peak at 0.0075 cycles/sample with odd harmonics 0.0225 and 0.0375
(= 60/180/300 Hz mains at 8000 Hz; probe ieeg-cv6-probe3); the stimulus artefact is located per file (largest NaN-aware
derivative of the trial mean) and used as each epoch's time zero. Here: one BIDS run per EPdata3D (run label = release run
folder), epochs back to back (RecordingType epoched, IEEE_FLOAT_32, only channel slots with data), one event per epoch at
the artefact. EPdata2, Coordinates (space not stated), es-fMRI and CGC folders go to sourcedata only.
Usage: python cv6_conv_lit165.py src-literature-165"""
import glob, json, os, re, shutil, sys
import numpy as np
import scipy.io as sio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cv6_common import *  # noqa

CID = sys.argv[1] if len(sys.argv) > 1 else "src-literature-165"
SRC = os.path.join(src_dir(CID), "files"); OUT = fresh_out(CID); REP = rep_dir(CID)
NODE = "dngv5"; URL = f"https://osf.io/{NODE}/"
CONV = "harness/cv6_conv_lit165.py (ieeg-nemar-20261005 campaign, convert_20261014 slice 6)"
FS = 8000.0
meta = osf_meta(NODE)
LIC_SRC = meta.get("license_name") or ""
assert "GNU General Public License" in LIC_SRC and "3.0" in LIC_SRC, LIC_SRC
LIC = "GPL-3.0"
authors = meta.get("contributors") or ["Hiroyuki Oya", "LeiQi"]


def labels_for(pt):
    import pandas as pd
    out = {}
    for x in glob.glob(os.path.join(SRC, pt, "*.xlsx")):
        df = pd.read_excel(x, header=None)
        for _, r in df.iterrows():
            try:
                n = int(float(str(r[0]).strip()))
            except Exception:
                continue
            lab = str(r[1]).strip()
            lab = re.sub(r"^\d+:\s*", "", lab)
            out[n] = lab
    return out


pub = {"cand_id": CID, "converter": CONV, "license_written": LIC, "osf_license": LIC_SRC, "sfreq_basis": "article 8 kHz + 60 Hz mains harmonics at 0.0075 cyc/sample (probe3)", "runs": []}
part = []
pts = sorted(d for d in os.listdir(SRC) if re.fullmatch(r"\d+", d))
for pt in pts:
    labs = labels_for(pt)
    files = sorted(glob.glob(os.path.join(SRC, pt, "*", "EPdata3D.mat")), key=lambda p: int(os.path.basename(os.path.dirname(p))))
    nrun = 0
    for p in files:
        runf = os.path.basename(os.path.dirname(p))
        X = sio.loadmat(p)["EP_data3D"]
        ntr, nt, nslot = X.shape
        keep = [c for c in range(nslot) if np.isfinite(X[:, :, c]).any()]
        if not keep:
            pub["runs"].append({"pt": pt, "run": runf, "skipped": "no channel slot with data"}); continue
        clean = [c for c in keep if np.isfinite(X[:, :, c]).all() and np.nanmax(np.abs(X[:, :, c])) < 990]
        tm = np.nanmean(X[:, :, clean if clean else keep], axis=0)
        d = np.nanmean(np.abs(np.diff(tm, axis=0)), axis=1)
        art = int(np.nanargmax(d)) + 1 if np.isfinite(d).any() else nt // 2
        art_basis = "artefact" if clean else "artefact (no fully clean channel; partial channels)"
        if abs(art - nt // 2) > 40:  # detection not near the centre (all well-detected runs are within 7 samples): use the centre
            art_basis = f"artefact detection ambiguous (found sample {art}); epoch centre used"; art = nt // 2
        sub = pt; ent = f"sub-{sub}_task-amygdalastim_run-{int(runf)}"
        Dd = os.path.join(OUT, f"sub-{sub}", "ieeg")
        names = [f"ch{c + 1:03d}" for c in keep]
        data = np.ascontiguousarray(X[:, :, keep].reshape(ntr * nt, len(keep)).astype(np.float32))
        write_bv(os.path.join(Dd, f"{ent}_ieeg"), data, FS, names, ["n/a"] * len(keep), "IEEE_FLOAT_32", [1.0] * len(keep),
                 f"{CONV}; {ntr} epochs x {nt} samples back to back; channel slots with data only")
        nan_ch = [names[i] for i, c in enumerate(keep) if not np.isfinite(X[:, :, c]).all()]
        clip_ch = [names[i] for i, c in enumerate(keep) if np.nanmax(np.abs(X[:, :, c])) >= 999]
        extra = [{"description": (labs.get(c + 1, "no label in the release spreadsheet")) + f" (release channel slot {c + 1})",
                  "status": "bad" if names[i] in nan_ch else "good",
                  "status_description": "contains NaN samples in the release" if names[i] in nan_ch else "n/a"} for i, c in enumerate(keep)]
        types = ["SEEG" if "depth" in labs.get(c + 1, "").lower() else ("ECOG" if re.search(r"strip|grid", labs.get(c + 1, ""), re.I) else "SEEG") for c in keep]
        write_channels(os.path.join(Dd, f"{ent}_channels.tsv"), names, types, ["n/a"] * len(keep), FS, extra=extra)
        ev = [[round((k * nt + art) / FS, 6), 0.0004, int(k * nt + art), "electrical_stimulation", k + 1] for k in range(ntr)]
        wtsv(os.path.join(Dd, f"{ent}_events.tsv"), ["onset", "duration", "sample", "trial_type", "epoch"], ev)
        wjson(os.path.join(Dd, f"{ent}_ieeg.json"), ieeg_sidecar(
            "amygdalastim", FS, ntr * nt / FS, types, 60, "n/a (not stated in the release)", manufacturer="Neuralynx (ATLAS, per the article)",
            RecordingType="epoched", EpochLength=nt / FS,
            TaskDescription="Single-pulse bipolar electrical stimulation of the amygdala (article: 60 charge-balanced biphasic pulses, 0.2 ms per phase, 0.5 Hz, 9 mA) with concurrent iEEG; the stimulated contact pair is not identified in the release.",
            Instructions="n/a", InstitutionName="n/a", SoftwareFilters="n/a", HardwareFilters="n/a", ElectricalStimulation=True,
            ElectricalStimulationParameters="article: biphasic square pulses 0.2 ms/phase, alternating polarity, 0.5 Hz with jitter, 9 mA, bipolar through adjacent amygdala contacts",
            iEEGPlacementScheme="subdural strips/grids and depth electrodes (labels from the release spreadsheets)"))
        nrun += 1
        pub["runs"].append({"pt": pt, "run": runf, "n_epochs": ntr, "n_samples": nt, "n_slots_with_data": len(keep), "n_clean": len(clean), "artefact_sample": art,
                            "artefact_basis": art_basis, "center": nt // 2, "nan_channels": len(nan_ch), "clipped_channels_ge_999": len(clip_ch)})
        print(ent, X.shape, "keep", len(keep), "clean", len(clean), "art", art, "center", nt // 2, flush=True)
        del X, data
    if nrun:
        part.append([f"sub-{sub}", "n/a", "n/a", "epilepsy"])
    # sourcedata for this patient: spreadsheets, Coordinates, EPdata2
    for s in glob.glob(os.path.join(SRC, pt, "**", "*"), recursive=True):
        if os.path.isdir(s) or os.path.basename(s) == "EPdata3D.mat":
            continue
        dst = os.path.join(OUT, "sourcedata", "osf_dngv5", os.path.relpath(s, SRC)); os.makedirs(os.path.dirname(dst), exist_ok=True)
        if s.endswith(".mat"):
            nb, _ = scrub_mat_header(open(s, "rb").read()); open(dst, "wb").write(nb)
        else:
            shutil.copyfile(s, dst)
add_electrodes_na(OUT, "Coordinates.mat files in the release do not state their space and are kept in sourcedata; x, y, z = n/a here.", types=("SEEG", "ECOG"))
wtsv(os.path.join(OUT, "participants.tsv"), ["participant_id", "age", "sex", "group"], part)
wjson(os.path.join(OUT, "participants.json"), {"participant_id": {"Description": "sub-<release patient number> (the 'PT' numbers used in the article)"},
      "age": {"Description": "not in the release"}, "sex": {"Description": "not in the release"}, "group": {"Description": "neurosurgical patients with epilepsy (article)"}})
wjson(os.path.join(OUT, "task-amygdalastim_events.json"), {"trial_type": {"Levels": {"electrical_stimulation": "single stimulation pulse at the epoch's time zero (located as the stimulus artefact in the release epochs)"}},
      "epoch": {"Description": "epoch index within the run (release trial order)"}})
nrec = sum(1 for r in pub["runs"] if "n_epochs" in r)
wjson(os.path.join(OUT, "dataset_description.json"), dataset_description(
    "Mapping effective connectivity of human amygdala with intracranial stimulation: es-TT evoked-potential epochs (OSF dngv5)", authors, LIC, URL,
    [URL, "https://doi.org/10.1038/s41467-022-32644-y", "https://doi.org/10.17605/OSF.IO/DNGV5"],
    f"Cite the OSF project doi:10.17605/OSF.IO/DNGV5 ({', '.join(authors)}) and Sawada et al., Nat Commun 2022, doi:10.1038/s41467-022-32644-y.",
    [{"Name": "cv6_conv_lit165.py", "Description": "EPdata3D epochs written back to back (epoched iEEG, float32); sampling rate 8 kHz from the article + mains-harmonic check; stimulus artefact as time zero. Code in code/."}],
    doi="10.17605/OSF.IO/DNGV5", keywords=["iEEG", "electrical stimulation", "evoked potentials", "amygdala", "effective connectivity"],
    ethics=["University of Iowa and California Institute of Technology Institutional Review Boards (article)"]))
open(os.path.join(OUT, "README"), "w").write(f"""# Mapping effective connectivity of human amygdala with intracranial stimulation - es-TT evoked potentials (OSF {NODE})

Evoked-potential epochs recorded with intracranial electrodes during single-pulse electrical stimulation of the amygdala
("electrical stimulation tract-tracing", es-TT) in neurosurgical patients, released on OSF by {', '.join(authors)}
(doi:10.17605/OSF.IO/DNGV5; licence on the OSF node: {LIC_SRC}) for Sawada et al., Nature Communications 2022
(doi:10.1038/s41467-022-32644-y). OSF description: "esTT data converted in to MATLAB formatted matrix."

## Content
- {len(part)} participants (`sub-<PT number>`, the numbers used in the article), {nrec} stimulation runs (`run-<release
  run folder>`), each the release's EP_data3D matrix (typically 60 epochs) written back to back (`RecordingType` epoched).
- Sampling rate 8000 Hz: not stored in the files; the article states 8 kHz acquisition and the single-trial baseline
  spectra show mains at 60/180/300 Hz only under that rate. Epochs are 16001 samples (2 s) in most runs; the stimulus
  artefact (sample index per run in code/conversion_report.json, usually the centre) is the epoch time zero and has an
  event in events.tsv. The stimulated amygdala contact pair is not identified in the release.
- Channels: only the release's channel slots that contain data, named `ch<slot>`; the contact label from the patient's
  spreadsheet (PT<n>.xlsx / Eleclocation.xlsx) is in the channel description, and labels containing "depth" are typed
  SEEG, "strip"/"grid" ECOG. Units are not stated in the release (`n/a`); values look like microvolts and are clipped at
  about +/-1000 in many channels (counts per run in the conversion report). Channels with NaN samples are marked bad.
- `sourcedata/osf_dngv5/`: per-patient spreadsheets, Coordinates.mat (space not stated, so not used for electrodes.tsv)
  and the few EPdata2.mat files whose layout ([254 x 16002]) is undocumented; MAT text-header dates set to day 01.
- Not included: es-fMRI folders (the fMRI data are on OpenNeuro ds002799) and the Granger-causality source data.

## Provenance
Converted by the ieeg-nemar-20261005 campaign (convert_20261014, slice 6) with `code/cv6_conv_lit165.py`.
""")
copy_code(CID, ["cv6_conv_lit165.py", "cv6_common.py"])
bidsignore(OUT, ["sourcedata/", "code/"])
import mne
r0 = next(r for r in pub["runs"] if "n_epochs" in r)
vh = glob.glob(os.path.join(OUT, f"sub-{r0['pt']}", "ieeg", f"*run-{int(r0['run'])}_ieeg.vhdr"))[0]
raw = mne.io.read_raw_brainvision(vh, preload=False, verbose="error")
X = sio.loadmat(os.path.join(SRC, r0["pt"], r0["run"], "EPdata3D.mat"))["EP_data3D"]
keep = [c for c in range(X.shape[2]) if np.isfinite(X[:, :, c]).any()]
ref = X[:2, :, keep[:3]].reshape(-1, 3).T.astype(np.float32).astype(np.float64)
x = raw.get_data(picks=[0, 1, 2], start=0, stop=ref.shape[1])
nz = np.isfinite(ref) & (np.abs(ref) > 1e-3)
sc = float(np.median(x[nz] / ref[nz])) if nz.any() else 1.0
dd = float(np.nanmax(np.abs(x / sc - ref)))
pub["roundtrip"] = {"run": vh, "mne_scale": sc, "max_abs_diff": dd, "n_times_ok": bool(raw.n_times == r0["n_epochs"] * r0["n_samples"])}
ok = dd < 1e-3 and pub["roundtrip"]["n_times_ok"]
pub["n_subjects"] = len(part); pub["n_runs"] = nrec
report(CID, pub)
print(json.dumps(pub["roundtrip"], default=str))
print("CONVERT_OK" if ok else "CONVERT_ROUNDTRIP_FAIL")
sys.exit(0 if ok else 5)
