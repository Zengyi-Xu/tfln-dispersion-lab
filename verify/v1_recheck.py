# -*- coding: utf-8 -*-
"""V1: A3/A5/A6 TMM 复核与 C2 判定（防幻觉核查，2026-09-25）。

复用 simulations/02_tolerance_scan.py 的 TMM 核心，但把 A5 的「摆幅提取窗口」
做成三种并排，判定 C2（摆幅随 L 线性，1–20mm 偏差 ~2%）是否应改为
「≥5 mm 偏差 ≤3%」：

  (a) R>0.5 全域平台（啁啾范围内所有 R>0.5 点，含带边）
  (b) R>0.9 平台 + 最长连续段
  (c) R>0.5 + 排除带边 2×局域带隙（= 02_tolerance_scan.py 现行实现）

A3 相位误差按任务书要求扩到 5 种子；A6 切趾确定性复核。
断点续跑：进度写入 results/verify/v1/_checkpoint.json。
输出: results/verify/v1/v1_tolerance_recheck.json + 对比图
"""
import os
import sys
import json
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "v1")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "simulations"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "tol", os.path.join(ROOT, "simulations", "02_tolerance_scan.py"))
tol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tol)

C0 = tol.C0
N_EFF = tol.N_EFF
KAPPA0 = tol.KAPPA0
C_NM_PER_MM = tol.C_NM_PER_MM
CKPT = os.path.join(OUT, "_checkpoint.json")

BASE = np.load(os.path.join(ROOT, "results", "tolerance_scan.npz"))


def load_ckpt():
    if os.path.exists(CKPT):
        with open(CKPT, encoding="utf-8") as fp:
            return json.load(fp)
    return {}


def save_ckpt(c):
    with open(CKPT, "w", encoding="utf-8") as fp:
        json.dump(c, fp)


def windows_metrics(lam, R, tau, lam_b0, chirp_nm, kappa0):
    """三种窗口并排返回 {swing_ps, D_ps_per_nm, ripple_pp_ps, band_nm, n_pts}"""
    gap_nm = lam_b0 ** 2 * kappa0 / (2 * np.pi * N_EFF) * 1e9
    span = (lam > lam_b0) & (lam < lam_b0 + chirp_nm * 1e-9)
    res = {}
    # (a) R>0.5 全域平台
    for name, rthr, edge_excl, longest in [
            ("a_R0.5_full", 0.5, False, False),
            ("b_R0.9_longest", 0.9, False, True),
            ("c_R0.5_noedge", 0.5, True, False)]:
        m = span & (R > rthr)
        if edge_excl:
            m &= ((lam > lam_b0 + 2 * gap_nm * 1e-9)
                  & (lam < lam_b0 + (chirp_nm - 2 * gap_nm) * 1e-9))
        if longest:
            idx = np.where(m)[0]
            if len(idx) == 0:
                res[name] = None
                continue
            splits = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
            seg = max(splits, key=len)
            m = np.zeros_like(m)
            m[seg] = True
        if m.sum() < 50:
            res[name] = None
            continue
        p = np.polyfit(lam[m], tau[m], 1)
        resid = tau[m] - np.polyval(p, lam[m])
        res[name] = {
            "swing_ps": float((tau[m].max() - tau[m].min()) * 1e12),
            "D_ps_per_nm": float(p[0] * 1e12 / 1e9),
            "ripple_pp_ps": float((resid.max() - resid.min()) * 1e12),
            "band_nm": float((lam[m].max() - lam[m].min()) * 1e9),
            "n_pts": int(m.sum()),
        }
    return res


