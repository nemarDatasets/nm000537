import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import scipy.io
import scipy.ndimage
import scipy.signal

MAINS_HZ = (60, 180, 300, 420, 540)
# integer rates and TDT-style rates (x 1.01725)
CANDIDATES_HZ = (2000, 2034.5, 4000, 4069, 8000, 8138, 16000, 16276, 24000, 24414, 32000)
SHOWN_HZ = (2000, 8000, 16000)
PEAK_MIN = 5
ART_HALF = 128
ART_NFFT = 4096
ART_PROBES = (0.16, 0.24)  # cycles/sample
LOCK_HALF = 20  # samples around the centre
LOCK_RATIO = 10
FORMATS = {"fit SE (Hz)": "{:.2f}", "NaN trial x channel": "{:.3f}"} | {
    k: "{:.3f}" for k in ("roll-off (cycle/sample)", "roll-off min", "roll-off max")
}


def baseline_spectrum(x: np.ndarray, centre: int, clip: float) -> dict:
    n = x.shape[1]
    length = centre - max(n // 80, 160)
    base = np.moveaxis(x[:, :length], 1, -1).reshape(-1, length)  # shape: (trials*slots, L)
    ok = np.isfinite(base).all(1) & (np.abs(base).max(1) < 0.98 * clip)
    clean = base[ok]
    del base
    nfft = 1 << int(np.ceil(np.log2(8 * length)))
    win = np.hanning(length)
    psd = np.zeros(nfft // 2 + 1)
    for i in range(0, len(clean), 400):
        seg = scipy.signal.detrend(clean[i : i + 400], axis=1)
        psd += (np.abs(np.fft.rfft(seg * win, nfft, axis=1)) ** 2).sum(0)
    psd /= len(clean)
    binw = 1 / nfft
    bg = np.exp(scipy.ndimage.median_filter(np.log(psd), int(0.006 / binw) | 1, mode="nearest"))
    slope = np.gradient(scipy.ndimage.uniform_filter1d(np.log10(bg), int(0.01 / binw)), binw)
    freqs = np.fft.rfftfreq(nfft)
    band = (freqs > 0.03) & (freqs < 0.47)
    roll_off = float(freqs[band][np.argmin(slope[band])])
    return dict(psd=psd, ratio=psd / bg, binw=binw, lobe=int(round(2 / length / binw)), roll_off=roll_off)


def peak_near(spec: dict, f: float) -> tuple[float, int]:
    b = int(round(f / spec["binw"]))
    seg = spec["ratio"][b - spec["lobe"] : b + spec["lobe"] + 1]
    return float(seg.max()), b - spec["lobe"] + int(seg.argmax())


def mains(spec: dict) -> dict:
    comb = {fs: [peak_near(spec, f / fs)[0] for f in MAINS_HZ] for fs in CANDIDATES_HZ}
    score = {fs: float(np.median(r)) for fs, r in comb.items()}
    best, runner = sorted(score, key=score.get, reverse=True)[:2]
    y = np.log(spec["psd"])
    ks, ps, ws = [], [], []
    for k in range(1, int(min(0.45 * best, 2000) // 60) + 1):
        height, b = peak_near(spec, k * 60 / best)
        if height < PEAK_MIN:
            continue
        d = 0.5 * (y[b - 1] - y[b + 1]) / (y[b - 1] - 2 * y[b] + y[b + 1])
        ks.append(k)
        ps.append((b + d) * spec["binw"])
        ws.append(np.log10(height))
    ks, ps, ws = map(np.asarray, (ks, ps, ws))
    c0 = (ws * ks * ps).sum() / (ws * ks**2).sum()
    se = np.sqrt((ws * (ps - ks * c0) ** 2).sum() / max(len(ks) - 1, 1) / (ws * ks**2).sum())
    present = [k for k in range(1, int(0.49 * best // 60) + 1) if peak_near(spec, k * 60 / best)[0] >= PEAK_MIN]
    return {
        **{f"comb median @{fs // 1000} kHz": score[fs] for fs in SHOWN_HZ},
        "best rate (Hz)": best,
        "runner-up (Hz, score)": f"{runner:g} ({score[runner]:.1f})",
        "comb @best 60/180/300/420/540": "/".join(f"{v:.1f}" for v in comb[best]),
        "fit (Hz)": 60 / c0,
        "fit SE (Hz)": 60 / c0**2 * se,
        "harmonics fitted": len(ks),
        "highest harmonic (Hz)": 60 * max(present),
        "odd/even harmonics present": f"{sum(k % 2 for k in present)}/{sum(1 - k % 2 for k in present)}",
        "roll-off (cycle/sample)": spec["roll_off"],
    }


def artefact_spectrum(x: np.ndarray, centre: int, clip: float) -> dict:
    w = ART_HALF
    seg = x[:, centre - 4 * w : centre + 4 * w + 1]  # shape: (trials, 8w+1, slots)
    seg = seg - np.nanmedian(seg[:, : 2 * w], axis=1, keepdims=True)
    core = seg[:, 4 * w - 8 : 4 * w + 9]
    sign = np.where(np.arange(len(x)) % 2 == 0, 1.0, -1.0)
    for _ in range(5):
        ref = np.nanmean(sign[:, None, None] * core, axis=0)
        sign = np.where(np.nansum(core * ref[None], axis=(1, 2)) >= 0, 1.0, -1.0)
    alt = np.nanmean(sign[:, None, None] * seg, axis=0)  # shape: (8w+1, slots)
    clipped = (np.abs(seg) >= 0.98 * clip).any(axis=(0, 1))
    noise = np.nanstd(alt[: 2 * w], axis=0)
    peak = np.nanmax(np.abs(alt[4 * w - 8 : 4 * w + 9]), axis=0)
    good = ~clipped & np.isfinite(alt).all(0) & (peak > 20 * noise)
    out = {"artefact channels": int(good.sum()), "artefact drop 0.16->0.24 (dB)": np.nan}
    if good.any():
        a = alt[3 * w : 5 * w + 1, good] * np.hanning(2 * w + 1)[:, None]
        spec = np.abs(np.fft.rfft(a, ART_NFFT, axis=0)) ** 2
        f = np.fft.rfftfreq(ART_NFFT)
        spec = np.median(spec / spec[(f > 0.005) & (f < 0.24)].sum(0), axis=1)
        lo, hi = (spec[np.argmin(np.abs(f - p))] for p in ART_PROBES)
        out["artefact drop 0.16->0.24 (dB)"] = float(10 * np.log10(lo / hi))
    return out


def lock(x: np.ndarray, centre: int, finite: np.ndarray) -> dict:
    ratios, sharpest_near = [], 0
    for t in range(len(x)):
        if not finite[t].any():
            continue
        d = np.abs(np.diff(x[t][:, finite[t]], axis=0))[:-1]  # last diff: into the padding sample
        prof = np.median(d, axis=1)
        win = prof[centre - LOCK_HALF - 1 : centre + LOCK_HALF]  # jumps ending at centre-20..centre+20
        ratios.append(float(win.max() / np.median(prof)))
        sharpest_near += abs(int(prof.argmax()) + 1 - centre) <= LOCK_HALF
    return {
        "epochs with artefact at centre": f"{sum(r >= LOCK_RATIO for r in ratios)}/{len(x)}",
        "epochs with sharpest jump at centre": f"{sharpest_near}/{len(x)}",
        "centre ratio median": float(np.median(ratios)),
    }


def zero_count(v: np.ndarray) -> str:
    v = v[np.isfinite(v)]
    return f"{int((v == 0).sum())}/{v.size}"


def annex_sha256(path: Path) -> str:
    head = path.read_bytes()[:200] if path.stat().st_size < 1024 else b""
    if head.startswith(b"/annex/objects/SHA256E-"):
        return head.decode().split("--")[1].split(".")[0]
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bids(root: Path, sub: str, run: str, n: int, n_tr: int, n_keep: int, eeg_sha: str) -> dict:
    stem = root / f"sub-{sub}" / "ieeg" / f"sub-{sub}_task-amygdalastim_run-{int(run)}"
    side = json.loads(Path(f"{stem}_ieeg.json").read_text())
    fs = side["SamplingFrequency"]
    ch = pd.read_csv(f"{stem}_channels.tsv", sep="\t")
    ev = pd.read_csv(f"{stem}_events.tsv", sep="\t")
    offset = ev["sample"].to_numpy() - np.arange(len(ev)) * n
    consistent = (
        len(ch) == n_keep
        and ch["sampling_frequency"].unique().tolist() == [fs]
        and abs(side["EpochLength"] - n / fs) < 1e-9
        and abs(side["RecordingDuration"] - n_tr * n / fs) < 1e-9
        and len(ev) == n_tr
        and len(set(offset)) == 1
        and np.abs(ev["onset"].to_numpy() - ev["sample"].to_numpy() / fs).max() < 1e-9
    )
    return {
        "BIDS SamplingFrequency": fs,
        "BIDS fields consistent": "yes" if consistent else "NO",
        "eeg = annex key": "yes" if annex_sha256(Path(f"{stem}_ieeg.eeg")) == eeg_sha else "NO",
    }


def measure(mat: Path, root: Path) -> dict:
    sub, run = mat.parent.parent.name, mat.parent.name
    x = scipy.io.loadmat(mat)["EP_data3D"]  # shape: (trials, samples, slots)
    n_tr, n, _ = x.shape
    centre = (n - 1) // 2
    clip = float(np.nanmax(np.abs(x)))
    keep = np.isfinite(x).any(axis=(0, 1))
    finite = np.isfinite(x).all(1)  # shape: (trials, slots)
    eeg = np.ascontiguousarray(x[:, :, keep].reshape(n_tr * n, int(keep.sum())).astype("<f4"))
    eeg_sha = hashlib.sha256(eeg.tobytes()).hexdigest()
    del eeg
    n_ch = finite.sum(1)
    few = [t + 1 for t in range(n_tr) if n_ch[t] <= 5]
    return {
        "run": f"{sub}/{run}",
        "epochs": n_tr,
        "samples/epoch": n,
        "channels": int(keep.sum()),
        "channels per epoch min/median/max": f"{n_ch.min()}/{np.median(n_ch):g}/{n_ch.max()}",
        "NaN trial x channel": float(1 - finite[:, keep].mean()),
        "epochs with <= 5 channels": ",".join(map(str, few)) if few else "-",
        "last sample = 0": zero_count(x[:, -1]),
        "second-to-last = 0": zero_count(x[:, -2]),
        **mains(baseline_spectrum(x, centre, clip)),
        **artefact_spectrum(x, centre, clip),
        **lock(x, centre, finite),
        **bids(root, sub, run, n, n_tr, int(keep.sum()), eeg_sha),
        "_sha256": hashlib.sha256(mat.read_bytes()).hexdigest(),
    }


def markdown(df: pd.DataFrame) -> str:
    def cell(col: str, v: object) -> str:
        if isinstance(v, float):
            return "n/a" if np.isnan(v) else FORMATS.get(col, "{:.1f}").format(v)
        return str(v)

    rows = [[cell(c, v) for c, v in zip(df.columns, r)] for r in df.itertuples(index=False)]
    lines = ["| " + " | ".join(r) + " |" for r in [list(df.columns), *rows]]
    lines.insert(1, "|" + "|".join("---" for _ in df.columns) + "|")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path, help="OSF dngv5 release root (<PT>/<run>/EPdata3D.mat)")
    parser.add_argument("bids", type=Path, help="nm000537 checkout")
    args = parser.parse_args()
    mats = sorted(args.release.glob("*/*/EPdata3D.mat"), key=lambda p: (int(p.parent.parent.name), int(p.parent.name)))
    n_bids = len(list(args.bids.glob("sub-*/ieeg/*_ieeg.json")))
    assert len(mats) == n_bids, f"{len(mats)} EPdata3D.mat in the release, {n_bids} runs in BIDS"
    print(f"numpy {np.__version__}, scipy {scipy.__version__}, pandas {pd.__version__}; {len(mats)} runs")
    rows = []
    for mat in mats:
        rows.append(measure(mat, args.bids))
        print(json.dumps(rows[-1], default=str), flush=True)
    df = pd.DataFrame(rows)
    rate = ["run", "epochs", "samples/epoch", "comb median @2 kHz", "comb median @8 kHz", "comb median @16 kHz",
            "best rate (Hz)", "runner-up (Hz, score)", "comb @best 60/180/300/420/540", "fit (Hz)", "fit SE (Hz)",
            "harmonics fitted", "highest harmonic (Hz)", "odd/even harmonics present", "roll-off (cycle/sample)",
            "BIDS SamplingFrequency",
            "BIDS fields consistent"]
    other = ["run", "best rate (Hz)", "artefact channels", "artefact drop 0.16->0.24 (dB)",
             "epochs with artefact at centre", "epochs with sharpest jump at centre", "centre ratio median",
             "channels", "channels per epoch min/median/max", "NaN trial x channel", "epochs with <= 5 channels",
             "last sample = 0", "second-to-last = 0", "eeg = annex key"]
    print("\n## rate\n\n" + markdown(df[rate]))
    print("\n## artefact, lock, padding\n\n" + markdown(df[other]))
    by_rate = df.groupby("best rate (Hz)")
    summary = pd.DataFrame({
        "runs": by_rate.size(),
        "BIDS rate = measured": by_rate.apply(lambda g: int((g["BIDS SamplingFrequency"] == g.name).sum())),
        "fit min (Hz)": by_rate["fit (Hz)"].min(),
        "fit max (Hz)": by_rate["fit (Hz)"].max(),
        "drop min (dB)": by_rate["artefact drop 0.16->0.24 (dB)"].min(),
        "drop max (dB)": by_rate["artefact drop 0.16->0.24 (dB)"].max(),
        "roll-off min": by_rate["roll-off (cycle/sample)"].min(),
        "roll-off max": by_rate["roll-off (cycle/sample)"].max(),
    }).reset_index()
    print("\n## by measured rate\n\n" + markdown(summary))
    print("\n## sha256 of the release files\n")
    print("\n".join(f"{r['_sha256']}  {r['run']}/EPdata3D.mat" for r in rows))


if __name__ == "__main__":
    main()
