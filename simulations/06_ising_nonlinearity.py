# -*- coding: utf-8 -*-
"""06: 片上非线性做 Ising 机 —— 激活函数器件真实化对打（7945HX 队列任务 4）。

动机：用户提供的 KAUST QD-laser PIM 草稿用激光器 LI 曲线做自旋激活；
我们平台的核心非线性是 TFLN MZM 的 sin²（EO 调制）。问题：换成器件真实
非线性后，Ising 求解质量掉多少？这决定"我们的器件能否兼做 Ising 机"。

模型（OEO/分岔式离散时间动力学，同 QD 论文 Eq.2）：
    x[k+1] = f_nl( alpha * x[k] - beta * (J @ x[k]) / sqrt(N) + noise[k] )

激活函数臂（全部奇对称、幅度归一到 |f|<=1）：
    tanh    —— 理想饱和（理论参照）
    sin     —— MZM 正交偏置 EO 传递（我们的平台；I ∝ sin(pi V / 2 Vpi)）
    laser   —— QD 激光器 LI 曲线（阈值+线性+饱和，奇延拓，仿 KAUST 草稿）
    clip    —— 硬限幅线性（数字 ADC 饱和基线）

基准：min E = -1/2 sᵀJs；3-正则图用反铁磁 J=-A（等价 max-cut），
      稠密 ±1 自旋玻璃
参照：模拟退火（SA）长程运行取 best-known energy（负值）
指标：E_found/E_BK（→1 表示追平 SA；>1 表示超过 SA 参照）、
      成功率（达到 97% E_BK 的比例）、time-to-solution

用法同 03/04：--quick / --workers N / --aggregate
断点续跑：results/ising_nonlinearity/results.jsonl
"""
import argparse
import hashlib
import itertools
import json
import os
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "ising_nonlinearity")
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# 激活函数（奇对称、|f|<=1）
# ---------------------------------------------------------------------------

def f_tanh(z):
    return np.tanh(z)


def f_sin(z, s=1.2):
    """MZM 正交偏置：奇对称正弦饱和。s 控制进入饱和区的深度。"""
    return np.sin(s * z)


def f_laser(z, th=0.25, slope=1.5, sat=1.0):
    """QD 激光器 LI 曲线的奇延拓：阈值以下 ~0，线性段，饱和段。"""
    a = np.abs(z)
    lin = np.clip(slope * (a - th), 0.0, sat)
    return np.sign(z) * lin


def f_clip(z):
    return np.clip(z, -1.0, 1.0)


ACTS = {"tanh": f_tanh, "sin": f_sin, "laser": f_laser, "clip": f_clip}


# ---------------------------------------------------------------------------
# 图与参照解
# ---------------------------------------------------------------------------

def gen_graph(kind, N, rng):
    """返回对称 J（无对角）。3-regular 或 dense ±1。"""
    J = np.zeros((N, N))
    if kind == "3reg":
        # configuration model：3N 个 stub 随机配对，有自环/重边就整体重试
        for _ in range(200):
            stubs = np.repeat(np.arange(N), 3)
            rng.shuffle(stubs)
            pairs = stubs.reshape(-1, 2)
            ok = True
            J[:] = 0
            for i, j in pairs:
                if i == j or J[i, j] != 0:
                    ok = False
                    break
                J[i, j] = J[j, i] = 1
            if ok:
                return J
        raise RuntimeError("3reg graph generation failed after 200 retries")
    else:  # dense
        mask = rng.random((N, N)) < 0.5
        w = rng.choice([-1.0, 1.0], (N, N))
        J = np.triu(mask * w, 1)
        J = J + J.T
    return J


def gen_graph(kind, N, rng):
    """返回对称 J（无对角）。约定：问题 = min E(s) = -1/2 sᵀJs。
    3reg：反铁磁 J=-A（基态 = max-cut）；dense：±1 自旋玻璃。"""
    if kind == "3reg":
        # configuration model：3N 个 stub 随机配对，有自环/重边就整体重试
        for _ in range(200):
            stubs = np.repeat(np.arange(N), 3)
            rng.shuffle(stubs)
            pairs = stubs.reshape(-1, 2)
            A = np.zeros((N, N))
            ok = True
            for i, j in pairs:
                if i == j or A[i, j] != 0:
                    ok = False
                    break
                A[i, j] = A[j, i] = 1
            if ok:
                return -A  # 反铁磁
        raise RuntimeError("3reg graph generation failed after 200 retries")
    mask = rng.random((N, N)) < 0.5
    w = rng.choice([-1.0, 1.0], (N, N))
    J = np.triu(mask * w, 1)
    return J + J.T


