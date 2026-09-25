# -*- coding: utf-8 -*-
"""L3: C1 真实信号链核查（防幻觉核查，2026-09-25，Stage 3 预备）。

C1 原文：TFLN 啁啾光栅延迟-损耗 FoM = 424 ps/dB（α=0.033 dB/mm 保守值），
且 M1 光子链（压缩→spike→蓄水池→慢读出）成立。
已知缺口（generate_report.py §限制）：spike 由解析高斯峰生成，未用真实光栅时域输出。

本脚本：
  1. 用实测 tau_r(λ)（chirp2d.npz，FDTD）重建复反射谱 H(ω)=sqrt(R)·exp(iφ)，
     φ 由 tau_r 数值积分得到 —— 替换解析高斯 spike，得到真实压缩脉冲 p_real(t)；
  2. 用 p_real 替换 comprehensive_simulation.generate_scene 里的高斯峰，
     原协议（等能量/等质心三类、40 延迟抽头、漏电慢读出）重跑蓄水池链；
  3. 重算 FoM 链：解析值 424.5 ps/dB vs 实测摆幅/损耗口径（含平台截断效率
     与 R<1 反射惩罚），判定 424 在真实信号链下是否成立。

运行：本机默认 python（CPU，秒级-分钟级）。输出 results/verify/l3/
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "l3")
os.makedirs(OUT, exist_ok=True)

import sys
sys.path.insert(0, os.path.join(ROOT, "lumerical"))
import comprehensive_simulation as cs   # 复用 reservoir/readout/eval 协议函数

C0 = 299792458.0
LAMBDA0 = 1.55e-6
OMEGA0 = 2 * np.pi * C0 / LAMBDA0
RES = os.path.join(ROOT, "lumerical", "results")

ALPHA_DB_PER_M = 0.033 * 1e3          # 0.033 dB/mm 保守深刻蚀值
N_G_CLAIM = 2.1                       # 申报口径
N_G_MEAS = 2.10457                    # V2 复核（ref_raw 重算）


# ---------------------------------------------------------------------------
# 1. 真实反射谱重建 + 真实压缩脉冲
# ---------------------------------------------------------------------------

def load_grating_response():
    """与 comprehensive_simulation.load_grating_response 相同的重建，直接读 npz。"""
    d = np.load(os.path.join(RES, "chirp2d.npz"))
    f, T, tau_r = d["f"], d["T"], d["tau_r"]
    order = np.argsort(f)
    f, T, tau_r = f[order], T[order], tau_r[order]
    omega = 2 * np.pi * f
    R = np.clip(1.0 - T, 0, None)
    domega = np.diff(omega, prepend=omega[0])
    phi = np.cumsum(tau_r * domega)
    phi = np.unwrap(phi - phi[0])
    H = np.sqrt(R) * np.exp(1j * phi)
    return omega, H, R, tau_r, d


def real_compressed_pulse():
    """单目标、零延迟，经实测 H 匹配滤波 -> 真实压缩脉冲形状（峰值归一）。"""
    omega, H, R, tau_r, d = load_grating_response()
    wl_nm = C0 / (omega / (2 * np.pi)) * 1e9
    platform = R > 0.9
    phi2 = np.polyfit(omega[platform] - OMEGA0, tau_r[platform], 1)[0]
    chirp_rate = -1.0 / phi2

    N = 16384
    dt = 2e-15
    t = (np.arange(N) - N // 2) * dt
    Omega_shift = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(N, dt))
    H_shift = np.interp(OMEGA0 + Omega_shift, omega, H, left=0, right=0)
    H_fft = np.fft.ifftshift(H_shift)

    B = 2 * np.pi * 8.0e12
    T_chirp = B / chirp_rate
    E_rx = np.exp(-(t)**2 / (2 * (T_chirp / 2.5)**2)) * np.exp(1j * 0.5 * chirp_rate * t**2)
    E_comp = np.fft.ifft(np.fft.fft(E_rx) * np.conj(H_fft))
    # E_comp 与单调递增的 t 天然配对；fftshift 版仅用于 FWHM 测量，
    # 绝不能把 fftshift 后的非单调 t 传给 np.interp（会静默得到全零）。
    I_comp = np.abs(E_comp)**2
    p_real = I_comp / I_comp.max()
    t_shift = np.fft.fftshift(t)

    meta = {
        "phi2": float(phi2), "chirp_rate": float(chirp_rate),
        "T_chirp_ps": float(T_chirp * 1e12),
        "platform_width_nm": float(wl_nm[platform].max() - wl_nm[platform].min()),
        "platform_R_mean": float(R[platform].mean()),
        "platform_R_min": float(R[platform].min()),
        "swing_platform_ps": float(tau_r[platform].max() * 1e12 - tau_r[platform].min() * 1e12),
        "D_ps_per_nm": float(np.polyfit(wl_nm[platform], tau_r[platform] * 1e12, 1)[0]),
        "pulse_fwhm_ps": float(cs.fwhm(t_shift, np.fft.fftshift(I_comp) / I_comp.max()) * 1e12),
    }
    return t, p_real, meta


# ---------------------------------------------------------------------------
# 2. 蓄水池链：真实脉冲替换高斯 spike（协议与 comprehensive_simulation 一致）
# ---------------------------------------------------------------------------

def make_generate_scene(pulse_t, pulse_shape):
    """与 cs.generate_scene 相同的三类等能量等质心场景，仅脉冲形状替换。"""
    p_t = np.asarray(pulse_t)
    p_s = np.asarray(pulse_shape)

    def gen(t, class_id, rng, timing_jitter=0.02, amp_noise=0.05):
        if class_id == 0:
            comps = [(2.0e-12, 1.0)]
        elif class_id == 1:
            comps = [(1.5e-12, 0.5), (2.5e-12, 0.5)]
        else:
            comps = [(1.4e-12, 1 / 3), (2.0e-12, 1 / 3), (2.6e-12, 1 / 3)]
        spikes = np.zeros_like(t)
        for dly, a in comps:
            dly += rng.normal(0, timing_jitter * 1e-12)
            a *= rng.uniform(1 - amp_noise, 1 + amp_noise)
            spikes += a * np.interp(t - dly, p_t, p_s, left=0.0, right=0.0)
        return spikes
    return gen


def reservoir_rerun(t, dt, generate_scene, label):
    """复刻 cs.reservoir_analysis 的核心协议（同种子/样本数/抽头/漏电参数）。"""
    rng = np.random.default_rng(2026)
    n_samples, n_taps = 300, 40
    delay_values = np.linspace(0.1e-12, 2.0e-12, n_taps)
    weights = rng.normal(0, 2.0, n_taps)
    tau_leak = 1.0e-9
    sigma_ro_rel = 0.02

    X = np.zeros((n_samples, len(t)))
    y = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        y[i] = i % 3
        X[i] = generate_scene(t, y[i], rng)

    S = np.zeros((n_samples, n_taps))
    for i in range(n_samples):
        S[i] = cs.integrate_states(cs.reservoir_states(X[i], delay_values, weights, dt), dt, t)
    sigma_ro = sigma_ro_rel * S.std()

    _, direct_acc = cs.eval_features(X.sum(axis=1, keepdims=True) * dt, y)
    idx_fs = np.linspace(0, len(t) - 1, 32).astype(int)
    fast_feats = [cs.reservoir_states(X[i], delay_values, weights, dt)[idx_fs, :].flatten()
                  for i in range(n_samples)]
    _, fast_acc = cs.eval_features(fast_feats, y)
    _, leaky_acc = cs.eval_features(cs.leaky_held_readout(S, 0.0, tau_leak, sigma_ro, rng), y)
    S_lin = np.zeros((n_samples, n_taps))
    for i in range(n_samples):
        S_lin[i] = cs.integrate_states(
            cs.reservoir_states(X[i], delay_values, weights, dt, nonlin=lambda u: u), dt, t)
    _, linear_acc = cs.eval_features(
        cs.leaky_held_readout(S_lin, 0.0, tau_leak, sigma_ro_rel * S_lin.std(), rng), y)

    # 慢读出保持曲线（tau_leak = 1 ns 档）
    readout_delays = np.logspace(-12, -8, 21)
    rd_accs = [cs.eval_features(cs.leaky_held_readout(S, rd, tau_leak, sigma_ro, rng), y)[1]
               for rd in readout_delays]
    # 时序抖动扫描（真实脉冲下的稳健性）
    jitters = np.linspace(0, 0.20, 11)
    jit_accs = []
    for jit in jitters:
        Sj = np.zeros((n_samples, n_taps))
        for i in range(n_samples):
            sj = generate_scene(t, y[i], rng, timing_jitter=jit)
            Sj[i] = cs.integrate_states(cs.reservoir_states(sj, delay_values, weights, dt), dt, t)
        _, a = cs.eval_features(
            cs.leaky_held_readout(Sj, 0.0, tau_leak, sigma_ro_rel * Sj.std(), rng), y)
        jit_accs.append(a)

    print("[%s] direct=%.3f fast=%.3f leaky=%.3f linear=%.3f" %
          (label, direct_acc, fast_acc, leaky_acc, linear_acc))
    return {"label": label, "direct_acc": float(direct_acc), "fast_acc": float(fast_acc),
            "leaky_acc": float(leaky_acc), "linear_acc": float(linear_acc),
            "readout_delays_ns": (readout_delays * 1e9).tolist(),
            "readout_accs": [float(a) for a in rd_accs],
            "jitters_ps": jitters.tolist(),
            "jit_accs": [float(a) for a in jit_accs]}


# ---------------------------------------------------------------------------
# 3. FoM 链重算
# ---------------------------------------------------------------------------

def fom_chain(meta, L_dev=250e-6):
    alpha = ALPHA_DB_PER_M
    swing_ideal = 2 * N_G_MEAS * L_dev / C0                     # 理想反射光栅摆幅
    swing_meas = meta["swing_platform_ps"] * 1e-12              # R>0.9 平台实测摆幅
    eta = swing_meas / swing_ideal                              # 平台截断效率
    prop_loss = alpha * L_dev                                   # dB
    r_penalty = -10 * np.log10(meta["platform_R_mean"])         # R<1 固定惩罚 dB

    fom_claim = 2 * N_G_CLAIM / (C0 * alpha) * 1e12             # 424.5 申报锚点
    fom_analytic_meas_ng = 2 * N_G_MEAS / (C0 * alpha) * 1e12
    fom_device = swing_meas / prop_loss * 1e12                  # 器件级（传播损耗口径）
    fom_device_with_r = swing_meas / (prop_loss + r_penalty) * 1e12

    # 应用级：3 dB 传播损耗预算（m3b 口径），摆幅随 L 缩放
    L_app = 3.0 / alpha
    swing_app = 2 * N_G_MEAS * L_app / C0 * eta
    fom_app = swing_app / (3.0 + r_penalty) * 1e12

    out = {
        "alpha_dB_per_m": alpha, "n_g_claim": N_G_CLAIM, "n_g_meas": N_G_MEAS,
        "L_device_um": L_dev * 1e6,
        "swing_ideal_ps": swing_ideal * 1e12, "swing_meas_ps": swing_meas * 1e12,
        "platform_efficiency_eta": float(eta),
        "prop_loss_dB": prop_loss, "R_penalty_dB": float(r_penalty),
        "FoM_claim_ps_per_dB": fom_claim,
        "FoM_analytic_meas_ng_ps_per_dB": fom_analytic_meas_ng,
        "FoM_device_real_chain_ps_per_dB": fom_device,
        "FoM_device_real_chain_with_R_ps_per_dB": fom_device_with_r,
        "FoM_app_3dB_budget_ps_per_dB": fom_app,
        "app_L_cm": L_app * 100, "app_swing_ps": swing_app * 1e12,
        "app_range_window_m": C0 * swing_app / 2,
    }
    print("\n[FoM chain]")
    print("  claim (n_g=2.1):            %.1f ps/dB" % fom_claim)
    print("  analytic (n_g=2.1046):      %.1f ps/dB" % fom_analytic_meas_ng)
    print("  device real chain:          %.1f ps/dB (eta=%.3f, prop loss %.5f dB)"
          % (fom_device, eta, prop_loss))
    print("  device real chain +R<1:     %.1f ps/dB (R penalty %.3f dB)"
          % (fom_device_with_r, r_penalty))
    print("  app scale (3dB budget):     %.1f ps/dB (swing %.0f ps, window %.3f m)"
          % (fom_app, swing_app * 1e12, C0 * swing_app / 2))
    return out


# ---------------------------------------------------------------------------

def main():
    t_pulse, p_real, meta = real_compressed_pulse()
    meta["pulse_floor_median"] = float(np.median(p_real))
    meta["pulse_energy_frac_within_1ps"] = float(
        p_real[np.abs(t_pulse - t_pulse[np.argmax(p_real)]) < 1e-12].sum() / p_real.sum())
    print("[real pulse] fwhm=%.3f ps, platform %.1f nm, R_mean=%.3f, swing=%.2f ps, D=%.4f ps/nm"
          % (meta["pulse_fwhm_ps"], meta["platform_width_nm"], meta["platform_R_mean"],
             meta["swing_platform_ps"], meta["D_ps_per_nm"]))

    # 高斯基线（同协议重跑，对齐随机种子消耗顺序）+ 真实脉冲（原始与阈值化两臂）
    def gauss_scene(t, class_id, rng, timing_jitter=0.02, amp_noise=0.05):
        return cs.generate_scene(t, class_id, rng, timing_jitter, amp_noise)

    N, dt = 16384, 2e-15
    t = (np.arange(N) - N // 2) * dt
    res_gauss = reservoir_rerun(t, dt, gauss_scene, "gaussian-baseline")
    res_real = reservoir_rerun(t, dt, make_generate_scene(t_pulse, p_real), "real-grating-pulse")
    # 阈值化臂：与链中「压缩→阈值→spike」一致（comprehensive 用 0.15 峰值阈值）
    p_thr = np.where(p_real > 0.15, p_real, 0.0)
    res_thr = reservoir_rerun(t, dt, make_generate_scene(t_pulse, p_thr),
                              "real-grating-pulse-thr0.15")

    fom = fom_chain(meta)

    out = {"pulse_meta": meta, "reservoir_gauss": res_gauss,
           "reservoir_real": res_real, "reservoir_real_thr015": res_thr,
           "fom_chain": fom,
           "baseline_comprehensive_npz": {
               "direct_acc": 0.267, "fast_acc": 1.0, "leaky_acc": 1.0, "linear_acc": 0.4}}
    with open(os.path.join(OUT, "l3_real_chain.json"), "w", encoding="utf-8") as fp:
        json.dump(out, fp, indent=1, ensure_ascii=False)

    # ---- 图 ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    tg = t * 1e12
    gauss = np.exp(-(t / 0.10e-12)**2)
    tp_ps = (t_pulse - t_pulse[np.argmax(p_real)]) * 1e12
    axes[0].plot(tg, gauss / gauss.max(), label="gaussian (old)", lw=1.5)
    axes[0].plot(tp_ps, p_real, label="real grating pulse (new)", lw=1.2)
    axes[0].plot(tp_ps, p_thr, label="real, thr 0.15", lw=1.0, ls="--")
    axes[0].set_xlim(-1.5, 2.5); axes[0].set_xlabel("t (ps)"); axes[0].set_ylabel("norm. power")
    axes[0].set_title("spike shape: analytic vs measured-chain"); axes[0].legend(); axes[0].grid(alpha=.3)
    for res, mk, lb in [(res_gauss, "o--", "gaussian"), (res_real, "s-", "real"),
                        (res_thr, "^-", "real thr0.15")]:
        axes[1].semilogx(res["readout_delays_ns"], res["readout_accs"], mk, ms=3, label=lb)
    axes[1].axhline(1/3, color="k", ls=":", alpha=.4)
    axes[1].set_xlabel("readout delay (ns)"); axes[1].set_ylabel("test acc")
    axes[1].set_title("slow-readout survival"); axes[1].legend(); axes[1].grid(alpha=.3)
    for res, mk, lb in [(res_gauss, "o--", "gaussian"), (res_real, "s-", "real"),
                        (res_thr, "^-", "real thr0.15")]:
        axes[2].plot(res["jitters_ps"], res["jit_accs"], mk, ms=3, label=lb)
    axes[2].axhline(1/3, color="k", ls=":", alpha=.4)
    axes[2].set_xlabel("timing jitter (ps)"); axes[2].set_ylabel("test acc")
    axes[2].set_title("jitter robustness"); axes[2].legend(); axes[2].grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "l3_real_chain.png"), dpi=150)
    print("saved l3_real_chain.json + l3_real_chain.png")


if __name__ == "__main__":
    main()
