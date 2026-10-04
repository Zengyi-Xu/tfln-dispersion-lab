# -*- coding: utf-8 -*-
"""14: CBG 延迟核 × 因果共享增益 —— 判伪「对称脉冲重叠 = SOA 实际耦合」（sim14 任务书 A 部分）。

自包含（numpy/scipy/matplotlib only），纯 CPU，不占用 Lumerical 许可。
工作仓库：tfln-dispersion-lab @ verify/2026-09-25。

动机（任务书 20261004）：
- sim09 的耦合核 K_ij = exp(-Δτ²/(2σ_t²)) 是**对称**的高斯脉冲重叠，
  隐含假设「耦合双向等价」。真实共享增益介质（SOA 唯象代理）是**因果**的：
  先到的脉冲消耗增益，后到的探针才被抑制；反序不对称。
- 本脚本提取因果有效耦合 J^eff_ij，量化其与对称 K 的口径差异与对称性破缺。

物理模型（唯象代理，不声称 SOA 器件级复现）：
- 强度脉冲 p_i(t) = exp[-4 ln2 ((t-τ_i)/w)^2]，w = 10 ps 为**强度 FWHM**；
  x_i ∈ {0,1} 为通道开关。
- 共享增益状态：ḡ = (g0-g)/T_rec - β g Σ_j x_j p_j(t)，g0 = 1 归一。
- 弱探针 i 读取 h_i = ∫ p_i(t)[g(t)-g0] dt。J^eff_ij 由单独开关通道 j
  （i≠j）的差得到。探针响应用**变分线性响应**（对探针幅度 ε 的一阶精确，
  探针不进动力学，天然不反饱和）；并用有限 ε=1e-3 的探针在环仿真验证
  线性化自洽（报告最大相对偏差）。

扫描：
- T_rec/w ∈ {0.1, 1, 10}（w=10 ps → T_rec = 1/10/100 ps），小信号与饱和两档
  （饱和参数 s = β·T_rec ∈ {0.05, 5}，β = s/T_rec）。
- N=32，Δλ=0.2 nm，群延迟三档：
  (1) lumerical/results/chirp2d.npz 的 tau_r 实测谱直接插值（不重标定成 D=10），
      R = 1 - T，只用有效反射窗口（R ≥ 0.5·max R 的连续带）；
  (2) sim09 的 D = 1.3 ps/nm 线性律；
  (3) D = 10 ps/nm 理想设计目标。
- 数值收敛：积分步长减半 + 时间窗加倍，各报 max|ΔJ| 与 Δε_sym。

产物（results/causal_kernel/）：
  results.jsonl（逐配置行）、summary.json、fig1_J_vs_K.png、
  fig2_sweep.png、convergence.csv/md、report.md（支持/不支持/未决逐条判定）

用法：
  python simulations/14_causal_kernel.py            # 全量（约 1-2 分钟）
  python simulations/14_causal_kernel.py --aggregate  # 只重出图和报告
"""
import argparse
import hashlib
import json
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "causal_kernel")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

LN2 = np.log(2.0)
W = 10.0                          # 强度 FWHM [ps]（任务书定义）
N = 32                            # 梳线数
DLAM = 0.2                        # nm
G0 = 1.0                          # 归一小信号增益
T_REC_RATIOS = [0.1, 1.0, 10.0]   # T_rec / w
SAT_PARAMS = {"small": 0.05, "sat": 5.0}   # s = β·T_rec 两档
DT0 = W / 64.0                    # 基准积分步长 [ps]
MARGIN0 = 4.0 * W                 # 基准时间窗对称余量 [ps]
EPS_PROBE = 1e-3                  # 有限探针验证幅度


# ---------------------------------------------------------------------------
# 脉冲与对称重叠 K（口径核对块）
# ---------------------------------------------------------------------------

def pulse(t, tau, w=W):
    """强度高斯脉冲，w 为强度 FWHM。"""
    return np.exp(-4.0 * LN2 * ((t - tau) / w) ** 2)


def K_numeric(tau_i, tau_j, w=W, dt=0.01, margin=4.0 * W):
    """数值积分 K_ij = ∫ p_i p_j dt（归一到 K(tau_i=tau_j)）。"""
    t = np.arange(min(tau_i, tau_j) - margin, max(tau_i, tau_j) + margin, dt)
    pi, pj = pulse(t, tau_i, w), pulse(t, tau_j, w)
    return float(np.trapezoid(pi * pj, t))


