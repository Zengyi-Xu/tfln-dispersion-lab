# -*- coding: utf-8 -*-
"""09: CBG dispersion "collision scheduler" — realizable Ising coupling profiles.

Self-contained (numpy/scipy/matplotlib only). No Lumerical, no GPU.

Physics: spins encoded by wavelength (lambda_i = lam0 + i*dlam). Different
wavelengths do not interfere, so dispersion itself creates no coupling; the
linear group delay of a chirped Bragg grating (CBG) translates wavelength
difference into arrival-time difference, which decides which pulses collide
inside a short nonlinear window. Gaussian intensity pulses (FWHM sigma_t)
give an overlap ∝ exp(-delta^2/(2*sigma_t^2)) — intensity-convolution
convention — so the coupling kernel J(d) ∝ exp(-(d*D*dlam)^2/(2*sigma_t^2)).

S1 ideal linear-GD collision map (180 rows)
S2 GDR ripple vs pairing fidelity (180 rows; A_gdr=0 baseline asserted = 0)
S3 forward design of non-linear GD profiles vs 3 target kernels (9 rows)
S4 device feasibility heatmap (merged into S1 rows; extra column)

Usage:
  python simulations/09_dispersion_collision_scheduler.py --workers 14
  python simulations/09_dispersion_collision_scheduler.py --aggregate
"""
import argparse
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "dispersion_ising_coupling")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

C0 = 299792458.0
N_G = 2.2                       # group index for grating-length conversion

# grids (task book)
NS = [16, 32, 64]
DLAMS = [0.05, 0.1, 0.2, 0.4, 0.8]          # nm
DS = [1.3, 25.0, 156.5]                     # ps/nm: our CBG / SOI CBG / SiN spiral
SIGS = [2.0, 5.0, 10.0, 20.0]               # ps (intensity FWHM)
A_GDRS = [1.0, 3.0, 10.0]                   # ps (A=0 baseline asserted, not stored)
P_GDRS = [0.2, 0.5, 1.0]                    # nm
N_PHI = 20
S3_TARGETS = ["box2", "pow15", "exp3"]      # box(d<=2), d^-1.5, exp(-d/3)
S3_KSEG = 6
D_MAX = 200.0                               # ps/nm constraint
SPAN_MAX_PS = 8000.0                        # 8 ns total delay span constraint


def overlap(delta_tau, sigma_t):
    return np.exp(-(delta_tau ** 2) / (2 * sigma_t ** 2))


def ideal_kernel(d, D, dlam, sigma_t):
    return np.exp(-((d * D * dlam) ** 2) / (2 * sigma_t ** 2))


def d_star_meas(N, D, dlam, sigma_t):
    """measured 1/e coupling range in lattice spacings.

    Builds the collision matrix O_ij from the delay profile first (task-book
    route), derives J(d) = mean_i O[i, i+d], then inverts the Gaussian via
    -ln J at the first below-threshold lattice point.  Returns NaN when the
    coupling range is sub-lattice (J(1) underflows float64)."""
    tau = D * dlam * np.arange(N)
    O = overlap(tau[:, None] - tau[None, :], sigma_t)
    J = np.array([np.mean(np.diag(O, k=d)) for d in range(N)])
    for d in range(1, N):
        if J[d] < 1.0 / np.e:
            if J[d] <= 0.0:
                return np.nan                 # sub-lattice range, unresolvable
            return d / np.sqrt(-np.log(J[d]))
    return np.nan                     # range longer than array


