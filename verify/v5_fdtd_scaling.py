# -*- coding: utf-8 -*-
"""
FDTD MPI scaling benchmark on this laptop (Ultra 5 338H, 12C/12T, 32GB).

v2 fixes from the first attempt:
- fdtd.switchtolayout() before every run, otherwise run() is a no-op once
  the loaded .fsp already contains results.
- calibration pass: the initial 2D problem solved in <2 s, dominated by
  engine startup. We time one calibration run, then scale sim_time so the
  solve takes ~TARGET_SOLVE_S, making parallel scaling measurable.

Runs the identical 2D waveguide .fsp under several (processes, threads)
resource configs, measuring wall time of fdtd.run() and peak system RAM.

Output: results/verify/fdtd_scaling.json
"""
import json
import os
import sys
import threading
import time

import numpy as np
import psutil

sys.path.append(os.environ.get(
    "LUMERICAL_API_PATH", r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python"))
import lumapi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify")
os.makedirs(OUT, exist_ok=True)
FSP = os.path.join(OUT, "scaling_bench.fsp")

LAMBDA0 = 1.55e-6
N_CORE = 2.07

X_SPAN = 30e-6
Y_SPAN = 10e-6
MESH_ACCURACY = 2
SIM_TIME_CAL = 2000e-15      # calibration run length
TARGET_SOLVE_S = 45.0        # desired per-config solve time after scaling
ENGINE_OVERHEAD_S = 1.5      # rough startup portion of the calibration wall time

NCPU = os.cpu_count() or 12
if NCPU >= 16:
    # e.g. 7945HX (16C/32T Zen4, all full-size cores): more ranks should scale
    CONFIGS = [(8, 1), (12, 1), (16, 1), (8, 2)]
else:
    # 338H laptop (12C/12T hybrid 4P+4E+4LPE): measured optimum is p6_t2
    CONFIGS = [
        (6, 1),   # current stable setting in run_bragg_2d.py / run_scan_2d.py
        (8, 1),   # 4P + 4E, avoids the weak LP-E cores
        (12, 1),  # all cores; previously unstable, retest while watching RAM
        (6, 2),   # same total parallelism as 12 via threads, less MPI traffic
        (4, 3),   # P-cores only, threaded
    ]


def S(fdtd, d):
    for k, v in d.items():
        fdtd.set(k, v)


def build_fsp(sim_time):
    fdtd = lumapi.FDTD(hide=True)
    fdtd.addfdtd()
    S(fdtd, {
        "dimension": "2D",
        "x": 0.0, "x span": X_SPAN,
        "y": 0.0, "y span": Y_SPAN,
        "z": 0.0, "z span": 1e-6,
        "mesh accuracy": MESH_ACCURACY,
        "simulation time": sim_time,
        # disable early termination: with default 1e-5 the fields decay and
        # the solver stops long before sim_time, making every config run the
        # same short step count regardless of the scaled sim_time.
        "auto shutoff min": 0,
        "x min bc": "PML", "x max bc": "PML",
        "y min bc": "PML", "y max bc": "PML",
    })
    fdtd.addrect()
    S(fdtd, {
        "x": 0.0, "x span": X_SPAN,
        "y": 0.0, "y span": 1.5e-6,
        "z": 0.0, "z span": 1e-6,
        "index": N_CORE, "name": "wg",
    })
    fdtd.addmode()
    S(fdtd, {
        "injection axis": "x", "direction": "forward",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": -10.0e-6,
        "center wavelength": LAMBDA0,
        "wavelength span": 0.1e-6,
        "set wavelength": 1,
    })
    fdtd.addpower()
    S(fdtd, {
        "monitor type": "2D X-normal",
        "y": 0.0, "y span": 4.0e-6,
        "z": 0.0, "z span": 1e-6,
        "x": 10.0e-6,
        "override global monitor settings": 1,
        "frequency points": 21,
        "name": "Tpow",
    })
    fdtd.save(FSP)
    fdtd.close()


class RamSampler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.peak = 0.0
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            self.peak = max(self.peak, psutil.virtual_memory().percent)
            time.sleep(0.5)


def timed_run(processes, threads):
    """Load FSP fresh, force layout mode, time a real solve."""
    fdtd = lumapi.FDTD(hide=True)
    try:
        fdtd.setresource("FDTD", 1, "processes", processes)
        fdtd.setresource("FDTD", 1, "threads", threads)
        fdtd.load(FSP)
        fdtd.switchtolayout()
        sampler = RamSampler()
        sampler.start()
        t0 = time.perf_counter()
        fdtd.run()
        wall = time.perf_counter() - t0
        sampler.stop_event.set()
        sampler.join()
        tres = fdtd.getresult("Tpow", "T")
        t_center = float(np.array(tres["T"]).flatten()[10])
        return {"ok": True, "wall_s": round(wall, 2),
                "ram_peak_pct": sampler.peak, "T_center": round(t_center, 6)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        try:
            fdtd.close()
        except Exception:
            pass


def main():
    # --- calibration at p6/t1 with the short sim ---
    build_fsp(SIM_TIME_CAL)
    print("calibrating ...", flush=True)
    cal = timed_run(6, 1)
    print("calibration:", cal, flush=True)
    if not cal.get("ok"):
        raise RuntimeError("calibration run failed")

    solve_s = max(cal["wall_s"] - ENGINE_OVERHEAD_S, 0.5)
    scale = TARGET_SOLVE_S / solve_s
    sim_time = SIM_TIME_CAL * scale
    print(f"scaling sim_time x{scale:.1f} -> {sim_time*1e15:.0f} fs", flush=True)

    # --- rebuild at final size and benchmark all configs ---
    build_fsp(sim_time)
    results = {}
    for p, t in CONFIGS:
        tag = f"p{p}_t{t}"
        print(f"--- config {tag} ---", flush=True)
        results[tag] = timed_run(p, t)
        print(tag, results[tag], flush=True)
        time.sleep(3)  # let RAM settle between sessions

    base = results.get("p6_t1", {})
    if base.get("ok"):
        for r in results.values():
            if r.get("ok") and r["wall_s"] > 0:
                r["speedup_vs_p6"] = round(base["wall_s"] / r["wall_s"], 3)

    out = os.path.join(OUT, "fdtd_scaling.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "machine": "Ultra 5 338H, 12C/12T no HT, 32GB",
            "domain_um": [X_SPAN * 1e6, Y_SPAN * 1e6],
            "sim_time_fs": sim_time * 1e15,
            "mesh_accuracy": MESH_ACCURACY,
            "calibration": cal,
            "configs": results,
        }, f, indent=2, ensure_ascii=False)
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()
