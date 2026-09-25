# 7945HX 主机端回执

> 本文档由 7945HX 主机端的 Kimi 生成，供 338H 本端查收与合并分析。
> 对应任务：`HANDOFF_TO_7945HX.md`（338H 端下发）。

---

## 一、主机环境确认

| 项目 | 实测值 |
|---|---|
| CPU | AMD Ryzen 9 7945HX（16C/32T，Zen 4，全大核 + SMT） |
| GPU | NVIDIA GeForce RTX 4050 Laptop（6 GB） |
| Lumerical | Ansys Lumerical v252，路径 `D:\LUMERICAL_2025R2\ANSYS Inc\v252\Lumerical` |
| Python | Conda 环境 `tfln-lab`（Python 3.10） |
| 许可证 | 已确认可用，FDTD 引擎可正常启动 |

已设置环境变量（用户级持久化）：

```powershell
LUMERICAL_API_PATH = D:/LUMERICAL_2025R2/ANSYS Inc/v252/Lumerical/api/python
FDTD_PROCESSES     = 8
FDTD_THREADS       = 1
```

---

## 二、并行配置基准

已执行 `verify/v5_fdtd_scaling.py`（30×10 µm 2D 波导，44.8 ps 等效求解）。

| 配置 | 耗时 | 备注 |
|---|---|---|
| p8_t1 | **42.01 s** | ✅ 选定配置 |
| p12_t1 | 45.96 s | 收益下降 |
| p16_t1 | 46.09 s | 同步开销抵消额外核心 |
| p8_t2 | 44.02 s | 线程版略慢 |

**结论**：7945HX 在该基准问题上最优为 **8 进程 × 1 线程**。

> 注：此前直接对 `run_bragg_2d.py` 的测试显示 12 进程比 6 进程快约 37%，但 v5 统一基准显示 8 进程更优。本次按 HANDOFF 要求以 v5 结果为准设置 env var；若后续发现特定仿真问题在 12 进程下更快，可临时覆盖。

---

## 三、正式仿真执行记录

| 脚本 | 耗时 | 产物 |
|---|---|---|
| `lumerical/run_bragg_2d.py` | 23.6 s | `lumerical/results/bragg2d.npz` |
| `lumerical/run_scan_2d.py` | 22.5 s | `lumerical/results/chirp2d.npz`、`chirp_raw.npz`、`scan_dn.npz` |

说明：
- `run_bragg_2d.py` 复用了仓库中的 `ref_raw.npz`，仅重新跑了光栅部分。
- `run_scan_2d.py` 复用了已有的 `dn010` / `dn040` 等结果，仅重新跑了啁啾扫描。
- 所有产物与 338H 端历史结果在物理量上保持一致（例如 Bragg 带隙中心透射率 ~0.001586）。

---

## 四、推回 338H 的文件

已随本次提交推送至 `origin/verify/2026-09-25`：

```
lumerical/results/bragg2d.npz
lumerical/results/chirp2d.npz
lumerical/results/chirp_raw.npz
lumerical/results/scan_dn.npz
lumerical/results/grating_raw.npz
results/verify/fdtd_scaling.json
results/verify/scaling_bench.fsp
results/verify/scaling_bench_p0.log
verify/v5_fdtd_scaling.py   （仅更新 machine 字段为 7945HX）
本文件：HANDOFF_FROM_7945HX.md
```

---

## 五、合并时请注意

1. **MPI 配置冲突已解决**  
   我本地曾硬编码 `processes=12`，338H 端改为 `FDTD_PROCESSES` / `FDTD_THREADS` 环境变量。合并后保留环境变量方案，7945HX 通过设 `8/1` 生效，338H 端不设则默认 `6/2`。

2. **v5 基准脚本**  
   `verify/v5_fdtd_scaling.py` 中的 `machine` 字段已改为 `"Ryzen 9 7945HX, 16C/32T Zen4"`。若 338H 端后续仍需跑同一脚本，建议把该字段改回或改为可配置。

3. **新拉取的 338H 文件**  
   推送前已拉取到 338H 端新增的 `verify/l1_*.py`、`verify/l2_*.py`、`verify/l3_*.py` 及对应结果，合并无冲突。

---

## 六、待 338H 端确认/下一步

- [ ] 拉取 `verify/2026-09-25` 最新提交
- [ ] 合并分析 `lumerical/results/*.npz`
- [ ] 如需继续跑 L1/L2/L3 验证链，可再发 HANDOFF 到 7945HX 端

---

**生成时间**：2026-09-26  
**生成端**：7945HX 主机端 Kimi
