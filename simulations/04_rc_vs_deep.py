# -*- coding: utf-8 -*-
"""04: RC 到底好不好用？—— 分任务类型的诚实对打（7945HX 队列任务 2）。

问题来源：同事反馈「蓄水池不好用」；商业化片上色散/衍射网络里没有 RC。
假设：RC 的优势是领域特异的 —— 时序任务 + 小训练预算 + 线速（免 ADC）场景下
RC 有不可替代性；静态任务上 RC 无优势，MLP 胜出。

四任务 × 四臂 × 训练预算扫描 × 5 种子：

  任务
    T1 NARMA-10（时序回归，NMSE）
    T2 非线性信道均衡（时序分类/SER：PAM4 符号经色散+非线性信道，恢复符号）
    T3 M1 三类 spike 场景（时序分类，L3 真实光栅脉冲）
    T4 静态对照：20 维高斯团三分类（无时序结构）

  臂
    rc_tanh / rc_sin2  —— 掩码 SCR 延迟环蓄水池（N=400, rho=0.95, gamma=1.0）
    mlp                —— sklearn MLP（数字基线）
    linear             —— 岭回归/LR 直接作用原始输入（无蓄水池消融）

  公平性约定：时序任务全体因果（MLP/linear 只用因果滑窗；信道均衡统一
  判决延迟 d=2）。RC 启动瞬态 washout：narma 1000 点 / channel 200 点。

用法：
  python simulations/04_rc_vs_deep.py --quick       # 自检
  python simulations/04_rc_vs_deep.py --workers 14  # 全量
  python simulations/04_rc_vs_deep.py --aggregate   # 出图
断点续跑：results/rc_vs_deep/results.jsonl
"""
import argparse
import hashlib
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "rc_vs_deep")
os.makedirs(OUT, exist_ok=True)

import importlib.util
spec = importlib.util.spec_from_file_location(
    "rc03", os.path.join(HERE, "03_reservoir_designspace.py"))
rc03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc03)

RC_CFG = {"N": 400, "rho": 0.95, "gamma": 1.0, "a": 1.0}


def run_reservoir_masked(u, N, rho, gamma, arch, mask_seed=7):
    """标准 SCR（Appeltant 式输入掩码）：x_i(n+1) = f(rho*x_{i-1}(n) + gamma*m_i*u(n))。
    注意：03 的无掩码版本在时序任务上退化（全部节点是同一标量序列的 Hankel 移位，
    NARMA NMSE>=0.28）；输入掩码打破退化，NARMA NMSE~0.12。
    物理对应：光时分复用环中一个符号周期内的快速输入幅度调制。"""
    f = rc03.make_f(arch)
    m = np.random.default_rng(mask_seed).uniform(-1.0, 1.0, N)
    T = len(u)
    x = np.zeros(N)
    X = np.empty((T, N))
    for n in range(T):
        x = f(rho * np.roll(x, 1) + gamma * m * u[n])
        X[n] = x
    return X


# ---------------------------------------------------------------------------
# 数据生成
# ---------------------------------------------------------------------------

def gen_narma(n):
    u = np.random.uniform(0.0, 0.5, n)
    return u, rc03.narma10(u)


def gen_channel(n, rng, snr_db=20):
    """PAM4 符号经线性色散 + 三次非线性 + 噪声（经典均衡基准）。"""
    sym = rng.choice([-3.0, -1.0, 1.0, 3.0], n) / 3.0
    h = np.array([0.34, 0.87, 0.34, -0.15, 0.06])       # 色散（ISI）
    x = np.convolve(sym, h)[:n]
    y = x + 0.2 * x**2 - 0.1 * x**3                      # 非线性失真
    sig = np.mean(y**2)
    noise = np.sqrt(sig * 10 ** (-snr_db / 10))
    return sym, y + rng.normal(0, noise, n)


