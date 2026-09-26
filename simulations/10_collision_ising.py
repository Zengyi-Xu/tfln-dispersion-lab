# -*- coding: utf-8 -*-
"""10: 碰撞调度 × 共享增益混频的结构化伊辛退火机（sim10，设计草案定稿版）。

依据：docs/sim10_design_draft.md（rq 第五十五/六十一/六十四批全部依赖已齐）。
物理链：自旋=波长 λ_i=i·Δλ（N=32，Δλ=0.2 nm，09 S4 可行性绿灯档），
高斯脉冲 σ_t=10 ps；GD 剖面 τ(λ) 决定到达时序，碰撞重叠
O_ij=exp(−(τ_i−τ_j)²/2σ_t²)=耦合强度；反铁磁 J=−O（零对角）。
共享增益混频器唯象模型（草案 §3）：测得局域场为压缩函数
  h_meas = P_sat · h_true / (P_sat + swing·|h_true|)
P_sat 标定到典型摆幅的 20–80% 压缩甜区（增益定标共同纪律）；
臂 D 把 swing×3 打进深饱和——按草案 §7 必须显著劣化，否则模型有误。

实验臂（草案 §6）：
  A 天花板：理想 Toeplitz 核 + 理想混频器（exp3=e^(−d/3)、pow15=d^−1.5、
    gauss=原生高斯 D=10）
  M 混频器代价：理想核 + XGM 箝位混频器（隔离臂 B/C 的核退化与混频惩罚）
  B GDR 退化（09 S2 路线：τ 加 A=3 ps/p=0.5 nm 正弦波纹，φ×3）
  C 拟合核（09 S3 实测拟合 GD 节点重建 exp3/pow15 实现核）
  D 失箝扫描（swing {3,10,30}，exp3 核）——本地 inst=0 标定结果：
    单调压缩**无折返失效**（30× 过驱动仅 0.926→0.860，−7%，仍高于
    理想混频器天花板臂）——06 sin² 的"增益定标纪律"不迁移到单调
    XGM（纪律的对象是非单调性，不是摆幅本身）；AGC 归一化对照
    （rms_ref≠1）下压缩甚至单调有益（软箝位整形）。固定增益接收机
    （rms_ref=1）为默认口径。

动力学（混合态，本地标定后定稿）：光学=强度脉冲有无 x=Θ(v)，电子=
双极模拟态 v（tanh 更新，06/06b 已验证）；混频器=强度和 S=O@x 单调
压缩 + x=0.5 参考直流差分扣除（草案 §2 差分读出）。P_sat 标定到 P80
摆幅 ~1/3 压缩（甜区 20–80%）。纯 sigmoid QUBO 动力学（v1 草案）本地
实测比混合态差 8–13pt（exp3 0.82 vs 0.91+），已弃用。
调度：beta_ramp（06b 定稿，rq 第六十四批；与 IPIM OPCS 实验互证）。
双指标（草案 §5）：
  self   = E_realized/E_BK(realized J)   退火质量
  target = E_target(σ*)/E_BK(target J)   核退化代价（臂 B/C 的关键指标）
SA 基准复用 06（同种子纪律）。输出 results/collision_ising/results.jsonl。
用法同 06b：--quick/--workers/--aggregate。
"""
import argparse
import importlib
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_m06 = importlib.import_module("06_ising_nonlinearity")

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "collision_ising")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

# --- 器件层（09 参考档，rq 第五十五批） ---
N = 32
DLAM = 0.2            # nm
SIG_T = 10.0          # ps（intensity FWHM 约定的重叠宽度）
D_GAUSS = 10.0        # ps/nm，原生高斯核档（d* = √2·σ_t/(D·Δλ) ≈ 7.1）
A_GDR, P_GDR = 3.0, 0.5     # GDR 波纹：我们 CBG 实测量级（09 S2 → ~6% 偏差）
ITERS = 300

