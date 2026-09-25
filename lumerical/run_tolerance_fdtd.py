# -*- coding: utf-8 -*-
"""
A1/A2 FDTD 标定扫描：条宽与折射率调制（等效刻蚀深度）容差

A1: w = 1.5 um ±10/20/30 nm，均匀光栅（L = 77.5 um，快）
    -> λ_B(w) -> n_bar(w) 敏感度 dλ_B/dw；带隙宽 -> κ(w)
A2: dn = 0.018 / 0.022（±10%，细粒度；0.01/0.02/0.04 粗粒度已有）
    -> κ(dn)、λ_B(dn) 细粒度标定
A2b（可选, --chirp）: 250 um 啁啾光栅 dn ±10% -> ripple 对 dn 的敏感度（长任务，放最后）

输出：results/tolerance_fdtd.npz
运行：用 Lumerical 自带 python:
  "E:/Program Files/ANSYS Inc/v252/Lumerical/python-3.13.1/python.exe" run_tolerance_fdtd.py [--chirp]
"""
import os
import sys
import numpy as np

sys.path.append(r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python")
import lumapi  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
sys.path.insert(0, HERE)
import run_scan_2d as rs   # 复用 build/extract/kappa_from_gap

C0 = 299792458.0
L_uni = rs.L_uni
lambda_B = rs.lambda_B


def band_center(wl, T):
    """T 最小值附近的抛物线拟合 -> λ_B；以及 T<0.5 的带隙宽度"""
    o = np.argsort(wl)
    wl, T = wl[o], T[o]
    ic = np.argmin(T)
    # 抛物线拟合谷底
    i0, i1 = max(ic - 2, 0), min(ic + 3, len(wl))
    p = np.polyfit(wl[i0:i1], T[i0:i1], 2)
    lam_min = -p[1] / (2 * p[0])
    # 带隙：T 首次升过 0.5 的两个交点
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


def run_uniform(tag, w, dn):
    raw = os.path.join(OUT, "%s_raw.npz" % tag)
    fsp = os.path.join(OUT, "%s.fsp" % tag)
    if os.path.exists(raw):
        d = np.load(raw)
        print("reusing saved %s" % tag, flush=True)
        return C0 / d["f"], d["T"]
    rs.w = w
    if not os.path.exists(fsp):
        print("building %s (w=%.0f nm, dn=%.3f) ..." % (tag, w * 1e9, dn), flush=True)
        rs.build(fsp, dn, L_uni)
    print("running %s ..." % tag, flush=True)
    f, T, tau, _ = rs.extract(fsp, tag)
    return C0 / f, T


def main():
    with_chirp = "--chirp" in sys.argv
    ref = np.load(os.path.join(OUT, "ref_raw.npz"))
    n_g = C0 * np.mean(ref["tau"]) / (L_uni + 4e-6)

    results = {"n_g": n_g, "lambda_B_design": lambda_B}

    # ---------------- A1: width sweep ----------------
    ws_nm = [1470, 1480, 1500, 1520, 1530]
    lamB, gaps, kappas = [], [], []
    for wnm in ws_nm:
        wl, T = run_uniform("w%d" % wnm, wnm * 1e-9, 0.02)
        lb, gap = band_center(wl, T)
        kap = gap * np.pi * n_g / lb**2
        lamB.append(lb); gaps.append(gap); kappas.append(kap)
        print("  w=%d nm: λ_B=%.2f nm, gap=%.2f nm, κ=%.0f /cm"
              % (wnm, lb * 1e9, gap * 1e9, kap / 100), flush=True)
    results.update(w_nm=np.array(ws_nm), lamB=np.array(lamB),
                   gap=np.array(gaps), kappa=np.array(kappas))
    if len(ws_nm) >= 2:
        dlb_dw = np.polyfit(np.array(ws_nm) * 1e-9, np.array(lamB), 1)[0]
        print("A1 标定: dλ_B/dw = %.2f nm/um -> dn_bar/dw = %.2f /um"
              % (dlb_dw * 1e6 / 1e9 * 1e9, dlb_dw / (2 * rs.Lambda0)), flush=True)
        results["dlamB_dwing"] = dlb_dw

    # ---------------- A2: dn fine sweep ----------------
    dns = [0.018, 0.022]
    lamB2, gaps2, kappas2 = [], [], []
    for dn in dns:
        tag = "dnf%03d" % round(dn * 1000)
        wl, T = run_uniform(tag, 1.5e-6, dn)
        lb, gap = band_center(wl, T)
        kap = gap * np.pi * n_g / lb**2
        lamB2.append(lb); gaps2.append(gap); kappas2.append(kap)
        print("  dn=%.3f: λ_B=%.2f nm, gap=%.2f nm, κ=%.0f /cm"
              % (dn, lb * 1e9, gap * 1e9, kap / 100), flush=True)
    results.update(dn_fine=np.array(dns), lamB_fine=np.array(lamB2),
                   gap_fine=np.array(gaps2), kappa_fine=np.array(kappas2))

    # ---------------- A2b（可选）: chirped grating dn ±10% ----------------
    if with_chirp:
        L_ch, chirp_dL = 250e-6, 17.3e-9
        for dn in [0.018, 0.022]:
            tag = "chirpdf%03d" % round(dn * 1000)
            raw = os.path.join(OUT, "%s_raw.npz" % tag)
            fsp = os.path.join(OUT, "%s.fsp" % tag)
            if not os.path.exists(raw):
                rs.w = 1.5e-6
                if not os.path.exists(fsp):
                    print("building %s ..." % tag, flush=True)
                    rs.build(fsp, dn, L_ch, chirp_dL)
                print("running %s (长任务) ..." % tag, flush=True)
                rs.extract(fsp, tag)
            else:
                print("reusing saved %s" % tag, flush=True)
            d = np.load(raw)
            results.setdefault("chirp_tags", []).append(tag)

    np.savez(os.path.join(OUT, "tolerance_fdtd.npz"), **results)
    print("saved results/tolerance_fdtd.npz", flush=True)


if __name__ == "__main__":
    main()
