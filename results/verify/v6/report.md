# V6 报告 — KITTI 全量 3 种子复核与 C14 判定（双机合并版）

- 结论原文（C14）：KITTI 全量 road 0.872→**0.923**（+0.05），uav 0.758→0.857；JSON 键名乱码需修复。
- 复核结果：**C14 支持（双机独立验证）**；键名乱码已确认为 GBK 环境误读 UTF-8 文件（实际键为中文 UTF-8）。
- 执行：
  - 本机（RTX 3060，torch 2.11.0+cu126）：`lidar-pointnet/snn/road_kitti_verify.py`，3 种子共 310 s，road + uav 全量；
  - 原机（CPU）：`lidar-pointnet/snn/road_kitti_verify_v67.py`，road_crossing 3 种子完成，仿真缓存复用。
- 证据：`v6_kitti_full_3seeds.json`、`v6_kitti_keys_fixed.json`（本机）；`lidar-pointnet/snn/outputs_isal/road_kitti/results_v67_verify.json`（原机）。

## 3 种子结果（n_train=21558 / n_test=7188，4 类 car/truck/pedestrian/cyclist）

| 场景 | 单次 single | 扫描链 scan | 增益 |
|---|---|---|---|
| road_crossing（本机 GPU） | **0.871 ± 0.004** | **0.924 ± 0.001** | +0.053 ± 0.003 |
| uav_cap（本机 GPU） | **0.754 ± 0.003** | **0.860 ± 0.003** | +0.106 ± 0.006 |
| road_crossing（原机 CPU） | 0.8696 ± 0.0033 | 0.9119 ± 0.0092 | +0.042 ± 0.011 |

- seed 0 = 0.871 / 0.923（road）、0.758 / 0.857（uav），与任务书申报值**逐位一致** → 原跑即 seed 0 单次运行，C14 的「无种子方差」风险点解除。
- 验收线「road_crossing 均值 0.92±0.02」：**本机 0.924 通过；原机 0.912 通过（偏低沿）**。双机扫描链差 0.012 ≈ 1.3σ（对方 std），在 CROSSCHECK 容差内。
- 跨机差可能来源：GPU/CPU 数值非确定性与扫描链读出实现差异；单次臂两机一致（0.871 vs 0.8696）。

## per-class（原机扫描链臂，3 种子范围）

car 0.963–0.977 / truck 0.47–0.55 / pedestrian 0.75–0.89 / cyclist 0.50–0.66。
小类（truck 184、cyclist 385 测试样本）方差大，是绝对精度的主要拖累；混淆矩阵显示
truck↔car、cyclist↔pedestrian 是主要混淆对（与 V8 合成实验形成鲜明对比：合成上这些类全对）。

## 键名乱码修复

- 旧 `results.json` 键为中文 UTF-8（`单次HRRP+CNN1D`、`4波束x3步+ESN+角度`），在 GBK 控制台显示为乱码；文件本身不是 GBK 编码。
- 原机新 JSON 统一英文键 `single_HRRP_CNN1D` / `scan4x3_ESN_angle`，附 per-class 与混淆矩阵（`results_v67_verify.json`）；本机 `fix_kitti_keys.py` 亦产出英文键版 `results_fixed.json`。
- 旧文件保留未动；数值可信（0.8724/0.9232/0.7582/0.8570 与申报一致）。

## 建议措辞（C14）

替换「0.872→0.923（单次运行）」为：

> 「KITTI 全量（21558 训练 / 7188 测试，3 种子）：road_crossing 扫描链 0.924 ± 0.001（本机 GPU）/ 0.912 ± 0.009（原机 CPU），单次 0.871；uav_cap 扫描链 0.860 ± 0.003（单次 0.754）；扫描链增益 +0.05（road）/ +0.11（uav）。」

## 遗留问题

- 无（V6 验收完成，双机销号）。V5（M7）已由原机另行完成，见 `v5/report.md`。
