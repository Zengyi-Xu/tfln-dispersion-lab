# -*- coding: utf-8 -*-
"""
Minimal FDTD smoke test: build a tiny straight waveguide in 2D and run.
The GUI is kept visible (hide=False) so the user can see Lumerical is active.
"""
import os
import sys
import numpy as np

sys.path.append(r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python")
import lumapi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

C0 = 299792458.0

n_core = 2.07
w = 1.5e-6
lambda0 = 1.55e-6

# very small domain and short sim time for a quick run
x_span = 12e-6
y_span_fdtd = 6e-6
sim_time = 500e-15

fsp = os.path.join(OUT, "hello_fdtd.fsp")


def S(fdtd, d):
    for k, v in d.items():
        fdtd.set(k, v)


def main():
    print("launching FDTD GUI ...", flush=True)
    fdtd = lumapi.FDTD(hide=False)
    fdtd.save(fsp)

    print("building geometry ...", flush=True)
    fdtd.addfdtd()
    S(fdtd, {
        "dimension": "2D",
        "x": 0.0, "x span": x_span,
        "y": 0.0, "y span": y_span_fdtd,
        "z": 0.0, "z span": 1e-6,
        "mesh accuracy": 1,
        "simulation time": sim_time,
        "x min bc": "PML", "x max bc": "PML",
        "y min bc": "PML", "y max bc": "PML",
    })

    fdtd.addrect()
    S(fdtd, {
        "x": 0.0, "x span": x_span,
        "y": 0.0, "y span": w,
        "z": 0.0, "z span": 1e-6,
        "index": n_core, "name": "wg",
    })

    fdtd.addmode()
    S(fdtd, {
        "injection axis": "x", "direction": "forward",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": -4.0e-6,
        "center wavelength": lambda0,
        "wavelength span": 0.1e-6,
        "set wavelength": 1,
    })

    fdtd.addpower()
    S(fdtd, {
        "monitor type": "2D X-normal",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": 4.0e-6,
        "override global monitor settings": 1,
        "frequency points": 11,
        "name": "Tpow",
    })

    fdtd.save(fsp)
    fdtd.setresource("FDTD", 1, "processes", 4)

    print("running FDTD (GUI should be visible) ...", flush=True)
    fdtd.run()
    print("FDTD run finished.", flush=True)

    Tres = fdtd.getresult("Tpow", "T")
    f = np.array(Tres["f"]).flatten()
    T = np.array(Tres["T"]).flatten()
    np.savez(os.path.join(OUT, "hello_fdtd.npz"), f=f, wl=C0/f, T=T)
    print("saved results/hello_fdtd.npz", flush=True)

    fdtd.close()
    print("done.", flush=True)


if __name__ == "__main__":
    main()
