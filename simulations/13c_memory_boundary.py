# -*- coding: utf-8 -*-
"""sim13c: P3 device-task memory criterion — T_mem boundary scan.

Task family: dual-pulse spacing classification (L4-v3 design: task, readout
and kernel length must match — validated in the MRR repro series).

For each T_mem = pulse spacing Δt (log 1 ps -> 10 ns, 15 pts):
  class A spacing = Δt, class B spacing = Δt*sqrt(2).
Frontends: MRR kernel (FWHM=20 GHz, CMT pulse train), CBG kernel (lab TMM,
D=1.3 ps/nm, span 2n_gL/c = 36.7 ps), CBG-concept (lab kernel time-stretched
x79 = the conservation-limited 2.9 ns span of the D=1000-equivalent device),
no-frontend baseline.
Unified readout: square-law detection -> power histogram -> ridge regression
(labels +/-1, sign decision).

Acceptance: MRR collapse near T_mem ~ 5/B (B=20 GHz -> 250 ps); CBG arms
flat within span then collapse beyond; 3 seeds, mean+-std; the accuracy vs
T_mem three-arm curve is the candidate P3 main figure.
"""
import argparse
import hashlib
import json
import os
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "sim13c")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

C0 = 299792458.0
N_EFF = 2.2
LAMB0 = 1550e-9
KAPPA0 = 5e3
FS = 2.56e12                 # 2.56 THz sampling (0.39 ps/pt)
N_FFT = 1 << 16              # 25.6 us window
PULSE_SIGMA = 2e-12          # 2 ps Gaussian pulses


# ---------------- kernels ----------------

def mrr_kernel(fwhm=20e9, fsr=400e9):
    """analytic add-drop MRR drop-port pulse train (L2 derivation)."""
    kap = np.sqrt(0.1)
    t_c = np.sqrt(1 - kap ** 2)
    from scipy.optimize import brentq
    r_tgt = fwhm / fsr
    a = brentq(lambda a: (1 - a * t_c ** 2) / (np.pi * np.sqrt(a) * t_c)
               - r_tgt, 1e-12, 0.999999)
    rho = a * t_c * t_c
    tau_rt = 1.0 / fsr
    k_max = int(np.ceil(np.log(1e-4) / np.log(rho)))
    k = np.arange(k_max)
    h = kap * kap * np.sqrt(a) * rho ** k
    t = k * tau_rt
    # resample onto FS grid
    tg = np.arange(N_FFT) / FS
    hg = np.interp(tg, t, h, left=0.0, right=0.0)
    return hg


def cbg_kernel(scale=1.0):
    """CBG reflection impulse response from TMM r(omega), via IFFT.

    np.fft.ifft uses the conjugate kernel, so the physical burst lands at
    negative time; we roll it to the window center BEFORE any time scaling
    (concept tier) so the stretched support stays inside the grid."""
    L = 2.5e-3
    N = 800
    dz = L / N
    z = (np.arange(N) + 0.5) * dz
    C = 12e-9 / 1e-3
    lam_b_z = LAMB0 + C * z
    kap = KAPPA0 * np.cos(np.pi * (z / L - 0.5))
    n_lam = 6000
    lam = np.linspace(LAMB0 - 2e-9, LAMB0 + 32e-9, n_lam)
    r = tmm_fast(lam, lam_b_z, kap, dz)
    f = C0 / lam
    o = np.argsort(f)
    f = f[o]
    ro = r[o]
    phase = np.unwrap(np.angle(ro))
    n = 1 << 16
    df = (f[-1] - f[0]) / (n - 1)
    fu = np.linspace(f[0], f[-1], n)
    ru = np.interp(fu, f, np.abs(ro)) * np.exp(1j * np.interp(fu, f, phase))
    h = np.fft.ifft(ru)
    h = np.fft.fftshift(h)
    # roll so the burst sits at the window center
    i_pk = int(np.argmax(np.abs(h)))
    i_c = n // 2
    h = np.roll(h, i_c - i_pk)
    t = (np.arange(n) - i_c) / (n * df)          # seconds, 0 at center
    if scale != 1.0:
        t = t * scale                               # stretch about center
        h = h / np.sqrt(scale)                      # energy conservation
    tg = np.arange(N_FFT) / FS
    t_c_fft = i_c / FS
    hg = np.interp(tg, t + t_c_fft, np.real(h), left=0.0, right=0.0)
    return hg


def tmm_fast(lam, lam_b_z, kappa_z, dz, block=2000):
    N = len(lam_b_z)
    r = np.empty(len(lam), complex)
    for b0 in range(0, len(lam), block):
        lb = lam[b0:b0 + block]
        delta = 2 * np.pi * N_EFF * (1.0 / lb[None, :]
                                     - 1.0 / lam_b_z[:, None])
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


# ---------------- task + readout ----------------

def make_signal(spacing, rng):
    """two unit Gaussians separated by `spacing` (s), random overall shift."""
    x = np.zeros(N_FFT)
    s = int(PULSE_SIGMA * FS)
    i0 = N_FFT // 4 + rng.integers(0, s * 4)
    i1 = i0 + int(spacing * FS)
    if i1 + 6 * s >= N_FFT:
        i1 = N_FFT - 6 * s - 1
        i0 = i1 - int(spacing * FS)
    for i in (i0, i1):
        lo, hi = max(0, i - 6 * s), min(N_FFT, i + 6 * s)
        tt = np.arange(lo, hi) - i
        x[lo:hi] += np.exp(-0.5 * (tt / s) ** 2)
    x += 0.01 * rng.standard_normal(N_FFT)
    return x


def hist_features(pw, n_bins=12):
    pw = pw / max(pw.max(), 1e-12)
    h, _ = np.histogram(pw, bins=n_bins, range=(0, 1), density=True)
    return h