def energy(J, s):
    return -0.5 * float(s @ J @ s)


def sa_reference(J, iters=20000, seed=0):
    """模拟退火最小化 E，返回 best-known energy（负值）。"""
    rng = np.random.default_rng(seed)
    N = len(J)
    s = rng.choice([-1, 1], N)
    m = J @ s                       # 局部场，增量维护
    E = -0.5 * float(s @ m)
    best = E
    T0, T1 = 2.0, 0.01
    for k in range(iters):
        T = T0 * (T1 / T0) ** (k / iters)
        i = rng.integers(N)
        dE = 2 * s[i] * m[i]        # 翻转 s_i 的能量变化
        if dE < 0 or rng.random() < np.exp(-dE / T):
            m -= 2 * s[i] * J[:, i]
            s[i] *= -1
            E += dE
            if E < best:
                best = E
    return best


# ---------------------------------------------------------------------------
# Ising 动力学
# ---------------------------------------------------------------------------

def run_ising(J, act, alpha, beta, noise0, iters=300, seed=0):
    """返回 (best_E, E 运行最优轨迹)。噪声线性退火到 0。
    动力学沿 E=-1/2 xᵀJx 的下降方向：x ← f(αx + β Jx/√N + η)。"""
    rng = np.random.default_rng(seed)
    N = len(J)
    f = ACTS[act]
    x = rng.uniform(-0.1, 0.1, N)
    Jn = J / np.sqrt(N)
    best = 0.0
    traj = []
    for k in range(iters):
        eta = noise0 * (1 - k / iters) * rng.normal(0, 1, N)
        x = f(alpha * x + beta * (Jn @ x) + eta)
        s = np.sign(x)
        s[s == 0] = 1
        E = energy(J, s)
        if E < best:
            best = E
        traj.append(best)
    return best, np.asarray(traj)


def run_config(cfg):
    t0 = time.time()
    rng = np.random.default_rng(52000 + cfg["inst"])
    out = dict(cfg)
    try:
        J = gen_graph(cfg["graph"], cfg["N"], rng)
        bk = sa_reference(J, iters=30000 if cfg["N"] <= 100 else 60000,
                          seed=cfg["inst"] * 7 + 1)
        out["bk_energy"] = float(bk)                    # 负值
        thr = 0.97 * bk                                 # 负值的 97%
        n_runs = 2 if cfg.get("quick") else 5
        ratios, tts = [], []
        for r in range(n_runs):
            best, traj = run_ising(J, cfg["act"], cfg["alpha"], cfg["beta"],
                                   cfg["noise"], iters=300,
                                   seed=cfg["inst"] * 100 + r)
            ratios.append(best / bk)                    # 负/负，→1 追平 SA
            hit = np.nonzero(traj <= thr)[0]
            tts.append(int(hit[0]) if len(hit) else 300)
        out["metric"] = float(np.mean(ratios))          # E/E_BK
        out["metric_name"] = "energy_ratio"
        out["success"] = float(np.mean([r >= 0.97 for r in ratios]))
        out["tts_mean"] = float(np.mean(tts))
        out["ok"] = True
    except Exception as e:                              # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    out["id"] = hashlib.sha1(json.dumps(
        {k: v for k, v in cfg.items() if k != "quick"},
        sort_keys=True).encode()).hexdigest()[:12]
    return out


def build_grid(quick=False):
    acts = list(ACTS)
    alphas = [0.5] if quick else [0.3, 0.5, 0.8, 1.0]
    betas = [2.0] if quick else [1.0, 2.0, 5.0, 10.0]
    noises = [0.1] if quick else [0.1, 0.5, 1.0]
    graphs = ["3reg"] if quick else ["3reg", "dense"]
    Ns = [100] if quick else [100, 1000]
    insts = [0] if quick else list(range(4))
    grid = []
    for a, al, be, no, g, n, i in itertools.product(
            acts, alphas, betas, noises, graphs, Ns, insts):
        c = {"act": a, "alpha": al, "beta": be, "noise": no,
             "graph": g, "N": n, "inst": i}
        if quick:
            c["quick"] = True
        grid.append(c)
    return grid


# ---------------------------------------------------------------------------
# 聚合出图
# ---------------------------------------------------------------------------

