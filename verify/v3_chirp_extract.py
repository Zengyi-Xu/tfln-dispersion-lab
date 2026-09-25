# -*- coding: utf-8 -*-
"""V3: A2b chirped-grating extraction robustness.

For chirpdf018/022_raw.npz (dn=0.018/0.022) and the dn=0.020 baseline
(chirp_raw.npz), extract dispersion D (ps/nm) and ripple_pp (ps) from tau_r(λ)
using R thresholds {0.5, 0.7, 0.8, 0.9, 0.95} crossed with
{all points above threshold, longest contiguous segment}.

Checks:
  - spread of D across thresholds for each method (is R>0.9 the robust choice?)
  - ripple_pp ratio dn=0.022 vs 0.020 (claim: +24%) and dn=0.018 vs 0.020

Output: results/verify/v3/v3_chirp_extract.json
"""
import json
import os

import numpy as np

C0 = 299792458.0
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "lumerical", "results")
OUT = os.path.join(ROOT, "results", "verify", "v3")
os.makedirs(OUT, exist_ok=True)

THRESHOLDS = [0.5, 0.7, 0.8, 0.9, 0.95]
TAGS = {"0.018": "chirpdf018_raw", "0.020": "chirp_raw", "0.022": "chirpdf022_raw"}


def load(tag):
    d = np.load(os.path.join(RES, "%s.npz" % tag))
    wl = C0 / d["f"]
    R = 1.0 - d["T"]  # 'T' in chirp raw files is transmission; R = 1 - T
    tau = d["tau_r"]
    o = np.argsort(wl)
    return wl[o], R[o], tau[o]


def longest_seg(mask):
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return mask & False
    cuts = np.where(np.diff(idx) > 1)[0]
    best = max(np.split(idx, cuts + 1), key=len)
    out = np.zeros_like(mask)
    out[best] = True
    return out


def extract(wl, tau, mask):
    if mask.sum() < 10:
        return None
    p = np.polyfit(wl[mask] * 1e9, tau[mask] * 1e12, 1)  # ps vs nm
    resid = tau[mask] * 1e12 - np.polyval(p, wl[mask] * 1e9)
    return {
        "D_ps_per_nm": float(p[0]),
        "ripple_pp_ps": float(resid.max() - resid.min()),
        "band_nm": float((wl[mask].max() - wl[mask].min()) * 1e9),
        "n_points": int(mask.sum()),
    }


report = {}
for dn, tag in TAGS.items():
    wl, R, tau = load(tag)
    rows = {}
    for thr in THRESHOLDS:
        m_all = R > thr
        m_seg = longest_seg(m_all)
        rows[str(thr)] = {
            "all": extract(wl, tau, m_all),
            "longest_seg": extract(wl, tau, m_seg),
        }
    Ds_all = [r["all"]["D_ps_per_nm"] for r in rows.values() if r["all"]]
    Ds_seg = [r["longest_seg"]["D_ps_per_nm"] for r in rows.values() if r["longest_seg"]]
    report[dn] = {
        "by_threshold": rows,
        "D_std_all": float(np.std(Ds_all)),
        "D_std_longest_seg": float(np.std(Ds_seg)),
        "D_range_all": [float(min(Ds_all)), float(max(Ds_all))],
        "D_range_longest_seg": [float(min(Ds_seg)), float(max(Ds_seg))],
    }

# ripple ratios at the robust setting (R>0.9, longest seg)
def robust(dn, key):
    return report[dn]["by_threshold"]["0.9"]["longest_seg"][key]

report["verdict"] = {
    "D_at_R09_seg": {dn: robust(dn, "D_ps_per_nm") for dn in TAGS},
    "ripple_at_R09_seg": {dn: robust(dn, "ripple_pp_ps") for dn in TAGS},
    "ripple_ratio_022_vs_020": robust("0.022", "ripple_pp_ps") / robust("0.020", "ripple_pp_ps"),
    "ripple_ratio_018_vs_020": robust("0.018", "ripple_pp_ps") / robust("0.020", "ripple_pp_ps"),
}

with open(os.path.join(OUT, "v3_chirp_extract.json"), "w") as fp:
    json.dump(report, fp, indent=2)

for dn in TAGS:
    print("dn=%s  D_std: all=%.4f  seg=%.4f  D_range(all)=%s  D_range(seg)=%s" % (
        dn, report[dn]["D_std_all"], report[dn]["D_std_longest_seg"],
        ["%.3f" % v for v in report[dn]["D_range_all"]],
        ["%.3f" % v for v in report[dn]["D_range_longest_seg"]]))
    for thr in THRESHOLDS:
        r = report[dn]["by_threshold"][str(thr)]
        a, s = r["all"], r["longest_seg"]
        fa = "D=%.4f rip=%.2f band=%.0fnm n=%d" % (a["D_ps_per_nm"], a["ripple_pp_ps"], a["band_nm"], a["n_points"]) if a else "n/a"
        fs = "D=%.4f rip=%.2f band=%.0fnm n=%d" % (s["D_ps_per_nm"], s["ripple_pp_ps"], s["band_nm"], s["n_points"]) if s else "n/a"
        print("   thr=%.2f  all: %-38s seg: %s" % (thr, fa, fs))
print("\nverdict:", json.dumps(report["verdict"], indent=2))
