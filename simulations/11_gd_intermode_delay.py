"""sim11: GD 模式间延迟硬件化——确定性色散延迟 vs 随机延迟（Cuevas 2025 杠杆）。

科学问题（rq 第七十/七十二批）：
Cuevas/Kuse 2025（Nanophotonics 14, 3063）实验证明"模式间随机延迟"是微梳频率
复用 RC 的最强单一杠杆（37 齿 Santa Fe NMSE 0.8→0.21→0.081），但其延迟只能在
后处理 trial-and-error——他们没有片上模式相关延迟器件。我们的啁啾光栅 GD 恰是
确定性、可设计的波长相关延迟元件。本仿真问：
  ① 确定性 GD 延迟轮廓（线性/啁啾）能否达到随机延迟试错的性能？
  ② 增益随符号率 f_s 如何缩放？（物理直觉：GD 延迟为 ps 级亚符号尺度，f_s 越高
     延迟覆盖的符号数越多——硬件化 sweet spot 应在 >1 GSa/s，恰是微梳 RC 想去
     的方向）
  ③ GD 物理可达域（工程化 D ≤ 10 ps/nm，模式间隔 100 GHz≈0.8 nm）能覆盖多少
     可用增益？

唯象模型（不开 LLE，03/04 同纪律）：
- 37 个频率节点（对齐 Cuevas 实验齿数），模式相关静态响应
  r_m(u) = g_m u + q_m u²（g_m/q_m 随模式变号=孤子失谐响应的模式多样性，
  定性对齐其 Fig 2c）；
- 记忆 = 单极点低通，τ_cav = 5.7 ns（28 MHz 线宽，对齐其器件）；
- 模式间延迟 y_m(t) = x_m(t−τ_m)，亚符号延迟用线性插值；
- 读出 = 岭回归（NARMA-10 NMSE / PAM4 信道均衡 SER），复用 04 基准。

臂：
  A 无延迟基线；
  B 随机延迟（D_max ∈ {2,6,12} 符号，K=10 图案，记录 mean 与 best=试错上限）；
  C 线性 GD：τ_m = a·c_m，a ∈ {1,3,10,30,100,300} ps/mode；
  D 啁啾 GD：τ_m = a·c_m + b·c_m²，a ∈ {10,30,100} × b ∈ {0.3,1,3}。
扫描 f_s ∈ {50M, 200M, 1G, 4G} × 任务 {narma, channel} × 种子 3。
"""
import argparse
import itertools
import json
import os
import time

import numpy as np

# ---------------- 器件/模型常量（对齐 Cuevas 2025 实验） ----------------
N_MODE = 37                 # 实验实测齿数
TAU_CAV = 5.7e-9            # s，28 MHz 线宽 → 光子寿命
MODE_SPACING_NM = 0.8       # 100 GHz @1550 nm ≈ 0.8 nm
GD_ENG_REACH = 10.0         # ps/nm，工程化 CBG 可达 GD 斜率（保守）
GD_DEMONSTRATED = 0.5       # ps/nm，已演示量级上限（实测 0.051，留裕量）
FS_GRID = [50e6, 200e6, 1e9, 4e9]
K_PATTERNS = 10             # B 臂随机延迟图案数（Cuevas 的 10 独立图案纪律）
ITERS_PAD = 64              # 延迟线需要的符号历史缓冲

_KEY_FIELDS = ["task", "arm", "fs", "a", "b", "dmax", "seed"]


# ---------------- 基准任务（复用 04 的生成器口径，内联保持自包含） ----------------
def narma10(u):
    """与 03_reservoir_designspace.narma10 逐行一致（数据口径纪律）。"""
    y = np.zeros(len(u))
    for n in range(10, len(u)):
        y[n] = (0.3 * y[n - 1] + 0.05 * y[n - 1] * np.sum(y[n - 10:n])
                + 1.5 * u[n - 10] * u[n - 1] + 0.1)
    return y