# 09 S3 实测拟合 GD 节点（results/dispersion_ising_coupling/results.jsonl）
FIT_KNOTS = {
    "exp3": [0.0, 27.4, 81.8, 271.3, 282.3, 296.6, 318.1],
    "pow15": [0.0, 37.1, 74.5, 83.5, 120.5, 160.1, 197.2],
}


def overlap(dt):
    return np.exp(-(dt ** 2) / (2 * SIG_T ** 2))


def kernel_from_tau(tau):
    """延迟剖面 → 反铁磁耦合矩阵（零对角）。"""
    O = overlap(tau[:, None] - tau[None, :])
    np.fill_diagonal(O, 0.0)
    return -O


def target_kernel(name):
    d = np.arange(N)
    if name == "exp3":
        K = np.exp(-d / 3.0)
    elif name == "pow15":
        with np.errstate(divide="ignore", invalid="ignore"):
            K = np.where(d == 0, 1.0, d ** -1.5)
    elif name == "gauss":
        K = np.exp(-((d * D_GAUSS * DLAM) ** 2) / (2 * SIG_T ** 2))
    else:
        raise ValueError(name)
    J = -K[np.abs(np.arange(N)[:, None] - np.arange(N)[None, :])]
    np.fill_diagonal(J, 0.0)
    return J


def tau_fitted(name):
    lam = np.arange(N) * DLAM
    lam_knots = np.linspace(lam[0], lam[-1], len(FIT_KNOTS[name]))
    return np.interp(lam, lam_knots, FIT_KNOTS[name])


def tau_gdr(phi):
    i = np.arange(N)
    return (D_GAUSS * DLAM * i
            + A_GDR * np.sin(2 * np.pi * (DLAM * i) / P_GDR + phi))


def mixer_field(J, x, swing, p_sat, mixer, rms_ref):
    """局域场读出。x=脉冲有无(0/1)。
    ideal: 直接 (J/√N)@(2x−1)（天花板，无混频器物理）。
    xgm:   强度和 S=O@x 经单调压缩 P_sat·S/(P_sat+S)，减去 x=0.5 参考
           直流（差分读出，草案 §2/§3），形状失真保留。
    两种模式都除以各自在随机 x 下的 RMS（AGC 校准），使 β 跨模式同义。"""
    if mixer == "ideal":
        hh = (J / np.sqrt(N)) @ (2 * x - 1)
    else:
        O = -J
        np.fill_diagonal(O, 0.0)
        S = swing * (O @ x)
        comp = p_sat * S / (p_sat + S)
        sbar = swing * (O @ np.full(N, 0.5))
        cbar = p_sat * sbar / (p_sat + sbar)
        hh = -(comp - cbar) / np.maximum(cbar, 1e-9)
    return hh / rms_ref


def field_rms(J, swing, p_sat, mixer):
    """随机 x 下未归一化场的 RMS（AGC 基准）。"""
    rng = np.random.default_rng(11)
    vals = []
    O = -J
    np.fill_diagonal(O, 0.0)
    sbar = swing * (O @ np.full(N, 0.5))
    cbar = p_sat * sbar / (p_sat + sbar)
    for _ in range(100):
        x = (rng.uniform(0, 1, N) > 0.5).astype(float)
        if mixer == "ideal":
            hh = (J / np.sqrt(N)) @ (2 * x - 1)
        else:
            S = swing * (O @ x)
            comp = p_sat * S / (p_sat + S)
            hh = -(comp - cbar) / np.maximum(cbar, 1e-9)
        vals.append(hh)
    return float(np.sqrt(np.mean(np.asarray(vals) ** 2)))


