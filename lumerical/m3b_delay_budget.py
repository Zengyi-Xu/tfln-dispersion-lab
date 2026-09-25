# -*- coding: utf-8 -*-
"""
M3b: physical delay budget for the dispersion device (analytic scaling laws).

Central question: can a TFLN chirped grating provide the ns-scale delay swing
needed to matched-filter a real LiDAR chirped pulse? What is the loss/bandwidth/
range tradeoff, and how do alternative architectures compare?

Physics:
  reflection-mode chirped grating delay swing:  dTau = 2 n_g L / c
  insertion loss:                                IL = alpha * L
  -> delay-per-loss figure of merit:             dTau/IL = 2 n_g / (c alpha)

  chirped-pulse LiDAR matched filter:
    delay swing must cover the range window  dTau = 2 R_max / c
    bandwidth B sets range resolution        dR = c / (2 B)
    time-bandwidth product (compression)     TBP = B * T_chirp
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

C0 = 299792458.0

# platform parameters
N_G = 2.1                # group index
PLATFORMS = {
    "TFLN (0.033 dB/mm)": 0.033 * 1e3,   # dB/m
    "SiN (0.3 dB/m)": 0.3,               # dB/m  (Geng 2026)
    "Si (1 dB/cm)": 1.0 * 1e2,           # dB/m  (rough)
}


def delay_swing(L, n_g=N_G):
    return 2 * n_g * L / C0


def loss_db(L, alpha_db_m):
    return alpha_db_m * L


def range_window(delay_swing):
    return C0 * delay_swing / 2.0


def main():
    print("=" * 60)
    print("M3b: delay budget")
    print("=" * 60)

    # ---- 1. delay-per-loss figure of merit ----
    print("\n[1] delay-swing-per-loss figure of merit (reflection grating)")
    for name, alpha in PLATFORMS.items():
        fom = 2 * N_G / (C0 * alpha)          # s/dB
        print("  %-22s dTau/IL = %.1f ps/dB" % (name, fom * 1e12))

    # ---- 2. delay swing vs loss curves ----
    L = np.logspace(-4, 0, 200)              # 0.1 mm to 1 m
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, alpha in PLATFORMS.items():
        ds = delay_swing(L) * 1e12           # ps
        il = loss_db(L, alpha)
        ax.loglog(ds, il, lw=2, label=name)
    # mark operating points
    for rng_m, lbl in [(0.75, "R=0.75 m"), (15, "R=15 m"), (150, "R=150 m")]:
        ds_needed = 2 * rng_m / C0 * 1e12    # ps
        ax.axvline(ds_needed, color="k", ls=":", alpha=0.4)
        ax.text(ds_needed, 2e-4, lbl, rotation=90, va="bottom", fontsize=8)
    ax.set_xlabel("delay swing = range window (ps)")
    ax.set_ylabel("insertion loss (dB)")
    ax.set_title("chirped-grating delay swing vs loss\n(vertical lines = required swing for max range)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "m3b_delay_loss.png"), dpi=150)
    print("  saved m3b_delay_loss.png")

    # ---- 3. what range can TFLN cover at a given loss budget ----
    print("\n[2] TFLN achievable range window vs loss budget")
    alpha_tfln = PLATFORMS["TFLN (0.033 dB/mm)"]
    for il_budget in (1, 3, 10, 30):
        L = il_budget / alpha_tfln
        ds = delay_swing(L)
        print("  IL budget %4.1f dB -> L=%.1f cm, delay swing %.2f ps, range window %.2f m"
              % (il_budget, L * 100, ds * 1e12, range_window(ds)))

    # ---- 4. architecture comparison at a target spec ----
    # target: R_max = 1.5 m -> delay swing 10 ns; B = 8 THz -> dR = 18.8 um
    print("\n[3] architecture comparison for R_max=1.5 m (10 ns swing), B=8 THz")
    ds_target = 10e-9
    B = 8e12
    dR = C0 / (2 * B)
    print("  required delay swing: %.1f ns ; range resolution: %.1f um" % (ds_target * 1e9, dR * 1e6))

    rows = []
    for name, alpha in PLATFORMS.items():
        L = ds_target * C0 / (2 * N_G)
        il = loss_db(L, alpha)
        rows.append([name, "%.2f m" % L, "%.1f dB" % il])
    print("  chirped-grating (reflection):")
    for r in rows:
        print("    %-22s L=%s, IL=%s" % tuple(r))
    print("  SiN spiral wins on loss; TFLN's edge is EO tunability, not raw delay.")

    # DBP comparison
    print("\n[4] dispersion-bandwidth product (DBP) at 3 dB loss budget")
    for name, alpha in PLATFORMS.items():
        L = 3.0 / alpha
        ds = delay_swing(L)
        dbp = ds * B                          # dimensionless TBP-equivalent
        print("  %-22s delay swing %.1f ps, DBP = %.2e (ps*THz: %.1f)"
              % (name, ds * 1e12, dbp, ds * 1e12 * B / 1e12))

    np.savez(os.path.join(OUT, "m3b_delay_budget.npz"),
             platforms=list(PLATFORMS.keys()),
             alphas=list(PLATFORMS.values()),
             delay_per_loss_ps_per_db=[2 * N_G / (C0 * a) * 1e12 for a in PLATFORMS.values()])


if __name__ == "__main__":
    main()
