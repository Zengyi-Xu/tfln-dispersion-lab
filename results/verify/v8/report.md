# V8 报告 — 合成↔真实一致性（同预算对照）

- 结论原文（C16）：合成 0.892/0.919 与真实 0.923 「惊人一致」→ 生成器被背书
- 脚本：`lidar-pointnet/snn/road_synth_verify_v8.py`（新增）
- 输出：`lidar-pointnet/outputs_isal/road_synth_v8/results_v8.json`
- 运行：本机 CPU，3.5 min

## 方法

用 `road_vehicles.py` 的参数化生成器重建数据集，**严格对齐 KITTI 全量预算**：
- 同样 4 类合并口径：car=sedan+suv、truck=truck+bus、pedestrian、cyclist=motorcycle+bicycle
- 同样的每类训练/测试数（取自 KITTI split(seed=0)）：
  train = {car 16570, truck 552, pedestrian 3282, cyclist 1154}（共 21,558），
  test = {5524, 184, 1095, 385}（共 7,188）
- 同样的仿真链（make_dataset_fast）与读出（CNN1D 100 ep / ESN+角度 200 ep，种子 0）

## 关键数字

| 场景 | 臂 | 合成（同预算） | KITTI 真实（全量） | 差距 |
|---|---|---|---|---|
| road_crossing | 单次 HRRP+CNN1D | **0.979** | 0.872（V6 复核 0.870） | **+10.7 pt** |
| road_crossing | 扫描链+ESN+角度 | **1.000** | 0.923（V6 seed0 0.903） | **+7.7 pt** |
| uav_cap | 单次 | 0.963 | 0.758 | +20.5 pt |
| uav_cap | 扫描链 | 0.999 | 0.857 | +14.2 pt |

合成数据的 per-class：truck/cyclist 小类在合成上也被轻松分开（混淆矩阵几乎对角），
而 KITTI 上 truck=0.26–0.50、cyclist=0.06–0.65（V6 复核），难度完全不在一个量级。

## 判定

- **C16：不支持**。原「一致性」是**不同任务口径下的巧合**：旧合成数字 0.892/0.919 来自
  350/类小预算 + 7 类（road_vehicles）或 2 类（car/person）任务；一旦把预算和类合并口径
  拉平到 KITTI 全量，合成精度冲到 0.96–1.00，与真实 0.87–0.92 差 8–21 个百分点。
- 物理解读：参数化生成器没有真实遮挡/截断/类内多样性（KITTI 的 truck 与 car 外观高度
  重叠、cyclist 小样本且形态多变），判别难度被系统性低估。

## 建议措辞（可写进论文的一句）

「参数化合成基准用于**协议对比**（单次 vs 扫描链的相对增益趋势与真实数据一致：
合成 +2.1 pt、KITTI +5.1 pt，方向与单调性吻合），但其绝对精度不能标定真实任务难度
——同预算下合成比 KITTI 高 8–11 pt（road_crossing），生成器缺少真实遮挡与类内多样性。
90% 级精度的声称应仅引用 KITTI 结果（0.923），不引用合成数字。」

## 遗留问题

- 若要「生成器标定」，需给合成链加遮挡/截断模型与类内形变（超出本任务范围）。
- uav_cap 差距更大（+14–21 pt）进一步印证该场景与车端几何不匹配（TASK_LOG 已有此结论）。
