# -*- coding: utf-8 -*-
"""L1 分析：细网格 + 宽窗口重跑后的 dλB/dw 与 κ 验收（防幻觉核查，2026-09-25）。

提取口径与 V2 完全一致（直接 import verify/v2_reextract_a1a2 的函数）：
λB = 最长 T<0.5 连续段的带边中点（midgap）；κ = gap·π·n_g/λB²。
禁止谷底 argmin（平底带 ±1.5nm 伪差）。

对照基准（双机已复核，CROSSCHECK §1）：
  n_g = 2.10457；midgap 斜率 40.65±0.53 nm/µm；κ(w1470..1530) = 607/607/606/608/607 /cm
验收：新斜率落在 40.65±0.53 区间（[40.12, 41.18]），κ 落在 606–608 ±3。

运行：python verify/l1_analyze.py（CPU，读 results/verify/l1/*_fine_raw.npz）
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "l1")
RES = os.path.join(ROOT, "lumerical", "results")
sys.path.insert(0, HERE)
from v2_reextract_a1a2 import longest_seg, kappa, fit_line, L_UNI  # noqa: E402

C0 = 299792458.0

# 双机复核基准（results/verify/v2/v2_a1a2_reextract.json，不改动）
BENCH = {
    "n_g": 2.10457,
    "slope_midgap_nm_per_um": 40.65, "slope_err": 0.53,
    "kappa_w1470_1530_per_cm": [607, 607, 606, 608, 607],
    "lamB_midgap_nm": [1566.608, 1567.071, 1567.901, 1568.679, 1569.059],
}
WS_NM = [1470, 1480, 1500, 1520, 1530]


def load_raw(path):
    d = np.load(path)
    wl = C0 / d["f"]
    o = np.argsort(wl)
    return wl[o], d["T"][o]


def extract(tag, n_g):
    wl, T = load_raw(os.path.join(OUT, "%s_raw.npz" % tag))
    lam_pt, lam_pq, gap, info = longest_seg(wl, T, thr=0.5)
    return {"tag": tag, "wl": wl, "T": T,
            "lamB_pt_nm": lam_pt * 1e9, "lamB_parab_nm": lam_pq * 1e9,
            "gap_nm": gap * 1e9, "midgap_nm": info["midgap_nm"],
            "kappa_per_cm": kappa(gap, lam_pt, n_g) / 100,
            "seg_min_T": info["seg_min_T"], "n_runs": info["n_runs"]}


def main():
    # n_g：细网格参考波导重算；与旧 ref_raw 口径对照
    ref = np.load(os.path.join(OUT, "ref_fine_raw.npz"))
    n_g_fine = C0 * float(np.mean(ref["tau"])) / (L_UNI + 4e-6)
    ref_old = np.load(os.path.join(RES, "ref_raw.npz"))
    n_g_old = C0 * float(np.mean(ref_old["tau"])) / (L_UNI + 4e-6)
    print("n_g: fine = %.6f, old = %.6f (bench 2.10457), diff = %.4f%%"
          % (n_g_fine, n_g_old, 100 * (n_g_fine / n_g_old - 1)))

    recs = {}
    for wnm in (1470, 1520):
        r = extract("w%d_fine" % wnm, n_g_fine)
        r["kappa_per_cm_old_ng"] = r["kappa_per_cm"] * n_g_old / n_g_fine
        recs[wnm] = r
        print("w%d_fine: midgap λB=%.3f nm (bench %.3f), gap=%.3f nm, κ=%.1f/cm "
              "(old_ng %.1f), minT=%.3f, runs=%d"
              % (wnm, r["midgap_nm"], BENCH["lamB_midgap_nm"][WS_NM.index(wnm)],
                 r["gap_nm"], r["kappa_per_cm"], r["kappa_per_cm_old_ng"],
                 r["seg_min_T"], r["n_runs"]))

    # --- dλB/dw：两端点斜率（纯细网格）---
    lam1470, lam1520 = recs[1470]["midgap_nm"], recs[1520]["midgap_nm"]
    slope_2pt = (lam1520 - lam1470) / 0.05   # nm per um
    # --- 混合 5 点拟合：新 w1470/w1520 + 旧 w1480/1500/1530 midgap（V2 JSON 值）---
    lam_mix = np.array([lam1470, BENCH["lamB_midgap_nm"][1], BENCH["lamB_midgap_nm"][2],
                        lam1520, BENCH["lamB_midgap_nm"][4]])
    slope_mix, intc, r2, sres, res = fit_line(np.array(WS_NM, float), lam_mix * 1e-9)
    print("slope: 2pt fine = %.2f nm/um | mixed-5pt = %.2f nm/um (R2=%.5f) | bench 40.65±0.53"
          % (slope_2pt, slope_mix * 1000, r2))

    # --- 阈值稳健性（两个新点）---
    thr_scan = {}
    for thr in [0.1, 0.3, 0.5, 0.7, 0.9]:
        lams = []
        for wnm in (1470, 1520):
            wl, T = load_raw(os.path.join(OUT, "w%d_fine_raw.npz" % wnm))
            _, _, _, info = longest_seg(wl, T, thr=thr)
            lams.append(info["midgap_nm"])
        thr_scan[str(thr)] = {"lamB_midgap_nm": lams,
                              "slope_2pt_nm_per_um": (lams[1] - lams[0]) / 0.05}
        print("  thr=%.1f: λB=%.3f/%.3f nm, slope=%.2f nm/um"
              % (thr, lams[0], lams[1], thr_scan[str(thr)]["slope_2pt_nm_per_um"]))

    # --- 验收判定（不修改验收标准，只报告）---
    lo, hi = BENCH["slope_midgap_nm_per_um"] - BENCH["slope_err"], \
             BENCH["slope_midgap_nm_per_um"] + BENCH["slope_err"]
    verdict = {
        "slope_2pt_in_bench_interval": bool(lo <= slope_2pt <= hi),
        "slope_mixed_in_bench_interval": bool(lo <= slope_mix * 1000 <= hi),
        "kappa_w1470_in_606_608": bool(606 - 3 <= recs[1470]["kappa_per_cm_old_ng"] <= 608 + 3),
        "kappa_w1520_in_606_608": bool(606 - 3 <= recs[1520]["kappa_per_cm_old_ng"] <= 608 + 3),
    }
    print("verdict:", json.dumps(verdict))

    out = {
        "n_g_fine": float(n_g_fine), "n_g_old": float(n_g_old),
        "grid": {"dx_nm": 5.0, "dy_nm": 20.0, "wl_window_nm": [1500, 1640], "n_freq": 281},
        "w1470": {k: v for k, v in recs[1470].items() if k not in ("wl", "T")},
        "w1520": {k: v for k, v in recs[1520].items() if k not in ("wl", "T")},
        "slope_2pt_nm_per_um": float(slope_2pt),
        "slope_mixed5_nm_per_um": float(slope_mix * 1000), "mixed5_R2": float(r2),
        "lamB_mixed5_nm": lam_mix.tolist(),
        "threshold_scan": thr_scan,
        "bench": BENCH, "verdict": verdict,
    }
    with open(os.path.join(OUT, "l1_fine_grid.json"), "w", encoding="utf-8") as fp:
        json.dump(out, fp, indent=1, ensure_ascii=False)

    # --- 图 ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, wnm in zip(axes[:2], (1470, 1520)):
        r = recs[wnm]
        ax.plot(r["wl"] * 1e9, r["T"], lw=.8, label="fine (dx=5nm, 281pt)")
        wl_o, T_o = load_raw(os.path.join(RES, "w%d_raw.npz" % wnm))
        ax.plot(wl_o * 1e9, T_o, lw=.8, alpha=.6, label="baseline (dx=10nm, 121pt)")
        ax.axhline(0.5, color="r", ls=":", lw=.6)
        ax.axvline(r["midgap_nm"], color="g", ls="--", lw=.8)
        ax.axvline(BENCH["lamB_midgap_nm"][WS_NM.index(wnm)], color="orange", ls=":", lw=.8)
        ax.set_title("w%d (green=fine midgap, orange=bench)" % wnm, fontsize=9)
        ax.set_xlabel("λ (nm)"); ax.legend(fontsize=7); ax.grid(alpha=.3)
    axes[0].set_ylabel("T")
    ax = axes[2]
    ax.errorbar([0], [BENCH["slope_midgap_nm_per_um"]], yerr=[BENCH["slope_err"]],
                fmt="o", capsize=5, label="bench 40.65±0.53")
    ax.plot([1], [slope_2pt], "s", label="fine 2-pt %.2f" % slope_2pt)
    ax.plot([2], [slope_mix * 1000], "^", label="mixed 5-pt %.2f" % (slope_mix * 1000))
    for i, (thr, v) in enumerate(thr_scan.items()):
        ax.plot([3 + i * 0.15], [v["slope_2pt_nm_per_um"]], ".", color="gray")
    ax.set_xlim(-0.5, 4); ax.set_ylabel("dλB/dw (nm/µm)")
    ax.set_title("slope check (gray = threshold scan)"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "l1_fine_grid.png"), dpi=150)
    print("saved l1_fine_grid.json + l1_fine_grid.png")


if __name__ == "__main__":
    main()
