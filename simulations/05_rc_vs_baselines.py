# -*- coding: utf-8 -*-
"""05: RC vs 更强数字基线 —— 扩展对打（7945HX 队列任务 3）。

04 只放了 MLP/线性两个弱基线；批评者可以说「赢 MLP 不算赢」。
本脚本补上各自领域的标准强基线：

  臂
    rc_tanh / rc_sin2   —— 掩码 SCR（同 04，N=400, rho=0.95, gamma=1.0）
    esn                 —— 稠密随机网络 Echo State Network（RC 的数字标准形）
    volterra            —— 二阶 Volterra/记忆多项式（信道均衡领域经典强基线）
    elm                 —— 随机特征极限学习机（静态任务标准基线）
    linear              —— 因果滑窗线性（消融底线）

  任务
    narma    —— NARMA-10，NMSE，预算扫描
    channel  —— 非线性信道均衡，判决延迟 d=2，预算 × SNR(10/20/30 dB) 扫描
    scene    —— M1 三类 spike 场景（真实脉冲），预算扫描

用法同 03/04：--quick / --workers N / --aggregate
断点续跑：results/rc_vs_baselines/results.jsonl
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
OUT = os.path.join(ROOT, "results", "rc_vs_baselines")
os.makedirs(OUT, exist_ok=True)

import importlib.util
for name, path in [("rc03", "03_reservoir_designspace.py"),
                   ("rc04", "04_rc_vs_deep.py")]:
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    globals()[name] = mod

RC_CFG = {"N": 400, "rho": 0.95, "gamma": 1.0}
ESN_CFG = {"N": 400, "rho": 0.95, "gamma": 1.0, "a": 0.3}
VOLT_MEM = 8


# ---------------------------------------------------------------------------
# 臂实现
# ---------------------------------------------------------------------------

def run_esn(u, N, rho, gamma, a, seed=11):
    """稠密 ESN：x[n+1] = (1-a)x[n] + a*tanh(gamma*Win*u[n] + Wres x[n])。"""
    rng = np.random.default_rng(seed)
    Win = rng.uniform(-1, 1, N)
    W = rng.uniform(-1, 1, (N, N))
    W *= rho / max(abs(np.linalg.eigvals(W)))
    x = np.zeros(N)
    X = np.empty((len(u), N))
    for n in range(len(u)):
        x = (1 - a) * x + a * np.tanh(gamma * Win * u[n] + W @ x)
        X[n] = x
    return X


def volterra_feats(y, mem=VOLT_MEM):
    """二阶 Volterra：因果滑窗的一阶 + 二阶交叉项。"""
    W1 = rc04.window_feats(y, w=mem)
    n = len(W1)
    triu = np.triu_indices(mem)
    X2 = np.einsum("ni,nj->nij", W1, W1)[:, triu[0], triu[1]]
    return np.hstack([W1, X2])


def elm_feats(y, w=11, n_feat=512, seed=13):
    """随机特征：因果滑窗 -> 随机投影 -> tanh。"""
    rng = np.random.default_rng(seed)
    Wr = rng.uniform(-1, 1, (w, n_feat))
    return np.tanh(rc04.window_feats(y, w) @ Wr)


def make_feats(arm, sig, seed):
    if arm.startswith("rc_"):
        return rc04.run_reservoir_masked(sig, RC_CFG["N"], RC_CFG["rho"],
                                         RC_CFG["gamma"], arm[3:])
    if arm == "esn":
        return run_esn(sig, ESN_CFG["N"], ESN_CFG["rho"], ESN_CFG["gamma"],
                       ESN_CFG["a"], seed=seed + 100)
    if arm == "volterra":
        return volterra_feats(sig)
    if arm == "elm":
        return elm_feats(sig, seed=seed + 200)
    return rc04.window_feats(sig)  # linear


def eval_reg(feats, ysig, n_train, seed, lam=1e-4):
    from sklearn.linear_model import Ridge
    reg = Ridge(lam)
    reg.fit(feats[:n_train], ysig[:n_train])
    yhat = reg.predict(feats[n_train:])
    return float(np.mean((yhat - ysig[n_train:]) ** 2) / np.var(ysig[n_train:]))


# ---------------------------------------------------------------------------
# 任务
# ---------------------------------------------------------------------------

def run_config(cfg):
    t0 = time.time()
    rng = np.random.default_rng(41000 + cfg["seed"])
    task, arm, n_train = cfg["task"], cfg["arm"], cfg["n_train"]
    out = dict(cfg)
    try:
        if task == "narma":
            u, ysig = rc04.gen_narma(max(4000, n_train + 2000) + 1000)
            feats = make_feats(arm, u, cfg["seed"])
            feats, ysig = feats[1000:], ysig[1000:]
            out["metric"] = eval_reg(feats, ysig, n_train, cfg["seed"])
            out["metric_name"] = "NMSE"

        elif task == "channel":
            snr = cfg["snr"]
            sym, y = rc04.gen_channel(max(4000, n_train + 2000) + 200, rng,
                                      snr_db=snr)
            tgt = np.roll(sym, 2)
            labels = ((tgt * 3 + 3) / 2).astype(int)
            feats = make_feats(arm, y, cfg["seed"])
            feats, labels = feats[200:], labels[200:]
            acc, train_s = rc04.eval_cls(feats, labels, n_train, cfg["seed"],
                                         "linear")  # 全臂统一岭/LR 读出
            out["metric"], out["metric_name"] = acc, "acc"

        elif task == "scene":
            n_total = max(300, n_train + 150)
            Xraw, labels = rc04.gen_scene(n_total, rng)
            if arm.startswith("rc_") or arm == "esn":
                if arm.startswith("rc_"):
                    f = lambda u: rc04.run_reservoir_masked(
                        u, RC_CFG["N"], RC_CFG["rho"], RC_CFG["gamma"], arm[3:])
                else:
                    f = lambda u: run_esn(u, ESN_CFG["N"], ESN_CFG["rho"],
                                          ESN_CFG["gamma"], ESN_CFG["a"],
                                          seed=cfg["seed"] + 100)
                feats = np.stack([np.concatenate([X[-1], X.sum(axis=0)])
                                  for X in map(f, Xraw)])
            else:
                feats = Xraw
            acc, train_s = rc04.eval_cls(feats, labels, n_train, cfg["seed"],
                                         "linear")
            out["metric"], out["metric_name"] = acc, "acc"

        out["ok"] = True
    except Exception as e:                                # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    out["id"] = hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]
    return out


def build_grid(quick=False):
    arms = ["rc_tanh", "rc_sin2", "esn", "volterra", "elm", "linear"]
    n_trains = [100, 500] if quick else [50, 100, 200, 500, 1000, 3000]
    snrs = [20] if quick else [10, 20, 30]
    seeds = [0] if quick else list(range(5))
    grid = []
    for arm, n, s in itertools.product(arms, n_trains, seeds):
        grid.append({"task": "narma", "arm": arm, "n_train": n, "seed": s})
        grid.append({"task": "scene", "arm": arm, "n_train": n, "seed": s})
    for arm, n, snr, s in itertools.product(arms, n_trains, snrs, seeds):
        grid.append({"task": "channel", "arm": arm, "n_train": n,
                     "snr": snr, "seed": s})
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
    arms = [("rc_tanh", "o-"), ("rc_sin2", "s-"), ("esn", "^-"),
            ("volterra", "v--"), ("elm", "d--"), ("linear", "x:")]

    fig, axes = plt.subplots(2, 3, figsize=(17, 8))
    panels = [("narma", None, "NARMA-10 NMSE (lower=better)"),
              ("channel", 30, "channel eq. acc @ SNR 30 dB"),
              ("channel", 10, "channel eq. acc @ SNR 10 dB"),
              ("scene", None, "spike scene acc (real pulse)"),
              ("channel", 20, "channel eq. acc @ SNR 20 dB")]
    for ax, (task, snr, title) in zip(axes.ravel(), panels):
        sub = [r for r in rows if r["task"] == task
               and (snr is None or r.get("snr") == snr)]
        ns = sorted({r["n_train"] for r in sub})
        for arm, mk in arms:
            m = [np.mean([r["metric"] for r in sub
                          if r["arm"] == arm and r["n_train"] == n]) for n in ns]
            ax.plot(ns, m, mk, ms=4, label=arm)
        ax.set_xscale("log")
        ax.set_xlabel("training samples")
        ax.set_title(title, fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(alpha=.3)
    # 第六格：SNR 20 时各臂的 train-time vs acc 帕累托（预算=1000）
    ax = axes.ravel()[-1]
    sub = [r for r in rows if r["task"] == "channel" and r.get("snr") == 20
           and r["n_train"] == 1000]
    for arm, mk in arms:
        pts = [r for r in sub if r["arm"] == arm]
        if pts:
            ax.scatter([np.mean([p.get("wall_s", 0) for p in pts])],
                       [np.mean([p["metric"] for p in pts])], label=arm)
    ax.set_xlabel("wall time per config (s)")
    ax.set_ylabel("acc @ SNR20, n=1000")
    ax.set_title("cost-accuracy", fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "rc_vs_baselines.png"), dpi=150)

    # 摘要：narma NMSE 最优预算、channel 各 SNR 大预算精度
    summ = {}
    for task in ["narma", "channel", "scene"]:
        summ[task] = {}
        for arm, _ in arms:
            big = [r["metric"] for r in rows if r["task"] == task
                   and r["arm"] == arm and r["n_train"] == 3000
                   and r.get("snr", 20) == 20]
            small = [r["metric"] for r in rows if r["task"] == task
                     and r["arm"] == arm and r["n_train"] <= 100
                     and r.get("snr", 20) == 20]
            summ[task][arm] = {
                "big_mean": float(np.mean(big)) if big else None,
                "small_mean": float(np.mean(small)) if small else None}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print("saved rc_vs_baselines.png + summary.json")


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
            if hashlib.sha1(json.dumps(c, sort_keys=True).encode()).hexdigest()[:12]
            not in done]
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
