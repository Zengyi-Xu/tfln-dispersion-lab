# -*- coding: utf-8 -*-
"""XPU (Intel Arc) acceleration sanity check.

Run with the .venv-xpu interpreter:
    .venv-xpu/Scripts/python.exe verify/xpu_check.py

Checks:
  1. torch.xpu availability + device name
  2. 4096x4096 fp32 matmul timing: CPU vs XPU
  3. OpenVINO: compile & run a small model on the "GPU" device (Arc iGPU)
"""
import time

import numpy as np
import torch

print("torch", torch.__version__)
print("xpu available:", torch.xpu.is_available())
if torch.xpu.is_available():
    print("xpu device:", torch.xpu.get_device_name(0))

N = 4096
a = torch.randn(N, N, dtype=torch.float32)
b = torch.randn(N, N, dtype=torch.float32)


def bench(dev, iters=10):
    x, y = a.to(dev), b.to(dev)
    # warmup
    for _ in range(3):
        z = x @ y
    if dev != "cpu":
        torch.xpu.synchronize()
    t0 = time.perf_counter()
    for _ in range(iters):
        z = x @ y
    if dev != "cpu":
        torch.xpu.synchronize()
    dt = (time.perf_counter() - t0) / iters
    tflops = 2 * N**3 / dt / 1e12
    return dt, tflops, z.float().cpu()


t_cpu, f_cpu, z_cpu = bench("cpu")
print("CPU : %.2f ms/iter, %.2f TFLOPS" % (t_cpu * 1e3, f_cpu))

if torch.xpu.is_available():
    t_xpu, f_xpu, z_xpu = bench("xpu")
    print("XPU : %.2f ms/iter, %.2f TFLOPS  (%.1fx vs CPU)"
          % (t_xpu * 1e3, f_xpu, t_cpu / t_xpu))
    err = (z_xpu - z_cpu).abs().max().item()
    rel = err / z_cpu.abs().max().item()
    print("matmul max abs diff: %.3e (rel %.3e)" % (err, rel))
else:
    print("!! XPU not available — check driver / wheel")

# ---- OpenVINO on Arc GPU ----
try:
    import openvino as ov
    core = ov.Core()
    print("\nopenvino devices:", core.available_devices)
    if "GPU" in core.available_devices:
        print("GPU name:", core.get_property("GPU", "FULL_DEVICE_NAME"))
        x = ov.Tensor(np.random.randn(1, 64).astype(np.float32))
        w = np.random.randn(64, 32).astype(np.float32)
        param = ov.opset13.parameter([1, 64], np.float32)
        mat = ov.opset13.constant(w)
        mm = ov.opset13.matmul(param, mat, False, False)
        relu = ov.opset13.relu(mm)
        model = ov.Model([relu], [param], "tiny")
        t0 = time.perf_counter()
        compiled = core.compile_model(model, "GPU")
        print("compile on GPU: %.2f s" % (time.perf_counter() - t0))
        res = compiled([x.data])[compiled.output(0)]
        ref = np.maximum(x.data @ w, 0)
        print("GPU inference OK, max err %.3e" % np.abs(res - ref).max())
    else:
        print("!! OpenVINO GPU device not found")
except Exception as e:
    print("openvino check failed:", repr(e))
