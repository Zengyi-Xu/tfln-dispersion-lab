# -*- coding: utf-8 -*-
"""V1: A3/A5/A6 TMM recheck + C2 verdict (swing linearity vs L).

Reuses the TMM core from simulations/02_tolerance_scan.py. For each
L in {1, 2.5, 5, 10, 20} mm the same (lam, R, tau) spectrum is reduced with
three extraction-window variants:
  (a) current: R>0.5 inside chirp range with 2x local-gap margins (as shipped)
  (b) R>0.9 plateau, longest contiguous segment
  (c) R>0.5 longest contiguous segment, then trim 2x local bandgap from its edges

A3 (phase error) is extended from 3 to 5 seeds as required by VERIFICATION_PLAN.md.

Output: results/verify/v1/v1_tolerance_recheck.json + v1_swing_windows.png
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "simulations"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tolscan", os.path.join(ROOT, "simulations", "02_tolerance_scan.py"))
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)

C0 = ts.C0
N_EFF = ts.N_EFF
KAPPA0 = ts.KAPPA0
C_NM_PER_MM = ts.C_NM_PER_MM

OUT = os.path.join(ROOT, "results", "verify", "v1")
os.makedirs(OUT, exist_ok=True)

lam_b0 = 1535e-9
GAP_NM = lam_b0**2 * KAPPA0 / (2 * np.pi * N_EFF) * 1e9  # local bandgap, nm


def window_masks(lam, R, chirp_nm):
    lam0 = lam_b0
    gap_m = GAP_NM * 1e-9
    base = (lam > lam0 + 2 * gap_m) & (lam < lam0 + (chirp_nm - 2 * GAP_NM) * 1e-9)
    mask_a = base & (R > 0.5)

    def longest_seg(mask):
        idx = np.where(mask)[0]
        if len(idx) == 0:
            return mask & False
        cuts = np.where(np.diff(idx) > 1)[0]
        segs = np.split(idx, cuts + 1)
        best = max(segs, key=len)
        out = np.zeros_like(mask)
        out[best] = True
        return out

    mask_b = longest_seg(R > 0.9)
    seg_c = longest_seg(R > 0.5)
    if seg_c.any():
        lo = lam[seg_c].min() + 2 * gap_m
        hi = lam[seg_c].max() - 2 * gap_m
        mask_c = seg_c & (lam >= lo) & (lam <= hi)
    else:
        mask_c = seg_c
    return {"a_R05": mask_a, "b_R09_seg": mask_b, "c_R05_seg_trim": mask_c}


def metrics(lam, R, tau, mask):
    if mask.sum() < 50:
        return None
    p = np.polyfit(lam[mask], tau[mask], 1)
    resid = tau[mask] - np.polyval(p, lam[mask])
    return {
        "D_ps_per_nm": float(p[0] * 1e12 / 1e9),
        "ripple_pp_ps": float((resid.max() - resid.min()) * 1e12),
        "swing_ps": float((tau[mask].max() - tau[mask].min()) * 1e12),
        "band_nm": float((lam[mask].max() - lam[mask].min()) * 1e9),
        "n_points": int(mask.sum()),
    }


report = {"local_gap_nm": float(GAP_NM), "n_eff": N_EFF, "kappa0": KAPPA0}

# ---------------- A5 with three windows ----------------
Ls_mm = [1.0, 2.5, 5.0, 10.0, 20.0]
a5 = {w: [] for w in ("a_R05", "b_R09_seg", "c_R05_seg_trim")}
a5_geo = []
for Lmm in Ls_mm:
    chirp = C_NM_PER_MM * Lmm
    lam, R, tau, m0 = ts.spectrum(lam_b0, Lmm * 1e-3, chirp, ts.kappa_uniform)
    masks = window_masks(lam, R, chirp)
    geo = 2 * N_EFF * Lmm * 1e-3 / C0 * 1e12
    a5_geo.append(geo)
    for name, mk in masks.items():
        m = metrics(lam, R, tau, mk)
        if m is None:
            m = {"D_ps_per_nm": float("nan"), "ripple_pp_ps": float("nan"),
                 "swing_ps": float("nan"), "band_nm": 0.0, "n_points": int(mk.sum()),
                 "swing_deviation_pct": float("nan")}
        m["swing_geo_ps"] = geo
        if m["n_points"] >= 50:
            m["swing_deviation_pct"] = 100 * (m["swing_ps"] / geo - 1)
        a5[name].append(m)
    print("L=%5.1f mm done (n_lam=%d)" % (Lmm, len(lam)), flush=True)

report["A5"] = {"L_mm": Ls_mm, "swing_geo_ps": a5_geo, "windows": a5}

# ---------------- A3 with 5 seeds ----------------
L_ref, chirp_ref = 2.5e-3, C_NM_PER_MM * 2.5
sigmas_nm = [0.0, 0.001, 0.003, 0.01, 0.03, 0.1]
a3 = []
for sig in sigmas_nm:
    rp = [ts.spectrum(lam_b0, L_ref, chirp_ref, ts.kappa_uniform,
                      sigma_lamb=sig * 1e-9, seed=s)[3]["ripple_pp"]
          for s in range(5)]
    a3.append({"sigma_nm": sig, "ripple_pp_mean": float(np.mean(rp)),
               "ripple_pp_std": float(np.std(rp)), "seeds": rp})
report["A3_sigma_scan_5seeds"] = a3

a3L = []
for Lmm in Ls_mm:
    rp = [ts.spectrum(lam_b0, Lmm * 1e-3, C_NM_PER_MM * Lmm, ts.kappa_uniform,
                      sigma_lamb=0.01e-9, seed=s)[3]["ripple_pp"]
          for s in range(5)]
    a3L.append({"L_mm": Lmm, "ripple_pp_mean": float(np.mean(rp)),
                "ripple_pp_std": float(np.std(rp))})
report["A3_ripple_vs_L_5seeds"] = a3L

# ---------------- A6 apodization ----------------
wins = [("uniform", ts.kappa_uniform), ("linear", ts.kappa_linear),
        ("gauss", ts.kappa_gauss), ("cosine", ts.kappa_cosine)]
a6 = []
for name, prof in wins:
    _, _, _, m = ts.spectrum(lam_b0, L_ref, chirp_ref, prof)
    a6.append({"window": name, "ripple_pp": m["ripple_pp"],
               "swing": m["swing"], "swing_geo": m["swing_geo"]})
report["A6"] = a6

# ---------------- A4 temperature ----------------
dlamb_per_K = lam_b0 * ts.DNDT / N_EFF * 1e9
D_ref = a5["a_R05"][1]["D_ps_per_nm"]
report["A4"] = {"dlamb_nm_per_K": float(dlamb_per_K),
                "tau_shift_ps_per_K": float(D_ref * dlamb_per_K)}
grad_rows = []
for grad in [0.01, 0.1, 1.0]:
    extra = lambda z, g=grad: dlamb_per_K * 1e-9 * (g * 1e3) * z
    _, _, _, m = ts.spectrum(lam_b0, L_ref, chirp_ref, ts.kappa_uniform,
                             extra_lamb_z=extra)
    grad_rows.append({"grad_K_per_mm": grad, "ripple_pp": m["ripple_pp"], "D": m["D"]})
report["A4_gradient"] = grad_rows

# ---------------- C2 verdict ----------------
dev = {name: [m["swing_deviation_pct"] for m in rows] for name, rows in a5.items()}
report["C2_verdict"] = {
    "swing_deviation_pct": dev,
    "L_mm": Ls_mm,
}
valid = {k: v[0] for k, v in dev.items() if not np.isnan(v[0])}
best = min(valid, key=lambda k: abs(valid[k])) if valid else None
report["C2_verdict"]["best_window_at_1mm"] = best
report["C2_verdict"]["dev_1mm_best_pct"] = valid[best] if best else None
report["C2_verdict"]["reword_needed"] = bool(abs(valid[best]) > 5) if best else True
dev5 = max(abs(v[2]) for v in dev.values())   # index 2 = 5 mm
dev10plus = max(max(abs(v[3]), abs(v[4])) for v in dev.values())
report["C2_verdict"]["max_abs_dev_5mm_pct"] = dev5
report["C2_verdict"]["max_abs_dev_10_20mm_pct"] = dev10plus

with open(os.path.join(OUT, "v1_tolerance_recheck.json"), "w") as fp:
    json.dump(report, fp, indent=2)

# ---------------- plot ----------------
fig, ax = plt.subplots(figsize=(7, 4.5))
for name, mk in [("a_R05", "s--"), ("b_R09_seg", "o-"), ("c_R05_seg_trim", "^-")]:
    ax.plot(Ls_mm, [m["swing_ps"] for m in a5[name]], mk, label=name)
ax.plot(Ls_mm, a5_geo, "k:", label="geometric 2n_gL/c")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("L (mm)")
ax.set_ylabel("delay swing (ps)")
ax.set_title("V1: swing vs L under three extraction windows")
ax.legend(fontsize=8)
ax.grid(alpha=0.3, which="both")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "v1_swing_windows.png"), dpi=150)

# ---------------- console ----------------
print("\nlocal bandgap = %.3f nm" % GAP_NM)
hdr = "L(mm)  geo(ps)"
for name in a5:
    hdr += " | %-22s" % name
print(hdr)
for i, Lmm in enumerate(Ls_mm):
    row = "%5.1f %8.1f" % (Lmm, a5_geo[i])
    for name in a5:
        m = a5[name][i]
        row += " | %7.1f ps (%+6.2f%%)" % (m["swing_ps"], m["swing_deviation_pct"])
    print(row)
print("\nD (ps/nm):")
for i, Lmm in enumerate(Ls_mm):
    print("  L=%5.1f: " % Lmm + "  ".join("%s=%.3f" % (n, a5[n][i]["D_ps_per_nm"]) for n in a5))
print("\nA3 5-seed ripple:", ["%.3g:%.2f±%.2f" % (r["sigma_nm"], r["ripple_pp_mean"], r["ripple_pp_std"]) for r in a3])
print("A3 vs L (σ=0.01nm):", ["%gmm:%.2f" % (r["L_mm"], r["ripple_pp_mean"]) for r in a3L])
print("A6:", [(r["window"], round(r["ripple_pp"], 3), round(r["swing"], 1)) for r in a6])
print("A4 tau_shift = %.4f ps/K; grad ripple:" % report["A4"]["tau_shift_ps_per_K"],
      [(g["grad_K_per_mm"], round(g["ripple_pp"], 3)) for g in grad_rows])
print("\nC2 verdict:", json.dumps(report["C2_verdict"], indent=2))
