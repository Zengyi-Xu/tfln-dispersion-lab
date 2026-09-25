# -*- coding: utf-8 -*-
"""L2 分析：啁啾光栅 dn=0.020 细网格（dx=5nm）D 收敛性验收（防幻觉核查，2026-09-25）。

提取口径与 V3 完全一致（import verify/v3_chirp_robust 的 extract）：
物理延迟斜坡在 tau_r 字段（tau/tau_g 是平台平坦分量，拿错得 D≈0）。
基准（双机复核）：chirp2d D@R>0.9 = 0.0512 ps/nm，验收 ±5% → [0.0486, 0.0538]。

运行：python verify/l2_analyze.py（CPU，读 results/verify/l2/chirp_fine_raw.npz）
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
OUT = os.path.join(ROOT, "results", "verify", "l2")
RES = os.path.join(ROOT, "lumerical", "results")
sys.path.insert(0, HERE)
from v3_chirp_robust import extract, THRS  # noqa: E402

C0 = 299792458.0
BENCH_D = 0.0512          # chirp2d @R>0.9 双机复核值
BENCH_ALL = {"chirp2d": 0.0512, "dnf018": 0.0518, "dnf022": 0.0507}


def load_fine():
    d = np.load(os.path.join(OUT, "chirp_fine_raw.npz"))
    wl = C0 / d["f"] * 1e9
    o = np.argsort(wl)
    # 字段陷阱：物理斜坡在 tau_r
    return wl[o], 1.0 - d["T"][o], d["tau_r"][o] * 1e12


def load_baseline():
    d = np.load(os.path.join(RES, "chirp2d.npz"))
    wl = d["wl"] * 1e9
    o = np.argsort(wl)
    return wl[o], 1.0 - d["T"][o], d["tau_r"][o] * 1e12


def main():
    wl_f, R_f, tau_f = load_fine()
    wl_b, R_b, tau_b = load_baseline()

    res = {"fine": {"R_max": float(R_f.max()),
                    "thr": {str(t): extract(wl_f, R_f, tau_f, t) for t in THRS}},
           "baseline": {"R_max": float(R_b.max()),
                        "thr": {str(t): extract(wl_b, R_b, tau_b, t) for t in THRS}}}

    print("L2 mesh convergence (baseline dx=10nm vs fine dx=5nm):")
    for t in THRS:
        row = []
        for dev in ("baseline", "fine"):
            e = res[dev]["thr"][str(t)]
            g = e["global"]
            row.append("%s/%s" % ("-" if g is None else "%.4f" % g["D_ps_per_nm"],
                                  "-" if e["longest"] is None else "%.4f" % e["longest"]["D_ps_per_nm"]))
        print("  thr=%.2f  baseline global/longest %s  fine %s" % (t, row[0], row[1]))

    D_fine_09 = res["fine"]["thr"]["0.9"]["global"]["D_ps_per_nm"]
    D_base_09 = res["baseline"]["thr"]["0.9"]["global"]["D_ps_per_nm"]
    dev_pct = 100 * (D_fine_09 / BENCH_D - 1)
    verdict = {
        "D_fine_at_R09": D_fine_09,
        "D_baseline_at_R09": D_base_09,
        "deviation_from_bench_pct": float(dev_pct),
        "within_pm5pct": bool(abs(dev_pct) <= 5.0),
    }
    print("D fine @R>0.9 = %.4f ps/nm vs bench 0.0512 -> %+.2f%% (accept ±5%%): %s"
          % (D_fine_09, dev_pct, verdict["within_pm5pct"]))

    # D 对阈值的稳健性（fine）
    for mode in ("global", "longest"):
        Ds = [res["fine"]["thr"][str(t)][mode]["D_ps_per_nm"] for t in THRS
              if res["fine"]["thr"][str(t)][mode] is not None]
        print("  fine %-7s D mean=%.4f std=%.4f range %.4f-%.4f"
              % (mode, np.mean(Ds), np.std(Ds), np.min(Ds), np.max(Ds)))
        verdict["fine_%s_D_mean" % mode] = float(np.mean(Ds))
        verdict["fine_%s_D_std" % mode] = float(np.std(Ds))

    res["bench"] = BENCH_ALL
    res["verdict"] = verdict
    with open(os.path.join(OUT, "l2_mesh_convergence.json"), "w", encoding="utf-8") as fp:
        json.dump(res, fp, indent=1, ensure_ascii=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(wl_b, tau_b, ".", ms=3, label="baseline dx=10nm")
    axes[0].plot(wl_f, tau_f, ".", ms=3, label="fine dx=5nm")
    axes[0].set_xlabel("λ (nm)"); axes[0].set_ylabel("τ_r (ps)")
    axes[0].set_title("chirp delay (tau_r field)"); axes[0].legend(); axes[0].grid(alpha=.3)
    for dev, mk in [("baseline", "o--"), ("fine", "s-")]:
        Ds = [res[dev]["thr"][str(t)]["global"]["D_ps_per_nm"]
              if res[dev]["thr"][str(t)]["global"] else np.nan for t in THRS]
        axes[1].plot(THRS, Ds, mk, ms=4, label=dev)
    axes[1].axhline(BENCH_D, color="gray", ls=":", label="bench 0.0512")
    axes[1].axhspan(BENCH_D * 0.95, BENCH_D * 1.05, color="gray", alpha=.15)
    axes[1].set_xlabel("R threshold"); axes[1].set_ylabel("D (ps/nm)")
    axes[1].set_title("D vs threshold (gray band = ±5%)"); axes[1].legend(); axes[1].grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "l2_mesh_convergence.png"), dpi=150)
    print("saved l2_mesh_convergence.json + .png")


if __name__ == "__main__":
    main()