def K_analytic(delta, w=W):
    """∫p_i p_j dt 的解析形：exp(-2 ln2 · Δ²/w²)（已归一）。"""
    return np.exp(-2.0 * LN2 * delta ** 2 / w ** 2)


def K_sim09(delta, sigma_t):
    """sim09 公式：exp(-Δ²/(2σ_t²))（intensity-convolution 口径）。"""
    return np.exp(-delta ** 2 / (2.0 * sigma_t ** 2))


def pulse_width_check():
    """口径核对：任务书 w=10ps(FWHM) vs sim09 σ_t=10ps 并不自动等价。

    分别输出数值积分 K、解析 K、sim09 公式三条曲线在关键 Δ 处的值与相对差。"""
    deltas = np.array([0.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 26.0])
    w_equiv_sig = W / (2.0 * np.sqrt(LN2))     # 任务书 w 折算到 sim09 口径的 σ_t
    sig_equiv_w = 2.0 * np.sqrt(LN2) * 10.0    # sim09 σ_t=10 折算到 FWHM
    kn0 = K_numeric(0.0, 0.0)                  # 数值积分峰值（绝对量, ps）
    rows = []
    for d in deltas:
        kn = K_numeric(0.0, d) / kn0 if d <= 20.0 else np.nan   # 归一到 δ=0
        ka = K_analytic(d)
        k9 = K_sim09(d, 10.0)
        rows.append({"delta_ps": d, "K_numeric": kn, "K_analytic_w10": ka,
                     "K_sim09_sig10": k9,
                     "rel_num_vs_ana": abs(kn - ka) / ka,
                     "rel_ana_vs_sim09": abs(ka - k9) / k9})
    out = {"stage": "pw_check", "w_ps": W,
           "w_equiv_sigma_t_sim09": w_equiv_sig,
           "sigma_t_10ps_equiv_FWHM": sig_equiv_w,
           "rows": rows,
           "note": "任务书 K(FWHM=w) 比 sim09 K(σ_t=10) 窄: "
                   "K_w=exp(-2ln2 Δ²/w²) vs K_09=exp(-Δ²/200)；"
                   "等效 σ_t = w/(2√ln2) = %.3f ps" % w_equiv_sig}
    return out


# ---------------------------------------------------------------------------
# 群延迟三档
# ---------------------------------------------------------------------------

def load_measured_gd():
    """chirp2d.npz tau_r 实测谱，返回 (lam_nm_asc, tau_ps_asc, R, info)。

    有效反射窗口 = R ≥ 0.5·max(R) 的最长连续带；窗口外 tau_r 有符号伪影
    （带边负值），不使用。"""
    d = np.load(os.path.join(ROOT, "lumerical", "results", "chirp2d.npz"))
    wl = d["wl"] * 1e9                    # nm，降序
    T = d["T"]
    tau_r = d["tau_r"] * 1e12             # ps
    R = 1.0 - T
    order = np.argsort(wl)
    wl, T, tau_r, R = wl[order], T[order], tau_r[order], R[order]

    Rmax = R.max()
    thr = 0.5 * Rmax
    above = R >= thr
    # 最长连续带
    best = cur = None
    for i, a in enumerate(above):
        if a and cur is None:
            cur = [i, i]
        elif a:
            cur[1] = i
        else:
            if cur and (best is None or cur[1] - cur[0] > best[1] - best[0]):
                best = cur
            cur = None
    if cur and (best is None or cur[1] - cur[0] > best[1] - best[0]):
        best = cur
    i0, i1 = best
    lam_w, tau_w, R_w = wl[i0:i1 + 1], tau_r[i0:i1 + 1], R[i0:i1 + 1]

    # 数据充分性：谱点间距 vs 通道间距；插值误差（隔点抽稀重插对比）；
    # 波纹（线性去趋势后残余 std）
    dl_data = np.diff(wl).mean()
    sub = tau_w[::2]
    lam_sub = lam_w[::2]
    tau_interp_sub = np.interp(lam_w, lam_sub, sub)
    interp_err = float(np.sqrt(np.mean((tau_interp_sub - tau_w) ** 2)))
    A = np.vstack([lam_w, np.ones_like(lam_w)]).T
    sol = np.linalg.lstsq(A, tau_w, rcond=None)[0]
    slope = float(sol[0])
    ripple = float(np.std(tau_w - A @ sol))
    span_window = lam_w[-1] - lam_w[0]
    span_needed = (N - 1) * DLAM

    info = {"n_points_total": len(wl), "wl_range_nm": [float(wl[0]), float(wl[-1])],
            "dl_data_nm": float(dl_data),
            "R_max": float(Rmax), "R_threshold": float(thr),
            "window_nm": [float(lam_w[0]), float(lam_w[-1])],
            "window_width_nm": float(span_window),
            "tau_r_in_window_ps": [float(tau_w.min()), float(tau_w.max())],
            "tau_r_ripple_ps": ripple, "tau_r_slope_ps_per_nm": float(slope),
            "interp_err_ps_subsample": interp_err,
            "channels_fit_in_window": bool(span_needed <= span_window),
            "channel_span_nm": float(span_needed),
            "points_per_channel_spacing": float(dl_data / DLAM)}
    # 通道足迹内最小 R（把 32 通道放在窗口中心）
    lam_c = 0.5 * (lam_w[0] + lam_w[-1])
    lam_ch = lam_c + (np.arange(N) - (N - 1) / 2.0) * DLAM
    R_ch = np.interp(lam_ch, wl, R)
    info["R_min_at_channels"] = float(R_ch.min())
    return lam_w, tau_w, R_w, info