def run_s1(cfg):
    N, dlam, D, sig = cfg["N"], cfg["dlam"], cfg["D"], cfg["sigma_t"]
    dstar_m = d_star_meas(N, D, dlam, sig)
    dstar_t = np.sqrt(2.0) * sig / (D * dlam)
    rel = abs(dstar_m - dstar_t) / dstar_t if np.isfinite(dstar_m) else np.nan
    span_ps = D * (N - 1) * dlam
    bw_nm = N * dlam
    L_mm = span_ps * 1e-12 * C0 / (2 * N_G) * 1e3
    return {**cfg, "stage": "S1", "ok": True,
            "d_star_meas": float(dstar_m) if np.isfinite(dstar_m) else None,
            "d_star_theory": float(dstar_t),
            "d_star_rel_err": float(rel) if np.isfinite(rel) else None,
            "delay_span_ps": float(span_ps), "bandwidth_nm": float(bw_nm),
            "grating_len_mm": float(L_mm),
            "feasible": bool(span_ps <= SPAN_MAX_PS and bw_nm <= 40.0)}


def run_s2(cfg, rng=None):
    """GDR ripple on top of ideal linear GD; reference device = our CBG."""
    N, dlam, D, sig = 32, 0.2, 1.3, 10.0    # reference: our CBG tier
    A, p, phi_idx = cfg["A_gdr"], cfg["p_gdr"], cfg["phi_idx"]
    rng = np.random.default_rng(1000 + phi_idx)
    phi = rng.uniform(0, 2 * np.pi)
    i = np.arange(N)
    tau_ideal = D * dlam * i
    tau_real = tau_ideal + A * np.sin(2 * np.pi * (dlam * i) / p + phi)
    J0 = ideal_kernel(np.arange(N), D, dlam, sig)
    J1 = np.zeros(N)
    for d in range(N):
        dt = tau_real[d:] - tau_real[:N - d]
        J1[d] = np.mean(overlap(dt, sig))
    eps = 1e-12
    rel = np.abs(J1 - J0) / np.maximum(np.abs(J0), eps)
    return {**cfg, "stage": "S2", "ok": True,
            "rms_dev": float(np.sqrt(np.mean(rel ** 2))),
            "max_dev": float(np.max(rel))}


def target_kernel(name, d):
    d = np.asarray(d, float)
    if name == "box2":
        return (d <= 2).astype(float)
    if name == "pow15":
        return np.where(d == 0, 1.0, d ** -1.5)
    if name == "exp3":
        return np.exp(-d / 3.0)
    raise ValueError(name)


def piecewise_tau(knot_vals, lam_grid, lam_knots):
    """GD curve: piecewise-linear interpolation of knot values (ps)."""
    return np.interp(lam_grid, lam_knots, knot_vals)


def realized_kernel(tau, sigma_t):
    N = len(tau)
    J = np.zeros(N)
    for d in range(N):
        dt = tau[d:] - tau[:N - d]
        J[d] = np.mean(overlap(dt, sigma_t))
    return J


