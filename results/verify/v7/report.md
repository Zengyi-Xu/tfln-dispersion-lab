# V7 报告 — blocked（未执行）

- 原因：核查主机无 GPU（nvidia-smi 不可用），且 lidar-pointnet 仓库正文未成功取得
  （本机网络对 github.com:443 传输反复中断，仅 41M/300M+ 对象；code/outputs_m7/outputs_isal/data 均缺失）。
- 依赖：
  1. GPU 主机（torch cuda）；
  2. LiDarSim 仓库完整克隆（建议 U 盘拷贝或换网络；`data/road_objects.npz` 82MB 与 `checkpoints/` 不在 git）；
  3. V6 还需修复 `road_kitti/results.json` 键名编码（GBK 乱码 → UTF-8 英文键）。
- 任务书验收标准未降低，待 GPU 主机按 VERIFICATION_PLAN.md 第 3 节执行。
