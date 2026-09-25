# -*- coding: utf-8 -*-
"""V2: A1/A2 带隙重提取（防幻觉核查，2026-09-25）。

对 lumerical/results/ 下已保存的 FDTD 原始谱（*_raw.npz，键 f/T）做两种
带隙提取并排输出：

  OLD  : run_tolerance_fdtd.py::band_center —— T 最小值抛物线谷底 + 从谷底
         向两侧走 T<0.5 的交点。已知问题：锚定在全局 T 最小值上，若谱有
         多个凹陷或采样粗，会把带边/旁瓣当带隙。
  NEW  : 「最长 T<thr 连续段」—— 找所有 T<0.5 的连续区间，取最长者为带隙，
         两端线性插值到 T=0.5 得带边，中心取段内 T 最小值（同时给抛物线精修）。
         段长与段内 min(T) 一并输出，便于判断该段是不是真带隙。

输出: results/verify/v2/v2_a1a2_reextract.json + lamB_vs_w.png + T 谱小图
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "v2")
os.makedirs(OUT, exist_ok=True)
RES = os.path.join(ROOT, "lumerical", "results")
C0 = 299792458.0

# 与 run_scan_2d.py / run_tolerance_fdtd.py 一致的设计常量
N_BAR = 2.02
LAMBDA0 = 387.5e-9
LAMBDA_B_DESIGN = 2 * N_BAR * LAMBDA0  # 1565.5 nm
L_UNI = 200 * LAMBDA0                  # 77.5 um


def band_center(wl, T):
    """旧法：逐行复制自 run_tolerance_fdtd.py（抛物线谷底 + 谷底锚定 T<0.5 交点）。"""
    o = np.argsort(wl)
    wl, T = wl[o], T[o]
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


def longest_seg(wl, T, thr=0.5):
    """新法：最长 T<thr 连续段。返回 (lamB_point, lamB_parab, gap, seg_info)。"""
    o = np.argsort(wl)
    wl, T = wl[o], T[o]
    below = T < thr
    # 所有连续段 [a, b]（含单点段）
    runs = []
    i = 0
    n = len(T)
    while i < n:
        if below[i]:
            a = i
            while i < n and below[i]:
                i += 1
            runs.append((a, i - 1))
        else:
            i += 1
    if not runs:
        return None, None, None, {"runs_nm": [], "n_runs": 0}
    # 最长段；并列取 T 更低者
    a, b = max(runs, key=lambda r: (r[1] - r[0], -T[r[0]:r[1] + 1].min()))
    # 带边：线性插值到 thr
    def cross(i, j):
        return wl[i] + (thr - T[i]) * (wl[j] - wl[i]) / (T[j] - T[i])
    gap = cross(b, b + 1) - cross(a - 1, a) if (a > 0 and b < n - 1) else np.nan
    midgap = 0.5 * (cross(b, b + 1) + cross(a - 1, a)) if (a > 0 and b < n - 1) else np.nan
    # 中心：段内 T 最小值点 + 抛物线精修
    seg = np.arange(a, b + 1)
    ic = seg[np.argmin(T[seg])]
    lam_pt = wl[ic]
    i0, i1 = max(ic - 2, 0), min(ic + 3, n)
    p = np.polyfit(wl[i0:i1], T[i0:i1], 2)
    lam_pq = -p[1] / (2 * p[0]) if p[0] > 0 else np.nan
    info = {
        "n_runs": len(runs),
        "runs_nm": sorted([(wl[r[0]] * 1e9, wl[r[1]] * 1e9, r[1] - r[0] + 1)
                           for r in runs], key=lambda x: -(x[1] - x[0])),
        "seg_min_T": float(T[seg].min()),
        "seg_width_samples": int(b - a + 1),
        "midgap_nm": None if midgap is None else midgap * 1e9,
    }
    return lam_pt, lam_pq, gap, info


def kappa(gap, lamB, n_g):
    return gap * np.pi * n_g / lamB ** 2


def load_spectrum(tag):
    d = np.load(os.path.join(RES, "%s_raw.npz" % tag))
    wl = C0 / d["f"]
    return np.sort(wl), d["T"][np.argsort(wl)]


def fit_line(x_nm, lamB_m):
    """λB(m) 对 w(nm) 线性拟合；返回 slope(nm/um), R2, 残差sigma(nm), 残差数组"""
    p = np.polyfit(x_nm, lamB_m * 1e9, 1)
    yhat = np.polyval(p, x_nm)
    res = lamB_m * 1e9 - yhat
    ss_res = float(np.sum(res ** 2))
    ss_tot = float(np.sum((lamB_m * 1e9 - lamB_m.mean() * 1e9) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return p[0], p[1], r2, float(res.std()), res


def analyze(tag, n_g):
    wl, T = load_spectrum(tag)
    lo_l, lo_g = band_center(wl, T)
    nw_pt, nw_pq, nw_g, info = longest_seg(wl, T)
    rec = {"tag": tag,
           "old": {"lamB_nm": lo_l * 1e9, "gap_nm": lo_g * 1e9,
                   "kappa_per_cm": kappa(lo_g, lo_l, n_g) / 100},
           "new": {"lamB_pt_nm": None if nw_pt is None else nw_pt * 1e9,
                   "lamB_parab_nm": None if nw_pq is None else nw_pq * 1e9,
                   "gap_nm": None if nw_g is None else nw_g * 1e9,
                   "kappa_per_cm": None if nw_g is None else kappa(nw_g, nw_pt, n_g) / 100,
                   "kappa_design_anchor_per_cm": None if nw_g is None else kappa(nw_g, LAMBDA_B_DESIGN, n_g) / 100},
           "seg_info": info, "wl_nm": wl * 1e9, "T": T}
    return rec


def main():
    # n_g 与 run_tolerance_fdtd.main() 相同算法：ref_raw 的 tau 均值 / (L_uni + 4 um)
    ref = np.load(os.path.join(RES, "ref_raw.npz"))
    n_g = C0 * float(np.mean(ref["tau"])) / (L_UNI + 4e-6)
    print("n_g (from ref_raw) = %.6f" % n_g)

    out = {"n_g": n_g, "lambda_B_design_nm": LAMBDA_B_DESIGN * 1e9,
           "A1": [], "A2_fine": [], "A2_coarse": []}

    # ---------------- A1: 条宽扫描 ----------------
    ws_nm = [1470, 1480, 1500, 1520, 1530]
    for wnm in ws_nm:
        rec = analyze("w%d" % wnm, n_g)
        rec["w_nm"] = wnm
        out["A1"].append(rec)
        print("w=%dnm OLD λB=%.3f gap=%.3f κ=%.0f/cm | NEW λB=%.3f gap=%.3f κ=%.0f/cm (runs=%d, minT=%.3f)"
              % (wnm, rec["old"]["lamB_nm"], rec["old"]["gap_nm"], rec["old"]["kappa_per_cm"],
                 rec["new"]["lamB_pt_nm"], rec["new"]["gap_nm"], rec["new"]["kappa_per_cm"],
                 rec["seg_info"]["n_runs"], rec["seg_info"]["seg_min_T"]))

    # 拟合 dλB/dw：旧法 vs 新法；并做 >3σ 残差离群剔除与单调性检查
    fits = {}
    for meth, key in [("old", "old"), ("new", "new")]:
        lam = np.array([r[key]["lamB_nm"] if meth == "old" else r["new"]["lamB_pt_nm"]
                        for r in out["A1"]], dtype=float)
        slope, intc, r2, sres, res = fit_line(np.array(ws_nm, float), lam * 1e-9)
        fits[meth] = {"all5": {"slope_nm_per_um": slope, "intercept_nm": intc,
                               "R2": r2, "resid_sigma_nm": sres,
                               "residuals_nm": res.tolist()}}
        # 3σ 剔除
        keep = np.abs(res) <= 3 * sres
        if keep.sum() >= 2 and (~keep).sum() > 0:
            slope2, intc2, r22, sres2, res2 = fit_line(
                np.array(ws_nm, float)[keep], (lam * 1e9)[keep] * 1e-9)
            fits[meth]["trimmed"] = {
                "kept_w_nm": np.array(ws_nm)[keep].tolist(),
                "dropped_w_nm": np.array(ws_nm)[~keep].tolist(),
                "slope_nm_per_um": slope2, "R2": r22, "resid_sigma_nm": sres2}
        fits[meth]["monotonic_increasing"] = bool(np.all(np.diff(lam) > 0))
    # 第三种估计：带边中点 midgap（平底带隙下比 argmin 更稳）
    lam_mid = np.array([r["seg_info"]["midgap_nm"] for r in out["A1"]], dtype=float)
    slope, intc, r2, sres, res = fit_line(np.array(ws_nm, float), lam_mid * 1e-9)
    fits["new_midgap"] = {"all5": {"slope_nm_per_um": slope, "intercept_nm": intc,
                                   "R2": r2, "resid_sigma_nm": sres,
                                   "residuals_nm": res.tolist()},
                          "lamB_midgap_nm": lam_mid.tolist(),
                          "monotonic_increasing": bool(np.all(np.diff(lam_mid) > 0))}
    out["A1_fits"] = fits
    # 阈值稳健性：midgap 斜率对 T 阈值 thr∈{0.1,...,0.9} 的敏感性
    thr_scan = {}
    for thr in [0.1, 0.3, 0.5, 0.7, 0.9]:
        lams = []
        for wnm in ws_nm:
            wl, T = load_spectrum("w%d" % wnm)
            _, _, _, info = longest_seg(wl, T, thr=thr)
            lams.append(info["midgap_nm"])
        p = np.polyfit(np.array(ws_nm, float), np.array(lams), 1)
        yhat = np.polyval(p, ws_nm)
        ss_res = np.sum((np.array(lams) - yhat) ** 2)
        ss_tot = np.sum((np.array(lams) - np.array(lams).mean()) ** 2)
        thr_scan[str(thr)] = {"slope_nm_per_um": float(p[0] * 1000),
                              "R2": float(1 - ss_res / ss_tot),
                              "lamB_midgap_nm": lams}
    out["A1_midgap_threshold_scan"] = thr_scan
    print("\nA1 midgap slope vs threshold:")
    for t, v in thr_scan.items():
        print(" thr=%s: slope=%.2f nm/um R2=%.5f" % (t, v["slope_nm_per_um"], v["R2"]))
    print("\nA1 fits:")
    for m, f in fits.items():
        print(" %s all5: slope=%.2f nm/um R2=%.6f resid_sigma=%.3f nm mono=%s"
              % (m, f["all5"]["slope_nm_per_um"] * 1000, f["all5"]["R2"],
                 f["all5"]["resid_sigma_nm"], f["monotonic_increasing"]))
        if "trimmed" in f:
            print(" %s trimmed: slope=%.2f R2=%.6f dropped=%s"
                  % (m, f["trimmed"]["slope_nm_per_um"] * 1000, f["trimmed"]["R2"],
                     f["trimmed"]["dropped_w_nm"]))

    # ---------------- A2: dn 细/粗扫描 ----------------
    for grp, tags, dns in [("A2_fine", ["dnf018", "dnf022"], [0.018, 0.022]),
                           ("A2_coarse", ["dn010", "dn040"], [0.010, 0.040])]:
        for tag, dn in zip(tags, dns):
            rec = analyze(tag, n_g)
            rec["dn"] = dn
            out[grp].append(rec)
            print("%s dn=%.3f OLD λB=%.3f gap=%.3f κ=%.0f | NEW λB=%.3f gap=%.3f κ=%.0f"
                  % (grp, dn, rec["old"]["lamB_nm"], rec["old"]["gap_nm"],
                     rec["old"]["kappa_per_cm"], rec["new"]["lamB_pt_nm"],
                     rec["new"]["gap_nm"], rec["new"]["kappa_per_cm"]))

    def kap_list(grp, meth):
        if meth == "old":
            return np.array([r["old"]["kappa_per_cm"] for r in out[grp]])
        return np.array([r["new"]["kappa_per_cm"] for r in out[grp]])

    a2 = {}
    for meth in ["old", "new"]:
        kf = kap_list("A2_fine", meth)
        kc = kap_list("A2_coarse", meth)
        # κ ∝ dn ? 细点比例与线性外推
        a2[meth] = {
            "kappa_fine_per_cm": kf.tolist(),
            "kappa_coarse_per_cm": kc.tolist(),
            "kappa_ratio_022_018": float(kf[1] / kf[0]),
            "expected_ratio_if_linear": 0.022 / 0.018,
            "deviation_from_linear_pct": float((kf[1] / kf[0]) / (0.022 / 0.018) - 1) * 100,
            "kappa_coarse_ratio_040_010": float(kc[1] / kc[0]),
            "lamB_fine_nm": [r["old"]["lamB_nm"] if meth == "old" else r["new"]["lamB_pt_nm"]
                             for r in out["A2_fine"]],
            "lamB_fine_drift_nm": float(abs(out["A2_fine"][1]["new"]["lamB_pt_nm"]
                                            - out["A2_fine"][0]["new"]["lamB_pt_nm"])
                                        if meth == "new" else
                                        abs(out["A2_fine"][1]["old"]["lamB_nm"]
                                            - out["A2_fine"][0]["old"]["lamB_nm"])),
        }
    out["A2_analysis"] = a2
    print("\nA2 analysis:", json.dumps(a2, indent=1))

    # ---------------- 图 ----------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    lam_old = [r["old"]["lamB_nm"] for r in out["A1"]]
    lam_new = [r["new"]["lamB_pt_nm"] for r in out["A1"]]
    ax.plot(ws_nm, lam_old, "o--", label="old band_center")
    ax.plot(ws_nm, lam_new, "s-", label="new longest T<0.5 seg")
    ax.axhline(LAMBDA_B_DESIGN * 1e9, color="gray", ls=":", label="design 1565.5")
    ax.set_xlabel("ridge width w (nm)"); ax.set_ylabel("λB (nm)")
    ax.set_title("A1: λB(w) re-extraction"); ax.legend(); ax.grid(alpha=.3)
    ax = axes[1]
    ax.plot(ws_nm, [r["old"]["kappa_per_cm"] for r in out["A1"]], "o--", label="old")
    ax.plot(ws_nm, [r["new"]["kappa_per_cm"] for r in out["A1"]], "s-", label="new")
    ax.set_xlabel("w (nm)"); ax.set_ylabel("κ (1/cm)")
    ax.set_title("A1: κ(w)"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "lamB_vs_w.png"), dpi=150)

    # 五个 A1 谱小图：直接看 w1470/w1520 是否有带隙误判
    fig, axes = plt.subplots(1, 5, figsize=(16, 3), sharey=True)
    for ax, r in zip(axes, out["A1"]):
        ax.plot(r["wl_nm"], r["T"], lw=.8)
        ax.axhline(0.5, color="r", ls=":", lw=.6)
        ax.axvline(r["new"]["lamB_pt_nm"], color="g", ls="--", lw=.8)
        ax.set_title("w=%d" % r["w_nm"], fontsize=9)
        ax.set_xlabel("λ (nm)", fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("T")
    fig.suptitle("A1 raw spectra (green=new λB, red=T=0.5)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "a1_spectra.png"), dpi=150)

    # 清理大数组后存 JSON
    for grp in ["A1", "A2_fine", "A2_coarse"]:
        for r in out[grp]:
            r.pop("wl_nm", None); r.pop("T", None)
    with open(os.path.join(OUT, "v2_a1a2_reextract.json"), "w", encoding="utf-8") as fp:
        json.dump(out, fp, indent=1, ensure_ascii=False)
    print("\nsaved", os.path.join(OUT, "v2_a1a2_reextract.json"))


if __name__ == "__main__":
    main()
