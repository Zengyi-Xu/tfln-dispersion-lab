# -*- coding: utf-8 -*-
"""
A 组容差仿真（纯 TMM/解析，无需 Lumerical）——KGFP Concept Note Objective 1 支撑数据

模型：与 lab-note.ipynb §21 相同的啁啾光栅 TMM（有效指数近似，无耗散）。
四组扫描：
  A5 长度外推：固定啁啾率 C，L = 0.25 -> 20 mm
     -> D vs L、延迟摆幅 vs L（校验 Δτ = 2 n_g L / c）、ripple 随 L 增长
  A3 相位误差：逐片 λ_B 白噪声抖动 σ_λB
     -> ripple(σ)、ripple(L) @ 固定 σ；对照 M1 的 0.1 ps 抖动容限
  A6 切趾：κ(z) 均匀 / 线性 / 高斯 / 升余弦
     -> ripple 抑制 vs 摆幅损失
  A4 温漂：dn/dT = 4e-5/K（LN 热光系数）
     -> 均匀温漂的 τ 平移（解析 + TMM 验证）；线性温度梯度的啁啾畸变 -> ripple

输出：results/tolerance_scan.npz + 控制台摘要 + results/tolerance_scan.png
运行：python simulations/02_tolerance_scan.py   （本机默认 python 即可）
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results")
os.makedirs(OUT, exist_ok=True)

C0 = 299792458.0
N_EFF = 2.2            # 与 lab-note §21 一致（无色散模型：n_g = n_eff）
KAPPA0 = 5e3           # 1/m，局域带隙 ~1.7 nm
C_NM_PER_MM = 12.0     # 啁啾率：30 nm / 2.5 mm（lab-note §21 设计）
DNDT = 4e-5            # LN 热光系数


# ---------------- TMM 核心（对波长分块向量化） ----------------
def tmm_reflect(lam, lam_b_z, kappa_z, dz, block=2000):
    """分段均匀 2x2 传递矩阵连乘，返回 r(λ)。lam_b_z/kappa_z: (N,)"""
    N = len(lam_b_z)
    r = np.empty(len(lam), complex)
    for b0 in range(0, len(lam), block):
        lb = lam[b0:b0 + block]
        delta = 2 * np.pi * N_EFF * (1.0 / lb[None, :] - 1.0 / lam_b_z[:, None])
        kap = kappa_z[:, None]
        gam = np.sqrt(kap**2 - delta**2 + 0j)
        s = np.sinh(gam * dz) / gam
        ch = np.cosh(gam * dz)
        a11 = ch - 1j * delta * s
        a12 = -1j * kap * s
        a21 = 1j * kap * s
        a22 = ch + 1j * delta * s
        t11 = np.ones(len(lb), complex); t12 = np.zeros(len(lb), complex)
        t21 = np.zeros(len(lb), complex); t22 = np.ones(len(lb), complex)
        for j in range(N):
            t11, t12, t21, t22 = (a11[j] * t11 + a12[j] * t21,
                                  a11[j] * t12 + a12[j] * t22,
                                  a21[j] * t11 + a22[j] * t21,
                                  a21[j] * t12 + a22[j] * t22)
        r[b0:b0 + block] = -t21 / t22
    return r


def spectrum(lam_b0, L, chirp_nm, kappa_prof, sigma_lamb=0.0, seed=0,
             extra_lamb_z=None, n_lam=None, kappa0=KAPPA0):
    """返回 (lam, R, tau)。kappa_prof: callable(z, L, kappa0) -> kappa"""
    N = max(400, int(round(L / (2.5e-3 / 800))))   # 与 2.5mm/800 片同分辨率
    dz = L / N
    z = (np.arange(N) + 0.5) * dz
    C = chirp_nm * 1e-9 / L
    lam_b_z = lam_b0 + C * z
    if extra_lamb_z is not None:
        lam_b_z = lam_b_z + extra_lamb_z(z)
    if sigma_lamb > 0:
        lam_b_z = lam_b_z + np.random.default_rng(seed).normal(0, sigma_lamb, N)
    kappa_z = kappa_prof(z, L, kappa0)

    gap_nm = lam_b0**2 * kappa0 / (2 * np.pi * N_EFF) * 1e9
    if n_lam is None:
        n_lam = int(np.clip(chirp_nm * 120, 4000, 12000))
        # 群延迟解缠绕要求 tau*Δf < pi/2：按几何摆幅加密波长采样
        swing_s = 2 * N_EFF * L / C0
        span_f = C0 * chirp_nm * 1e-9 / lam_b0**2
        n_lam = max(n_lam, min(60000, int(3 * swing_s * span_f) + 1))
    lam = np.linspace(lam_b0 - 2e-9, lam_b0 + (chirp_nm + 2) * 1e-9, n_lam)
    r = tmm_reflect(lam, lam_b_z, kappa_z, dz)
    R = np.abs(r)**2
    phi = np.unwrap(np.angle(r))
    tau = -np.gradient(phi, 2 * np.pi * C0 / lam)

    band = ((lam > lam_b0 + 2 * gap_nm * 1e-9)
            & (lam < lam_b0 + (chirp_nm - 2 * gap_nm) * 1e-9) & (R > 0.5))
    if band.sum() < 50:
        return lam, R, tau, None
    p = np.polyfit(lam[band], tau[band], 1)
    resid = tau[band] - np.polyval(p, lam[band])
    met = {
        "D": p[0] * 1e-3,                       # s/m -> ps/nm: *1e12 s/ps /1e9 m/nm... 见下
        "ripple_pp": (resid.max() - resid.min()) * 1e12,   # ps
        "ripple_std": resid.std() * 1e12,                  # ps
        "swing": (tau[band].max() - tau[band].min()) * 1e12,  # ps
        "R_band_mean": R[band].mean(),
        "band_nm": (lam[band].max() - lam[band].min()) * 1e9,
    }
    met["D"] = p[0] * 1e12 / 1e9                # s/m -> ps/nm
    met["swing_geo"] = 2 * N_EFF * L / C0 * 1e12
    return lam, R, tau, met


# ---------------- 切趾窗 ----------------
def kappa_uniform(z, L, kappa0=KAPPA0):
    return np.full_like(z, kappa0)


def kappa_linear(z, L, kappa0=KAPPA0):
    return kappa0 * np.minimum(1.0, 2.5 * (1 - np.abs(2 * z / L - 1)))


def kappa_gauss(z, L, kappa0=KAPPA0):
    return kappa0 * np.exp(-((z / L - 0.5) / 0.25)**2)


def kappa_cosine(z, L, kappa0=KAPPA0):
    return kappa0 * np.sin(np.pi * z / L)**2


def main():
    lam_b0 = 1535e-9
    lambda_B_fdtd = 1565.5e-9   # chirp2d 的中心波长（2×2.02×387.5nm）
    summary = {}

    print("=" * 70)
    print("A5 长度外推（C = %.0f nm/mm 固定）" % C_NM_PER_MM)
    print("=" * 70)
    # 短长度在 C=12nm/mm 下啁啾总量 < 4×局域带隙(~1.7nm)，无平台区，从 1mm 起
    Ls_mm = [1.0, 2.5, 5.0, 10.0, 20.0]
    a5 = []
    for Lmm in Ls_mm:
        chirp = C_NM_PER_MM * Lmm
        _, _, _, m = spectrum(lam_b0, Lmm * 1e-3, chirp, kappa_uniform)
        assert m is not None, "band empty at L=%g" % Lmm
        a5.append(m)
        print("  L = %6.2f mm: D = %8.2f ps/nm, 摆幅 = %7.1f ps "
              "(几何 %7.1f), ripple_pp = %6.2f ps, R_band = %.2f"
              % (Lmm, m["D"], m["swing"], m["swing_geo"],
                 m["ripple_pp"], m["R_band_mean"]))
    summary["a5_L_mm"] = np.array(Ls_mm)
    for k in ("D", "swing", "swing_geo", "ripple_pp"):
        summary["a5_" + k] = np.array([m[k] for m in a5])

    # FDTD 交叉校验点：250 µm, Λ 啁啾 17.3 nm -> λ 啁啾 ~80 nm（chirp2d regime）
    # 该区啁啾极快（320 nm/mm），局域有效 κL 小，需用 FDTD 对应的 κ≈4dn/λ_B≈5.1e4/m
    _, _, _, m_fdtd = spectrum(lam_b0, 250e-6, 80.0, kappa_uniform,
                               kappa0=4 * 0.02 / lambda_B_fdtd)
    print("  [交叉校验] L=0.25mm, chirp=80nm: D = %.3f ps/nm "
          "(FDTD chirp2d 实测 0.051)" % m_fdtd["D"])
    summary["a5_fdtd_check_D"] = m_fdtd["D"]

    print("=" * 70)
    print("A3 相位误差（λ_B 逐片抖动）")
    print("=" * 70)
    L_ref = 2.5e-3
    chirp_ref = C_NM_PER_MM * 2.5
    sigmas_nm = [0.0, 0.001, 0.003, 0.01, 0.03, 0.1]
    a3 = []
    for sig in sigmas_nm:
        rp = []
        for seed in range(3):
            _, _, _, m = spectrum(lam_b0, L_ref, chirp_ref, kappa_uniform,
                                  sigma_lamb=sig * 1e-9, seed=seed)
            rp.append(m["ripple_pp"])
        a3.append(np.mean(rp))
        print("  σ_λB = %6.3f nm: ripple_pp = %7.2f ps (3 种子)"
              % (sig, np.mean(rp)))
    summary["a3_sigma_nm"] = np.array(sigmas_nm)
    summary["a3_ripple_pp"] = np.array(a3)

    print("  -- ripple 随长度增长 @ σ_λB = 0.01 nm --")
    a3L = []
    for Lmm in [1.0, 2.5, 5.0, 10.0, 20.0]:
        rp = []
        for seed in range(3):
            _, _, _, m = spectrum(lam_b0, Lmm * 1e-3, C_NM_PER_MM * Lmm,
                                  kappa_uniform, sigma_lamb=0.01e-9, seed=seed)
            rp.append(m["ripple_pp"])
        a3L.append((Lmm, np.mean(rp)))
        print("    L = %5.1f mm: ripple_pp = %7.2f ps" % (Lmm, np.mean(rp)))
    summary["a3L_L_mm"] = np.array([x[0] for x in a3L])
    summary["a3L_ripple_pp"] = np.array([x[1] for x in a3L])

    print("=" * 70)
    print("A6 切趾（L = 2.5 mm）")
    print("=" * 70)
    wins = [("uniform", kappa_uniform), ("linear", kappa_linear),
            ("gauss", kappa_gauss), ("cosine", kappa_cosine)]
    a6 = []
    for name, prof in wins:
        _, _, _, m = spectrum(lam_b0, L_ref, chirp_ref, prof)
        a6.append((name, m["ripple_pp"], m["swing"], m["R_band_mean"]))
        print("  %-8s: ripple_pp = %6.2f ps, 摆幅 = %6.1f ps (均匀基准 %.1f), "
              "R_band = %.2f" % (name, m["ripple_pp"], m["swing"],
                                 a5[1]["swing"], m["R_band_mean"]))
    summary["a6_names"] = np.array([x[0] for x in a6])
    summary["a6_ripple_pp"] = np.array([x[1] for x in a6])
    summary["a6_swing"] = np.array([x[2] for x in a6])

    print("=" * 70)
    print("A4 温漂（dn/dT = %.0e/K）" % DNDT)
    print("=" * 70)
    # 均匀温漂：λ_B 平移 -> τ 平移 D×Δλ_B（线性啁啾一阶不变形）
    dlamb_per_K = lam_b0 * DNDT / N_EFF * 1e9
    D_ref = a5[1]["D"]
    print("  均匀温漂: Δλ_B = %.4f nm/K -> τ 平移 = %.2f ps/K "
          "(D = %.0f ps/nm), 占 2.5mm 摆幅 %.2f%%/K"
          % (dlamb_per_K, D_ref * dlamb_per_K, D_ref,
             100 * D_ref * dlamb_per_K / a5[1]["swing"]))
    summary["a4_tau_shift_ps_per_K"] = D_ref * dlamb_per_K
    # 温度梯度：dT/dz 等效附加啁啾 -> ripple
    for grad in [0.01, 0.1, 1.0]:    # K/mm
        extra = lambda z, g=grad: dlamb_per_K * 1e-9 * (g * 1e3) * z
        _, _, _, m = spectrum(lam_b0, L_ref, chirp_ref, kappa_uniform,
                              extra_lamb_z=extra)
        print("  梯度 %5.2f K/mm: ripple_pp = %7.2f ps, D = %7.2f ps/nm"
              % (grad, m["ripple_pp"], m["D"]))
    summary["a4_grad_K_per_mm"] = np.array([0.01, 0.1, 1.0])

    np.savez(os.path.join(OUT, "tolerance_scan.npz"), **summary)

    # ---------------- 图 ----------------
    fig, axs = plt.subplots(1, 3, figsize=(13, 4))
    axs[0].loglog(summary["a5_L_mm"], summary["a5_swing"], "o-",
                  label="TMM swing")
    axs[0].loglog(summary["a5_L_mm"], summary["a5_swing_geo"], "k--",
                  label=r"$2n_gL/c$")
    axs[0].set(xlabel="L (mm)", ylabel="delay swing (ps)",
               title="A5: swing scales linearly with L")
    axs[0].legend(); axs[0].grid(alpha=.3, which="both")

    axs[1].loglog(summary["a3_sigma_nm"][1:], summary["a3_ripple_pp"][1:],
                  "o-", label=r"ripple vs $\sigma_{\lambda_B}$ (L=2.5mm)")
    axs[1].loglog(summary["a3L_L_mm"], summary["a3L_ripple_pp"], "s--",
                  label=r"ripple vs L ($\sigma$=0.01nm)")
    axs[1].axhline(0.1, color="r", ls=":", label="M1 jitter tolerance 0.1 ps")
    axs[1].set(xlabel=r"$\sigma_{\lambda_B}$ (nm) / L (mm)",
               ylabel=r"ripple p-p (ps)", title="A3: phase-error accumulation")
    axs[1].legend(); axs[1].grid(alpha=.3, which="both")

    x = np.arange(len(a6))
    axs[2].bar(x - 0.2, summary["a6_ripple_pp"], 0.4, label="ripple p-p (ps)")
    axs[2].bar(x + 0.2, summary["a6_swing"], 0.4, label="swing (ps)")
    axs[2].set_xticks(x); axs[2].set_xticklabels(summary["a6_names"])
    axs[2].set(title="A6: apodization trade-off")
    axs[2].legend(); axs[2].grid(alpha=.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "tolerance_scan.png"), dpi=150)
    print("\nsaved results/tolerance_scan.npz / .png")


if __name__ == "__main__":
    main()
