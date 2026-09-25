# 给另一台机器上 Kimi 的接续指令（防幻觉核查）

> 把本文件整段作为新会话的开头发给 Kimi 即可。生成日期 2026-09-25。

---

## 你的任务

这是一组 KGFP 申请支撑仿真的**结果核查（防幻觉）**任务。主仓库已经把 17 条关键结论
登记成表，其中 **2 条的证据目前不在仓库里**（可能不可复现）。你的工作是按
`VERIFICATION_PLAN.md` 逐条复算，能复现的固化证据，不能复现的给出修正措辞。

**先读这三个文件，再动手**：
1. `VERIFICATION_PLAN.md`（任务书：结论登记表 + 已确认疑点 + V1–V10）
2. `TASK_LOG.md`（项目状态与背景）
3. 本文件（执行流程）

**原则**：以数据为准，不要替原结论辩护；复现不出来就如实写「不支持」并给建议措辞。

## 环境准备

```bash
# 若 22 端口不通，一律用 443（本机就是这样 push 成功的）
git clone ssh://git@ssh.github.com:443/Zengyi-Xu/tfln-dispersion-lab.git
git clone ssh://git@ssh.github.com:443/Zengyi-Xu/LiDarSim.git lidar-pointnet
# 两个仓库必须并排放在同一父目录下（lidar 脚本按相对路径引用）
cd tfln-dispersion-lab && git checkout -b verify/2026-09-25
mkdir -p results/verify
```

依赖：`python>=3.11`，`numpy matplotlib scipy`，GPU 任务另需 `torch`(cuda)。
**数据缺口**：`lidar-pointnet/data/road_objects.npz`（82MB）不在 git 里。
有它才能跑 V6–V8；没有就先做 V1–V4 + V9，并在报告里把 V6–V8 标 blocked。
**本机没有 Lumerical**：`VERIFICATION_PLAN.md` 第 5 节的 L1–L3 直接跳过。

## 执行顺序

| 顺序 | 任务 | 算力 | 预计 | 说明 |
|------|------|------|------|------|
| 1 | **V2** A1/A2 重提取 | CPU | 5 min | **最高优先级**：判定 46 nm/µm 与 κ=594/cm 是否成立；用「最长 T<0.5 连续段」法，与旧 band_center 并排输出 |
| 2 | V1 A3/A5/A6 复核 | CPU | 10 min | 判定「1–20mm 偏差~2%」是否要改成「≥5mm ≤3%」；试 R>0.5 / R>0.9 / 去带边三种窗口 |
| 3 | V3 啁啾提取稳健性 | CPU | 10 min | R 阈值×最长连续段扫描，确认 D=0.051 与 ripple +24% |
| 4 | V4 解析式/常量核对 | CPU | 30 min | Δτ=2n_gL/c 等公式逐条对脚本行号；n_g∈{2.05,2.1,2.2,2.3} 敏感性 |
| 5 | V6 KITTI 3 种子复核 | GPU | 1 h | 需 road_objects.npz；顺手修 results.json 键名乱码（改 UTF-8 英文键） |
| 6 | V5 M7 扩 10 种子 | GPU | 1–2 h | 新增「角度加密 echo」臂验证丢角度机理 |
| 7 | V7 预算扫描 | GPU | 2–3 h | 1200/3000/6000/12000/21558 × 3 种子 |
| 8 | V8 合成↔真实一致性 | GPU | 1 h | 同 4 类口径对比 |
| 9 | V9 文献常量核查 | 联网 | — | TFLN/SiN/Si 损耗、dn/dT、n_g；影响 C1/C6 |
| 10 | V10 文书数字一致性 | CPU | 30 min | 需 Concept Note 第二版 docx；没有就跳过并在报告说明 |

每个任务的详细验收标准见 `VERIFICATION_PLAN.md` 第 3 节，不要自己降低标准。

## 提交规范

- 所有结果写 `results/verify/<任务号>/`，每个任务附一份 `report.md`（模板见任务书第 6 节）。
- 若产出了可复用的提取脚本（V2 的「最长连续段」重提取一定要），放到 `verify/` 目录一并提交。
- 完成后回填 `TASK_LOG.md`（每条的最终结论 + 证据路径），然后：
  ```bash
  git add -A && git commit -m "verify: Vx ... 结论"
  git push ssh://git@ssh.github.com:443/Zengyi-Xu/tfln-dispersion-lab.git verify/2026-09-25
  ```

## 最终汇报格式

```
## 核查结果总表
| 结论# | 复核结果 | 旧值 → 新值 | 证据路径 |
（17 条逐条填：支持 / 部分支持 / 不支持 / 未执行及原因）

## 必须修改的表述
（列出 Concept Note / TASK_LOG / 推荐信里需要改写的句子，给替换文本）

## 遗留
（blocked 任务与原因）
```

**特别提醒**：V2 的结果直接决定 A1 条宽窗口（46 nm/µm）这条写进申请书 Objective 1 的结论
是否成立，务必先做、做仔细；w1470/w1520 两点曾出现带隙提取误判，判据用残差 >3σ 或非单调。