def run_anneal(J, alpha, beta, noise0, swing, p_sat, mixer="xgm",
               iters=ITERS, seed=0, track_spin=False, rms_ref=None):
    """混合态动力学：光学=强度脉冲（x=Θ(v)），电子=双极模拟态 v(tanh)。
    beta_ramp 调度（06b 定稿）。返回 (best_E, traj[, best_s])。"""
    rng = np.random.default_rng(seed)
    if rms_ref is None:
        rms_ref = field_rms(J, swing, p_sat, mixer)
    v = rng.uniform(-0.1, 0.1, N)
    best = np.inf
    best_s = None
    traj = []
    for k in range(iters):
        m = 1 - k / iters
        g = min(1.0, k / (0.5 * iters))           # beta_ramp（06b 定稿）
        x = (v > 0).astype(float)                 # 光学发射：脉冲有无
        hh = mixer_field(J, x, swing, p_sat, mixer, rms_ref)
        v = np.tanh(alpha * v + g * beta * hh
                    + noise0 * m * rng.normal(0, 1, N))
        s = np.sign(v)
        s[s == 0] = 1
        E = _m06.energy(J, s)
        if E < best:
            best = E
            if track_spin:
                best_s = s.copy()
        traj.append(best)
    if track_spin:
        return best, np.asarray(traj), best_s
    return best, np.asarray(traj)


def calibrate_p_sat(J):
    """P_sat 标定：随机 x 下强度和 S=O@x 的 P80 映射到 ~1/3 压缩
    （增益压缩甜区 20–80%，草案 §3 共同纪律）。"""
    rng = np.random.default_rng(7)
    O = -J
    np.fill_diagonal(O, 0.0)
    Ss = np.abs(O @ rng.uniform(0, 1, (N, 200)))
    return 2.0 * np.percentile(Ss, 80)


def run_config(cfg):
    t0 = time.time()
    out = dict(cfg)
    try:
        # --- 实现核（臂定义） ---
        if cfg["arm"] in ("A", "M"):
            J_real = target_kernel(cfg["kernel"])
            J_tgt = J_real
        elif cfg["arm"] == "B":
            J_real = kernel_from_tau(tau_gdr(cfg["phi"]))
            J_tgt = target_kernel("gauss")
        elif cfg["arm"] == "C":
            J_real = kernel_from_tau(tau_fitted(cfg["kernel"]))
            J_tgt = target_kernel(cfg["kernel"])
        elif cfg["arm"] == "D":
            J_real = target_kernel("exp3")
            J_tgt = J_real
        else:
            raise ValueError(cfg["arm"])

        bk_real = _m06.sa_reference(J_real, iters=60000,
                                    seed=cfg["inst"] * 7 + 1)
        bk_tgt = bk_real if cfg["arm"] in ("A", "M", "D") else \
            _m06.sa_reference(J_tgt, iters=60000, seed=cfg["inst"] * 7 + 1)
        out["bk_real"] = float(bk_real)
        out["bk_tgt"] = float(bk_tgt)

        mixer = "ideal" if cfg["arm"] == "A" else "xgm"
        swing = cfg.get("swing", 1.0)
        p_sat = calibrate_p_sat(J_real)
        # 固定增益接收机（rms_ref=1，无 AGC）：本地对照显示 AGC 会把深饱和
        # 的对比度损失一阶抵消（单调压缩反而成软箝位、单调有益），为看到
        # 真实的失箝容限必须固定增益——这本身是可报告物理（rq 待入库）。
        rms_ref = 1.0
        thr = 0.97 * bk_real
        n_runs = 2 if cfg.get("quick") else 5
        self_r, tts = [], []
        best_s0, best_r0 = None, None
        for r in range(n_runs):
            if r == 0:
                b0, traj, best_s0 = run_anneal(
                    J_real, cfg["alpha"], cfg["beta"], cfg["noise"],
                    swing, p_sat, mixer, seed=cfg["inst"] * 100 + r,
                    track_spin=True, rms_ref=rms_ref)
                best_r0 = b0
            else:
                _, traj = run_anneal(J_real, cfg["alpha"], cfg["beta"],
                                     cfg["noise"], swing, p_sat, mixer,
                                     seed=cfg["inst"] * 100 + r,
                                     rms_ref=rms_ref)
            self_r.append(traj[-1] / bk_real)
            hit = np.nonzero(traj <= thr)[0]
            tts.append(int(hit[0]) if len(hit) else ITERS)
        out["metric"] = float(np.mean(self_r))
        out["metric_name"] = "energy_ratio_self"
        out["success"] = float(np.mean([r >= 0.97 for r in self_r]))
        out["tts_mean"] = float(np.mean(tts))
        # 目标保真（臂 B/C）：r=0 的 best 自旋在目标 J 下的能量
        if cfg["arm"] in ("B", "C"):
            E_t = _m06.energy(J_tgt, best_s0)
            out["target_ratio"] = float(E_t / bk_tgt)
        out["ok"] = True
    except Exception as e:  # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    return out