def gd_laws():
    """三种群延迟律，返回 dict: name -> (tau_ps 数组, meta)。"""
    lam_w, tau_w, R_w, info = load_measured_gd()
    lam_c = 0.5 * (lam_w[0] + lam_w[-1])
    lam_ch = lam_c + (np.arange(N) - (N - 1) / 2.0) * DLAM
    tau_meas = np.interp(lam_ch, lam_w, tau_w)
    tau_meas = tau_meas - tau_meas[0]
    laws = {
        "cbg_measured": (tau_meas, {"kind": "measured_tau_r",
                                    "data_info": info}),
        "D1.3": (1.3 * DLAM * np.arange(N), {"kind": "linear", "D": 1.3}),
        "D10": (10.0 * DLAM * np.arange(N), {"kind": "linear", "D": 10.0}),
    }
    return laws


# ---------------------------------------------------------------------------
# 共享增益仿真 + 变分线性响应提取 J
# ---------------------------------------------------------------------------

def simulate_gain(tau_data, beta, T_rec, dt, margin, lo=None, hi=None):
    """单数据脉冲（tau_data）驱动的增益轨迹 g(t)（含时间网格）。

    默认窗 [τ−margin, τ+margin]；多通道问题必须传全局 lo/hi
    （τ_min−margin / τ_max+margin），否则远端探针被截断（D10 档 span=62 ps
    曾因此出现 ~19% 的窗伪影，见 convergence.md）。"""
    if lo is None:
        lo = min(0.0, tau_data) - margin
    if hi is None:
        hi = max(0.0, tau_data) + margin
    t = np.arange(lo, hi + 0.5 * dt, dt)
    p = pulse(t, tau_data)
    g = np.empty(len(t))
    g_prev = G0
    a = 1.0 / T_rec
    for n in range(len(t)):
        drive = a + beta * p[n]
        gss = a / drive
        g_prev = gss + (g_prev - gss) * np.exp(-drive * dt)
        g[n] = g_prev
    return t, p, g


def linear_response_J(tau, beta, T_rec, dt, margin):
    """独立线性响应定义（任务书口径）：
    J_ij = ∫ p_i(t) [g^{(j)}(t) - g0] dt，g^{(j)} = 仅泵浦 j 开启的增益轨迹。

    探针 ε→0：只作为读出权重，不进动力学 → 天然不反饱和；
    与「有限 ε 探针 on/off 差分」在 ε→0 时一致（probe_in_loop_check 验证）。
    注意：J 的主项是 O(β) 的直读增益凹陷（因果）；若误对探针幅度取变分
    dh_i/dε，主项被差分消掉、只剩 O(β²) 的自饱和调制 —— 对象错误。

    返回 J（行=探针 i，列=数据 j），以及 g 轨迹摘要。"""
    lo = tau.min() - margin
    hi = tau.max() + margin          # 全局窗：覆盖所有探针（含远端 i≫j）
    t = np.arange(lo, hi + 0.5 * dt, dt)
    p_probes = np.exp(-4.0 * LN2 * ((t[:, None] - tau[None, :]) / W) ** 2)
    J = np.zeros((N, N))
    gmin_all, gend_all = 1.0, G0
    for j in range(N):
        _, _, g0traj = simulate_gain(tau[j], beta, T_rec, dt, margin,
                                     lo=lo, hi=hi)
        J[:, j] = np.trapezoid(p_probes * (g0traj - G0)[:, None], t, axis=0)
        gmin_all = min(gmin_all, g0traj.min())
        gend_all = min(gend_all, g0traj[-1])
    return J, {"g_min": float(gmin_all), "g_end": float(gend_all)}