def gen_santafe(n=4001):
    """Santa Fe 激光混沌序列（SFI 竞赛 A 集，reservoirpy 镜像，10093 点）。
    归一化到 [0,1]；返回 (u, tgt) = 一步预测对（对齐 Cuevas：train 3000/test 1000）。"""
    s = np.load("data/santafe_laser.npy").ravel().astype(float) / 255.0
    u, tgt = s[:n - 1], s[1:n]
    return u, tgt


def gen_narma(n, rng):
    u = rng.uniform(0.0, 0.5, n)
    return u, narma10(u)


def gen_channel(n, rng, snr_db=20):
    sym = rng.choice([-3.0, -1.0, 1.0, 3.0], n) / 3.0
    h = np.array([0.34, 0.87, 0.34, -0.15, 0.06])
    x = np.convolve(sym, h)[:n]
    y = x + 0.2 * x**2 - 0.1 * x**3
    sig = np.mean(y**2)
    noise = np.sqrt(sig * 10 ** (-snr_db / 10))
    return sym, y + rng.normal(0, noise, n)


# ---------------- 频率复用蓄水池（唯象） ----------------
def mode_coeffs():
    """模式相关静态响应系数：g_m=cos θ, q_m=sin θ（跨模式变号=响应多样性）。"""
    theta = np.pi * np.arange(N_MODE) / (N_MODE - 1)
    return np.cos(theta), np.sin(theta)


def reservoir_states(u, fs, tau_m, gamma=0.10):
    """欠阻尼二阶孤子弛豫振荡（对齐 Cuevas Fig 3：阶跃响应振荡周期 ~6.8 ns、
    持续 >100 ns——有效记忆远超裸光子寿命 5.7 ns，这是孤子腔内 Kerr-失谐
    动力学的关键物理）：
      x[k+1] = 2ρcosω·x[k] − ρ²·x[k−1] + (1−ρ²)·r_m(u[k]) + γ·u[k]·x[k]
    全齿共享同一动态（模式多样性在静态响应 (g_m,q_m)，其 Fig 7d 各齿波形
    高度相关正是如此）；动态去相关完全由模式间延迟 τ_m 提供——臂间差异
    干净归因于延迟轮廓。γ=双线性 Kerr 交叉调制（NARMA 交叉项来源）。
    tau_m: (N_MODE,) 秒。返回 (n, N_MODE) 特征矩阵。
    """
    tau_ring = 40e-9          # s，弛豫振荡衰减（>100 ns 瞬态的 1/e 量级）
    f_ring = 150e6            # Hz，弛豫振荡频率（≈1/6.8 ns）
    dt = 1.0 / fs
    rho = np.exp(-dt / tau_ring)
    om = 2 * np.pi * f_ring * dt
    a1, a2 = 2 * rho * np.cos(om), -rho**2
    g, q = mode_coeffs()
    drive = g[None, :] * u[:, None] + q[None, :] * u[:, None] ** 2
    n = len(u)
    x = np.zeros((n + 1, N_MODE))
    xp = np.zeros(N_MODE)     # x[k-1]
    gain = 1 - rho**2
    for k in range(n):
        xn = a1 * x[k] + a2 * xp + gain * drive[k] \
            + gamma * u[k] * x[k] * gain
        xp = x[k]
        x[k + 1] = xn
    x = x[1:n + 1]
    g, q = mode_coeffs()
    drive = g[None, :] * u[:, None] + q[None, :] * u[:, None] ** 2
    n = len(u)
    x = np.zeros((n + 1, N_MODE))
    for k in range(n):
        x[k + 1] = rho * x[k] + (1 - rho) * drive[k] \
            + gamma * u[k] * x[k] * (1 - rho)
    x = x[1:n + 1]
    # 模式间延迟（符号单位，支持亚符号线性插值）
    d = np.asarray(tau_m) * fs
    d_int = np.floor(d).astype(int)
    frac = d - d_int
    idx = np.arange(n)[:, None]
    y = np.empty((n, N_MODE))
    i0 = np.clip(idx - d_int[None, :], 0, n - 1)
    i1 = np.clip(idx - d_int[None, :] - 1, 0, n - 1)
    y = (1 - frac)[None, :] * x[i0, np.arange(N_MODE)] \
        + frac[None, :] * x[i1, np.arange(N_MODE)]
    return y