def run_config(cfg):
    t0 = time.time()
    try:
        arm = cfg["arm"]
        dt = cfg["dt"]
        seed = cfg["seed"]
        rng = np.random.default_rng(abs(seed * 1000 + int(np.log10(dt) * 100)))
        n_train, n_test = 150, 100
        if arm == "mrr":
            h = mrr_kernel()
        elif arm == "cbg_lab":
            h = cbg_kernel(1.0)
        elif arm == "cbg_concept":
            h = cbg_kernel(79.0)
        elif arm == "baseline":
            h = None
        H = np.fft.fft(h) if h is not None else None

        Xtr, ytr, Xte, yte = [], [], [], []
        for i in range(2 * (n_train + n_test)):
            cls = i % 2
            sp = dt * (np.sqrt(2) if cls else 1.0)
            x = make_signal(sp, rng)
            if H is not None:
                y = np.fft.ifft(np.fft.fft(x) * H)
                pw = np.abs(y) ** 2
            else:
                pw = np.abs(x) ** 2
            feat = hist_features(pw)
            (Xtr if i < 2 * n_train else Xte).append(feat)
            (ytr if i < 2 * n_train else yte).append(1 if cls else -1)
        Xtr = np.array(Xtr); Xte = np.array(Xte)
        ytr = np.array(ytr, float); yte = np.array(yte)
        Xtr_b = np.hstack([Xtr, np.ones((len(Xtr), 1))])
        Xte_b = np.hstack([Xte, np.ones((len(Xte), 1))])
        A = Xtr_b.T @ Xtr_b + 1e-3 * np.eye(Xtr_b.shape[1])
        w = np.linalg.solve(A, Xtr_b.T @ ytr)
        acc = float(np.mean(np.sign(Xte_b @ w) == yte))
        out = dict(cfg)
        out.update(acc=acc, ok=True,
                   wall_s=round(time.time() - t0, 3),
                   id=hashlib.md5(json.dumps(cfg, sort_keys=True).encode()
                                  ).hexdigest()[:12])
        return out
    except Exception as e:
        out = dict(cfg)
        out.update(ok=False, error=f"{type(e).__name__}: {e}",
                   wall_s=round(time.time() - t0, 3),
                   id=hashlib.md5(json.dumps(cfg, sort_keys=True).encode()
                                  ).hexdigest()[:12])
        return out


def build_grid():
    cfgs = []
    dts = np.logspace(np.log10(1e-12), np.log10(1e-8), 15)
    for arm in ("mrr", "cbg_lab", "cbg_concept", "baseline"):
        for dt in dts:
            for seed in (0, 1, 2):
                cfgs.append(dict(arm=arm, dt=float(dt), seed=seed))
    return cfgs


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
    print(f"grid {len(grid)}, todo {len(todo)}, workers {a.workers}", flush=True)
    t0 = time.time()
    n = len(have)
    if todo:
        with Pool(a.workers) as pool:
            with open(JSONL, "a", encoding="utf-8") as f:
                for out in pool.imap_unordered(run_config, todo):
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
    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
    rows = [r for r in rows if r.get("ok")]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    cols = {"mrr": "#1EA2AA", "cbg_lab": "#B85042",
            "cbg_concept": "#D9A21B", "baseline": "#888888"}
    lbls = {"mrr": "MRR kernel (FWHM=20 GHz)",
            "cbg_lab": "CBG kernel lab (span 36.7 ps)",
            "cbg_concept": "CBG kernel concept (span 2.9 ns)",
            "baseline": "no frontend"}
    for arm in ("mrr", "cbg_lab", "cbg_concept", "baseline"):
        rs = [r for r in rows if r["arm"] == arm]
        dts = sorted(set(r["dt"] for r in rs))
        mu, sd = [], []
        for dt in dts:
            accs = [r["acc"] for r in rs if r["dt"] == dt]
            mu.append(np.mean(accs)); sd.append(np.std(accs))
        ax.errorbar(np.array(dts) * 1e12, mu, yerr=sd, fmt="o-", ms=4,
                    color=cols[arm], label=lbls[arm], capsize=2)
    ax.axvline(250, color="#1EA2AA", ls=":", alpha=.5)
    ax.axvline(36.7, color="#B85042", ls=":", alpha=.5)
    ax.axvline(2900, color="#D9A21B", ls=":", alpha=.5)
    ax.axhline(0.5, color="k", ls="--", alpha=.3, label="chance")
    ax.set_xscale("log")
    ax.set(xlabel="task memory $T_{mem}$ = pulse spacing (ps)",
           ylabel="test accuracy", ylim=(0.35, 1.02),
           title="P3: device-task memory boundary (dual-pulse spacing, 3 seeds)")
    ax.legend(fontsize=8); ax.grid(alpha=.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_memory_boundary.png"), dpi=150)
    plt.close(fig)
    # collapse-point table: report both edges (bandpass arms have two)
    print(f"{'arm':14s} {'usable range (ps)':>22s}")
    for arm in ("baseline", "cbg_lab", "mrr", "cbg_concept"):
        rs = [r for r in rows if r["arm"] == arm]
        dts = sorted(set(r["dt"] for r in rs))
        acc_mu = [np.mean([r["acc"] for r in rs if r["dt"] == dt]) for dt in dts]
        good = [dt for dt, a in zip(dts, acc_mu) if a >= 0.6]
        lo = min(good) * 1e12 if good else None
        hi = max(good) * 1e12 if good else None
        print(f"{arm:14s} {lo if lo else '-':>10} .. {hi if hi else '-':>10}")
    print("saved fig1_memory_boundary.png")


if __name__ == "__main__":
    main()
