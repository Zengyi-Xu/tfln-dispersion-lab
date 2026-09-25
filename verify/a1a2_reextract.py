# -*- coding: utf-8 -*-
"""V2: A1/A2 bandgap re-extraction — longest contiguous T<0.5 segment.

Reads lumerical/results/{w*,dnf*,dn010,dn040}_raw.npz and extracts, for each run:
  - band edges = interpolated T=0.5 crossings at both ends of the longest
    contiguous T<0.5 segment
  - lambda_B two ways: (a) wavelength of min T inside the segment (old-style,
    unstable because T sits on the ~1e-3 monitor floor across ~18 nm),
    (b) midpoint of the two band edges (robust)
  - kappa = gap * pi * n_g / lambda_B^2

Compares against the old band_center (parabola around argmin) values stored in
lumerical/results/tolerance_fdtd.npz, fits d lambda_B/dw with R^2, applies the
outlier criteria from VERIFICATION_PLAN.md (residual > 3 sigma or non-monotonic).

Output: results/verify/v2/v2_a1a2_reextract.json + v2_lambdaB_w.png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

C0 = 299792458.0
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "lumerical", "results")
OUT = os.path.join(ROOT, "results", "verify", "v2")
os.makedirs(OUT, exist_ok=True)

ref = np.load(os.path.join(RES, "ref_raw.npz"))
L_uni = 200 * 387.5e-9  # N_per * Lambda0, run_scan_2d.py
N_G = float(C0 * np.mean(ref["tau"]) / (L_uni + 4e-6))


def load(tag):
    d = np.load(os.path.join(RES, "%s_raw.npz" % tag))
    wl = C0 / d["f"]
    T = d["T"]
    o = np.argsort(wl)
    return wl[o], T[o]


def band_center_old(wl, T):
    """verbatim port of run_tolerance_fdtd.py:band_center"""
    ic = np.argmin(T)
    i0, i1 = max(ic - 2, 0), min(ic + 3, len(wl))
    p = np.polyfit(wl[i0:i1], T[i0:i1], 2)
    lam_min = -p[1] / (2 * p[0])

    def cross(i, j):
        return wl[i] + (0.5 - T[i]) * (wl[j] - wl[i]) / (T[j] - T[i])

    i1 = ic
    while i1 > 0 and T[i1] < 0.5:
        i1 -= 1
    i2 = ic
    while i2 < len(T) - 1 and T[i2] < 0.5:
        i2 += 1
    gap = cross(i2, i2 + 1) - cross(i1 - 1, i1)
    return lam_min, gap


def longest_segment(wl, T, thr=0.5):
    """longest contiguous T<thr segment; edges via linear T=thr interpolation."""
    below = T < thr
    segs = []
    i = 0
    while i < len(T):
        if below[i]:
            j = i
            while j < len(T) and below[j]:
                j += 1
            segs.append((i, j))  # [i, j) all below
            i = j
        else:
            i += 1
    if not segs:
        return None
    i, j = max(segs, key=lambda s: wl[s[1] - 1] - wl[s[0]])

    def cross_down(k):  # T[k-1] >= thr > T[k]
        return wl[k - 1] + (thr - T[k - 1]) * (wl[k] - wl[k - 1]) / (T[k] - T[k - 1])

    def cross_up(k):  # T[k] < thr <= T[k+1]... interpolate between j-1 and j
        return wl[k] + (thr - T[k]) * (wl[k + 1] - wl[k]) / (T[k + 1] - T[k])

    lo = cross_down(i)
    hi = cross_up(j - 1)
    lam_minT = float(wl[i + np.argmin(T[i:j])])
    lam_mid = 0.5 * (lo + hi)
    return {
        "edge_lo_nm": float(lo * 1e9),
        "edge_hi_nm": float(hi * 1e9),
        "gap_nm": float((hi - lo) * 1e9),
        "lambdaB_minT_nm": lam_minT * 1e9,
        "lambdaB_mid_nm": float(lam_mid * 1e9),
        "n_segments": len(segs),
        "n_points_in_segment": int(j - i),
    }


def kappa_per_cm(gap_nm, lamB_nm):
    gap = gap_nm * 1e-9
    lam = lamB_nm * 1e-9
    return float(gap * np.pi * N_G / lam**2 / 100.0)


def extract(tag):
    wl, T = load(tag)
    old_lam, old_gap = band_center_old(wl, T)
    new = longest_segment(wl, T)
    row = {
        "tag": tag,
        "old": {"lambdaB_nm": float(old_lam * 1e9), "gap_nm": float(old_gap * 1e9),
                "kappa_per_cm": kappa_per_cm(old_gap * 1e9, old_lam * 1e9)},
        "new": new,
    }
    row["new"]["kappa_per_cm"] = kappa_per_cm(new["gap_nm"], new["lambdaB_mid_nm"])
    return row


def linfit(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    p = np.polyfit(x, y, 1)
    yhat = np.polyval(p, x)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot
    resid = y - yhat
    return p, r2, resid


report = {"n_g": N_G, "runs": {}}

# ---------------- A1: width sweep (dn=0.02) ----------------
ws_nm = [1470, 1480, 1500, 1520, 1530]
for wnm in ws_nm:
    report["runs"]["w%d" % wnm] = extract("w%d" % wnm)

lamB_mid = [report["runs"]["w%d" % w]["new"]["lambdaB_mid_nm"] for w in ws_nm]
lamB_minT = [report["runs"]["w%d" % w]["new"]["lambdaB_minT_nm"] for w in ws_nm]
lamB_old = [report["runs"]["w%d" % w]["old"]["lambdaB_nm"] for w in ws_nm]

fits = {}
for name, vals in [("mid", lamB_mid), ("minT", lamB_minT), ("old", lamB_old)]:
    p, r2, resid = linfit(ws_nm, vals)
    sigma = float(np.std(resid, ddof=2)) if len(vals) > 2 else 0.0
    outliers = [int(w) for w, r in zip(ws_nm, resid) if sigma > 0 and abs(r) > 3 * sigma]
    monotonic = bool(np.all(np.diff(vals) > 0))
    fits[name] = {
        "slope_nm_per_nm": float(p[0]),
        "slope_nm_per_um": float(p[0] * 1000.0),
        "intercept_nm": float(p[1]),
        "R2": float(r2),
        "residuals_nm": [float(r) for r in resid],
        "resid_sigma_nm": sigma,
        "outliers_3sigma": outliers,
        "monotonic_increasing": monotonic,
    }
report["A1_fits"] = fits

# dn_bar/dw conversion used in run_tolerance_fdtd.py: dλB/dw / (2*Lambda0)
Lambda0 = 387.5e-9
report["A1_dnbar_dw_per_um"] = {
    name: f["slope_nm_per_um"] * 1e-9 / (2 * Lambda0) / 1e-6 for name, f in fits.items()
}

# ---------------- A2: dn sweep (w=1500 nm) ----------------
dn_tags = [(0.010, "dn010"), (0.018, "dnf018"), (0.020, "w1500"),
           (0.022, "dnf022"), (0.040, "dn040")]
for dn, tag in dn_tags:
    if tag not in report["runs"]:
        report["runs"][tag] = extract(tag)

k_dn = [report["runs"][t]["new"]["kappa_per_cm"] for _, t in dn_tags]
lamB_dn = [report["runs"][t]["new"]["lambdaB_mid_nm"] for _, t in dn_tags]
dns = [d for d, _ in dn_tags]
p, r2, resid = linfit(dns, k_dn)
sigma = float(np.std(resid, ddof=2))
report["A2_kappa_vs_dn"] = {
    "dn": dns,
    "kappa_per_cm": k_dn,
    "lambdaB_mid_nm": lamB_dn,
    "linear_fit_slope_per_cm": float(p[0]),
    "linear_fit_intercept_per_cm": float(p[1]),
    "R2": float(r2),
    "residuals_per_cm": [float(r) for r in resid],
    "max_rel_deviation": float(np.max(np.abs(resid) / np.abs(np.polyval(p, dns)))),
    "lambdaB_drift_dn_pm10pct_nm": float(max(lamB_dn[1], lamB_dn[3]) - min(lamB_dn[1], lamB_dn[3])),
}

# ---------------- verdicts ----------------
f = fits["mid"]
report["verdict"] = {
    "dlamB_dw_nm_per_um": f["slope_nm_per_um"],
    "R2": f["R2"],
    "claim_46nm_per_um_holds": bool(abs(f["slope_nm_per_um"] - 46.0) < 3.0 and f["R2"] > 0.99),
    "kappa_w1470_per_cm": report["runs"]["w1470"]["new"]["kappa_per_cm"],
    "claim_kappa594_holds": bool(abs(report["runs"]["w1470"]["new"]["kappa_per_cm"] - 594) < 30),
}

with open(os.path.join(OUT, "v2_a1a2_reextract.json"), "w") as fp:
    json.dump(report, fp, indent=2)

# ---------------- plot ----------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
ax = axes[0]
ax.plot(ws_nm, lamB_old, "s--", label="old band_center (npz)", color="gray")
ax.plot(ws_nm, lamB_minT, "o:", label="new: min-T center", color="tab:orange")
ax.plot(ws_nm, lamB_mid, "o-", label="new: edge midpoint", color="tab:blue")
xs = np.linspace(1465, 1535, 50)
ax.plot(xs, np.polyval(np.polyfit(ws_nm, lamB_mid, 1), xs), "-", color="tab:blue", alpha=0.4,
        label="fit: %.1f nm/µm, R²=%.4f" % (f["slope_nm_per_um"], f["R2"]))
ax.set_xlabel("width w (nm)")
ax.set_ylabel("λ_B (nm)")
ax.legend(fontsize=8)
ax.set_title("A1: λ_B(w)")
ax = axes[1]
ax.plot(dns, k_dn, "o-", color="tab:blue", label="κ(dn), new extraction")
ax.plot(dns, np.polyval(np.polyfit(dns, k_dn, 1), dns), "--", color="gray",
        label="linear fit, R²=%.4f" % report["A2_kappa_vs_dn"]["R2"])
ax.set_xlabel("dn")
ax.set_ylabel("κ (/cm)")
ax.legend(fontsize=8)
ax.set_title("A2: κ(dn)")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "v2_lambdaB_w.png"), dpi=150)

# ---------------- console summary ----------------
print("n_g = %.6f" % N_G)
print("\n%-8s %-22s %-22s %-22s" % ("tag", "old λB/gap/κ", "new minT λB", "new mid λB/gap/κ"))
for tag in ["w%d" % w for w in ws_nm] + [t for _, t in dn_tags if t != "w1500"]:
    r = report["runs"][tag]
    print("%-8s %8.2f %6.2f %6.0f | %8.2f | %8.2f %6.2f %6.0f" % (
        tag,
        r["old"]["lambdaB_nm"], r["old"]["gap_nm"], r["old"]["kappa_per_cm"],
        r["new"]["lambdaB_minT_nm"],
        r["new"]["lambdaB_mid_nm"], r["new"]["gap_nm"], r["new"]["kappa_per_cm"]))
print("\nA1 fits (dλB/dw):")
for name, ff in fits.items():
    print("  %-4s slope=%6.2f nm/µm  R²=%.5f  outliers=%s  monotonic=%s" % (
        name, ff["slope_nm_per_um"], ff["R2"], ff["outliers_3sigma"], ff["monotonic_increasing"]))
print("\nA2 κ(dn):", ["%d" % k for k in k_dn], " R²=%.4f max rel dev=%.1f%%"
      % (report["A2_kappa_vs_dn"]["R2"], 100 * report["A2_kappa_vs_dn"]["max_rel_deviation"]))
print("A2 λB drift dn±10%%: %.3f nm" % report["A2_kappa_vs_dn"]["lambdaB_drift_dn_pm10pct_nm"])
print("\nverdict:", json.dumps(report["verdict"], indent=2))
