# -*- coding: utf-8 -*-
"""sim13b: P1 distribution-invariance — three geometries realizing one R(ω).

Geometries (same target reflectance):
  G1 straight: L=2.5 mm, C=12 nm/mm, kappa(z)=k0*cos(pi*(z/L-0.5))
  G2 spiral : length-stretched s=N_turn (L'=sL, C'=C/s, k'=k(z'/s)/s) with
              accumulated propagation loss (TFLN 33 dB/m & SiN 0.3 dB/m)
  G3 cascade: N_seg apodized sub-gratings, junction phases from TMM directly
              (junction dips measured honestly)

Metrics: |R| and group-delay agreement in the reflection window vs G1;
santafe@50M functional NMSE agreement (kernel = IFFT of r); junction dip
depth; conservation-law compliance (dtau <= 2 n_g L/c per implementation).

TMM core copied from simulations/02_tolerance_scan.py (extended with an
optional field-loss alpha_f; alpha_f=0 reduces to the original exactly).
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
OUT = os.path.join(ROOT, "results", "sim13b")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

C0 = 299792458.0
N_EFF = 2.2
LAMB0 = 1550e-9
KAPPA0 = 5e3
GAP_NM = LAMB0 ** 2 * KAPPA0 / (2 * np.pi * N_EFF) * 1e9
L_MM = 2.5
C_NM_PER_MM = 12.0
CHIRP_NM = C_NM_PER_MM * L_MM


def dbm_to_alpha_f(dB_per_m):
    """power dB/m -> field attenuation alpha_f [1/m] (amplitude)."""
    return dB_per_m * np.log(10) / 20.0


def tmm_reflect_lossy(lam, lam_b_z, kappa_z, dz, alpha_f=0.0, n_eff=N_EFF,
                      block=2000):
    """2x2 transfer matrix with optional uniform field loss alpha_f and
    effective index n_eff (n_eff=N_EFF/s reproduces a length-stretched
    grating with identical r(omega))."""
    N = len(lam_b_z)
    r = np.empty(len(lam), complex)
    for b0 in range(0, len(lam), block):
        lb = lam[b0:b0 + block]
        delta = 2 * np.pi * n_eff * (1.0 / lb[None, :] - 1.0 / lam_b_z[:, None])
        kap = kappa_z[:, None]
        gam = np.sqrt(kap ** 2 - delta ** 2 - alpha_f ** 2 + 0j)
        s = np.sinh(gam * dz) / gam
        ch = np.cosh(gam * dz)
        q11 = delta - 1j * alpha_f
        q22 = delta + 1j * alpha_f
        a11 = ch - 1j * q11 * s
        a12 = -1j * kap * s
        a21 = 1j * kap * s
        a22 = ch + 1j * q22 * s
        t11 = np.ones(len(lb), complex); t12 = np.zeros(len(lb), complex)
        t21 = np.zeros(len(lb), complex); t22 = np.ones(len(lb), complex)
        for j in range(N):
            t11, t12, t21, t22 = (a11[j] * t11 + a12[j] * t21,
                                  a11[j] * t12 + a12[j] * t22,
                                  a21[j] * t11 + a22[j] * t21,
                                  a21[j] * t12 + a22[j] * t22)
        r[b0:b0 + block] = -t21 / t22
    return r


# ---------------- geometry builders ----------------

def g1_straight(n_lam=6000, apod=True):
    L = L_MM * 1e-3
    N = 800
    dz = L / N
    z = (np.arange(N) + 0.5) * dz
    C = C_NM_PER_MM * 1e-9 / 1e-3
    lam_b_z = LAMB0 + C * z
    kap = KAPPA0 * np.cos(np.pi * (z / L - 0.5)) if apod else np.full(N, KAPPA0)
    lam = np.linspace(LAMB0 - 2e-9, LAMB0 + (CHIRP_NM + 2) * 1e-9, n_lam)
    r = tmm_reflect_lossy(lam, lam_b_z, kap, dz)
    return lam, r


def g2_spiral(stretch=5.0, loss_db_per_m=33.0, n_lam=6000, apod=True):
    """same r(omega) as G1 in a length-stretched spiral layout.

    Stretch z'=s*z keeps r(omega) invariant iff detuning and coupling scale
    together: n_eff'=n_eff/s, kappa'=kappa/s, C'=C/s, L'=sL (same ODE in the
    stretched coordinate).  Loss accumulates over the physical spiral length.
    """
    s = stretch
    L = s * L_MM * 1e-3
    N = int(800 * s)
    dz = L / N
    zp = (np.arange(N) + 0.5) * dz
    z = zp / s
    Cp = C_NM_PER_MM * 1e-9 / 1e-3 / s
    lam_b_z = LAMB0 + Cp * zp
    kap = KAPPA0 * np.cos(np.pi * (z / (L_MM * 1e-3) - 0.5)) / s if apod \
        else np.full(N, KAPPA0 / s)
    lam = np.linspace(LAMB0 - 2e-9, LAMB0 + (CHIRP_NM + 2) * 1e-9, n_lam)
    af = dbm_to_alpha_f(loss_db_per_m)
    r = tmm_reflect_lossy(lam, lam_b_z, kap, dz, alpha_f=af, n_eff=N_EFF / s)
    return lam, r


def g3_cascade(n_seg=4, n_lam=6000, apod=True, overlap=True):
    """N_seg concatenated apodized sub-gratings covering the chirp band.

    overlap=True: 50%-overlapped raised-cosine windows, overlap-added and
    renormalized -> kappa(z) approximates the continuous target profile;
    junction dips are the honest residual cost (measured, not suppressed).
    overlap=False: abutted sin^2 windows (kappa -> 0 at each junction,
    matched per-segment coupling integral) -- the strong-segmentation case.
    """
    L = L_MM * 1e-3
    N = 1600
    dz = L / N
    z = (np.arange(N) + 0.5) * dz
    C = C_NM_PER_MM * 1e-9 / 1e-3
    lam_b_z = LAMB0 + C * z
    if apod:
        k_t = KAPPA0 * np.cos(np.pi * (z / L - 0.5))     # continuous target
        if overlap:
            kap = np.zeros(N)
            wsum = np.zeros(N)
            for j in range(n_seg):
                zc = (j + 0.5) / n_seg * L
                half = L / n_seg                           # 50% overlap
                w = 0.5 * (1 + np.cos(np.pi * np.clip((z - zc) / half,
                                                      -1, 1)))
                kap += w * KAPPA0 * np.cos(np.pi * (zc / L - 0.5))
                wsum += w
            kap = kap / np.maximum(wsum, 1e-12)
        else:
            seg = np.minimum((z / L * n_seg).astype(int), n_seg - 1)
            zs = (z / L - seg / n_seg) * L
            u = zs * n_seg / L
            z_mid = (seg + 0.5) / n_seg * L
            k_mid = KAPPA0 * np.cos(np.pi * (z_mid / L - 0.5))
            kap = (2 * k_mid) * np.sin(np.pi * u) ** 2
    else:
        kap = np.full(N, KAPPA0)
    lam = np.linspace(LAMB0 - 2e-9, LAMB0 + (CHIRP_NM + 2) * 1e-9, n_lam)
    r = tmm_reflect_lossy(lam, lam_b_z, kap, dz)
    return lam, r


def group_delay(lam, r):
    dphi = np.angle(r[1:] / r[:-1])
    domega = 2 * np.pi * C0 * (1 / lam[:-1] - 1 / lam[1:])
    tau = -dphi / domega
    return 0.5 * (lam[:-1] + lam[1:]), tau


def window_mask(lam):
    lo = LAMB0 + 2.5 * GAP_NM * 1e-9
    hi = LAMB0 + (CHIRP_NM - 2.5 * GAP_NM) * 1e-9
    return (lam > lo) & (lam < hi)


def kernel_from_r(lam, r):
    """impulse response h(t) via IFFT on a uniform frequency grid."""
    f = C0 / lam
    o = np.argsort(f)
    f = f[o]
    ro = r[o]
    n = 1 << int(np.ceil(np.log2(len(f) * 8)))
    df = (f[-1] - f[0]) / (n - 1)
    fu = np.linspace(f[0], f[-1], n)
    ru = np.interp(fu, f, np.abs(ro)) * np.exp(1j * np.interp(fu, f, np.unwrap(np.angle(ro))))
    h = np.fft.ifft(ru)
    t = np.fft.fftfreq(n, df)
    o = np.argsort(t)
    return t[o], np.fft.fftshift(h)[o]


def santafe_nmse(lam, r, baud=50e9, n_train=3000, n_test=1000, seed=0):
    """functional invariance test: L3-style chain with this kernel."""
    y = np.load(os.path.join(ROOT, "data", "santafe_laser.npy")).flatten()
    y = (y - y.mean()) / y.std()
    fs = 256e9
    sps = int(fs / baud)
    sig = np.repeat(y, sps)
    sig = sig / max(np.max(np.abs(sig)), 1e-12)
    t, h = kernel_from_r(lam, r)
    dt = t[1] - t[0]
    H = np.fft.fft(h)
    N = len(sig)
    out = np.fft.ifft(np.fft.fft(sig, len(H)) * H)[:N]
    pw = np.abs(out) ** 2
    idx = np.arange(0, N, sps)
    feat = pw[idx]
    feat = feat / max(feat.max(), 1e-12)
    K = 16
    T = len(feat)
    X = np.stack([feat[K - 1 - k: T - 1 - k] for k in range(K)], axis=1)
    target = y[K:]
    Xtr, Xte = X[:n_train], X[n_train:n_train + n_test]
    ytr, yte = target[:n_train], target[n_train:n_train + n_test]
    Xtr_b = np.hstack([Xtr, np.ones((len(Xtr), 1))])
    Xte_b = np.hstack([Xte, np.ones((len(Xte), 1))])
    A = Xtr_b.T @ Xtr_b + 1e-6 * np.eye(Xtr_b.shape[1])
    w = np.linalg.solve(A, Xtr_b.T @ ytr)
    pred = Xte_b @ w
    return float(np.mean((pred - yte) ** 2) / np.var(yte))


def run_one(cfg):
    t0 = time.time()
    try:
        kind = cfg["kind"]
        if kind == "straight":
            lam, r = g1_straight(apod=cfg.get("apod", True))
        elif kind == "spiral":
            lam, r = g2_spiral(stretch=cfg.get("stretch", 5.0),
                               loss_db_per_m=cfg.get("loss", 33.0),
                               apod=cfg.get("apod", True))
        elif kind == "cascade":
            lam, r = g3_cascade(n_seg=cfg.get("n_seg", 4),
                                apod=cfg.get("apod", True))
        else:
            raise ValueError(kind)
        lam_gd, tau = group_delay(lam, r)
        lam0, r0 = g1_straight(apod=cfg.get("apod", True))
        lam_gd0, tau0 = group_delay(lam0, r0)
        m = window_mask(lam)
        m_gd = window_mask(lam_gd)
        dR = np.abs(np.abs(r[m]) ** 2 - np.abs(r0[m]) ** 2)
        # interpolate tau0 onto lam_gd
        tau0_i = np.interp(lam_gd, lam_gd0, tau0)
        dtau = np.abs(tau - tau0_i)[m_gd]
        nmse = santafe_nmse(lam, r, baud=cfg.get("baud", 50e9))
        span_ps = float((tau[m_gd].max() - tau[m_gd].min()) * 1e12)
        cons_ps = 2 * N_EFF * (L_MM * 1e-3) / C0 * 1e12
        # junction dips (cascade only): worst in-window R ratio vs straight
        junc = None
        if kind == "cascade" and cfg.get("apod", True):
            n_seg = cfg.get("n_seg", 4)
            C = C_NM_PER_MM
            dips = []
            R_ref = np.abs(r0) ** 2
            R_ca = np.abs(r) ** 2
            for j in range(1, n_seg):
                lj = LAMB0 + C * L_MM * j / n_seg * 1e-9
                sel = np.abs(lam - lj) < (C * L_MM / n_seg * 0.25) * 1e-9
                if sel.sum() > 3:
                    dips.append(float(R_ca[sel].min()
                                      / max(R_ref[sel].mean(), 1e-9)))
            if dips:
                junc = {"dip_depth_min": float(np.min(dips)),
                        "dip_depth_mean": float(np.mean(dips)),
                        "n_junctions": len(dips)}
        out = dict(cfg)
        out.update(
            max_dR=float(dR.max()), mean_dR=float(dR.mean()),
            max_dtau_ps=float(dtau.max() * 1e12),
            mean_dtau_ps=float(dtau.mean() * 1e12),
            nmse_santafe50M=nmse,
            delay_span_ps=span_ps,
            cons_limit_ps=cons_ps,
            junction=junc,
            ok=bool(span_ps <= cons_ps * 1.05),
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
    cfgs = [dict(kind="straight")]
    for st in (3.0, 5.0, 8.0):
        for loss in (33.0, 0.3):
            cfgs.append(dict(kind="spiral", stretch=st, loss=loss))
    for n in (2, 4, 8, 16, 32):
        cfgs.append(dict(kind="cascade", n_seg=n))
    cfgs.append(dict(kind="straight", apod=False))
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
                for out in pool.imap_unordered(run_one, todo):
                    f.write(json.dumps(out, ensure_ascii=False) + "\n")
                    f.flush()
                    n += 1
                    print(f"  {n}/{len(grid)} elapsed {time.time()-t0:.0f}s "
                          f"({out.get('kind')} ok={out.get('ok')})", flush=True)
    print(f"ALL DONE -> {JSONL}", flush=True)


def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
    ok = [r for r in rows if r.get("ok")]
    ref = [r for r in ok if r["kind"] == "straight"
           and r.get("apod", True)][0]
    print(f"rows {len(rows)}, ok {len(ok)}")
    print(f"reference (straight apod): santafe NMSE = "
          f"{ref['nmse_santafe50M']:.4f}")
    print(f"{'kind':10s} {'cfg':22s} {'max dR':>8s} {'max dtau(ps)':>12s} "
          f"{'NMSE':>8s} {'NMSE-ref':>9s}")
    for r in sorted(ok, key=lambda x: (x["kind"], str(x))):
        cfg = {k: v for k, v in r.items() if k in
               ("stretch", "loss", "n_seg", "apod", "baud")}
        print(f"{r['kind']:10s} {str(cfg):22s} {r['max_dR']:8.4f} "
              f"{r['max_dtau_ps']:12.3f} {r['nmse_santafe50M']:8.4f} "
              f"{r['nmse_santafe50M']-ref['nmse_santafe50M']:9.4f}")

    # junction-dip measurement: cascade R vs straight R, in-window min ratio
    lam0, r0 = g1_straight()
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
    ax = axes[0]
    ax.plot((lam0 - LAMB0) * 1e9, np.abs(r0) ** 2, "k-", lw=1.5,
            label="straight (target)")
    for n in (4, 8, 16):
        lam, r = g3_cascade(n_seg=n)
        ax.plot((lam - LAMB0) * 1e9, np.abs(r) ** 2, lw=.9,
                label=f"cascade N={n}")
    for st, loss, ls in ((5.0, 33.0, "--"), (5.0, 0.3, ":")):
        lam, r = g2_spiral(stretch=st, loss_db_per_m=loss)
        ax.plot((lam - LAMB0) * 1e9, np.abs(r) ** 2, ls, lw=.9,
                label=f"spiral s={st} {loss}dB/m")
    ax.set(xlabel="Δλ from λ_B (nm)", ylabel="R",
           title="R(λ): three geometries vs target")
    ax.legend(fontsize=7); ax.grid(alpha=.3)
    ax = axes[1]
    lam_gd0, tau0 = group_delay(lam0, r0)
    m = window_mask(lam_gd0)
    ax.plot((lam_gd0[m] - LAMB0) * 1e9, tau0[m] * 1e12, "k-", lw=1.5,
            label="straight")
    for n in (4, 8, 16):
        lam, r = g3_cascade(n_seg=n)
        lg, tg = group_delay(lam, r)
        mm = window_mask(lg)
        ax.plot((lg[mm] - LAMB0) * 1e9, tg[mm] * 1e12, lw=.9,
                label=f"cascade N={n}")
    ax.set(xlabel="Δλ from λ_B (nm)", ylabel="τ (ps)",
           title="Group delay: cascade junction structure")
    ax.legend(fontsize=7); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_geometries.png"), dpi=150)
    plt.close(fig)
    print("saved fig1_geometries.png")


if __name__ == "__main__":
    main()
