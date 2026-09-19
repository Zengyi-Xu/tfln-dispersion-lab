# -*- coding: utf-8 -*-
"""Re-extract phase/group-delay from saved .fsp results (no solver rerun).

The original run_bragg_2d.py flattened the complex E field incorrectly
(mixed the 3 field components), giving meaningless phases. This script
loads the completed runs from the .fsp files, picks the dominant field
component at the ridge center, and rebuilds bragg2d.npz.
"""
import os
import sys
import numpy as np

sys.path.append(r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python")
import lumapi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
C0 = 299792458.0


def extract(fsp, tag):
    fdtd = lumapi.FDTD(hide=True)
    fdtd.load(fsp)

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
    tau = np.gradient(phi, f) / (2 * np.pi)
    print("%s: dominant component E[%d], tau mean = %.4f ps"
          % (tag, comp, np.mean(tau) * 1e12), flush=True)

    fdtd.close()
    return f, T, tau, comp


def main():
    d = np.load(os.path.join(OUT, "bragg2d.npz"))
    lambda_B, L = d["lambda_B"], d["L"]
    kappa, dn, n_bar = d["kappa"], d["dn"], d["n_bar"]
    n_core = d["n_core"] if "n_core" in d else 2.07

    f, T_ref, tau_ref, _ = extract(os.path.join(OUT, "ref2d.fsp"), "ref")
    f, T_g, tau_g, _ = extract(os.path.join(OUT, "bragg2d.fsp"), "grating")

    wl = C0 / f
    np.savez(os.path.join(OUT, "bragg2d.npz"),
             f=f, wl=wl, T=T_g, R=1.0 - T_g,
             tau_g=tau_g - tau_ref,
             tau_g_abs=tau_g, tau_ref=tau_ref,
             lambda_B=lambda_B, L=L, kappa=kappa, dn=dn, n_bar=n_bar,
             n_core=n_core, N_per=d["N_per"], Lambda=d["Lambda"])
    print("rebuilt results/bragg2d.npz", flush=True)


if __name__ == "__main__":
    main()
