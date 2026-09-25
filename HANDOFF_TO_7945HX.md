# 接管说明：在 7945HX 主机上运行本项目的 Lumerical 仿真

> 本文档由 338H 本端（Ultra 5 338H 笔记本）的 Kimi 编写，供 7945HX 主机端的 Kimi 阅读执行。
> 目标机器：Ryzen 9 7945HX（16C/32T Zen4，全规格大核 + SMT）。

## 一、需要传输的文件

整个仓库（推荐 git，或直接复制以下目录）：

- `lumerical/` — 仿真脚本（`run_bragg_2d.py`、`run_scan_2d.py` 等）
- `simulations/` — Python 端仿真
- `verify/v5_fdtd_scaling.py` — FDTD 并行配置基准（**先跑这个**）
- `lumerical/results/` 下已有的 `.fsp` / `.npz`（`ref2d.fsp`、`ref_raw.npz` 被扫描脚本复用，务必带上）

## 二、前提检查（按顺序）

1. **Lumerical 安装**：确认 Ansys Lumerical v252（或兼容版本）已安装，记下安装路径。
2. **许可证**：确认引擎（Accelerator）许可配额足够；CPU 求解每个 MPI 进程消耗配额。
3. **lumapi 路径**：脚本通过环境变量 `LUMERICAL_API_PATH` 定位 lumapi，
   默认值是本端的 `E:/Program Files/ANSYS Inc/v252/Lumerical/api/python`。
   若主机安装路径不同，设置：
   ```powershell
   setx LUMERICAL_API_PATH "D:/Program Files/ANSYS Inc/v252/Lumerical/api/python"
   ```
4. **Python**：用 Lumerical 自带 Python 即可（`v252/Lumerical/python-3.13.1/python.exe`），
   需要 `numpy`、`matplotlib`、`psutil`：
   ```
   <lumerical_python> -m pip install numpy matplotlib psutil
   ```

## 三、第一步必做：并行配置基准

**不要直接沿用本端的 6 进程 × 2 线程**——那是针对 338H 混合架构（4P+4E+4LPE）调出来的。
7945HX 是 16 个全规格核，scaling 特性完全不同。基准脚本已按核数自动切换配置组
（≥16 核时测 p8t1 / p12t1 / p16t1 / p8t2）：

```
<python> verify/v5_fdtd_scaling.py
```

约 5~10 分钟，结果写入 `results/verify/fdtd_scaling.json`。
取最快的 `pX_tY` 组合，设为环境变量：

```powershell
setx FDTD_PROCESSES 12
setx FDTD_THREADS 1
```

`run_bragg_2d.py` / `run_scan_2d.py` 会读取这两个变量（默认值 6×2 是 338H 的最优，不设也不会错，只是未必最快）。

## 四、运行仿真

```
<python> lumerical/run_bragg_2d.py     # 均匀光栅 + 参考波导
<python> lumerical/run_scan_2d.py      # dn 扫描 + 啁啾光栅
```

产物在 `lumerical/results/`（`.npz`）。跑完把该目录传回 338H 本端做分析绘图。

## 五、已知坑（本端踩过，复现时注意）

1. Lumerical 的 2D FDTD 是 **Z-normal**（XY 面内传播），沿 z 布局会报 "z min bc inactive"
2. lumapi 批量 `set({...})` 不可靠，脚本里已改为逐属性 `set(k, v)`，新代码请保持
3. 监视器设频点前先 `override global monitor settings = 1`
4. 复场监视器的 E 是 5 维 `(x, y, z, f, component)`，取相位前**先选主导偏振分量**
5. 338H 端曾有"12 进程丢 engine"的记录——实测是混合核导致的 4.5 倍减速误判；
   7945HX 无此问题，但跑基准时仍留意 engine 稳定性

## 六、参考基准（338H 本端实测，供对比）

- 基准问题（30×10 µm 2D 波导，44.8 ps，禁用 auto-shutoff）：6×2 配置 **26.1 s**
- 7945HX 预期 **10~13 s**（约 2×）；若实测偏离很大，检查许可证/进程配置

## 七、称呼约定

双机协作期间：本机自称「7945HX 主机端」，对方是「338H 本端」，避免"这台电脑"歧义。
