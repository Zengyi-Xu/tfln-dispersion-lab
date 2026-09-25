# -*- coding: utf-8 -*-
"""CUDA (NVIDIA eGPU, RTX 3080 Ti) acceleration sanity check.

Run with the .venv-cu interpreter:
    .venv-cu/Scripts/python.exe verify/cuda_check.py

Checks:
  1. torch.version.cuda and torch.cuda availability + device name
  2. 4096x4096 fp32 matmul timing: CPU vs CUDA
  3. numerical agreement between CPU and CUDA results

Note: torch.cuda.is_available() is False while the eGPU dock is
disconnected — that is expected, not an install failure.
"""
import time

import torch

print("torch", torch.__version__, "| built for CUDA", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("cuda device:", torch.cuda.get_device_name(0))

N = 4096
a = torch.randn(N, N, dtype=torch.float32)
b = torch.randn(N, N, dtype=torch.float32)


def bench(dev, iters=10):
    x, y = a.to(dev), b.to(dev)
    for _ in range(3):
        z = x @ y
    if dev != "cpu":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(iters):
        z = x @ y
    if dev != "cpu":
        torch.cuda.synchronize()
    dt = (time.perf_counter() - t0) / iters
    tflops = 2 * N**3 / dt / 1e12
    return dt, tflops, z.float().cpu()


t_cpu, f_cpu, z_cpu = bench("cpu")
print("CPU : %.2f ms/iter, %.2f TFLOPS" % (t_cpu * 1e3, f_cpu))

if torch.cuda.is_available():
    t_gpu, f_gpu, z_gpu = bench("cuda")
    print("CUDA: %.2f ms/iter, %.2f TFLOPS  (%.1fx vs CPU)"
          % (t_gpu * 1e3, f_gpu, t_cpu / t_gpu))
    err = (z_gpu - z_cpu).abs().max().item()
    rel = err / z_cpu.abs().max().item()
    print("matmul max abs diff: %.3e (rel %.3e)" % (err, rel))
else:
    print("!! CUDA not available — expected when the eGPU dock is disconnected")
