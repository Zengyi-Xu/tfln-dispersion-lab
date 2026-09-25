# -*- coding: utf-8 -*-
"""L2: 啁啾光栅 dn=0.020 基准的网格收敛性（防幻觉核查，2026-09-25）。

只改网格：dx 10nm -> 5nm（dy 保持 20nm）。波长窗口、频点数、几何、
chirp 参数与 chirp2d 基准逐一同（隔离网格变量）。
基准已复核值：D = 0.0512 ps/nm（R>0.9 平台，tau_r 字段）。验收 ±5%。

运行（Lumerical 自带 python）：
  "E:/Program Files/ANSYS Inc/v252/Lumerical/python-3.13.1/python.exe" verify/l2_chirp_mesh.py

输出：results/verify/l2/chirp_fine_raw.npz + .fsp + _p0.log
"""
import os
import sys
import numpy as np

sys.path.append(r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python")
import lumapi  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "l2")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "lumerical"))
import run_scan_2d as rs

# ---- L2 overrides: mesh only ----
rs.OUT = OUT
rs.DX = 5e-9                  # was 10e-9; window/n_freq/geometry unchanged

L_CH = 250e-6
CHIRP_DL = 17.3e-9            # identical to run_scan_2d.main / chirp2d baseline


def main():
    print("L2 chirp mesh convergence: dx=%.1f nm (baseline 10 nm), dy=%.1f nm, "
          "L=%.0f um, dn=0.020, dLambda=%.2f nm, n_freq=%d"
          % (rs.DX * 1e9, rs.DY * 1e9, L_CH * 1e6, CHIRP_DL * 1e9, rs.n_freq),
          flush=True)
    raw = os.path.join(OUT, "chirp_fine_raw.npz")
    fsp = os.path.join(OUT, "chirp_fine.fsp")
    if os.path.exists(raw):
        print("reusing saved chirp_fine_raw.npz", flush=True)
        return
    rs.w = 1.5e-6
    if not os.path.exists(fsp):
        print("building chirp_fine ...", flush=True)
        rs.build(fsp, 0.02, L_CH, CHIRP_DL)
    print("running chirp_fine (long) ...", flush=True)
    rs.extract(fsp, "chirp_fine")
    print("L2 FDTD run done.", flush=True)


if __name__ == "__main__":
    main()
