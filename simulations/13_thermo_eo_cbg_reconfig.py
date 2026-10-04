# -*- coding: utf-8 -*-
"""sim13: TFLN chirped-grating thermo/EO co-tunable group-delay reconfiguration.

Segmented local-index-perturbation TMM model quantifying the two-tier
reconfiguration domain:
  thermal tier (coarse, ms-s):  dn = 3.95e-5/K * dT,  dT in [0,100] K
  EO tier     (fine, ns-us):    dn = 0.5*n^3*r33*(V/gap)*Gamma,
                                n=2.2, r33=11 pm/V (LPR 3 um-gap anchor),
                                gap=3 um, Gamma=0.5  -> dn(50 V) ~ 4.9e-4

Dispersion amplification: a uniform dn translates the delay window by
  d_tau = D * dlam_B,   dlam_B = lam_B * dn / n_eff.

Base TMM: copied from simulations/02_tolerance_scan.py (NOT modified).
Physics conventions (anchors C3/C4/C6/C7 + V4 conservation law):
  N_EFF = 2.2 (n_g = n_eff, lossless TMM; R_max ~ 0.77 -> R>0.5 window)
  lab tier:     L=2.5 mm, C=12 nm/mm   -> D ~ 1.22 ps/nm
  concept tier: L=2.5 mm, C=14.67 nm/mm -> D ~ 1000 ps/nm (scaled argument;
                a real device needs n_g*L ~ 15-20 cm equivalent)

Traps honored (task book):
  * window translation measured from the R>0.5 band POSITION shift in
    wavelength (dlam_B), then dtau = D*dlam_B  -- avoids the tau_r/tau field
    ambiguity entirely (D itself from tau-slope fit inside the window).
  * 1 mm device: not used (C2 correction); all sims at L=2.5 mm.

Usage:
  python simulations/13_thermo_eo_cbg_reconfig.py --workers 14
  python simulations/13_thermo_eo_cbg_reconfig.py --aggregate
"""
import argparse
import hashlib
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "thermo_eo_cbg")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

C0 = 299792458.0
N_EFF = 2.2                 # repo TMM convention (n_g = n_eff)
LAMB0 = 1550e-9
KAPPA0 = 5e3                # 1/m
GAP_NM = LAMB0 ** 2 * KAPPA0 / (2 * np.pi * N_EFF) * 1e9   # ~1.77 nm

# actuators
DNDT = 3.95e-5              # /K  (C6)
R33 = 11e-12                # m/V (LPR 2026, 3 um gap)
GAP_EO = 3e-6               # m
GAMMA_OL = 0.5              # overlap
N_EO = 2.2

# tiers — lab geometry is simulated; the concept tier (D~1000 ps/nm) is
# obtained by exact linear scaling of the amplification law
# (dtau = D*dlam_B is strictly linear in D; dlam_B is D-independent).
# A physical D=1000 ps/nm device at L=2.5 mm would violate the conservation
# law (needs C=0.0147 nm/mm -> chirp 0.037 nm < gap 1.77 nm), so it is NOT
# simulated directly — per task book "等效缩放口径".
TIERS = {
    "lab": dict(L_mm=2.5, C_nm_per_mm=12.0),
}
D_CONCEPT = 1000.0            # ps/nm (concept-book equivalent)
RIPPLE_ANCHOR_FDTD_PS = 0.09  # C4 (FDTD apodized); TMM lossless baseline differs


# ---------------- TMM core (verbatim from 02_tolerance_scan.py) ----------------
def tmm_reflect(lam, lam_b_z, kappa_z, dz, block=2000):
    """分段均匀 2x2 传递矩阵连乘，返回 r(λ)。"""
    N = len(lam_b_z)
    r = np.empty(len(lam), complex)
    for b0 in range(0, len(lam), block):
        lb = lam[b0:b0 + block]
        delta = 2 * np.pi * N_EFF * (1.0 / lb[None, :] - 1.0 / lam_b_z[:, None])
        kap = kappa_z[:, None]
        gam = np.sqrt(kap ** 2 - delta ** 2 + 0j)
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


def dn_to_dlam_b(dn):
    """uniform local-index offset -> Bragg wavelength shift (m)."""
    return LAMB0 * dn / N_EFF


