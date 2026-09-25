# RQ 证据日志（通宵调研产出）

> 配套 `RQ清单_调研草案.md` / `论文零号稿_草稿.md`。格式：`[RQx.y] 文献 | 关键数字/声明 | 支撑/威胁零号稿哪段 | 判据`。
> 起始日期 2026-09-26。维护：小白（文献会话）。所有数字引用公开来源，写论文前需按引用规范二次核实原文。

---

## 2026-09-26 第一批：RQ1（可调色散需求）+ RQ2（电子 ADC 边界）

### RQ1.1/RQ1.2 主证据：光真时延（OTTD）波束形成综述

- [RQ1.1/RQ1.2] An T. et al., "A review of research on optical true time delay technology", J. Eur. Opt. Society-Rapid Publ. 21, 2 (2025)（[全文](https://jeos.edpsciences.org/articles/jeos/full_html/2025/01/jeos20240056/jeos20240056.html)）| 宽带相控阵**结构性需要** TTD：相移器方案孔径效应限制相对带宽 Δf/f₀ ≤ 1–2%（扫到 60°、波束宽 1–2° 时），L 波段 1.3 GHz 雷达只剩 13–26 MHz 瞬时带宽，"远不足以满足高分辨成像"；TTD 使指向角与频率解耦 | **支撑**零号稿 b)（色散/延迟器件的真实应用牵引）；支撑 RQ1 主线 | 部分触发判据（给了"为什么需要"，还需"调多快"）
- [RQ1.2] 同上综述 §5 四路线对比 | 现有可调延迟方案的极限表（全部集成/半集成）：
  - 微环阵列：连续可调、范围大（Burla 2013 Ku 波段 236 ps；Xiang 2018 SiN SCISSOR 500 ps；Shan 2021 带宽 16 GHz、范围 160 ps、步进 20 ps），**但调谐是热调 → 波束切换慢（µs–ms 级）**；
  - 光栅延迟线：易集成，但离散不可连续调、或需扫波长（LCFBG 5-bit 0–168.6 ps、精度 2.46 ps；Sun 2020 SOI SWG 光栅步进 6.6 ps/范围 60 ps；Wang 2021 40 级 SWG 范围 181.9 ps@10 GHz 带宽；Srivastava 2020 RCFBG 精度 0.2 ps/范围 200 ps、Ku 波段 ±36.8° 无斜视扫描）；
  - 多路开关延迟线：**切换 ns 级**（电光开关），但离散、精度低（Pérez-López 2018 mesh 13.5 ps/步、最大 148.5 ps；Zhu 2020 Optica 1×8 波束成形器 0–496 ps）；
  - 波长选择型：范围大（Duan 2017 最大 20 µs）但依赖快速连续可调激光器 | **支撑** RQ1.2 对比表全部三槽 | ✅ 触发判据
- **RQ1 判据句（v0.1，可写进零号稿）**：宽带相控阵波束形成要求真延迟在**连续、≥100 ps 范围、ns–µs 切换**三个指标上同时达标；现有集成方案中微环（热调）慢、光开关离散、波长扫描依赖昂贵快调激光——"连续 × 大范围 × 电光 ns 级调谐"的交集在集成平台上未被占据，而 TFLN 电光调谐色散器件恰好落在这个交集。三槽出处：JEOS-RP 2025 综述（需求侧 + 微环热调慢）、Srivastava IEEE T-MTT 2020（光栅方案精度/范围）、Pérez-López JLT 2018（开关方案 ns 但离散）。
- [RQ1.1 反证，必须记录] 相干光通信的"可调色散补偿"需求已被数字 DSP 吸收：现代相干接收机在电域用均衡算法补偿 CD（如 ResearchGate 2024 widely-linear 均衡工作），ITU-T G.667 时代的可调光补偿器需求主要来自动态路由 WDM 的 40 Gbit/s 时代 | **威胁**零号稿 RQ1 主线若走电信场景——**电信不是可调色散的好需求**，需求论证必须落在雷达/波束形成/脉冲整形等"检测前处理"场景 | ✅ 反证记录完毕，RQ1 应用清单应剔除电信动态补偿

### RQ2.1 主证据：ADC 能效边界

- [RQ2.1] Murmann ADC Performance Survey 1997–2026（ISSCC+VLSI 数据，[github.com/bmurmann/ADC-survey](https://github.com/bmurmann/ADC-survey)）| 论文级权威数据源；公认趋势：采样率超过 ~1 GS/s 后 Walden FoM 系统性恶化（架构前沿 vs 技术前沿分叉）| 支撑零号稿 a) 的"互锁"声明 | 需从数据集提取 ≥5 GS/s、ENOB≥8 区域散点（可本地跑数据出图）
- [RQ2.1] TI ADC12DJ5200RF（[产品页](https://www.ti.com/product/ADC12DJ5200RF)，商用 RF 直采标杆）| 10.4 GS/s 单通道、12-bit 标称、**ENOB 8.6–8.8、功耗 4 W** → 385 fJ/样本（≈1 fJ/conv-step，已是该速率下世界级水平）；输入带宽 8 GHz，可用输入 >10 GHz | 支撑 a)：一次匹配滤波需 TBP~10³ 样本 → 仅 ADC 就 ~10²–10³ pJ/决策，还没算 DSP；且这是桌面级功耗，机载/星载不可承受 | ✅ 提供锚点
- [RQ2.1 结构性上限] 孔径抖动限制：SNR_jitter = −20log₁₀(2π f_in σ_j)。σ_j=50 fs 时 f_in=20 GHz → SNR≈44 dB → **ENOB≈7**；f_in=60 GHz → ENOB≈5.7。抖动随工艺改善缓慢（十年改善 <4×），这是 a) 段"ENOB-采样率互锁"的物理根源 | 支撑 a) | ✅ 可写公式进零号稿

### 待办（下一批）

- RQ2.2：数字脉压/匹配滤波 FPGA/ASIC 功耗实测数字；
- RQ2.3：光子 ADC 动机综述（找别人写过的"电子做不起"论证，划差异化区间）；
- RQ3.1：time-stretch/色散计算占据图（部分已在 ising_literature_digest §三）；
- 用 Murmann 数据集出"fs vs fJ/step"边界图（本地脚本，标注我们目标工作点）。