def gen_scene(n_samples, rng):
    """复用 03 的场景生成（L3 真实脉冲），返回 (n, 256) 符号流。"""
    pulse_t, pulse = rc03.get_real_pulse()
    t_scene = np.arange(2048) * 2e-15
    X, y = [], []
    for i in range(n_samples):
        cls = i % 3
        s = rc03.make_scene(t_scene, cls, rng, pulse_t, pulse)
        u = s.reshape(256, -1).mean(axis=1)
        X.append(u / (u.max() + 1e-30))
        y.append(cls)
    return np.asarray(X), np.asarray(y)


def gen_static(n_samples, rng, d=20, n_cls=3):
    """静态对照：20 维高斯团（类中心随机固定一次，尺度 0.8 使类间有交叠）。"""
    centers = rng.normal(0, 0.8, (n_cls, d))
    y = np.arange(n_samples) % n_cls
    X = centers[y] + rng.normal(0, 1.0, (n_samples, d))
    return X, y


# ---------------------------------------------------------------------------
# 四臂
# ---------------------------------------------------------------------------

def arm_rc(u, cfg, arch):
    """时序流 -> RC 状态（末态+积分拼接）。"""
    X = run_reservoir_masked(u, cfg["N"], cfg["rho"], cfg["gamma"], arch)
    return np.concatenate([X[-1], X.sum(axis=0)])


def eval_cls(feats, labels, n_train, seed, arm):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(labels))
    tr, te = idx[:n_train], idx[n_train:]
    if arm == "mlp":
        from sklearn.neural_network import MLPClassifier
        clf = make_pipeline(StandardScaler(),
                            MLPClassifier(hidden_layer_sizes=(64,), max_iter=2000,
                                          random_state=seed))
    else:
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    t0 = time.time()
    clf.fit(feats[tr], labels[tr])
    train_s = time.time() - t0
    return float(clf.score(feats[te], labels[te])), train_s


def window_feats(y, w=11):
    """因果滑窗特征（只用 y[n-w+1..n]，MLP/linear 臂用于时序任务）。"""
    return np.stack([np.pad(y[max(0, i - w + 1):i + 1],
                            (w - len(y[max(0, i - w + 1):i + 1]), 0),
                            mode="edge")
                     for i in range(len(y))])


def run_config(cfg):
    t0 = time.time()
    rng = np.random.default_rng(31000 + cfg["seed"])
    task, arm, n_train = cfg["task"], cfg["arm"], cfg["n_train"]
    out = dict(cfg)
    try:
        if task == "narma":
            u, ysig = gen_narma(max(4000, n_train + 2000) + 1000)
            if arm.startswith("rc_"):
                feats = run_reservoir_masked(u, RC_CFG["N"], RC_CFG["rho"],
                                             RC_CFG["gamma"], arm[3:])
            else:
                feats = window_feats(u)
            feats, ysig = feats[1000:], ysig[1000:]   # washout：丢弃启动瞬态
            ntr = n_train
            from sklearn.linear_model import Ridge
            if arm == "mlp":
                from sklearn.neural_network import MLPRegressor
                reg = MLPRegressor(hidden_layer_sizes=(64,), max_iter=2000,
                                   random_state=cfg["seed"])
            else:
                reg = Ridge(1e-6)
            t_train0 = time.time()
            reg.fit(feats[:ntr], ysig[:ntr])
            out["train_s"] = round(time.time() - t_train0, 2)
            yhat = reg.predict(feats[ntr:])
            out["metric"] = float(np.mean((yhat - ysig[ntr:]) ** 2) / np.var(ysig[ntr:]))
            out["metric_name"] = "NMSE"

        elif task == "channel":
            sym, y = gen_channel(max(4000, n_train + 2000) + 200, rng)
            d_eq = 2  # 判决延迟：预测 sym[n-2]，全体因果（诊断：sym[n] 在当前
                      # 接收样本里权重仅 h[0]=0.34，无延迟对 RC 臂不公平）
            tgt = np.roll(sym, d_eq)
            labels = ((tgt * 3 + 3) / 2).astype(int)
            if arm.startswith("rc_"):
                feats = run_reservoir_masked(y, RC_CFG["N"], RC_CFG["rho"],
                                             RC_CFG["gamma"], arm[3:])
            else:
                feats = window_feats(y)
            feats, labels = feats[200:], labels[200:]  # washout：丢弃启动瞬态
            acc, train_s = eval_cls(feats, labels, n_train, cfg["seed"], cfg["arm"])
            out["metric"], out["metric_name"], out["train_s"] = acc, "acc", train_s

        elif task == "scene":
            n_total = max(300, n_train + 150)
            Xraw, labels = gen_scene(n_total, rng)
            if arm.startswith("rc_"):
                feats = np.stack([arm_rc(u, RC_CFG, arm[3:]) for u in Xraw])
            else:
                feats = Xraw
            acc, train_s = eval_cls(feats, labels, n_train, cfg["seed"], cfg["arm"])
            out["metric"], out["metric_name"], out["train_s"] = acc, "acc", train_s

        elif task == "static":
            Xraw, labels = gen_static(max(600, n_train + 300), rng)
            if arm.startswith("rc_"):
                # 静态向量以时序流方式喂给 RC（它只能这样接收）
                feats = np.stack([arm_rc(v, RC_CFG, arm[3:]) for v in Xraw])
            else:
                feats = Xraw
            acc, train_s = eval_cls(feats, labels, n_train, cfg["seed"], cfg["arm"])
            out["metric"], out["metric_name"], out["train_s"] = acc, "acc", train_s

        out["ok"] = True
    except Exception as e:                                # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    out["id"] = hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]
    return out


