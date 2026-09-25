# RQ 清单（调研草案 v0.1）

> 上游文档：`论文零号稿_草稿.md`（每个 RQ 标注支撑/威胁零号稿哪一段）。
> 用法：每个 RQ 都带"锁死的自由度"和"判据"——找到判据要求的证据就停，不漫游。
> 日期：2026-09-25。主线 RQ1 优先，其余可并行。

---

## RQ1（主线·生死线）：谁真的需要"可调"色散？要多快、多大范围？

**锁死的自由度**：TFLN vs SiN——"可调"是 TFLN 唯一不可替代性来源（删部件测试结论）。
**支撑/威胁**：零号稿 b) 段与目标数 3；"可调"若无真实需求，平台防线塌。

| 子问题 | 检索关键词（中/英） | 要找的证据形态 |
|---|---|---|
| 1.1 哪些应用明确要求色散（或延迟）**动态可重构**，而非固定值？ | tunable dispersion / reconfigurable delay line / adaptive chromatic dispersion compensation; 可调色散补偿 / 可重构延迟 | 应用场景清单：相干光通信动态补偿、脉冲整形、光相控阵真时延波束形成、可编程匹配滤波……每个注明"调什么、调多快、调多大" |
| 1.2 这些应用里，现有可调方案是什么、极限在哪？ | electrically tunable grating / thermo-optic tuning speed; TFLN electro-optic tuning bandwidth | 调谐机制对比表：热光（µs–ms 级）、电光（ns 级）、机械；各自的范围 × 速度 × 功耗 |
| 1.3 LiDAR/毫米波时间模式识别这个具体场景，"可调"对应什么功能？ | adaptive matched filter photonics; programmable chirp processing; 波形敏捷雷达 光处理 | 波形捷变（agile waveform）场景下匹配滤波器必须跟随波形重配的文献；若无——"可调"需求改由别的论证承载（如多目标/多距离窗切换） |

**判据（找到就停）**：能写出一句"应用 X 要求色散在 τ 时间内改变 ΔD，现有方案 Y 做不到，因为 Z"——三个槽都有文献出处。
**反证也要记录**：若主流文献里"可调色散"需求其实由固定色散 + 可调激光波长替代（等效调延迟），则 TFLN 电光可调的必要性被削弱，必须改写零号稿。

---

## RQ2（命门）：电子 ADC+DSP 在哪个带宽/分辨率区间结构性做不起？

**锁死的自由度**：论证 a) 的成立区间——目标波形参数必须落在该区间内。
**支撑/威胁**：零号稿 a) 段全部；威胁清单第 2 条。

| 子问题 | 检索关键词 | 要找的证据形态 |
|---|---|---|
| 2.1 ADC 功耗-采样率-ENOB 的经验边界（Walden/Schreier FoM）最新到哪？ | ADC Walden FoM survey 2020s; energy per conversion step vs sampling rate | 一张"采样率 vs fJ/conversion-step"散点/边界线，标出 ≥5 GS/s、ENOB≥8 区域的功耗水平 |
| 2.2 数字匹配滤波/脉压的功耗量级？ | digital pulse compression FPGA ASIC power; radar matched filter digital implementation energy | pJ/样本 或 W @ GHz 量级的实测数字（FPGA 与 ASIC 分开记） |
| 2.3 光 ADC / 光前端替代数字化的已有论证怎么说？ | photonic ADC motivation; why optical front-end radar; 光子模数转换 动机 | 别人已经写过的"电子做不起"论证——直接引用 + 找他们没覆盖的区间（我们的差异化空间） |

**判据**：能填上零号稿 a) 段的三个空（T_chirp、B、pJ/决策），且该工作点落在 ADC FoM 边界的"贵区"。
**反证**：若目标带宽（如 <1 GHz）下商用 ADC+ASIC 已能做到 <1 pJ/决策，论证 a) 在该区间不成立——必须上移带宽或换应用。