def ridge_fit(F, t, lam=1e-3):
    F = np.hstack([F, np.ones((len(F), 1))])
    A = F.T @ F + lam * np.trace(F.T @ F) / F.shape[1] * np.eye(F.shape[1])
    return np.linalg.solve(A, F.T @ t)


def eval_narma(u, tgt, fs, tau_m, n_train=3000):
    F = reservoir_states(u, fs, tau_m)
    w = ridge_fit(F[:n_train], tgt[:n_train])
    Fb = np.hstack([F, np.ones((len(F), 1))])
    pred = Fb @ w
    d, p = tgt[n_train:], pred[n_train:]
    return float(np.mean((d - p) ** 2) / np.var(d))


def eval_channel(u, sym, fs, tau_m, n_train=4000):
    F = reservoir_states(u, fs, tau_m)
    w = ridge_fit(F[:n_train], sym[:n_train])
    Fb = np.hstack([F, np.ones((len(F), 1))])
    pred = Fb @ w
    const = np.array([-3, -1, 1, 3]) / 3.0
    dec = const[np.argmin(np.abs(pred[:, None] - const[None, :]), axis=1)]
    return float(np.mean(dec[n_train:] != sym[n_train:]))


# ---------------- 延迟轮廓 ----------------
def tau_linear(a_ps, fs):
    c = np.arange(N_MODE) - (N_MODE - 1) / 2
    return a_ps * 1e-12 * c


def tau_chirp(a_ps, b_ps, fs):
    c = np.arange(N_MODE) - (N_MODE - 1) / 2
    return 1e-12 * (a_ps * c + b_ps * c**2 / N_MODE)


# ---------------- 单配置执行 ----------------
def run_config(cfg):
    t0 = time.time()
    out = dict(cfg)
    try:
        rng = np.random.default_rng(cfg["seed"] * 7919 + 13)
        n = 4200 if cfg["task"] == "narma" else 8400
        if cfg["task"] == "santafe":
            u, tgt = gen_santafe()
        elif cfg["task"] == "narma":
            u, tgt = gen_narma(n, rng)
        else:
            tgt, u = gen_channel(n, rng)
        fs = cfg["fs"]
        arm = cfg["arm"]
        ev = eval_narma if cfg["task"] in ("narma", "santafe") else eval_channel
        if arm == "A":
            tau = np.zeros(N_MODE)
            out["metric"] = ev(u, tgt, fs, tau)
        elif arm == "B":
            rng_d = np.random.default_rng(cfg["seed"] * 31 + 7)
            mets = []
            for _ in range(K_PATTERNS):
                tau = rng_d.uniform(0, cfg["dmax"] / fs, N_MODE)
                mets.append(ev(u, tgt, fs, tau))
            out["metric"] = float(np.mean(mets))
            out["metric_best"] = float(np.min(mets))
            out["metric_std"] = float(np.std(mets))
        elif arm == "C":
            tau = tau_linear(cfg["a"], fs)
            out["metric"] = ev(u, tgt, fs, tau)
        elif arm == "D":
            tau = tau_chirp(cfg["a"], cfg["b"], fs)
            out["metric"] = ev(u, tgt, fs, tau)
        # 物理映射注记（C/D 臂）：GD 斜率需求与可达性
        if arm in ("C", "D"):
            span_ps = float((np.max(tau) - np.min(tau)) * 1e12)
            slope = span_ps / (N_MODE * MODE_SPACING_NM)
            out["delay_span_ps"] = span_ps
            out["gd_slope_ps_per_nm"] = slope
            out["gd_feasible_eng"] = bool(slope <= GD_ENG_REACH)
            out["gd_feasible_demo"] = bool(slope <= GD_DEMONSTRATED)
        out["metric_name"] = "NMSE" if cfg["task"] in ("narma", "santafe") \
            else "SER"
        out["ok"] = True
    except Exception as e:  # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    return out