def compute_spectrum(lam_b0, L, chirp_nm, kappa_prof, sigma_lamb=0.0, seed=0,
                     extra_lamb_z=None, kappa0=KAPPA0):
    """复制 tol.spectrum 的谱计算（不提取指标），返回 lam,R,tau"""
    N = max(400, int(round(L / (2.5e-3 / 800))))
    dz = L / N
    z = (np.arange(N) + 0.5) * dz
    Cc = chirp_nm * 1e-9 / L
    lam_b_z = lam_b0 + Cc * z
    if extra_lamb_z is not None:
        lam_b_z = lam_b_z + extra_lamb_z(z)
    if sigma_lamb > 0:
        lam_b_z = lam_b_z + np.random.default_rng(seed).normal(0, sigma_lamb, N)
    kappa_z = kappa_prof(z, L, kappa0)
    gap_nm = lam_b0 ** 2 * kappa0 / (2 * np.pi * N_EFF) * 1e9
    n_lam = int(np.clip(chirp_nm * 120, 4000, 12000))
    swing_s = 2 * N_EFF * L / C0
    span_f = C0 * chirp_nm * 1e-9 / lam_b0 ** 2
    n_lam = max(n_lam, min(60000, int(3 * swing_s * span_f) + 1))
    lam = np.linspace(lam_b0 - 2e-9, lam_b0 + (chirp_nm + 2) * 1e-9, n_lam)
    r = tol.tmm_reflect(lam, lam_b_z, kappa_z, dz)
    R = np.abs(r) ** 2
    phi = np.unwrap(np.angle(r))
    tau = -np.gradient(phi, 2 * np.pi * C0 / lam)
    return lam, R, tau


