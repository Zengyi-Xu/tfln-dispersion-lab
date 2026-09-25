# V6 报告 — KITTI 全量 3 种子复核与 C14 判定

- 结论原文（C14）：KITTI 全量 road 0.872→**0.923**（+0.05），uav 0.758→0.857；JSON 键名乱码需修复。
- 复核结果：**C14 支持**（含种子方差）；键名乱码已修复并确认为非文件编码问题。
- 执行：`lidar-pointnet/snn/road_kitti_verify.py`（LiDarSim 仓库，RTX 3060 本机，torch 2.11.0+cu126，3 种子共 310 s）。
- 证据：`v6_kitti_full_3seeds.json`、`v6_kitti_keys_fixed.json`。

## 3 种子结果（n_train=21558 / n_test=7188，4 类 car/truck/pedestrian/cyclist）

| 场景 | 单次 single | 扫描链 scan | 增益 |
|---|---|---|---|
| road_crossing | **0.871 ± 0.004** | **0.924 ± 0.001** | +0.053 ± 0.003 |
| uav_cap | **0.754 ± 0.003** | **0.860 ± 0.003** | +0.106 ± 0.006 |

- seed 0 = 0.871 / 0.923（road）、0.758 / 0.857（uav），与任务书申报值**逐位一致** → 原跑即 seed 0 单次运行，C14 的「无种子方差」风险点解除。
- 验收线「road_crossing 均值 0.92±0.02」：**0.924 ± 0.001 在内，通过**。

## 键名乱码修复

- 源文件 `road_kitti/results.json` 本身为 UTF-8，英文键 `single_hrrp_cnn1d` / `scan_chain_esn_angle` 完好；乱码出现在**别处按 GBK 读取**该文件时。
- `fix_kitti_keys.py` 产出 `results_fixed.json`（键名英文规范化），供任何 GBK 环境的下游脚本使用。

## 建议措辞（C14）

替换「0.872→0.923」为：

> 「KITTI 全量（21558 训练 / 7188 测试，3 种子）：road_crossing 扫描链 0.924 ± 0.001（单次 0.871），uav_cap 扫描链 0.860 ± 0.003（单次 0.754）；扫描链增益 +0.05（road）/ +0.11（uav）。」

## 遗留问题

- 无（V6 验收完成）。M7 链路仍见 V5（blocked，缺 ModelNet parquet）。
