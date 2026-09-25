# -*- coding: utf-8 -*-
"""L1: w1470/w1520 细网格 + 更宽波长采样 FDTD 重跑（防幻觉核查，2026-09-25）。

目的：排除 V2 重提取值（dλB/dw=40.65±0.53 nm/µm，κ≈607/cm）是 dx=10nm
网格/窄窗口采样造成的数值假象。

与原始 w* 运行的差异（其余全部复用 run_scan_2d 模型，不改物理）：
  - mesh override: dx 10nm -> 5nm（dy 保持 20nm；光栅指标台阶沿 x，y 向 75 格已细）
  - 波长窗口: 1515-1625nm/121pt (0.92nm) -> 1500-1640nm/281pt (0.50nm)
  - 参考波导 ref 也用细网格重跑（n_g 进 κ 公式，须同网格口径）

原始模型未改动（run_scan_2d.py 仅把 dx/dy 提为模块全局，默认值不变）。

运行（Lumerical 自带 python）：
  "E:/Program Files/ANSYS Inc/v252/Lumerical/python-3.13.1/python.exe" verify/l1_fdtd_rerun.py

输出：results/verify/l1/{ref_fine,w1470_fine,w1520_fine}_raw.npz + .fsp + _p0.log
"""
import os
import sys
import numpy as np

sys.path.append(r"E:/Program Files/ANSYS Inc/v252/Lumerical/api/python")
import lumapi  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "verify", "l1")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "lumerical"))
import run_scan_2d as rs

# ---- L1 overrides (physics identical to run_tolerance_fdtd A1 runs) ----
rs.OUT = OUT                  # extract() writes *_raw.npz here
rs.DX = 5e-9                  # was 10e-9
rs.n_freq = 281               # was 121
rs.wl_lo, rs.wl_hi = 1.500e-6, 1.640e-6   # was 1.515-1.625 um


def run_one(tag, w_nm, dn):
    raw = os.path.join(OUT, "%s_raw.npz" % tag)
    fsp = os.path.join(OUT, "%s.fsp" % tag)
    if os.path.exists(raw):
        print("reusing saved %s" % tag, flush=True)
        return
    rs.w = w_nm * 1e-9
    if not os.path.exists(fsp):
        print("building %s (w=%.0f nm, dn=%.3f, dx=%.1f nm) ..."
              % (tag, w_nm, dn, rs.DX * 1e9), flush=True)
        rs.build(fsp, dn, rs.L_uni)
    print("running %s ..." % tag, flush=True)
    rs.extract(fsp, tag)


def main():
    print("L1 fine-grid rerun: dx=%.1f nm, dy=%.1f nm, wl %.0f-%.0f nm x %d pts"
          % (rs.DX * 1e9, rs.DY * 1e9, rs.wl_lo * 1e9, rs.wl_hi * 1e9, rs.n_freq),
          flush=True)
    # reference first (n_g enters kappa); dn=0 -> plain waveguide
    run_one("ref_fine", 1500, 0.0)
    for wnm in (1470, 1520):
        run_one("w%d_fine" % wnm, wnm, 0.02)
    print("L1 FDTD runs done.", flush=True)


if __name__ == "__main__":
    main()