def main():
    lam_b0 = 1535e-9
    ck = load_ckpt()
    done = ck.setdefault("done", {})

    # ---------------- A5: 三种窗口 × 5 长度 ----------------
    Ls_mm = [1.0, 2.5, 5.0, 10.0, 20.0]
    a5 = ck.setdefault("a5", {})
    for Lmm in Ls_mm:
        key = "L%.1f" % Lmm
        if key in done:
            continue
        t0 = time.time()
        chirp = C_NM_PER_MM * Lmm
        lam, R, tau = compute_spectrum(lam_b0, Lmm * 1e-3, chirp, tol.kappa_uniform)
        met = windows_metrics(lam, R, tau, lam_b0, chirp, KAPPA0)
        geo = 2 * N_EFF * Lmm * 1e-3 / C0 * 1e12
        a5[key] = {"geo_ps": geo, "windows": met}
        done[key] = True
        save_ckpt(ck)
        print("A5 %s: geo=%.2f ps | %s (%.0fs)" % (
            key, geo,
            " ".join("%s=%.2f" % (k, v["swing_ps"]) for k, v in met.items() if v),
            time.time() - t0), flush=True)

    # ---------------- A3: 相位误差 5 种子 @2.5mm + 随 L 增长 ----------------
    L_ref, chirp_ref = 2.5e-3, C_NM_PER_MM * 2.5
    a3 = ck.setdefault("a3", {})
    for sig in [0.0, 0.001, 0.003, 0.01, 0.03, 0.1]:
        key = "a3_sig%g" % sig
        if key in done:
            continue
        rps = []
        seeds = [0] if sig == 0 else list(range(5))
        for seed in seeds:
            lam, R, tau = compute_spectrum(lam_b0, L_ref, chirp_ref, tol.kappa_uniform,
                                           sigma_lamb=sig * 1e-9, seed=seed)
            met = windows_metrics(lam, R, tau, lam_b0, chirp_ref, KAPPA0)
            rps.append(met["c_R0.5_noedge"]["ripple_pp_ps"])
        a3[key] = {"sigma_nm": sig, "seeds": seeds, "ripple_pp_ps": rps,
                   "mean": float(np.mean(rps)), "std": float(np.std(rps))}
        done[key] = True
        save_ckpt(ck)
        print("A3 σ=%gnm: ripple=%.3f±%.3f ps (%d seeds)" % (
            sig, a3[key]["mean"], a3[key]["std"], len(seeds)), flush=True)

    a3L = ck.setdefault("a3L", {})
    for Lmm in Ls_mm:
        key = "a3L_L%.1f" % Lmm
        if key in done:
            continue
        rps = []
        for seed in range(5):
            lam, R, tau = compute_spectrum(lam_b0, Lmm * 1e-3, C_NM_PER_MM * Lmm,
                                           tol.kappa_uniform,
                                           sigma_lamb=0.01e-9, seed=seed)
            met = windows_metrics(lam, R, tau, lam_b0, C_NM_PER_MM * Lmm, KAPPA0)
            rps.append(met["c_R0.5_noedge"]["ripple_pp_ps"])
        a3L[key] = {"L_mm": Lmm, "ripple_pp_ps": rps,
                    "mean": float(np.mean(rps)), "std": float(np.std(rps))}
        done[key] = True
        save_ckpt(ck)
        print("A3L L=%gmm: ripple=%.3f±%.3f ps" % (Lmm, a3L[key]["mean"], a3L[key]["std"]),
              flush=True)

    # ---------------- A6: 切趾（确定性） ----------------
    a6 = ck.setdefault("a6", {})
    for name, prof in [("uniform", tol.kappa_uniform), ("linear", tol.kappa_linear),
                       ("gauss", tol.kappa_gauss), ("cosine", tol.kappa_cosine)]:
        key = "a6_" + name
        if key in done:
            continue
        lam, R, tau = compute_spectrum(lam_b0, L_ref, chirp_ref, prof)
        met = windows_metrics(lam, R, tau, lam_b0, chirp_ref, KAPPA0)
        a6[name] = met
        done[key] = True
        save_ckpt(ck)
        print("A6 %s: %s" % (name, {k: round(v["ripple_pp_ps"], 3) for k, v in met.items() if v}),
              flush=True)

    # ---------------- 汇总 JSON ----------------
    summary = {"N_EFF": N_EFF, "KAPPA0": KAPPA0, "C_nm_per_mm": C_NM_PER_MM,
               "a5": a5, "a3": a3, "a3L": a3L, "a6": a6,
               "baseline": {k: np.atleast_1d(BASE[k]).tolist() for k in BASE.files}}
    with open(os.path.join(OUT, "v1_tolerance_recheck.json"), "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=1, ensure_ascii=False)

    # 图：三种窗口 swing/L 与几何线对比
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    Ls = np.array(Ls_mm)
    ax.loglog(Ls, [a5["L%.1f" % l]["geo_ps"] for l in Ls], "k--", label=r"geo $2n_gL/c$")
    style = {"a_R0.5_full": ("o-", "R>0.5 full"),
             "b_R0.9_longest": ("s-", "R>0.9 longest"),
             "c_R0.5_noedge": ("^-", "R>0.5 no-edge (current)")}
    for wname, (st, lab) in style.items():
        vals = [(a5["L%.1f" % l]["windows"] or {}).get(wname) for l in Ls]
        lab_eff = lab if any(v is None for v in vals) else lab
        pts = [(l, v["swing_ps"]) for l, v in zip(Ls, vals) if v is not None]
        if not pts:
            ax.plot([], [], st, label=lab + " (empty: R<0.9 in model)")
            continue
        ax.loglog([p[0] for p in pts], [p[1] for p in pts], st, label=lab)
        geo_d = {l: a5["L%.1f" % l]["geo_ps"] for l in Ls}
        for x, y in pts:
            d = 100 * (y / geo_d[x] - 1)
            ax.annotate("%.1f%%" % d, (x, y), textcoords="offset points",
                        xytext=(6, 4), fontsize=7)
    ax.set_xlabel("L (mm)"); ax.set_ylabel("delay swing (ps)")
    ax.set_title("V1 A5: swing vs L, three extraction windows (anno = dev from geo)")
    ax.legend(); ax.grid(alpha=.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "v1_swing_windows.png"), dpi=150)
    print("\nsaved v1_tolerance_recheck.json + v1_swing_windows.png; all done =",
          len(done), "items")


if __name__ == "__main__":
    main()
