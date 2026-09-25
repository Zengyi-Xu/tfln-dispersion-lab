# -*- coding: utf-8 -*-
"""V3: A2b 啁啾提取稳健性（防幻觉核查，2026-09-25）。

对 lumerical/results/chirpdf018/022_raw.npz（dn=0.020±10%，250um 啁啾光栅）
与 chirp2d.npz（dn=0.020 基准）做 R 阈值扫描：

  R 阈值 {0.5, 0.7, 0.8, 0.9, 0.95} × 提取方式 {全域拟合, 最长连续段}
    -> D (ps/nm) 与 ripple_pp (ps)

判定：
  1. D 对阈值/方式的标准差——确认 D=0.051 的稳健性；
  2. ripple 最坏 +24%（dn=0.022 vs 0.020 基准）是否成立；
  3. 检验「必须用 R>0.9 平台」的说法（lab-note §17 规则 5）。

注意（V1 已发现）：无耗 TMM 单侧探针模型带内 R_max≈0.77，R>0.9 不可行；
但本任务数据是 FDTD（有耗/真实几何），R_max≈1.0，平台存在。
chirpdf*_raw.npz 的 tau_r（参考脊）为坏数据（含负值），故用绝对 tau 的斜坡。
输出: results/verify/v3/v3_chirp_extract.json + 图
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "v3")
os.makedirs(OUT, exist_ok=True)
RES = os.path.join(ROOT, "lumerical", "results")
C0 = 299792458.0

THRS = [0.5, 0.7, 0.8, 0.9, 0.95]


def load_chirpdf(tag):
    d = np.load(os.path.join(RES, "%s_raw.npz" % tag))
    wl = C0 / d["f"] * 1e9
    o = np.argsort(wl)
    # 注意：本数据集里物理斜坡在 tau_r 上（与 comprehensive_simulation.py 一致，
    # D=0.051 的来源）；'tau'/'tau_g' 在平台上是平的（D≈0），字段命名有误导性。
    return wl[o], 1.0 - d["T"][o], d["tau_r"][o] * 1e12  # wl(nm), R, tau(ps)


def load_chirp2d():
    d = np.load(os.path.join(RES, "chirp2d.npz"))
    wl = d["wl"] * 1e9
    o = np.argsort(wl)
    return wl[o], 1.0 - d["T"][o], d["tau_r"][o] * 1e12


def extract(wl, R, tau, thr):
    """返回 {'global': (D,ripple,band,n), 'longest': (...)}；不可用为 None"""
    m = R > thr
    out = {}
    for mode in ["global", "longest"]:
        mm = m.copy()
        if mode == "longest":
            idx = np.where(mm)[0]
            if len(idx) == 0:
                out[mode] = None
                continue
            segs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
            seg = max(segs, key=len)
            mm = np.zeros_like(mm)
            mm[seg] = True
        if mm.sum() < 10:
            out[mode] = None
            continue
        p = np.polyfit(wl[mm], tau[mm], 1)
        resid = tau[mm] - np.polyval(p, wl[mm])
        out[mode] = {"D_ps_per_nm": float(p[0]),
                     "ripple_pp_ps": float(resid.max() - resid.min()),
                     "band_nm": float(wl[mm].max() - wl[mm].min()),
                     "n_pts": int(mm.sum())}
    return out


def main():
    devices = {"chirp2d_dn020": load_chirp2d(),
               "chirpdf018": load_chirpdf("chirpdf018"),
               "chirpdf022": load_chirpdf("chirpdf022")}
    res = {}
    for name, (wl, R, tau) in devices.items():
        res[name] = {"R_max": float(R.max()),
                     "thr": {str(t): extract(wl, R, tau, t) for t in THRS}}
        print("%s: R_max=%.3f" % (name, R.max()))
        for t in THRS:
            e = res[name]["thr"][str(t)]
            g = e["global"]; l = e["longest"]
            print("  thr=%.2f global D=%s ripple=%s | longest D=%s ripple=%s band=%.1fnm" % (
                t,
                "-" if g is None else "%.4f" % g["D_ps_per_nm"],
                "-" if g is None else "%.3f" % g["ripple_pp_ps"],
                "-" if l is None else "%.4f" % l["D_ps_per_nm"],
                "-" if l is None else "%.3f" % l["ripple_pp_ps"],
                0 if l is None else l["band_nm"]))

    # D 对阈值的稳健性统计（逐设备逐模式）
    stats = {}
    for name in devices:
        stats[name] = {}
        for mode in ["global", "longest"]:
            Ds = [res[name]["thr"][str(t)][mode]["D_ps_per_nm"] for t in THRS
                  if res[name]["thr"][str(t)][mode] is not None]
            rps = [res[name]["thr"][str(t)][mode]["ripple_pp_ps"] for t in THRS
                   if res[name]["thr"][str(t)][mode] is not None]
            stats[name][mode] = {"D_mean": float(np.mean(Ds)), "D_std": float(np.std(Ds)),
                                 "D_min": float(np.min(Ds)), "D_max": float(np.max(Ds)),
                                 "ripple_mean": float(np.mean(rps))}
    res["stats"] = stats
    print("\nD robustness:")
    for name, s in stats.items():
        for mode in ["global", "longest"]:
            print(" %s %-7s D=%.4f±%.4f (range %.4f-%.4f)" % (
                name, mode, s[mode]["D_mean"], s[mode]["D_std"],
                s[mode]["D_min"], s[mode]["D_max"]))

    # ripple 增益：dn022 vs 基准（chirp2d 与 dn018 两个参照）
    for mode in ["global", "longest"]:
        for base in ["chirp2d_dn020", "chirpdf018"]:
            rb = [res[base]["thr"][str(t)][mode]["ripple_pp_ps"] for t in THRS
                  if res[base]["thr"][str(t)][mode] is not None]
            r2 = [res["chirpdf022"]["thr"][str(t)][mode]["ripple_pp_ps"] for t in THRS
                  if res["chirpdf022"]["thr"][str(t)][mode] is not None]
            # 逐阈值配对
            pairs = [(res[base]["thr"][str(t)][mode]["ripple_pp_ps"],
                      res["chirpdf022"]["thr"][str(t)][mode]["ripple_pp_ps"])
                     for t in THRS
                     if res[base]["thr"][str(t)][mode] is not None
                     and res["chirpdf022"]["thr"][str(t)][mode] is not None]
            gains = [100 * (b / a - 1) for a, b in pairs]
            print("ripple gain 022 vs %s [%s]: per-thr %s, worst=%+.1f%%, mean=%+.1f%%" % (
                base, mode, ["%+.0f" % g for g in gains],
                max(gains), float(np.mean(gains))))
            res.setdefault("ripple_gain", {})["%s_vs_%s_%s" % ("chirpdf022", base, mode)] = {
                "per_thr_pct": gains, "worst_pct": float(max(gains)),
                "mean_pct": float(np.mean(gains))}

    with open(os.path.join(OUT, "v3_chirp_extract.json"), "w", encoding="utf-8") as fp:
        json.dump(res, fp, indent=1, ensure_ascii=False)

    # 图：tau 谱 + 阈值平台示例 + D/ripple vs thr
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for name, (wl, R, tau) in devices.items():
        axes[0].plot(wl, tau, ".", ms=3, label=name)
    axes[0].set_xlabel("λ (nm)"); axes[0].set_ylabel("τ (ps)")
    axes[0].set_title("chirp delay (tau_r field)"); axes[0].legend(); axes[0].grid(alpha=.3)
    for mode, st in [("global", "-"), ("longest", "--")]:
        for name, mk in [("chirpdf018", "o"), ("chirpdf022", "s"), ("chirp2d_dn020", "^")]:
            Ds = [res[name]["thr"][str(t)][mode]["D_ps_per_nm"] if res[name]["thr"][str(t)][mode] else np.nan
                  for t in THRS]
            axes[1].plot(THRS, Ds, mk + st, label="%s %s" % (name, mode), ms=4)
    axes[1].axhline(0.051, color="gray", ls=":", label="claim 0.051")
    axes[1].set_xlabel("R threshold"); axes[1].set_ylabel("D (ps/nm)")
    axes[1].set_title("D vs extraction threshold"); axes[1].legend(fontsize=7)
    axes[1].grid(alpha=.3)
    for mode, st in [("global", "-"), ("longest", "--")]:
        for name, mk in [("chirpdf018", "o"), ("chirpdf022", "s"), ("chirp2d_dn020", "^")]:
            rps = [res[name]["thr"][str(t)][mode]["ripple_pp_ps"] if res[name]["thr"][str(t)][mode] else np.nan
                   for t in THRS]
            axes[2].plot(THRS, rps, mk + st, label="%s %s" % (name, mode), ms=4)
    axes[2].set_xlabel("R threshold"); axes[2].set_ylabel("ripple p-p (ps)")
    axes[2].set_title("ripple vs extraction threshold"); axes[2].legend(fontsize=7)
    axes[2].grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "v3_chirp_robust.png"), dpi=150)
    print("saved v3_chirp_extract.json + v3_chirp_robust.png")


if __name__ == "__main__":
    main()