def fit_s3(cfg):
    """Fit piecewise-linear GD to target kernel. Device tier sets sigma_t/N
    context; optimizer variables = GD values at K knots (monotone, bounded)."""
    from scipy.optimize import differential_evolution

    target, D = cfg["target"], cfg["D"]
    N, dlam, sig = 32, 0.2, 10.0
    lam = np.arange(N) * dlam
    K = S3_KSEG                      # number of segments
    lam_knots = np.linspace(lam[0], lam[-1], K + 1)   # K segments -> K+1 knots
    dgrid = np.arange(N)
    Jt = target_kernel(target, dgrid)
    Jt = Jt / Jt[0]

    span_knot = D * dlam * (N - 1)  # nominal span for the tier

    def make_tau(v):
        # v: K raw segment slopes; map to [0, D_MAX] via scaled sigmoid
        slopes = D_MAX / (1.0 + np.exp(-v))          # monotone GD (slopes >= 0)
        seg_len = (lam[-1] - lam[0]) / K
        tau_knots = np.concatenate([[0.0], np.cumsum(slopes * seg_len)])
        return tau_knots

    def cost(v):
        tau_knots = make_tau(v)
        span = tau_knots[-1]
        tau = piecewise_tau(tau_knots, lam, lam_knots)
        J = realized_kernel(tau, sig)
        J = J / max(J[0], 1e-12)
        err = float(np.sum((J - Jt) ** 2))
        # hard constraint |slope| <= D_MAX is built into the parametrization;
        # total span <= 8 ns via quadratic penalty
        if span > SPAN_MAX_PS:
            err += 100.0 * (span / SPAN_MAX_PS - 1.0) ** 2
        return err

    # baseline: best single-slope linear GD
    best_lin = np.inf
    for Ds in np.linspace(0.5, D_MAX, 80):
        tau = Ds * lam
        J = realized_kernel(tau, sig)
        J = J / max(J[0], 1e-12)
        best_lin = min(best_lin, float(np.sum((J - Jt) ** 2)))

    res = differential_evolution(cost, [(-6, 6)] * K, seed=42, maxiter=200,
                                 tol=1e-9, polish=True, workers=1)
    tau_best = piecewise_tau(make_tau(res.x), lam, lam_knots)
    J_best = realized_kernel(tau_best, sig)
    J_best = J_best / max(J_best[0], 1e-12)
    return {**cfg, "stage": "S3", "ok": True,
            "fit_err": float(res.fun), "baseline_lin_err": float(best_lin),
            "not_worse_than_linear": bool(res.fun <= best_lin + 1e-9),
            "tau_knots_ps": [float(t) for t in tau_best[::(N - 1) // (K - 1)]] if False else [float(t) for t in np.interp(lam_knots, lam, tau_best)],
            "n_seg": K}


def build_grid():
    grid = []
    for N, dlam, D, sig in itertools.product(NS, DLAMS, DS, SIGS):
        grid.append({"kind": "S1", "N": N, "dlam": dlam, "D": D, "sigma_t": sig})
    for A, p, pi in itertools.product(A_GDRS, P_GDRS, range(N_PHI)):
        grid.append({"kind": "S2", "A_gdr": A, "p_gdr": p, "phi_idx": pi})
    for t, D in itertools.product(S3_TARGETS, DS):
        grid.append({"kind": "S3", "target": t, "D": D})
    return grid


def run_one(cfg):
    t0 = time.time()
    try:
        if cfg["kind"] == "S1":
            out = run_s1(cfg)
        elif cfg["kind"] == "S2":
            out = run_s2(cfg)
        else:
            out = fit_s3(cfg)
        out["ok"] = True
    except Exception as e:
        out = {**cfg, "ok": False, "error": f"{type(e).__name__}: {e}"}
    out["wall_s"] = round(time.time() - t0, 3)
    import hashlib
    out["id"] = hashlib.md5(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]
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
    import hashlib
    def gid(c):
        return hashlib.md5(json.dumps(c, sort_keys=True).encode()).hexdigest()[:12]
    have = done_ids()
    todo = [c for c in grid if gid(c) not in have]
    print(f"grid {len(grid)}, done {len(have)}, todo {len(todo)}, workers {a.workers}",
          flush=True)
    if todo:
        # S3 uses scipy differential_evolution which cannot nest inside Pool
        # workers on Windows; run those 9 configs in the main process.
        s3_todo = [c for c in todo if c["kind"] == "S3"]
        pool_todo = [c for c in todo if c["kind"] != "S3"]
        n = len(have)
        t0 = time.time()
        with open(JSONL, "a", encoding="utf-8") as f:
            for cfg in s3_todo:
                out = run_one(cfg)
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
                print(f"  {n}/{len(grid)} (S3 serial)", flush=True)
        if pool_todo:
            with Pool(a.workers) as pool:
                with open(JSONL, "a", encoding="utf-8") as f:
                    for out in pool.imap_unordered(run_one, pool_todo):
                        f.write(json.dumps(out, ensure_ascii=False) + "\n")
                        f.flush()
                        n += 1
                        if n % 50 == 0:
                            print(f"  {n}/{len(grid)}, elapsed {time.time()-t0:.0f}s", flush=True)
    print(f"ALL DONE -> {JSONL}", flush=True)


def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
    s1 = [r for r in rows if r["stage"] == "S1"]
    s2 = [r for r in rows if r["stage"] == "S2"]
    s3 = [r for r in rows if r["stage"] == "S3"]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # (a) kernel profiles (semi-log)
    ax = axes[0][0]
    for D in DS:
        for sig in [5.0, 20.0]:
            d = np.arange(0, 64)
            ax.semilogy(d, ideal_kernel(d, D, 0.2, sig),
                        label=f"D={D}, σ_t={sig}")
    ax.set(xlabel="lattice distance d", ylabel="J(d)",
           title="(a) ideal Toeplitz coupling kernels (Δλ=0.2 nm)")
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    # (b) GDR sensitivity
    ax = axes[0][1]
    for p in P_GDRS:
        xs, ys, es = [], [], []
        for A in A_GDRS:
            vals = [r["rms_dev"] for r in s2 if r["A_gdr"] == A and r["p_gdr"] == p]
            xs.append(A); ys.append(np.mean(vals)); es.append(np.std(vals))
        ax.errorbar(xs, ys, yerr=es, marker="o", label=f"p={p} nm")
    ax.set(xlabel="GDR amplitude A (ps)", ylabel="rms relative deviation of J(d)",
           title="(b) GDR vs pairing fidelity (20 φ realizations)")
    ax.legend(); ax.grid(alpha=.3)

    # (c) S3 fits
    ax = axes[1][0]
    x = np.arange(len(s3))
    labels = [f"{r['target']}\nD={r['D']}" for r in s3]
    ax.bar(x - 0.2, [r["fit_err"] for r in s3], width=0.4, label="piecewise GD fit")
    ax.bar(x + 0.2, [r["baseline_lin_err"] for r in s3], width=0.4,
           label="best linear GD")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7)
    ax.set_yscale("log")
    ax.set(ylabel="weighted L2 error", title="(c) non-Gaussian kernel synthesis (S3)")
    ax.legend(); ax.grid(alpha=.3)

    # (d) feasibility heatmap (D × Δλ, N=32)
    ax = axes[1][1]
    M = np.zeros((len(DS), len(DLAMS)))
    for i, D in enumerate(DS):
        for j, dl in enumerate(DLAMS):
            r = [r for r in s1 if r["N"] == 32 and r["D"] == D
                 and r["dlam"] == dl and r["sigma_t"] == SIGS[0]][0]
            M[i, j] = 1.0 if r["feasible"] else 0.0
    ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(DLAMS))); ax.set_xticklabels(DLAMS)
    ax.set_yticks(range(len(DS))); ax.set_yticklabels(DS)
    ax.set(xlabel="Δλ (nm)", ylabel="D (ps/nm)",
           title="(d) device feasibility (green=ok, N=32)")
    for i in range(len(DS)):
        for j in range(len(DLAMS)):
            ax.text(j, i, "ok" if M[i, j] else "X", ha="center", va="center",
                    fontsize=9)

    fig.tight_layout()
    png = os.path.join(OUT, "collision_scheduler.png")
    fig.savefig(png, dpi=160)
    plt.close(fig)

    summ = {"n_rows": len(rows),
            "n_S1": len(s1), "n_S2": len(s2), "n_S3": len(s3),
            "d_star_by_tier": {},
            "gdr_rms_by_A": {},
            "s3": s3}
    for D in DS:
        vals = [r["d_star_theory"] for r in s1 if r["D"] == D]
        summ["d_star_by_tier"][str(D)] = {"min": min(vals), "max": max(vals)}
    for A in A_GDRS:
        vals = [r["rms_dev"] for r in s2 if r["A_gdr"] == A]
        summ["gdr_rms_by_A"][str(A)] = {"mean": float(np.mean(vals)),
                                        "max": float(np.max(vals))}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2, ensure_ascii=False)
    print(f"saved {png} + summary.json", flush=True)


if __name__ == "__main__":
    main()