def simulate(L_mm, C_nm_per_mm, dn_seg, n_probe=300):
    """Fixed-wavelength-frame measurement.

    Uniform dn slides the delay window UNDER a fixed probe grid by
    dlam_B = lam_B*dn/n_eff  ->  dtau = D * dlam_B (dispersion amplification).
    Window-following grids normalize the shift away, so we probe at FIXED
    wavelengths and read the group delay via a two-point phase difference
    (ratio phase is single-valued: immune to the unwrap-density trap).

    Returns metrics dict (lab-geometry TMM)."""
    L = L_mm * 1e-3
    C = C_nm_per_mm * 1e-9 / 1e-3               # nm/mm -> m/m rate
    chirp_nm = C_nm_per_mm * L_mm
    N = max(400, int(round(L / (2.5e-3 / 800))))
    dz = L / N
    z = (np.arange(N) + 0.5) * dz
    edges = np.linspace(0, L, len(dn_seg) + 1)
    idx = np.clip(np.searchsorted(edges, z, side="right") - 1, 0, len(dn_seg) - 1)
    dn_z = dn_seg[idx]
    lam_b_z = LAMB0 + C * z + dn_to_dlam_b(dn_z)

    # probe grid: fixed frame, inside nominal window with margin > max shift
    margin_nm = max(3.5, 0.15 * chirp_nm)
    lam_p = np.linspace(LAMB0 + margin_nm * 1e-9,
                        LAMB0 + (chirp_nm - margin_nm) * 1e-9, n_probe)
    dlam = (lam_p[1] - lam_p[0]) * 0.05          # tiny step for phase difference
    lam2 = lam_p + dlam
    r1 = tmm_reflect(lam_p, lam_b_z, np.full(N, KAPPA0), dz)
    r2 = tmm_reflect(lam2, lam_b_z, np.full(N, KAPPA0), dz)
    dphi = np.angle(r2 / r1)                      # single-valued
    domega = 2 * np.pi * C0 * (1 / lam_p - 1 / lam2)
    tau = -dphi / domega                          # group delay at each probe

    # reference (dn=0) on the same probe grid, for the window-shift readout
    lam_b_z0 = LAMB0 + C * z
    r1_0 = tmm_reflect(lam_p, lam_b_z0, np.full(N, KAPPA0), dz)
    r2_0 = tmm_reflect(lam2, lam_b_z0, np.full(N, KAPPA0), dz)
    tau0 = -np.angle(r2_0 / r1_0) / domega

    p = np.polyfit(lam_p, tau, 1)
    resid = tau - np.polyval(p, lam_p)
    D_ps_nm = p[0] * 1e3                          # s/m -> ps/nm (1e-3 s/m = 1 ps/nm)
    p0 = np.polyfit(lam_p, tau0, 1)
    dtau = float((np.polyval(p, lam_p[len(lam_p) // 2])
                  - np.polyval(p0, lam_p[len(lam_p) // 2])))
    dn_bar = float(np.mean(dn_seg))
    delay_span = D_ps_nm * chirp_nm
    cons_limit = 2 * N_EFF * L / C0 * 1e12
    return {
        "D_ps_per_nm": float(D_ps_nm),
        "D_analytic_ps_per_nm": float(2 * N_EFF / (C0 * C) * 1e3),
        "ripple_pp_ps": float((resid.max() - resid.min()) * 1e12),
        "delay_span_ps": float(delay_span),
        "cons_limit_ps": float(cons_limit),
        "dlam_b_nm": float(LAMB0 * dn_bar / N_EFF * 1e9),
        "dtau_shift_ps": float(dtau * 1e12),
        "dtau_analytic_ps": float(2 * N_EFF / (C0 * C) * 1e3
                                  * (LAMB0 * dn_bar / N_EFF) * 1e9),
        "chirp_nm": float(chirp_nm),
        "ok": bool(delay_span <= cons_limit * 1.05),
    }


def eo_dn(volt):
    return 0.5 * N_EO ** 3 * R33 * (volt / GAP_EO) * GAMMA_OL


def th_dn(dT):
    return DNDT * dT


def build_grid():
    cfgs = []
    # S1: dispersion-amplification law, uniform dn, 20 pts (lab geometry)
    for dn in np.linspace(0, 4e-3, 20):
        cfgs.append(dict(stage="S1_law", tier="lab", dn_uniform=float(dn),
                         n_seg=1, pattern="uniform"))
    # S2: two-tier coverage + combined
    for dT in np.linspace(0, 100, 11):
        cfgs.append(dict(stage="S2_coverage", tier="lab", dT=float(dT),
                         n_seg=1, pattern="uniform", tier_act="thermal"))
    for V in np.linspace(0, 50, 11):
        cfgs.append(dict(stage="S2_coverage", tier="lab", V=float(V),
                         n_seg=1, pattern="uniform", tier_act="eo"))
    for dT in (0, 50, 100):
        for V in (0, 25, 50):
            cfgs.append(dict(stage="S2_combined", tier="lab", dT=float(dT),
                             V=float(V), n_seg=1, pattern="uniform",
                             tier_act="combined"))
    # S3: segmented reconstruction
    for n_seg in (1, 4, 8, 16):
        for pattern in ("ramp", "randn"):
            for dn_max in (1e-3, 2e-3, 4e-3):
                cfgs.append(dict(stage="S3_segmented", tier="lab",
                                 n_seg=n_seg, pattern=pattern,
                                 dn_max=float(dn_max)))
    return cfgs


def run_one(cfg):
    t0 = time.time()
    tier = TIERS[cfg["tier"]]
    try:
        n_seg = cfg["n_seg"]
        if cfg["stage"] == "S1_law":
            dn_seg = np.full(n_seg, cfg["dn_uniform"])
            tier_act = "combined"
        elif cfg["stage"] in ("S2_coverage", "S2_combined"):
            dn = th_dn(cfg.get("dT", 0.0)) + eo_dn(cfg.get("V", 0.0))
            dn_seg = np.full(n_seg, dn)
            tier_act = cfg["tier_act"]
        else:  # S3
            dn_max = cfg["dn_max"]
            if cfg["pattern"] == "ramp":
                dn_seg = np.linspace(0, dn_max, n_seg)
            else:
                dn_seg = np.random.default_rng(
                    int(hashlib.md5(json.dumps(cfg, sort_keys=True).encode())
                        .hexdigest()[:6], 16)).normal(0, dn_max, n_seg)
            tier_act = "segmented"
        m = simulate(tier["L_mm"], tier["C_nm_per_mm"], dn_seg)
        if m is None:
            raise RuntimeError("band extraction failed")
        out = dict(cfg)
        out.update(m)
        out["dn_seg"] = [float(v) for v in dn_seg]
        out["tier_act"] = tier_act
        out["wall_s"] = round(time.time() - t0, 3)
        out["id"] = hashlib.md5(json.dumps(cfg, sort_keys=True).encode()
                                ).hexdigest()[:12]
        return out
    except Exception as e:
        out = dict(cfg)
        out.update(ok=False, error=f"{type(e).__name__}: {e}",
                   wall_s=round(time.time() - t0, 3),
                   id=hashlib.md5(json.dumps(cfg, sort_keys=True).encode()
                                  ).hexdigest()[:12])
        return out


def done_ids():
    if not os.path.exists(JSONL):
        return set()
    ids = set()
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["id"])
            except Exception:
                pass
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    if a.aggregate:
        aggregate()
        return
    grid = build_grid()
    have = done_ids()
    todo = [c for c in grid
            if hashlib.md5(json.dumps(c, sort_keys=True).encode()
                           ).hexdigest()[:12] not in have]
    print(f"grid {len(grid)}, done {len(have)}, todo {len(todo)}, "
          f"workers {a.workers}", flush=True)
    t0 = time.time()
    n = len(have)
    if todo:
        with Pool(a.workers) as pool:
            with open(JSONL, "a", encoding="utf-8") as f:
                for out in pool.imap_unordered(run_one, todo):
                    f.write(json.dumps(out, ensure_ascii=False) + "\n")
                    f.flush()
                    n += 1
                    if n % 20 == 0:
                        print(f"  {n}/{len(grid)} elapsed "
                              f"{time.time()-t0:.0f}s", flush=True)
    print(f"ALL DONE -> {JSONL}", flush=True)


def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    SCALE = D_CONCEPT / 1.3        # lab D~1.3 ps/nm -> concept D=1000 ps/nm

    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
    rows = [r for r in rows if r.get("ok")]
    s1 = [r for r in rows if r["stage"] == "S1_law"]
    s2 = [r for r in rows if r["stage"] in ("S2_coverage", "S2_combined")]
    s3 = [r for r in rows if r["stage"] == "S3_segmented"]

    def cdtau(r):
        """concept-tier (scaled) delay-window shift, ns."""
        return r["dtau_shift_ps"] * SCALE / 1e3

    # ---- fig 1: dtau vs dn (lab TMM + concept scaled) + law deviation ----
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    ax = axes[0]
    rs = sorted(s1, key=lambda r: r["dn_uniform"])
    dn = np.array([r["dn_uniform"] for r in rs])
    ax.plot(dn * 1e3, [r["dtau_shift_ps"] for r in rs], "o-",
            color="#1EA2AA", ms=3, label="lab TMM (D≈1.3 ps/nm)")
    ax.plot(dn * 1e3, [r["dtau_analytic_ps"] for r in rs], "--",
            color="#1EA2AA", alpha=.5, label="lab analytic")
    ax.set_ylabel("Δτ lab tier (ps)", color="#1EA2AA")
    ax.set_xlabel("uniform Δn (1e-3)")
    ax2 = ax.twinx()
    ax2.plot(dn * 1e3, [cdtau(r) for r in rs], "s-", color="#D9A21B", ms=3,
             label="concept (×%.0f)" % SCALE)
    ax2.plot(dn * 1e3, [r["dtau_analytic_ps"] * SCALE / 1e3 for r in rs],
             "--", color="#D9A21B", alpha=.5)
    ax2.set_ylabel("Δτ concept tier (ns)", color="#D9A21B")
    ax.set_title("Dispersion amplification: Δτ = D·λ_B·Δn/n_eff")
    ax.grid(alpha=.3)
    ln1, lb1 = ax.get_legend_handles_labels()
    ln2, lb2 = ax2.get_legend_handles_labels()
    ax.legend(ln1 + ln2, lb1 + lb2, fontsize=8, loc="upper left")
    ax = axes[1]
    dev = np.array([abs(r["dtau_shift_ps"] - r["dtau_analytic_ps"])
                    / max(r["dtau_analytic_ps"], 1e-12) for r in rs])
    ax.plot(dn * 1e3, dev * 100, "o-", color="#1EA2AA", ms=3)
    ax.axhline(5, color="r", ls="--", alpha=.5, label="5% tolerance")
    ax.set(xlabel="uniform Δn (1e-3)", ylabel="|deviation| (%)",
           title="Law validation (lab TMM vs analytic)")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_amplification_law.png"), dpi=150)
    plt.close(fig)

    # ---- fig 2: two-tier coverage (concept-scaled ns) ----
    fig, ax = plt.subplots(figsize=(8, 4.5))
    th = sorted([r for r in s2 if r["tier_act"] == "thermal"],
                key=lambda r: r.get("dT", 0))
    eo = sorted([r for r in s2 if r["tier_act"] == "eo"],
                key=lambda r: r.get("V", 0))
    ax.plot([r.get("dT", 0) for r in th], [cdtau(r) for r in th],
            "o-", color="#B85042", label="thermal coarse (ms–s)")
    ax.plot([r.get("V", 0) for r in eo], [cdtau(r) for r in eo],
            "s-", color="#1EA2AA", label="EO fine (ns–µs)")
    cb = [r for r in s2 if r["tier_act"] == "combined"]
    ax.plot([r.get("dT", 0) + eo_dn(r.get("V", 0)) / DNDT * 0.01
             for r in cb], [cdtau(r) for r in cb], "d",
            color="#666666", alpha=.6, label="combined")
    ax.set(xlabel="actuator setting (K thermal / V EO)",
           ylabel="Δτ (ns)", title="Two-tier coverage @ concept D=1000 ps/nm "
           "(lab-TMM ×%.0f scaled)" % SCALE)
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_two_tier_coverage.png"), dpi=150)
    plt.close(fig)

    # ---- fig 3: segmentation triple (lab TMM) ----
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    D0 = float(np.mean([abs(r["D_ps_per_nm"]) for r in s1
                        if r["dn_uniform"] == 0]))       # measured baseline
    # (a) chirp-rate tunable range vs N_seg (ramp)
    ax = axes[0]
    for dn_max, mk in ((1e-3, "^"), (2e-3, "s"), (4e-3, "o")):
        rs = [r for r in s3 if r["pattern"] == "ramp"
              and abs(r["dn_max"] - dn_max) < 1e-12 and r["n_seg"] > 1]
        ns = sorted([r["n_seg"] for r in rs])
        if ns:
            dD = [abs(np.mean([abs(r["D_ps_per_nm"]) for r in rs if r["n_seg"] == n])
                      - D0) / D0 * 100 for n in ns]
            ax.plot(ns, dD, mk + "-", label=f"ramp → {dn_max*1e3:.0f}e-3")
    ax.axhline(10, color="r", ls=":", alpha=.6, label="task-book expectation ~10%")
    ax.set(xlabel="N_seg", ylabel="|ΔD|/D₀ (%)",
           title=f"Chirp-rate tunable range\n(baseline |D|={D0:.3f} ps/nm)")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    # (b) ripple vs N_seg (randn, σ=4e-3)
    ax = axes[1]
    rs = [r for r in s3 if r["pattern"] == "randn"
          and abs(r["dn_max"] - 4e-3) < 1e-12]
    ns = sorted([r["n_seg"] for r in rs])
    rip = [np.mean([r["ripple_pp_ps"] for r in rs if r["n_seg"] == n]) for n in ns]
    ax.plot(ns, rip, "s-", color="#B85042", label="TMM ripple")
    rip_c = [r * SCALE for r in rip]
    ax.plot(ns, rip_c, "s--", color="#D9A21B", alpha=.6,
            label="concept-scaled")
    ax.axhline(RIPPLE_ANCHOR_FDTD_PS, color="r", ls=":", alpha=.7,
               label="C4 FDTD anchor 0.09 ps")
    ax.set(xlabel="N_seg", ylabel="ripple_pp (ps)",
           title="Ripple vs segmentation\n(randn σ=4e-3)")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    # (c) ripple vs dn strength (randn, N_seg=16)
    ax = axes[2]
    rs = [r for r in s3 if r["pattern"] == "randn" and r["n_seg"] == 16]
    dns = sorted([r["dn_max"] for r in rs])
    rip = [np.mean([r["ripple_pp_ps"] for r in rs if r["dn_max"] == d])
           for d in dns]
    ax.plot(np.array(dns) * 1e3, rip, "s-", color="#B85042")
    ax.set(xlabel="segment dn σ (1e-3)", ylabel="ripple_pp (ps)",
           title="Ripple vs perturbation strength\n(randn, N_seg=16)")
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_segmentation.png"), dpi=150)
    plt.close(fig)

    # summary
    devs = [abs(r["dtau_shift_ps"] - r["dtau_analytic_ps"])
            / max(r["dtau_analytic_ps"], 1e-12) for r in s1]
    rs2t = [r for r in s2 if r["tier_act"] == "thermal" and r.get("dT") == 100]
    rs2e = [r for r in s2 if r["tier_act"] == "eo" and r.get("V") == 50]
    rmp = [r for r in s3 if r["pattern"] == "ramp"
           and abs(r["dn_max"] - 4e-3) < 1e-12]
    ns16 = [r for r in rmp if r["n_seg"] == 16]
    summ = {
        "n_rows": len(rows),
        "D_lab_mean_ps_per_nm": float(np.mean([r["D_ps_per_nm"] for r in s1])),
        "law_max_dev_pct": float(np.max(devs) * 100),
        "thermal_dtau_max_lab_ps": float(np.mean([r["dtau_shift_ps"] for r in rs2t])),
        "eo_dtau_max_lab_ps": float(np.mean([r["dtau_shift_ps"] for r in rs2e])),
        "thermal_dtau_max_concept_ns": float(np.mean([cdtau(r) for r in rs2t])),
        "eo_dtau_max_concept_ns": float(np.mean([cdtau(r) for r in rs2e])),
        "chirp_tunable_range_pct_ramp4e-3_N16": float(
            abs(np.mean([abs(r["D_ps_per_nm"]) for r in ns16]) - D0) / D0 * 100)
        if ns16 else None,
        "ripple_baseline_ps": float(np.mean(
            [r["ripple_pp_ps"] for r in s1 if r["dn_uniform"] == 0])),
    }
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    print(json.dumps(summ, indent=2, ensure_ascii=False))
    print("saved figs + summary.json")


if __name__ == "__main__":
    main()