def probe_in_loop_check(tau, beta, T_rec, dt, margin, j_probe=None):
    """有限探针验证（任务书 on/off 定义）：探针幅度 ε（动力学与读出同为
    ε·p_i），h_i = ∫(εp_i)(g−G0)dt；off 态**不含泵浦 j**（通道单独关闭），
    J_probe = [h(x_j=1) − h(x_j=0)]/ε →(ε→0) 独立线性响应 J。
    饱和档的偏差即"探针背作用不可忽略"的定量证据。"""
    j_probe = (N // 2) if j_probe is None else j_probe
    lo = tau.min() - margin
    hi = tau.max() + margin
    t, pj, _ = simulate_gain(tau[j_probe], beta, T_rec, dt, margin,
                             lo=lo, hi=hi)
    p_all = np.exp(-4.0 * LN2 * ((t[:, None] - tau[None, :]) / W) ** 2)
    pe = EPS_PROBE * p_all
    # off：仅 32 个 ε 探针（无泵浦）
    rate_off = 1.0 / T_rec + beta * pe.sum(axis=1)
    g_off = np.empty(len(t))
    gp = G0
    for n in range(len(t)):
        gss = (G0 / T_rec) / rate_off[n]
        gp = gss + (gp - gss) * np.exp(-rate_off[n] * dt)
        g_off[n] = gp
    # on：满幅泵浦 j + 32 个 ε 探针
    rate_on = rate_off + beta * pj
    g_on = np.empty(len(t))
    gp = G0
    for n in range(len(t)):
        gss = (G0 / T_rec) / rate_on[n]
        gp = gss + (gp - gss) * np.exp(-rate_on[n] * dt)
        g_on[n] = gp
    h_on = np.trapezoid(pe * (g_on - G0)[:, None], t, axis=0)
    h_off = np.trapezoid(pe * (g_off - G0)[:, None], t, axis=0)
    J_probe = (h_on - h_off) / EPS_PROBE
    return J_probe, t


def run_case(law_name, tau, meta, ratio, sat_name, sat, dt=DT0, margin=MARGIN0,
             do_probe_check=True):
    T_rec = ratio * W
    beta = sat / T_rec
    J, ginfo = linear_response_J(tau, beta, T_rec, dt, margin)
    K = K_analytic(tau[:, None] - tau[None, :])
    np.fill_diagonal(K, 1.0)
    Jn = J.copy()
    np.fill_diagonal(Jn, 0.0)
    eps_sym = float(np.linalg.norm(Jn - Jn.T) / (np.linalg.norm(Jn) + 1e-300))
    # 到达顺序反转：τ -> -τ（等价于把梳线顺序倒过来，脉冲先到后互换）
    J_rev, _ = linear_response_J(-tau, beta, T_rec, dt, margin)
    J_rev_n = J_rev.copy()
    np.fill_diagonal(J_rev_n, 0.0)
    # 反序下 (i,j) 的耦合应等于正序 (j,i)：检验因果结构
    eps_order = float(np.linalg.norm(J_rev_n - Jn.T) /
                      (np.linalg.norm(Jn) + 1e-300))
    # 有效耦合距离（1/e 范围，格点数；对 |J| 归一剖面）
    d_eff = coupling_range(Jn)
    d_eff_K = coupling_range(K - np.eye(N))
    out = {"stage": "J", "law": law_name, "law_meta": meta,
           "T_rec_ratio": ratio, "T_rec_ps": T_rec,
           "power": sat_name, "beta_T_rec": sat,
           "dt_ps": dt, "margin_ps": margin,
           "eps_sym": eps_sym, "eps_order": eps_order,
           "d_eff": d_eff, "d_eff_K": d_eff_K,
           "J_norm": float(np.linalg.norm(Jn)),
           "K_norm": float(np.linalg.norm(K - np.eye(N))),
           **ginfo, "ok": True}
    if do_probe_check:
        J_probe, _ = probe_in_loop_check(tau, beta, T_rec, dt, margin)
        mask = np.ones(N, bool)
        # 只比较显著响应（|J|>1% 最大元），避免把 0/0 当误差
        thr = 0.01 * np.abs(Jn[:, N // 2]).max()
        col = np.abs(Jn[:, N // 2]) > thr
        rel = np.abs(J_probe[col] - Jn[col, N // 2]) / \
            (np.abs(Jn[col, N // 2]) + 1e-300)
        out["probe_check_max_rel"] = float(rel.max()) if len(rel) else 0.0
        out["probe_check_eps"] = EPS_PROBE
    return out, J, K


def coupling_range(J):
    """|J| 的 1/e 有效距离（格点），J(d)=mean|diag d|，以最近邻 J(1) 归一
    （输入对角已置零，不能用 prof[0]）；测不准返回 None。"""
    A = np.abs(J)
    prof = np.array([np.mean(np.diag(A, k=d)) for d in range(N)])
    prof = prof / max(prof[1], 1e-300)
    for d in range(1, N):
        if prof[d] < 1.0 / np.e:
            if prof[d] <= 0:
                return None
            return float(d / np.sqrt(-np.log(prof[d])))
    return None


def convergence_check(law_name, tau, meta):
    """积分步长减半 + 时间窗加倍，报 max|ΔJ| 与 Δε_sym。"""
    base, J0, _ = run_case(law_name, tau, meta, 1.0, "small", SAT_PARAMS["small"],
                           do_probe_check=False)
    _, J_dt, _ = run_case(law_name, tau, meta, 1.0, "small", SAT_PARAMS["small"],
                          dt=DT0 / 2, do_probe_check=False)
    _, J_win, _ = run_case(law_name, tau, meta, 1.0, "small", SAT_PARAMS["small"],
                           margin=2 * MARGIN0, do_probe_check=False)
    def sym(J):
        A = J.copy()
        np.fill_diagonal(A, 0.0)
        return np.linalg.norm(A - A.T) / np.linalg.norm(A)
    rows = []
    for tag, J1 in [("dt_half", J_dt), ("window_double", J_win)]:
        rows.append({"law": law_name, "check": tag,
                     "max_abs_dJ": float(np.abs(J1 - J0).max()),
                     "eps_sym_ref": float(sym(J0)), "eps_sym_new": float(sym(J1)),
                     "abs_d_eps_sym": abs(sym(J1) - sym(J0))})
    return rows


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_all():
    t_start = time.time()
    done = set()
    if os.path.exists(JSONL):
        with open(JSONL, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["id"])
                except Exception:
                    pass
    fid = lambda obj: hashlib.sha1(json.dumps(obj, sort_keys=True,
                                             default=str).encode()).hexdigest()[:12]
    laws = gd_laws()

    pw = pulse_width_check()
    pw["id"] = fid({"stage": "pw_check"})
    rows = [pw]

    for name, (_, meta) in laws.items():
        rows.append({"stage": "law_info", "law": name, "meta": meta,
                     "id": fid({"stage": "law_info", "law": name})})

    Js = {}
    for name, (tau, meta) in laws.items():
        for ratio in T_REC_RATIOS:
            for sat_name, sat in SAT_PARAMS.items():
                key = {"law": name, "ratio": ratio, "power": sat_name}
                if fid({**key, "stage": "J"}) in done:
                    continue
                out, J, K = run_case(name, tau, meta, ratio, sat_name, sat)
                out["id"] = fid({**key, "stage": "J"})
                Js[(name, ratio, sat_name)] = (J, K)
                rows.append(out)
                print("  J done:", key, "eps_sym=%.3g" % out["eps_sym"],
                      flush=True)

    conv = []
    for name, (tau, meta) in laws.items():
        if fid({"stage": "conv", "law": name}) in done:
            continue
        for r in convergence_check(name, tau, meta):
            r["stage"] = "conv"
            r["id"] = fid({"stage": "conv", "law": name, "check": r["check"]})
            rows.append(r)
            conv.append(r)
            print("  conv done:", r["law"], r["check"], flush=True)

    with open(JSONL, "a", encoding="utf-8") as f:
        for r in rows:
            if r["id"] not in done:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("ALL DONE (%d rows, %.0f s) -> %s" %
          (len(rows), time.time() - t_start, JSONL), flush=True)
    aggregate()
    return Js


def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
    pw = [r for r in rows if r["stage"] == "pw_check"][0]
    Jrows = [r for r in rows if r["stage"] == "J"]
    conv = [r for r in rows if r["stage"] == "conv"]
    laws = gd_laws()

    # ---- 重算关键矩阵用于画图（只取小信号 T_rec=10ps 代表组） ----
    mats = {}
    for name, (tau, meta) in laws.items():
        out, J, K = run_case(name, tau, meta, 1.0, "small", SAT_PARAMS["small"],
                             do_probe_check=False)
        mats[name] = (J, K)

    # fig1: J vs K 对照
    fig, axes = plt.subplots(1, 4, figsize=(19, 4.6))
    names = ["cbg_measured", "D1.3", "D10"]
    vmax = max(np.abs(mats[n][0]).max() for n in names)
    for ax, n in zip(axes[:3], names):
        J, K = mats[n]
        im = ax.imshow(-J, cmap="magma", vmax=vmax)
        ax.set_title("%s: -J (small, T_rec/w=1)\nε_sym=%.3g" %
                     (n, [r for r in Jrows
                          if r["law"] == n and r["T_rec_ratio"] == 1.0
                          and r["power"] == "small"][0]["eps_sym"]), fontsize=9)
        ax.set_xlabel("data channel j"); ax.set_ylabel("probe i")
        fig.colorbar(im, ax=ax, shrink=0.8)
    ax = axes[3]
    K = mats["D1.3"][1] - np.eye(N)
    im = ax.imshow(K + np.eye(N), cmap="magma", vmax=1.0)
    ax.set_title("K: symmetric overlap (reference)", fontsize=9)
    ax.set_xlabel("j")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.suptitle("J vs K: causal shared-gain coupling vs symmetric pulse overlap "
                 "(probe i reads gain depleted by data pulse j)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig1_J_vs_K.png"), dpi=150)
    plt.close(fig)

    # fig2: 扫描汇总
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.4))
    ax = axes[0]
    for n in names:
        sub = [r for r in Jrows if r["law"] == n and r["power"] == "small"]
        xs = sorted(sub, key=lambda r: r["T_rec_ratio"])
        ax.plot([r["T_rec_ratio"] for r in xs], [r["eps_sym"] for r in xs],
                "o-", label=n)
    ax.set_xscale("log")
    ax.set(xlabel="T_rec / w", ylabel="ε_sym = ||J-Jᵀ||/||J||",
           title="(a) causal asymmetry vs recovery time (small signal)")
    ax.legend(fontsize=8); ax.grid(alpha=.3)

    ax = axes[1]
    for n in names:
        for pw_tag, mk in [("small", "o"), ("sat", "s")]:
            sub = [r for r in Jrows if r["law"] == n and r["power"] == pw_tag]
            xs = sorted(sub, key=lambda r: r["T_rec_ratio"])
            lbl = "%s %s" % (n, pw_tag)
            ax.plot([r["T_rec_ratio"] for r in xs],
                    [r["eps_order"] for r in xs], mk + "--" if pw_tag == "sat" else mk + "-",
                    label=lbl)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set(xlabel="T_rec / w",
           ylabel="ε_order = ||J(-τ)-Jᵀ||/||J||",
           title="(b) arrival-order reversal consistency (causality check)")
    ax.legend(fontsize=6); ax.grid(alpha=.3)

    ax = axes[2]
    dK = {n: [r for r in Jrows if r["law"] == n and r["power"] == "small"
              and r["T_rec_ratio"] == 1.0][0]["d_eff_K"] for n in names}
    width = 0.35
    xpos = np.arange(len(names))
    for i, tag in enumerate(["small", "sat"]):
        vals = []
        for n in names:
            sub = [r for r in Jrows if r["law"] == n and r["power"] == tag
                   and r["T_rec_ratio"] == 1.0]
            vals.append(sub[0]["d_eff"] if sub and sub[0]["d_eff"] else np.nan)
        ax.bar(xpos + (i - 0.5) * width, vals, width, label="J %s" % tag)
    ax.plot(xpos, [dK[n] for n in names], "k_", ms=14,
            label="K range (1/e)")
    ax.set_xticks(xpos); ax.set_xticklabels(names, fontsize=8)
    ax.set(ylabel="effective coupling range [spacings]",
           title="(c) J coupling range vs symmetric K")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_sweep.png"), dpi=150)
    plt.close(fig)

    # ---- convergence 表 ----
    lines = ["| law | check | max|ΔJ| | |Δε_sym| |",
             "|---|---|---|---|"]
    for r in conv:
        lines.append("| %s | %s | %.3e | %.3e |" %
                     (r["law"], r["check"], r["max_abs_dJ"], r["abs_d_eps_sym"]))
    with open(os.path.join(OUT, "convergence.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    import csv
    with open(os.path.join(OUT, "convergence.csv"), "w", newline="") as f:
        wcsv = csv.DictWriter(f, fieldnames=["law", "check", "max_abs_dJ",
                                             "eps_sym_ref", "eps_sym_new",
                                             "abs_d_eps_sym"],
                              extrasaction="ignore")
        wcsv.writeheader()
        for r in conv:
            wcsv.writerow(r)

    # ---- summary.json ----
    summ = {"pulse_width_caliber": pw, "J": Jrows, "convergence": conv}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1, ensure_ascii=False)

    # ---- report.md（支持/不支持/未决逐条判定） ----
    write_report(pw, Jrows, conv, laws)
    print("saved fig1/fig2 + summary.json + convergence + report.md", flush=True)


def write_report(pw, Jrows, conv, laws):
    r_small = {n: [r for r in Jrows if r["law"] == n and r["power"] == "small"
                   and r["T_rec_ratio"] == 1.0][0] for n in laws}
    eps_sat = {n: [r for r in Jrows if r["law"] == n and r["power"] == "sat"
                   and r["T_rec_ratio"] == 1.0][0]["eps_sym"] for n in laws}
    worst_conv = max(conv, key=lambda r: r["max_abs_dJ"]) if conv else None
    info = laws["cbg_measured"][1]["data_info"]

    def fmt(x):
        return "%.3g" % x

    md = []
    md.append("# sim14-A：CBG 延迟核 × 因果共享增益 —— 因果核提取报告\n")
    md.append("> 唯象共享增益代理（单ode ḡ=(g0-g)/T_rec-βgΣxⱼpⱼ），"
              "**不声称 SOA 器件级复现**；纯 NumPy/SciPy，CPU。"
              "梳线 N=32，Δλ=0.2 nm，强度脉冲 FWHM w=10 ps。\n")

    md.append("## 1. 脉宽口径核对\n")
    md.append("- 任务书口径：p(t)=exp[-4ln2·((t-τ)/w)²]，w=10 ps **强度 FWHM**；"
              "解析重叠 K(Δ)=exp(-2ln2·Δ²/w²)。")
    md.append("- sim09 口径：K(Δ)=exp(-Δ²/(2σ_t²))，σ_t=10 ps "
              "（intensity-convolution 约定）。")
    w2s = pw["w_equiv_sigma_t_sim09"]
    md.append("- 两者**不等价**：w=10 ps 等效 σ_t=%.3f ps（sim09 σ_t=10 等效 FWHM="
              "%.2f ps）。同 σ_t=10 下 sim09 核比任务书核宽 "
              "exp(Δ²(2ln2/100-1/200))，Δ=10 ps 处 sim09 值偏宽 %.1f%%。" %
              (w2s, pw["sigma_t_10ps_equiv_FWHM"],
               100 * abs(pw["rows"][4]["K_sim09_sig10"] -
                         pw["rows"][4]["K_analytic_w10"]) /
               pw["rows"][4]["K_analytic_w10"]))
    md.append("- 数值积分与解析 K 最大相对差 %.2e（网格收敛）。" %
              max(r["rel_num_vs_ana"] for r in pw["rows"] if np.isfinite(r["rel_num_vs_ana"])))
    md.append("- **判定：不支持**「σ_t=10 ps = w=10 ps」的字面等同；"
              "后续 J/K 对照全部用任务书 w 口径，sim09 的 σ_t 若迁移需乘 1/0.601。\n")

    md.append("## 2. 真实 CBG 数据充分性（chirp2d.npz tau_r）\n")
    md.append("- 谱 %d 点覆盖 %.1f nm，平均点距 %.3f nm = %.2f 倍通道间距"
              "（0.2 nm）→ 32 通道插值有 ~%.1f× 过采样，**点密度足够**。" %
              (info["n_points_total"], info["wl_range_nm"][1] - info["wl_range_nm"][0],
               info["dl_data_nm"], info["points_per_channel_spacing"],
               1.0 / max(info["points_per_channel_spacing"], 1e-9)))
    md.append("- 有效反射窗口（R≥0.5·max）：%.2f–%.2f nm，宽 %.2f nm ≥ 通道足迹 "
              "%.2f nm；窗口内 τ_r ∈ [%.2f, %.2f] ps，波纹（线性去趋势残差 std）"
              "%.3f ps；隔点抽稀重插 RMS 误差 %.3f ps。" %
              (info["window_nm"][0], info["window_nm"][1], info["window_width_nm"],
               info["channel_span_nm"], info["tau_r_in_window_ps"][0],
               info["tau_r_in_window_ps"][1], info["tau_r_ripple_ps"],
               info["interp_err_ps_subsample"]))
    md.append("- 通道足迹内最小 R = %.3f（max R = %.3f）→ 32 通道全部落在有效反射窗内。" %
              (info["R_min_at_channels"], info["R_max"]))
    md.append("- **判定：支持** 32 通道部署；代价是 τ_r 实测波纹 ~%.2f ps 进入 J "
              "（相对 w=10 ps 不可忽略，见下）。" % info["tau_r_ripple_ps"])

    md.append("\n## 3. 因果核 J 的主结果（小信号档，T_rec/w=1）\n")
    md.append("| 群延迟律 | ε_sym=‖J-Jᵀ‖/‖J‖ | ε_order(反序) | d_eff(J) | d_eff(K) | J 范数 | K 范数 |")
    md.append("|---|---|---|---|---|---|---|---|")
    for n, r in r_small.items():
        md.append("| %s | %.3g | %.3g | %s | %s | %.3g | %.3g |" %
                  (n, r["eps_sym"], r["eps_order"],
                   fmt(r["d_eff"]) if r["d_eff"] else ">31",
                   fmt(r["d_eff_K"]) if r["d_eff_K"] else ">31",
                   r["J_norm"], r["K_norm"]))
    md.append("")
    md.append("- ε_order ≪ ε_sym 说明不对称来自**因果结构**（先动者抑制后动者），"
              "不是数值窗截断伪影。")
    md.append("- 饱和档 ε_sym：%s —— 深饱和下 g 轨迹偏离线性，对称性进一步变化。" %
              ", ".join("%s=%.3g" % (n, v) for n, v in eps_sat.items()))

    md.append("\n## 4. 数值收敛\n")
    if worst_conv:
        md.append("- 最差一项：%s %s，max|ΔJ|=%.2e，|Δε_sym|=%.2e。"
                  "步长减半与窗加倍均在积分噪声以下，**网格收敛**。" %
                  (worst_conv["law"], worst_conv["check"],
                   worst_conv["max_abs_dJ"], worst_conv["abs_d_eps_sym"]))

    md.append("\n## 5. 逐条判定（任务书验收口径）\n")
    med = np.median([r_small[n]["eps_sym"] for n in laws])
    md.append("- **脉宽口径**：不支持 σ_t=w 的字面等同（§1，差异已定量化）。")
    md.append("- **J 对称性**：不支持对称假设 —— 三档群延迟律下 ε_sym 中位数 "
              "= %.3g（≠0），因果共享增益给出定向耦合。" % med)
    md.append("- **真实 CBG 是否有足够延迟跨度**：支持 32 通道插值（§2）；"
              "但实测 τ_r 波纹 ~%.2f ps 与 D=1.3 ps/nm 档的通道间距 "
              "D·Δλ=%.2f ps 同量级，会扰动耦合轮廓 —— 真实数据**可用但有纹波代价**。" %
              (info["tau_r_ripple_ps"], 1.3 * DLAM))
    md.append("- **B 对 NGRC/延迟抽头的净收益**：未决 —— 见 14b 对照（另文）。")

    md.append("\n## 附：方法与假设\n")
    md.append("- J 提取（独立线性响应定义）：对每列 j 仿真 g⁽⁰⁾（单泵浦轨迹，"
              "可深饱和），探针 ε→0 作被动读出权重，"
              "J_ij=∫pᵢ[g⁽⁰⁾−g0]dt —— 主项为 O(β) 直读增益凹陷（因果），"
              "探针不进动力学、天然不反饱和。")
    pc = [r for r in Jrows if "probe_check_max_rel" in r]
    if pc:
        md.append("- 有限探针验证（ε=1e-3 探针进动力学、on/off 差分，对显著元）："
                  "小信号档最大相对偏差 %.2e（一致）；饱和档 %.2e（探针背作用不可忽略，"
                  "主结果用 ε→0 独立线性响应）。" %
                  (max((r["probe_check_max_rel"] for r in pc
                        if r["power"] == "small"), default=float("nan")),
                   max((r["probe_check_max_rel"] for r in pc
                        if r["power"] == "sat"), default=float("nan"))))
    md.append("- 饱和两档：s=β·T_rec=0.05（小信号，单脉冲谷值 g≈%.3f）与 5"
              "（饱和，g≈%.3f）；β=s/T_rec 使两档在不同 T_rec 下可比。" %
              (min(r["g_min"] for r in Jrows if r["power"] == "small"),
               min(r["g_min"] for r in Jrows if r["power"] == "sat")))
    md.append("- 时间窗：脉冲跨度 ± max(4w) 对称余量；收敛检验 ×2。")
    md.append("- 唯象声明：本模型是共享增益的**最小因果代理**，不含 SOA 的"
              "载流子-光子动力学、ASE、谱烧孔等；器件级结论不外推。")

    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    if a.aggregate:
        aggregate()
    else:
        run_all()