def build_grid(quick=False):
    tasks = ["narma", "channel", "scene", "static"]
    arms = ["rc_tanh", "rc_sin2", "mlp", "linear"]
    n_trains = [100, 500] if quick else [50, 100, 200, 500, 1000, 3000]
    seeds = [0] if quick else list(range(5))
    return [{"task": t, "arm": a, "n_train": n, "seed": s}
            for t, a, n, s in itertools.product(tasks, arms, n_trains, seeds)]


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
    tasks = ["narma", "channel", "scene", "static"]
    arms = [("rc_tanh", "o-"), ("rc_sin2", "s-"), ("mlp", "^--"), ("linear", "d:")]
    titles = {"narma": "T1 NARMA-10 (NMSE, lower=better)",
              "channel": "T2 channel equalization (acc)",
              "scene": "T3 spike scene, real pulse (acc)",
              "static": "T4 static blobs, no temporal structure (acc)"}

    fig, axes = plt.subplots(1, 4, figsize=(19, 4.2))
    for ax, task in zip(axes, tasks):
        sub = [r for r in rows if r["task"] == task]
        ns = sorted({r["n_train"] for r in sub})
        for arm, mk in arms:
            m = [np.mean([r["metric"] for r in sub if r["arm"] == arm and r["n_train"] == n])
                 for n in ns]
            e = [np.std([r["metric"] for r in sub if r["arm"] == arm and r["n_train"] == n])
                 for n in ns]
            ax.errorbar(ns, m, yerr=e, fmt=mk, ms=4, capsize=2, label=arm)
        ax.set_xscale("log")
        ax.set_xlabel("training samples")
        ax.set_title(titles[task], fontsize=9)
        ax.legend(fontsize=7); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "rc_vs_deep.png"), dpi=150)

    # 摘要表：小预算 (<=200) vs 大预算 (3000)
    summ = {}
    for task in tasks:
        summ[task] = {}
        for arm, _ in arms:
            small = [r["metric"] for r in rows
                     if r["task"] == task and r["arm"] == arm and r["n_train"] <= 200]
            big = [r["metric"] for r in rows
                   if r["task"] == task and r["arm"] == arm and r["n_train"] == 3000]
            summ[task][arm] = {"small_mean": float(np.mean(small)) if small else None,
                               "big_mean": float(np.mean(big)) if big else None}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print("saved rc_vs_deep.png + summary.json")


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
    todo = [c for c in grid
            if hashlib.sha1(json.dumps(c, sort_keys=True).encode()).hexdigest()[:12] not in done]
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
                          % (i + 1, len(todo), el, el / (i + 1) * (len(todo) - i - 1)),
                          flush=True)
    print("ALL DONE in %.0fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