def build_grid(quick=False):
    tasks = ["santafe", "narma"] if quick else ["santafe", "narma", "channel"]
    fss = [50e6, 1e9] if quick else FS_GRID
    seeds = [0] if quick else [0, 1, 2]
    cfgs = []
    for task, fs, seed in itertools.product(tasks, fss, seeds):
        sf_b_only = (task == "santafe" and seed > 0)
        # Santa Fe 数据确定：A/C/D 行跨种子重复只跑 seed 0；B 臂保留全种子
        # （随机延迟图案多样性是其指标的一部分）
        if not sf_b_only:
            cfgs.append(dict(task=task, arm="A", fs=fs, a=0, b=0, dmax=0,
                             seed=seed))
        dmaxs = [6] if quick else [2, 6, 12]
        for dmax in dmaxs:
            cfgs.append(dict(task=task, arm="B", fs=fs, a=0, b=0, dmax=dmax,
                             seed=seed))
        if sf_b_only:
            continue
        aas = [10, 100] if quick else [1, 3, 10, 30, 100, 300]
        for a in aas:
            cfgs.append(dict(task=task, arm="C", fs=fs, a=a, b=0, dmax=0,
                             seed=seed))
        if not quick:
            for a in [10, 30, 100]:
                for b in [0.3, 1.0, 3.0]:
                    cfgs.append(dict(task=task, arm="D", fs=fs, a=a, b=b,
                                     dmax=0, seed=seed))
    return cfgs


# ---------------- 聚合 ----------------
def aggregate(rows):
    print("\n== sim11 聚合：GD 模式间延迟硬件化 ==")
    ok = [r for r in rows if r.get("ok")]
    print("ok %d / %d" % (len(ok), len(rows)))
    for task in ["narma", "channel"]:
        for fs in FS_GRID:
            sub = [r for r in ok if r["task"] == task and r["fs"] == fs]
            if not sub:
                continue
            base = [r["metric"] for r in sub if r["arm"] == "A"]
            print("\n[%s @ %.0f MSa/s] A(无延迟)=%.4f"
                  % (task, fs / 1e6, np.mean(base) if base else float("nan")))
            for r in sorted(sub, key=lambda r: (r["arm"], r["a"], r["dmax"])):
                if r["arm"] == "A":
                    continue
                tag = {"B": "rand dmax=%d" % r["dmax"],
                       "C": "GD a=%gps/m" % r["a"],
                       "D": "chirp a=%g b=%g" % (r["a"], r["b"])}[r["arm"]]
                extra = ""
                if r["arm"] == "B":
                    extra = " best=%.4f" % r.get("metric_best", 0)
                if "gd_slope_ps_per_nm" in r:
                    extra += " D=%.2gps/nm%s" % (
                        r["gd_slope_ps_per_nm"],
                        "✓eng" if r["gd_feasible_eng"] else "✗eng")
                print("  %s %-18s %.4f%s"
                      % (r["arm"], tag, r["metric"], extra))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--out", default="results/gd_intermode_delay/results.jsonl")
    args = ap.parse_args()
    if args.aggregate:
        rows = [json.loads(l) for l in open(args.out)]
        aggregate(rows)
        return
    cfgs = build_grid(args.quick)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            r = json.loads(l)
            done.add(tuple(r[k] for k in _KEY_FIELDS))
    todo = [c for c in cfgs if tuple(c[k] for k in _KEY_FIELDS) not in done]
    print("grid=%d done=%d todo=%d" % (len(cfgs), len(done), len(todo)))
    with open(args.out, "a") as f:
        if args.workers > 1:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(args.workers) as ex:
                futs = {ex.submit(run_config, c): c for c in todo}
                for fut in as_completed(futs):
                    r = fut.result()
                    f.write(json.dumps(r) + "\n")
                    f.flush()
        else:
            for c in todo:
                r = run_config(c)
                f.write(json.dumps(r) + "\n")
                f.flush()


if __name__ == "__main__":
    main()