ARMS = [
    # A 天花板：理想核+理想混频器；M 混频器代价：理想核+XGM 箝位
    *[{"arm": "A", "kernel": k, "phi": None} for k in ("exp3", "pow15", "gauss")],
    *[{"arm": "M", "kernel": k, "phi": None} for k in ("exp3", "pow15", "gauss")],
    *[{"arm": "B", "kernel": "gauss", "phi": p}
      for p in (0.0, 2.094, 4.189)],
    *[{"arm": "C", "kernel": k, "phi": None} for k in ("exp3", "pow15")],
    # D 失箝扫描（swing 档位）：v1 发现 swing=3 未达深饱和（P_sat=2×P80 下
    # 仅 60% 压缩）且单调压缩无折返——改为容限曲线扫描 {3,10,30}
    *[{"arm": "D", "kernel": "exp3", "phi": None, "swing": s}
      for s in (3.0, 10.0, 30.0)],
]


def build_grid(quick=False):
    grid = []
    arms = ARMS[:2] if quick else ARMS
    insts = [0] if quick else list(range(4))
    for a, inst in itertools.product(arms, insts):
        c = {"arm": a["arm"], "kernel": a["kernel"], "phi": a["phi"],
             "alpha": 0.8, "beta": 2.0, "noise": 1.0, "N": N, "inst": inst}
        if a.get("swing"):
            c["swing"] = a["swing"]
        if quick:
            c["quick"] = True
        grid.append(c)
    return grid


_KEY_FIELDS = ("arm", "kernel", "phi", "swing", "alpha", "beta", "noise",
               "N", "inst")


def done_keys():
    keys = set()
    if os.path.exists(JSONL):
        with open(JSONL) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    keys.add(json.dumps({k: r.get(k) for k in _KEY_FIELDS},
                                        sort_keys=True))
                except Exception:
                    pass
    return keys


def key_of(cfg):
    return json.dumps({k: cfg.get(k) for k in _KEY_FIELDS}, sort_keys=True)


def aggregate():
    import collections
    agg = collections.defaultdict(list)
    with open(JSONL) as f:
        for line in f:
            r = json.loads(line)
            if not r.get("ok"):
                continue
            agg[(r["arm"], r["kernel"], str(r.get("phi")))].append(
                (r["metric"], r.get("target_ratio"), r["success"],
                 r["tts_mean"]))
    print(f"{'arm':<4} {'kernel':<6} {'phi':<6} {'self':>7} {'target':>7} "
          f"{'succ':>5} {'TTS':>6} {'n':>3}")
    for (arm, kernel, phi), vals in sorted(agg.items()):
        m = np.mean([v[0] for v in vals])
        tg = [v[1] for v in vals if v[1] is not None]
        t = np.mean([v[3] for v in vals])
        s = np.mean([v[2] for v in vals])
        tgs = f"{np.mean(tg):7.3f}" if tg else "      -"
        print(f"{arm:<4} {kernel:<6} {phi:<6} {m:7.3f} {tgs} "
              f"{s:5.2f} {t:6.1f} {len(vals):>3}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--aggregate", action="store_true")
    args = ap.parse_args()
    if args.aggregate:
        aggregate()
        return
    grid = build_grid(args.quick)
    keys = done_keys()
    todo = [c for c in grid if key_of(c) not in keys]
    print(f"total={len(grid)} done={len(grid)-len(todo)} todo={len(todo)}")
    t0 = time.time()
    if args.workers > 1:
        with Pool(args.workers) as p:
            results = p.map(run_config, todo)
    else:
        results = [run_config(c) for c in todo]
    with open(JSONL, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(results)} rows in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