---

## RQ3（占据图）："色散/光纤器件 + 时间域计算"已有多少人在做？

**锁死的自由度**：叙事主权——"时间既是对象又是算法"是否已被占据（威胁清单第 1 条）。
**支撑/威胁**：零号稿 c) 段的独创性声明。

| 子问题 | 检索关键词 | 要找的证据形态 |
|---|---|---|
| 3.1 色散作为计算元件 | dispersive Fourier transform computing; time-stretch computing; chromatic dispersion neural network; 色散傅里叶变换 计算 | 用色散做卷积/变换/ reservoir 的代表作，注明：是否有学习？是否可调？是否时间编码读出？ |
| 3.2 光子 SNN / 时间编码光计算 | photonic spiking neural network; temporal coding photonics; VCSEL spiking; 光子脉冲神经网络 | 现有光子 SNN 的"突触/延迟"用什么实现（多为延迟线/微环），有没有人用色散器件 |
| 3.3 时间拉伸 + 机器学习 | time-stretch analog-to-information; warped stretch machine learning | 色散前端 + 数字后端的工作，看它们的后端是不是 SNN/时间编码 |

**判据**：画出占据-开放图（横轴：前端{固定色散/可调色散/延迟线}，纵轴：后端{数字/模拟非时间编码/时间编码 SNN}），我们的格子要么空、要么能指出占据者的具体缺陷。
**反证**：若"可调色散 + 时间编码读出"已有强占位（如带学习的时间拉伸系统），独创性声明降级为"改进"，零号稿 c) 重写。

---

## RQ4（副线）：SNN vs 储备池——spike timing 读出的不可替代性

**锁死的自由度**：删部件测试第二行（SNN → 储备池故事死不死）。
**支撑**：零号稿 b) 段"同一个本体论的两半"。

- 检索：reservoir computing photonics time delay vs spiking neural network temporal coding advantages; 储备池计算 vs 脉冲神经网络 时间编码
- 要找：储备池需要掩模/虚拟节点时分复用（引入时钟与开销），而 SNN 原生吃异步 spike timing 的对比论证；色散输出是连续时间模拟信号时，哪种后端接口成本更低。
- **判据**：能写出"SNN 在接口处省掉了 X（如时分掩模时钟/采样保持），因为色散输出本身就是时间编码"或承认储备池等价、把 SNN 降级为工程选择。

---

## RQ5（副线）：集成色散器件的性能边界（对标与目标数 3）

**锁死的自由度**：目标数 3（0.05–1.6 ps/nm、摆幅 ≥100 ps）距物理上限多远（审稿人四问第 ④ 问）。
**支撑**：零号稿 b) 段与目标数表格。

- 检索：integrated chirped Bragg grating dispersion ps/nm; TFLN dispersion engineering; SiN chirped grating group delay ripple; on-chip true time delay range
- 要找：各平台已实现的最大 |D|、最大延迟摆幅、最小 ripple、调谐范围——我们已有的核查数字（1.22–1.30 ps/nm；Yu et al. 1.6 ps/nm in 2.5 mm；424–5300 ps/dB）放进这张表里定位。
- **判据**：目标数 3 的每个值能标注"已被文献实现过 / 未被实现但无物理禁阻 / 有物理上限卡在下面"。

---

## 执行顺序与产出

1. **RQ1 → RQ2**（先主线后命门，约 2–3 天）：这两条决定零号稿 a)、b) 段活不活；
2. **RQ3**（1–2 天）：占据图，决定 c) 段怎么写；
3. RQ4、RQ5 并行（各半天~1 天）；
4. 全部结束后：重做删部件测试 + 重定三个数，与零号稿 v0.1 做 diff = 调研净产出。

**记录格式**：每条证据一行——`[RQx.y] 文献 | 关键数字/声明 | 支撑或威胁零号稿哪一段 | 是否触发判据`。
