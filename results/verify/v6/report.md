# V6 报告 — KITTI 全量复核（部分完成：road_crossing ✓，uav_cap 待续）

- 结论原文（C14）：KITTI 全量 road 0.872→**0.923**（+0.05），uav 0.758→0.857；键名乱码待修
- 脚本：`lidar-pointnet/snn/road_kitti_verify_v67.py`（新增；`--v6-only` / `--v7-only` 分段，仿真缓存复用）
- 输出：`lidar-pointnet/snn/outputs_isal/road_kitti/results_v67_verify.json`（UTF-8 英文键，乱码已修）+ `sim_cache_*.npz`
- 运行：本机 **CPU**（torch 2.14 cpu 版；无需 GPU），仿真 ~2.5 min/场景，读出 ~2–3 min/种子
- 状态：road_crossing 3 种子完成；uav_cap 仿真已缓存、读出因用户转移中断，续跑一条命令即可

## road_crossing（train 21,558 / test 7,188 固定 75% 划分，3 种子）

| 种子 | 单次 HRRP+CNN1D | 扫描链+ESN+角度 | 增益 |
|---|---|---|---|
| 0 | 0.8695 | 0.9028 | +0.033 |
| 1 | 0.8663 | 0.9207 | +0.054 |
| 2 | 0.8730 | 0.9122 | +0.039 |
| **均值±std** | **0.8696 ± 0.0033** | **0.9119 ± 0.0092** | **+0.042 ± 0.011** |

- 对照申报值 0.872 / 0.923：单次臂完全吻合；扫描链均值 0.912 落在任务书验收线
  **0.92±0.02 内（偏低沿）** ✓；增益 +0.042 ≈ 申报的 +0.05 ✓。
- **C14（road_crossing 部分）：支持**，建议表述改为「0.870±0.003 → 0.912±0.009（3 种子）」。

## per-class（扫描链臂，3 种子范围）

car 0.963–0.977 / truck 0.47–0.55 / pedestrian 0.75–0.89 / cyclist 0.50–0.66。
小类（truck 184、cyclist 385 测试样本）方差大，是绝对精度的主要拖累；混淆矩阵显示
truck↔car、cyclist↔pedestrian 是主要混淆对（与 V8 合成实验形成鲜明对比：合成上这些类全对）。

## 键名乱码修复

- 旧 `results.json` 键为中文 UTF-8（GBK 控制台显示为乱码）：`单次HRRP+CNN1D`、`4波束x3步+ESN+角度`。
- 新 JSON 统一英文键：`single_HRRP_CNN1D`、`scan4x3_ESN_angle`，并附 per-class 与混淆矩阵。
- 旧文件保留未动；数值可信（0.8724/0.9232/0.7582/0.8570 与申报一致）。

## 遗留

- uav_cap：仿真缓存已就位（`sim_cache_uav_cap.npz`），续跑 `python snn/road_kitti_verify_v67.py --v6-only` 约 10 min。
- 仿真种子口径说明：复核版对全库 28,746 对象统一用 seed_off=0 仿真（对象级种子流含 +i，train/test 天然独立），与原脚本 train=0/test=1 统计等价。
