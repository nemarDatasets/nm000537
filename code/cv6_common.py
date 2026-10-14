"""convert_20261014 slice 6 shared helpers (inside Voyager Jobs). Re-exports o5c_B_common helpers but with the brief's
layout: work/<cid>/bids (BIDS tree) and work/<cid>/reports (private reports, pseudonym maps)."""
import json, os, shutil, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import o5c_B_common as _B
from o5c_B_common import (wtsv, wjson, wjson_any, sha256_file, add_electrodes_na, write_channels, channels_rows, count_types,
                          ieeg_sidecar, bidsignore, CH_COLS, flag)  # noqa: F401
from b3w3_common import write_vhdr, scrub_mat_header  # noqa: F401
wjson = wjson_any  # numpy-safe JSON writer for every sidecar

R = os.environ.get("R", "/voyager/ceph/groups/sdp190/bpinto/ieeg-nemar-20261005")
OPEN500 = os.path.join(R, "work", "open500")


def src_dir(cid):
    return os.path.join(OPEN500, cid)


def out_dir(cid):
    return os.path.join(R, "work", cid, "bids")


def rep_dir(cid):
    d = os.path.join(R, "work", cid, "reports"); os.makedirs(d, exist_ok=True); return d


def fresh_out(cid):
    o = out_dir(cid)
    if os.path.exists(os.path.join(o, ".nemar", "config.json")):
        raise SystemExit(f"REFUSE: {o} already has .nemar (uploaded tree)")
    if os.path.isdir(o):
        shutil.rmtree(o)
    os.makedirs(o)
    return o


def report(cid, obj):
    p = os.path.join(rep_dir(cid), "conversion_report.json")
    wjson_any(p, obj)
    o = out_dir(cid)
    if os.path.isdir(o):
        wjson_any(os.path.join(o, "code", "conversion_report.json"), obj)
    return p


def copy_code(cid, files):
    cd = os.path.join(out_dir(cid), "code"); os.makedirs(cd, exist_ok=True)
    for f in files:
        shutil.copyfile(os.path.join(HERE, f), os.path.join(cd, f))


def dataset_description(name, authors, license_, url, refs, how_to_ack, generated_by, doi=None, dataset_type="raw", keywords=None, ethics=None, funding=None, extra=None):
    sd = {"URL": url}
    if doi:
        sd["DOI"] = doi if doi.startswith("doi:") else f"doi:{doi}"
    d = {"Name": name, "BIDSVersion": "1.10.0", "DatasetType": dataset_type, "License": license_, "Authors": authors,
         "HowToAcknowledge": how_to_ack, "ReferencesAndLinks": refs, "SourceDatasets": [sd], "GeneratedBy": generated_by}
    if ethics:
        d["EthicsApprovals"] = ethics
    if funding:
        d["Funding"] = funding
    if keywords:
        d["Keywords"] = keywords
    if extra:
        d.update(extra)
    return d


def write_bv(base, data_tc, sfreq, names, units, fmt, resolutions, comment, markers=None):
    """data_tc: (n_times, n_ch) array already in the on-disk dtype (int16 / int32 / float32). Writes .eeg/.vhdr/.vmrk."""
    os.makedirs(os.path.dirname(base), exist_ok=True)
    dt = {"INT_16": "<i2", "INT_32": "<i4", "IEEE_FLOAT_32": "<f4"}[fmt]
    np.ascontiguousarray(data_tc.astype(dt, copy=False)).tofile(base + ".eeg")
    write_vhdr(base, len(names), sfreq, names, units, fmt=fmt, resolutions=resolutions, comment=comment, markers=markers)


def osf_meta(node):
    """OSF node title/licence/contributors from the public API (inside the Job); returns dict (errors recorded)."""
    import urllib.request
    out = {"node": node}
    try:
        a = json.load(urllib.request.urlopen(f"https://api.osf.io/v2/nodes/{node}/?embed=license", timeout=60))["data"]
        out["title"] = a["attributes"]["title"]; out["description"] = a["attributes"].get("description")
        lic = a.get("embeds", {}).get("license", {}).get("data")
        out["license_name"] = lic["attributes"]["name"] if lic else None
        out["node_license"] = a["attributes"].get("node_license")
        c = json.load(urllib.request.urlopen(f"https://api.osf.io/v2/nodes/{node}/contributors/?page%5Bsize%5D=50&embed=users", timeout=60))
        out["contributors"] = [x["embeds"]["users"]["data"]["attributes"]["full_name"] for x in c["data"] if x["attributes"]["bibliographic"] and "data" in x["embeds"]["users"]]
    except Exception as e:
        out["error"] = repr(e)
    return out