def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads(l) for l in open(os.path.join(OUT, "results.jsonl"),
                                        encoding="utf-8")]
    rows = [r for r in rows if r.get("ok")]
    acts = [("tanh", "o-"), ("sin", "s-"), ("laser", "^-"), ("clip", "d:")]

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))
    # 面板1：各激活函数的最优 E/E_BK（对 alpha,beta,noise 取 max），按图类型×N
    ax = axes[0]
    labels, vals, errs = [], [], []
    for act, _ in acts:
        for g in ["3reg", "dense"]:
            for N in [100, 1000]:
                sub = [r for r in rows if r["act"] == act
                       and r["graph"] == g and r["N"] == N]
                if not sub:
                    continue
                by_cfg = {}
                for r in sub:
                    key = (r["alpha"], r["beta"], r["noise"])
                    by_cfg.setdefault(key, []).append(r["metric"])
                best_per_inst = {}
                for r in sub:
                    pass
                # 每个 (alpha,beta,noise) 组合在实例上的均值，再取最大
                cfg_mean = {k: float(np.mean(v)) for k, v in by_cfg.items()}
                top = max(cfg_mean.values())
                labels.append(f"{act}\n{g},N={N}")
                vals.append(top)
                errs.append(0)
    ax.bar(range(len(vals)), vals)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=6, rotation=45)
    ax.set_ylabel("best E/E_BK (over hyper)")
    ax.set_title("peak solution quality per activation")
    ax.grid(alpha=.3)

    # 面板2：E/E_BK vs alpha（最优 beta,noise），3reg N=1000
    ax = axes[1]
    for act, mk in acts:
        xs, ys = [], []
        for al in sorted({r["alpha"] for r in rows}):
            sub = [r for r in rows if r["act"] == act and r["alpha"] == al
                   and r["graph"] == "3reg" and r["N"] == 1000]
            if sub:
                by = {}
                for r in sub:
                    by.setdefault((r["beta"], r["noise"]), []).append(r["metric"])
                xs.append(al)
                ys.append(max(float(np.mean(v)) for v in by.values()))
        ax.plot(xs, ys, mk, label=act)
    ax.set_xlabel("feedback strength alpha")
    ax.set_ylabel("best E/E_BK")
    ax.set_title("3-regular, N=1000")
    ax.legend(fontsize=7)
    ax.grid(alpha=.3)

    # 面板3：成功率 vs 噪声幅度
    ax = axes[2]
    for act, mk in acts:
        xs, ys = [], []
        for no in sorted({r["noise"] for r in rows}):
            sub = [r for r in rows if r["act"] == act and r["noise"] == no]
            if sub:
                xs.append(no)
                ys.append(float(np.mean([r["success"] for r in sub])))
        ax.plot(xs, ys, mk, label=act)
    ax.set_xlabel("initial noise amplitude")
    ax.set_ylabel("success rate (>=97% BK)")
    ax.set_title("noise annealing robustness")
    ax.legend(fontsize=7)
    ax.grid(alpha=.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ising_nonlinearity.png"), dpi=150)

    summ = {}
    for act, _ in acts:
        sub = [r for r in rows if r["act"] == act]
        if not sub:
            continue
        by_cfg = {}
        for r in sub:
            key = (r["alpha"], r["beta"], r["noise"], r["graph"], r["N"])
            by_cfg.setdefault(key, []).append(r["metric"])
        key_best = max(by_cfg, key=lambda k: np.mean(by_cfg[k]))
        summ[act] = {"best_cfg": dict(zip(
            ("alpha", "beta", "noise", "graph", "N"), key_best)),
            "best_energy_ratio": float(np.mean(by_cfg[key_best])),
            "global_mean": float(np.mean([r["metric"] for r in sub]))}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print("saved ising_nonlinearity.png + summary.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    args = ap.parse_args()

    if args.aggregate:
        aggregate()
        return

    jsonl = os.path.join(OUT, "results.jsonl")
    done = set()
    if os.path.exists(jsonl):
        with open(jsonl, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["id"])
                except Exception:                       # noqa: BLE001
                    pass
    grid = build_grid(args.quick)
    todo = []
    for c in grid:
        cid = hashlib.sha1(json.dumps(
            {k: v for k, v in c.items() if k != "quick"},
            sort_keys=True).encode()).hexdigest()[:12]
        if cid not in done:
            todo.append(c)
    print("grid %d, done %d, todo %d, workers %d"
          % (len(grid), len(done), len(todo), args.workers), flush=True)

    t0 = time.time()
    with open(jsonl, "a", encoding="utf-8") as fout:
        with Pool(args.workers) as pool:
            for i, res in enumerate(pool.imap_unordered(run_config, todo)):
                fout.write(json.dumps(res, ensure_ascii=False) + "\n")
                fout.flush()
                if (i + 1) % 50 == 0:
                    el = time.time() - t0
                    print("  %d/%d, elapsed %.0fs, ETA %.0fs"
                          % (i + 1, len(todo), el,
                             el / (i + 1) * (len(todo) - i - 1)), flush=True)
    print("ALL DONE in %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
