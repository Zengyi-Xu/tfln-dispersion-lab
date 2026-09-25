# -*- coding: utf-8 -*-
"""
Parametrized 2D FDTD runs for the dn scan and the chirped grating.

Part A (dn scan): uniform gratings with dn = 0.01 / 0.04 (dn = 0.02 reuses the
    existing bragg2d run). Validates bandgap width  ~ kappa ~ dn.

Part B (chirp): Lambda(z) linear over L = 250 um, total chirp 80 nm.
    Validates linear tau(lambda) with slope ~ n_g/(n_bar*c*C), and the
    validity criterion (chirp total >> local gap ~ lambda^2*kappa/2pi*n).

Both reuse the reference waveguide run (ref2d.fsp / ref_raw.npz) for the
baseline delay; the chirp run additionally uses the measured n_g for its
longer propagation length.

Run with Lumerical's bundled python:
  "E:/Program Files/ANSYS Inc/v252/Lumerical/python-3.13.1/python.exe" run_scan_2d.py
"""
import os
import sys
import shutil
import numpy as np

sys.path.append(r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python")
import lumapi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
C0 = 299792458.0

# shared design constants (same as run_bragg_2d.py)
n_core = 2.07
n_bar = 2.02
Lambda0 = 387.5e-9
lambda_B = 2 * n_bar * Lambda0
N_per = 200
L_uni = N_per * Lambda0
w = 1.5e-6
n_freq = 121

wl_lo, wl_hi = 1.515e-6, 1.625e-6

N_G = None  # measured below from ref_raw.npz


def S(fdtd, d):
    for k, v in d.items():
        fdtd.set(k, v)


def add_rect(fdtd, xc, xspan, index, name):
    fdtd.addrect()
    S(fdtd, {
        "x": xc, "x span": xspan,
        "y": 0.0, "y span": w,
        "z": 0.0, "z span": 1e-6,
        "index": index, "name": name,
    })


def add_source_monitors(fdtd, x_src, x_T):
    fdtd.addmode()
    S(fdtd, {
        "injection axis": "x", "direction": "forward",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": x_src,
        "center wavelength": lambda_B,
        "wavelength span": (wl_hi - wl_lo),
        "set wavelength": 1,
    })
    for obj, typ in (("addpower", "2D X-normal"), ("addprofile", "2D X-normal")):
        getattr(fdtd, obj)()
        S(fdtd, {
            "monitor type": typ,
            "y": 0.0, "y span": 4.0e-6,
            "z": 0.0, "z span": 1e-6,
            "x": x_T,
            "override global monitor settings": 1,
            "frequency points": n_freq,
            "name": "Tpow" if obj == "addpower" else "Tfield",
        })
    # reflection field monitor BEHIND the source: only backward light there,
    # so its phase gives the reflection group delay (the correct geometry for
    # a reflective/chirped grating — the through phase is meaningless when T~0)
    fdtd.addprofile()
    S(fdtd, {
        "monitor type": "2D X-normal",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": x_src - 1.5e-6,
        "override global monitor settings": 1,
        "frequency points": n_freq,
        "name": "Rfield",
    })


def build(fname, dn, L, chirp_dLambda=0.0):
    """Uniform (chirp_dLambda=0) or linearly chirped grating."""
    fdtd = lumapi.FDTD(hide=False)
    x_src, x_T = -2.0e-6, L + 2.0e-6
    x_lo, x_hi = -6.0e-6, L + 6.0e-6
    fdtd.save(fname)

    fdtd.addfdtd()
    S(fdtd, {
        "dimension": "2D",
        "x": (x_lo + x_hi) / 2, "x span": x_hi - x_lo,
        "y": 0.0, "y span": 6.0e-6,
        "z": 0.0, "z span": 1e-6,
        "mesh accuracy": 1,
        "simulation time": 3000e-15,
        "x min bc": "PML", "x max bc": "PML",
        "y min bc": "PML", "y max bc": "PML",
    })
    fdtd.addmesh()
    S(fdtd, {
        "x": (x_lo + x_hi) / 2, "x span": x_hi - x_lo,
        "y": 0.0, "y span": 6.0e-6,
        "z": 0.0, "z span": 1e-6,
        "dx": 10e-9, "dy": 20e-9, "dz": 20e-9,
        "override x mesh": 1, "override y mesh": 1, "override z mesh": 0,
    })

    for xc, xspan in ((x_lo / 2, -x_lo), ((x_hi + L) / 2, x_hi - L)):
        add_rect(fdtd, xc, xspan, n_core, "wg")

    C = chirp_dLambda / L
    z = 0.0
    i = 0
    while z < L - 1e-12:
        lam_local = Lambda0 + C * (z - L / 2) if chirp_dLambda else Lambda0
        seg = lam_local / 2
        add_rect(fdtd, z + seg / 2, seg,
                 n_core + dn if i % 2 == 0 else n_core - dn, "gr%d" % i)
        z += seg
        i += 1
    print("  grating: %d segments, L = %.1f um, chirp dLambda = %.2f nm"
          % (i, z * 1e6, chirp_dLambda * 1e9), flush=True)

    add_source_monitors(fdtd, x_src, x_T)
    fdtd.save(fname)
    return fdtd


def extract(fsp, tag):
    fdtd = lumapi.FDTD(hide=False)
    fdtd.setresource("FDTD", 1, "processes", 12)
    fdtd.load(fsp)
    fdtd.run()

    Tres = fdtd.getresult("Tpow", "T")
    f = np.array(Tres["f"]).flatten()
    T = np.array(Tres["T"]).flatten()
    Eres = fdtd.getresult("Tfield", "E")
    E = np.squeeze(Eres["E"])
    y = np.array(Eres["y"]).flatten()
    idx = np.abs(y).argmin()
    comp = np.abs(E[idx, :, :]).sum(axis=0).argmax()
    Eline = E[idx, :, comp]
    phi = np.unwrap(np.angle(Eline))
    tau = np.gradient(phi, f) / (2 * np.pi)
    # reflection group delay (if the fsp has an Rfield monitor)
    tau_r = None
    try:
        Rres = fdtd.getresult("Rfield", "E")
        Er = np.squeeze(Rres["E"])
        yr = np.array(Rres["y"]).flatten()
        idr = np.abs(yr).argmin()
        compr = np.abs(Er[idr, :, :]).sum(axis=0).argmax()
        Erline = Er[idr, :, compr]
        phi_r = np.unwrap(np.angle(Erline))
        tau_r = np.gradient(phi_r, f) / (2 * np.pi)
    except Exception:
        pass
    np.savez(os.path.join(OUT, "%s_raw.npz" % tag), f=f, T=T, tau=tau,
             tau_r=tau_r if tau_r is not None else np.zeros_like(tau) * np.nan)
    fdtd.close()
    print("  %s done. tau mean = %.4f ps%s" % (
        tag, np.mean(tau) * 1e12,
        ", tau_r mean = %.4f ps" % (np.mean(tau_r) * 1e12) if tau_r is not None else ""), flush=True)
    return f, T, tau, tau_r


def kappa_from_gap(wl, T, n_g, lam_B):
    o = np.argsort(wl)
    wl, T = wl[o], T[o]
    ic = np.argmin(np.abs(wl - lam_B))
    i1 = ic
    while i1 > 0 and T[i1] < 0.5:
        i1 -= 1
    i2 = ic
    while i2 < len(T) - 1 and T[i2] < 0.5:
        i2 += 1
    def cross(i):
        x0, x1 = wl[i], wl[i + 1]
        y0, y1 = T[i], T[i + 1]
        return x0 + (0.5 - y0) * (x1 - x0) / (y1 - y0)
    return (cross(i2) - cross(i1)) * np.pi * n_g / lam_B**2


def main():
    # measured group index from the reference run
    ref = np.load(os.path.join(OUT, "ref_raw.npz"))
    f_ref, tau_ref = ref["f"], ref["tau"]
    n_g = C0 * np.mean(tau_ref) / (L_uni + 4e-6)
    print("n_g (from reference) = %.3f" % n_g, flush=True)

    # ---------------- Part A: dn scan ----------------
    dns = [0.01, 0.02, 0.04]
    kappas, widths = [], []
    for dn in dns:
        tag = "dn%03d" % round(dn * 1000)
        if dn == 0.02:
            d = np.load(os.path.join(OUT, "bragg2d.npz"))
            k = kappa_from_gap(d["wl"], d["T"], n_g, lambda_B)
            print("dn=0.02: reuse existing run, kappa_fit = %.0f /cm" % (k / 100), flush=True)
        else:
            raw = os.path.join(OUT, "%s_raw.npz" % tag)
            fsp = os.path.join(OUT, "%s.fsp" % tag)
            if os.path.exists(raw):
                d = np.load(raw)
                f, T = d["f"], d["T"]
                print("reusing saved %s run" % tag, flush=True)
            else:
                if not os.path.exists(fsp):
                    print("building %s ..." % tag, flush=True)
                    build(fsp, dn, L_uni)
                print("running %s ..." % tag, flush=True)
                f, T, tau, _ = extract(fsp, tag)
            k = kappa_from_gap(C0 / f, T, n_g, lambda_B)
            print("dn=%.2f: kappa_fit = %.0f /cm" % (dn, k / 100), flush=True)
        kappas.append(k)
        widths.append(k * lambda_B**2 / (np.pi * n_g))

    np.savez(os.path.join(OUT, "scan_dn.npz"),
             dn=np.array(dns), kappa=np.array(kappas), width=np.array(widths),
             n_g=n_g, lambda_B=lambda_B, L=L_uni)

    # ---------------- Part B: chirped grating ----------------
    L_ch = 250e-6
    chirp_dL = 17.3e-9           # Lambda: 380.9 -> 398.2 nm  (80 nm in lambda)
    fsp = os.path.join(OUT, "chirp2d.fsp")
    if not os.path.exists(fsp):
        print("building chirp ...", flush=True)
        build(fsp, 0.02, L_ch, chirp_dL)
    print("running chirp ... (this is the long one)", flush=True)
    f, T, tau, tau_r = extract(fsp, "chirp")
    np.savez(os.path.join(OUT, "chirp2d.npz"),
             f=f, wl=C0 / f, T=T, tau_g=tau, tau_r=tau_r,
             n_g=n_g, L=L_ch, chirp_dLambda=chirp_dL,
             Lambda0=Lambda0, lambda_B=lambda_B)
    print("chirp done. saved chirp2d.npz", flush=True)


if __name__ == "__main__":
    main()
