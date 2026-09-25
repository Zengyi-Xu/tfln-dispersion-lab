# -*- coding: utf-8 -*-
"""
2D FDTD (effective-index approximation) of a uniform Bragg grating in a TFLN ridge.

Note: Lumerical's 2D FDTD is Z-normal, i.e. the simulation plane is XY and
the structure is invariant along Z. Propagation is therefore along X here.

Validates the CMT/TMM picture from lab-note.ipynb:
  - bandgap centered at lambda_B = 2*n_bar*Lambda
  - tau ~ 0 inside the band (evanescent), group-delay peaks at band edges (slow light)
  - R + T = 1 (lossless)

Runs two simulations: with grating, and a plain reference waveguide (for
subtracting the propagation delay when computing group delay from phase).

Output: results/bragg2d.npz  (f, wl, T, R, tau_g, tau_ref, params)

Run with Lumerical's bundled python:
  "E:/Program Files/ANSYS Inc/v252/Lumerical/python-3.13.1/python.exe" run_bragg_2d.py
"""
import os
import sys
import numpy as np

sys.path.append(os.environ.get(
    "LUMERICAL_API_PATH", r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python"))
import lumapi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

C0 = 299792458.0

# ---------------- design parameters ----------------
# design uses the *mode* effective index n_bar; the 2D ridge core index must
# be slightly higher because the fundamental slab mode is not fully confined:
# w = 1.5 um at 1.55 um -> n_core = 2.07 gives n_eff(mode) ~ 2.02.
n_core = 2.07         # ridge core index in the 2D simulation
n_bar = 2.02          # mode effective index the design is based on
dn = 0.02             # square-wave index modulation amplitude -> kappa ~ 4*dn/lambda_B
N_per = 200           # grating periods
Lambda = 387.5e-9     # period; lambda_B = 2*n_bar*Lambda = 1565.5 nm
L = N_per * Lambda
w = 1.5e-6            # ridge width (transverse, y)
lambda_B = 2 * n_bar * Lambda
kappa = 4 * dn / lambda_B   # first-harmonic coupling coefficient [1/m]

wl_lo, wl_hi = 1.520e-6, 1.620e-6
n_freq = 121

# simulation domain (propagation along x)
x_src, x_T = -2.0e-6, L + 2.0e-6
y_span_fdtd = 6.0e-6
x_lo, x_hi = -6.0e-6, L + 6.0e-6


def S(fdtd, d):
    """lumapi batch set(dict) is unreliable on 2025 R2; set one by one."""
    for k, v in d.items():
        fdtd.set(k, v)


def build(fname, with_grating):
    fdtd = lumapi.FDTD(hide=False)
    fdtd.save(fname)

    fdtd.addfdtd()
    S(fdtd, {
        "dimension": "2D",
        "x": (x_lo + x_hi) / 2, "x span": x_hi - x_lo,
        "y": 0.0, "y span": y_span_fdtd,
        "z": 0.0, "z span": 1e-6,
        "mesh accuracy": 1,
        "simulation time": 3000e-15,
        "x min bc": "PML", "x max bc": "PML",
        "y min bc": "PML", "y max bc": "PML",
    })

    # uniform mesh override (fine along propagation)
    fdtd.addmesh()
    S(fdtd, {
        "x": (x_lo + x_hi) / 2, "x span": x_hi - x_lo,
        "y": 0.0, "y span": y_span_fdtd,
        "z": 0.0, "z span": 1e-6,
        "dx": 10e-9, "dy": 20e-9, "dz": 20e-9,
        "override x mesh": 1, "override y mesh": 1, "override z mesh": 0,
    })

    # waveguide: plain ridge segments before / after the grating region
    for xc, xspan in ((x_lo / 2, -x_lo), ((x_hi + L) / 2, x_hi - L)):
        fdtd.addrect()
        S(fdtd, {
            "x": xc, "x span": xspan,
            "y": 0.0, "y span": w,
            "z": 0.0, "z span": 1e-6,
            "index": n_core, "name": "wg",
        })

    if with_grating:
        # grating as alternating index blocks (each Lambda/2 long, along x)
        for i in range(2 * N_per):
            fdtd.addrect()
            S(fdtd, {
                "x": (i + 0.5) * Lambda / 2, "x span": Lambda / 2,
                "y": 0.0, "y span": w,
                "z": 0.0, "z span": 1e-6,
                "index": n_core + dn if i % 2 == 0 else n_core - dn,
                "name": "gr%d" % i,
            })
    else:
        fdtd.addrect()
        S(fdtd, {
            "x": L / 2, "x span": L,
            "y": 0.0, "y span": w,
            "z": 0.0, "z span": 1e-6,
            "index": n_core, "name": "wg_mid",
        })

    # mode source injecting +x
    fdtd.addmode()
    S(fdtd, {
        "injection axis": "x", "direction": "forward",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": x_src,
        "center wavelength": lambda_B,
        "wavelength span": (wl_hi - wl_lo) * 0.55,
        "set wavelength": 1,
    })

    # transmitted power monitor (T is normalized to source power)
    fdtd.addpower()
    S(fdtd, {
        "monitor type": "2D X-normal",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": x_T,
        "override global monitor settings": 1,
        "frequency points": n_freq,
        "name": "Tpow",
    })

    # complex field monitor at the same plane (for group delay via phase)
    fdtd.addprofile()
    S(fdtd, {
        "monitor type": "2D X-normal",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": x_T,
        "override global monitor settings": 1,
        "frequency points": n_freq,
        "name": "Tfield",
    })

    fdtd.save(fname)
    return fdtd


def run_and_extract(fsp, tag):
    fdtd = lumapi.FDTD(hide=False)
    # measured optimum on the 338H laptop (verify/v5_fdtd_scaling.py);
    # override per machine via env, e.g. FDTD_PROCESSES=12 FDTD_THREADS=1
    # on a 16-core all-P-core host.
    fdtd.setresource("FDTD", 1, "processes",
                     int(os.environ.get("FDTD_PROCESSES", 6)))
    fdtd.setresource("FDTD", 1, "threads",
                     int(os.environ.get("FDTD_THREADS", 2)))
    fdtd.load(fsp)
    fdtd.run()

    Tres = fdtd.getresult("Tpow", "T")
    f = np.array(Tres["f"]).flatten()
    T = np.array(Tres["T"]).flatten()

    Eres = fdtd.getresult("Tfield", "E")
    # E dims: (x, y, z, f, component); squeeze -> (y, f, 3)
    E = np.squeeze(Eres["E"])
    y = np.array(Eres["y"]).flatten()
    idx = np.abs(y).argmin()
    # dominant polarization component at ridge center
    comp = np.abs(E[idx, :, :]).sum(axis=0).argmax()
    Eline = E[idx, :, comp]
    phi = np.unwrap(np.angle(Eline))
    tau = np.gradient(phi, f) / (2 * np.pi)   # dphi/domega

    np.savez(os.path.join(OUT, "%s_raw.npz" % tag), f=f, T=T, tau=tau)
    fdtd.close()
    return f, T, tau


def main():
    print("design: lambda_B = %.1f nm, L = %.1f um, kappa = %.0f /cm, kappa*L = %.2f"
          % (lambda_B * 1e9, L * 1e6, kappa / 100, kappa * L), flush=True)

    fsp_g = os.path.join(OUT, "bragg2d.fsp")
    fsp_r = os.path.join(OUT, "ref2d.fsp")

    if not os.path.exists(fsp_g):
        print("building grating fsp ...", flush=True)
        build(fsp_g, with_grating=True)
    if not os.path.exists(fsp_r):
        print("building reference fsp ...", flush=True)
        build(fsp_r, with_grating=False)

    ref_npz = os.path.join(OUT, "ref_raw.npz")
    if os.path.exists(ref_npz):
        d = np.load(ref_npz)
        f, T_ref, tau_ref = d["f"], d["T"], d["tau"]
        print("reusing saved reference run (ref_raw.npz)", flush=True)
    else:
        print("running reference ...", flush=True)
        f, T_ref, tau_ref = run_and_extract(fsp_r, "ref")
        print("reference done. running grating ...", flush=True)
    f, T_g, tau_g = run_and_extract(fsp_g, "grating")
    print("grating done.", flush=True)

    wl = C0 / f
    np.savez(os.path.join(OUT, "bragg2d.npz"),
             f=f, wl=wl, T=T_g, R=1.0 - T_g,
             tau_g=tau_g - tau_ref,
             tau_g_abs=tau_g, tau_ref=tau_ref,
             lambda_B=lambda_B, L=L, kappa=kappa, dn=dn, n_bar=n_bar, n_core=n_core,
             N_per=N_per, Lambda=Lambda)
    print("saved results/bragg2d.npz", flush=True)
    order = np.argsort(wl)
    print("T at band center: %.4f" % T_g[order[np.argmin(np.abs(wl[order] - lambda_B))]], flush=True)


if __name__ == "__main__":
    main()
