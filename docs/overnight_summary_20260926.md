# 通宵研究总结（2026-09-26 夜，小白 · 文献会话）
## 一页导航：全部成果、关键判定、待办

> 分支 `verify/2026-09-25`。详证：`docs/rq_evidence_log.md`（33 批）、
> `docs/ising_literature_digest.md`。本文件只做导航。

## 一、最重要的五个判定

1. **我们的格子仍然空着，且全部先占已精读销项**：TFLN×RC 五家
   （Wang 2024 / Abdalla 2023 / Kong 2026 / PIC-OPO 2026 / 忆阻器 2023）
   全部全文读完。最强的 PIC-OPO（Marandi 组，实验，10 GHz）也是
   固定 τ + 电子读出 + 基准任务——**"可调色散×事件读出×雷达负载"无人占据**。
   ⚠️ 措辞纪律：禁止"首次 TFLN RC"，用"首个基于在线可调色散器件的
   时间编码处理链路"。
2. **"蓄水池不好用"有了我们自己的定量回答**（7945HX 通宵，10 种子）：
   RC 在时序任务完胜（NARMA 0.117 赢教科书 ESN 0.274、MLP 0.338），
   静态任务连线性臂都输（0.838 vs 0.987）——**领域特异性实锤，场景选错而已**。
   器件层面 sin²（真实 MZM）仅比理想 tanh 损 12% MC（23,520 run）。
3. **护城河重新定位**：渐近精度不是护城河（大预算信道任务输 Volterra/
   linear），**小训练预算 + 免校准 + 免 ADC 采样**才是。
   对应"不比精度比能效"的零号稿判据。
4. **威胁 #3（可调是否真有需求）闭环**：EO 调谐的不可替代场景 =
   高 PRF（≥1 MHz）逐脉冲波形敏捷 + 脉内重构；物理对手是 DRFM 环路
   （~0.1–1 µs）。建议目标数 3 加"调谐时间 ≤100 ns"。
   CPI 级慢切换热调即可——别踩这个坑。
5. **FTO 预警**：光子 RC 全领域仅 3 件有效专利、全归 IMEC，
   2026-03 最新 EP 覆盖"片上光学读出训练"。学术无碍，商业化前必须
   正式专利检索（digest §六）。

## 二、给同事的标准回答（三十秒版）

RC 缺席商业化 = 生态错位（前馈有现成负载、RC 要自造负载）+ 商业化通道
被电信均衡单点占据（Nokia/华为/黄超然 Science），不是潜力死刑：
Shahi 2022（被引 183）证明门控 RNN 在混沌时序上慢 RC 三个数量级；
我们自己的 2.4 万次仿真证明 RC 在时序任务赢所有数字基线、真实 MZM
非线性只损 12%。连衍射社区 2026 年都在重新发明递归（ReDON、MMF RC）。
**详细教学：`docs/rc_tutorial.md`**（原理/方法/版图/我们器件映射/FAQ 全在里面）。

## 三、文件地图

| 文件 | 内容 |
|---|---|
| `docs/rc_tutorial.md` | RC 系统教程（晨读首选） |
| `docs/rq_evidence_log.md` | 33 批逐条证据（含批次待办链） |
| `docs/ising_literature_digest.md` | 伊辛机+TFLN-RC 先占地图、Wan 组相容性、FTO 风险 |
| `docs/zero_draft_alignment_review.md` | 零号稿需要更新的句子清单（原稿未动） |
| `docs/sim10_taskbook_draft.md` | 仿真 10 骨架（等 09 结果） |
| `results/rc_designspace/` | 23,520 run：sin² vs tanh 设计空间 |
| `results/rc_vs_deep/` | 480 配置：领域特异性对打（图可直接进论文） |
| `results/rc_vs_baselines/` | 900 行：强基线边界（Volterra 反超的诚实记录） |

## 四、小黑（7945HX）队列状态

- 已完成并验收：rc_designspace ✅、rc_vs_deep ✅、rc_vs_baselines ✅
  （sanity 一处偏差已按纪律记录，双方 JSON 入档）；
- 在跑/排队：06 器件非线性 Ising 机 → 07 RC vs NGRC → 08 接口读出全量
  → 09 色散碰撞调度（任务书已在中转夹）；
- 回执与验收记录都在中转夹（RECEIPT_*.md）。

## 五、需要你做的

1. **下载**（中转夹 DOWNLOAD_REQUESTS_20260926.md，剩 3 件）：
   #1 Li ACS Photonics 2024（TFLN 伊辛机实验）、#2 Al-Kayed Nature 2025 SI、
   #4 Zhang & Cornelius RC 局限原文。#3/#5/#6 我已自行解决销项。
2. **决定零号稿是否按 `zero_draft_alignment_review.md` 更新**（11 条清单）。
3. 明早看一眼 `results/rc_vs_deep/rc_vs_deep.png`——那张图是回应
   "RC 不好用"的论文级证据。
