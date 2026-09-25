# -*- coding: utf-8 -*-
"""07: RC vs NGRC —— 时延多项式特征路线对打（7945HX 队列任务 4）。

动机（docs/ising_literature_digest.md §三-9/10，两篇全文已读）：
- 光学 NGRC（arXiv:2404.07857, Light Sci. Appl. 2025）证明「时延输入的多项式
  特征」在很多任务上可取代真循环动力学——这是对我们 CBG 延迟抽头平台的直接利好；
- 但 Zhang & Lai, Chaos 35, 073142 (2025) 发现 NGRC 的「数据越多越发散」失败
  模式：病根在数字读出层（延迟特征近似线性相关 → 设计矩阵病态 → 固定 λ 下
  权重范数暴涨 → 病态积分器），缓解靠 λ 随数据量同步增大。
本脚本在我们自己的任务生态位上公平对打，并遵守「NGRC 必须扫 λ×数据量」的纪律
（digest §三-10 结论③）。

  臂
    rc_tanh / rc_sin2 —— 掩码 SCR（同 04/05，N=400, rho=0.95, gamma=1.0）
    esn               —— 稠密 ESN
    ngrc              —— 数字 NGRC/NVAR 二阶（标量任务 k=8, s=1：与 volterra
                        mem=8 同窗口、特征数 45≈44 公平对打；lorenz k=2, s=1
                        同光学 NGRC 论文；特征=[1, taps 拼接, 二次上三角]）
    volterra          —— 二阶 Volterra 滑窗（NGRC 的经典近亲，仅标量任务）
    linear            —— 因果滑窗底线（仅标量任务）

  任务
    narma    —— NARMA-10 一步预测 NMSE，n_train × λ 扫描
    channel  —— 非线性信道均衡 acc（SNR 20，λ 固定 1e-4，分类协议同 05）
    lorenz   —— Lorenz63 闭环自治预测，有效预测时间 VPT（Lyapunov 时间，
                阈值 0.4，λ_max=0.91，dt=0.02）——NGRC 数据诱导不稳定性的试金石。
                仅 rc_tanh / esn / ngrc 三臂（闭环需要自洽的态演化）。

用法同 03-06：--quick / --workers N / --aggregate
断点续跑：results/rc_vs_ngrc/results.jsonl
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
OUT = os.path.join(ROOT, "results", "rc_vs_ngrc")
os.makedirs(OUT, exist_ok=True)

import importlib.util
for name, path in [("rc03", "03_reservoir_designspace.py"),
                   ("rc04", "04_rc_vs_deep.py"),
                   ("rc05", "05_rc_vs_baselines.py")]:
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    globals()[name] = mod

RC_CFG = {"N": 400, "rho": 0.95, "gamma": 1.0}
ESN_CFG = {"N": 400, "rho": 0.95, "gamma": 1.0, "a": 0.3}
LORENZ_DT = 0.02
LORENZ_LMAX = 0.91
VPT_THRESH = 0.4


# ---------------------------------------------------------------------------
# NGRC 特征（NVAR 二阶，taps = u_t, u_{t-1}）
# ---------------------------------------------------------------------------

def _quad(A):
    """行向量的二次单项式（上三角去重）。"""
    i, j = np.triu_indices(A.shape[1])
    return np.einsum("ni,nj->nij", A, A)[:, i, j]


def ngrc_feats(U, k=2, s=1):
    """U: (T,) 或 (T,M)。NVAR 标准形：v = concat(u_t, u_{t-s}, ..., u_{t-(k-1)s})，
    特征 = [1, v, U(v⊗v)]（上三角去重）。返回 (T-(k-1)s, D)，第 i 行对应时刻
    i+(k-1)s。"""
    U = np.asarray(U, dtype=float)
    if U.ndim == 1:
        U = U[:, None]
    T, M = U.shape
    d = (k - 1) * s
    v = np.hstack([U[d - i * s: T - i * s] for i in range(k)])
    return np.hstack([np.ones((len(v), 1)), v, _quad(v)])


# ---------------------------------------------------------------------------
# 多变量 SCR / ESN（lorenz 闭环用；标量任务走 04/05 的实现）
# ---------------------------------------------------------------------------

def run_scr_mv(U, N, rho, gamma, arch, mask_seed=7):
    f = rc03.make_f(arch)
    M = np.random.default_rng(mask_seed).uniform(-1.0, 1.0, (N, U.shape[1]))
    x = np.zeros(N)
    X = np.empty((len(U), N))
    for n in range(len(U)):
        x = f(rho * np.roll(x, 1) + gamma * (M @ U[n]))
        X[n] = x
    return X


def run_esn_mv(U, N, rho, gamma, a, seed=11):
    rng = np.random.default_rng(seed)
    Win = rng.uniform(-1, 1, (N, U.shape[1]))
    W = rng.uniform(-1, 1, (N, N))
    W *= rho / max(abs(np.linalg.eigvals(W)))
    x = np.zeros(N)
    X = np.empty((len(U), N))
    for n in range(len(U)):
        x = (1 - a) * x + a * np.tanh(gamma * (Win @ U[n]) + W @ x)
        X[n] = x
    return X


def make_feats_scalar(arm, sig, seed):
    """标量任务（narma/channel）。返回 (feats, drop)：drop = 目标序列要从头部
    丢掉的样本数（NGRC 的首行对应 t=(k-1)s；hybrid 与之对齐）。"""
    if arm.startswith("rc_"):
        return rc04.run_reservoir_masked(sig, RC_CFG["N"], RC_CFG["rho"],
                                         RC_CFG["gamma"], arm[3:]), 0
    if arm == "esn":
        return rc05.run_esn(sig, ESN_CFG["N"], ESN_CFG["rho"], ESN_CFG["gamma"],
                            ESN_CFG["a"], seed=seed + 100), 0
    if arm == "ngrc":
        # 标量任务用 k=8, s=1：与 volterra mem=8 同窗口、特征数 45≈44，公平对打
        return ngrc_feats(sig, k=8, s=1), 7
    if arm == "hybrid":
        # Chepuri et al. 2024 (arXiv:2403.18953)：H = r ⊕ O，SCR(tanh) 状态
        # 与 NGRC 特征拼接，单一岭读出
        r = rc04.run_reservoir_masked(sig, RC_CFG["N"], RC_CFG["rho"],
                                      RC_CFG["gamma"], "tanh")
        o = ngrc_feats(sig, k=8, s=1)
        return np.hstack([r[7:], o]), 7
    if arm == "volterra":
        return rc05.volterra_feats(sig), 0
    return rc04.window_feats(sig), 0  # linear


def make_feats_mv(arm, U, seed):
    """多变量任务（lorenz）。返回 (feats, drop)。"""
    if arm.startswith("rc_"):
        return run_scr_mv(U, RC_CFG["N"], RC_CFG["rho"], RC_CFG["gamma"],
                          arm[3:]), 0
    if arm == "esn":
        return run_esn_mv(U, ESN_CFG["N"], ESN_CFG["rho"], ESN_CFG["gamma"],
                          ESN_CFG["a"], seed=seed + 100), 0
    if arm == "ngrc":
        return ngrc_feats(U, k=2, s=1), 1
    if arm == "hybrid":
        r = run_scr_mv(U, RC_CFG["N"], RC_CFG["rho"], RC_CFG["gamma"], "tanh")
        o = ngrc_feats(U, k=2, s=1)
        return np.hstack([r[1:], o]), 1
    raise ValueError("arm %s not available for lorenz" % arm)


def ridge_fit(feats, y, lam):
    from sklearn.linear_model import Ridge
    reg = Ridge(lam)
    reg.fit(feats, y)
    return reg


# ---------------------------------------------------------------------------
# Lorenz63 闭环
# ---------------------------------------------------------------------------

def gen_lorenz(n, dt=LORENZ_DT, seed=0):
    def f(s):
        x, y, z = s
        return np.array([10.0 * (y - x), x * (28.0 - z) - y, x * y - 8.0 / 3.0 * z])
    rng = np.random.default_rng(seed)
    s = np.array([1.0, 1.0, 1.0]) + 0.1 * rng.standard_normal(3)
    U = np.empty((n, 3))
    for i in range(n):
        k1 = f(s)
        k2 = f(s + dt / 2 * k1)
        k3 = f(s + dt / 2 * k2)
        k4 = f(s + dt * k3)
        s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        U[i] = s
    return U


def run_lorenz(arm, n_train, lam, seed, n_wash=500, n_test=1000):
    """闭环自治预测。返回 (VPT [Lyapunov 时间], 是否发散)。"""
    U = gen_lorenz(n_wash + n_train + n_test, seed=seed)
    Utr = U[:n_wash + n_train]
    Ute = U[n_wash + n_train:]
    sd = Utr[n_wash:].std(axis=0)

    feats, drop = make_feats_mv(arm, Utr, seed)
    # 一步映射：feats[n]（对应时刻 n+drop）→ Utr[n+drop+1]
    tgt = Utr[drop + 1:]
    feats = feats[:len(tgt)]
    reg = ridge_fit(feats[n_wash - drop:], tgt[n_wash - drop:], lam)

    if arm == "ngrc":
        u_prev, u = Utr[-2].copy(), Utr[-1].copy()
        preds = np.empty((n_test, 3))
        blew = n_test
        for t in range(n_test):
            feat = ngrc_feats(np.vstack([u_prev, u]))
            u_prev, u = u, reg.predict(feat)[-1]
            preds[t] = u
            if not np.all(np.isfinite(u)) or np.max(np.abs(u)) > 1e6:
                blew = t + 1
                break
        preds = preds[:blew]
    elif arm == "hybrid":
        # SCR(tanh) 状态 + NGRC taps 联合闭环
        f = rc03.make_f("tanh")
        M = np.random.default_rng(7).uniform(-1.0, 1.0, (RC_CFG["N"], 3))
        rho, gamma = RC_CFG["rho"], RC_CFG["gamma"]
        x = np.zeros(RC_CFG["N"])
        for n in range(len(Utr)):
            x = f(rho * np.roll(x, 1) + gamma * (M @ Utr[n]))
        u_prev, u = Utr[-2].copy(), Utr[-1].copy()
        preds = np.empty((n_test, 3))
        blew = n_test
        for t in range(n_test):
            if t:
                x = f(rho * np.roll(x, 1) + gamma * (M @ u))
            feat = np.hstack([x, ngrc_feats(np.vstack([u_prev, u]))[-1]])
            u_prev, u = u, reg.predict(feat[None, :])[0]
            preds[t] = u
            if not np.all(np.isfinite(u)) or np.max(np.abs(u)) > 1e6:
                blew = t + 1
                break
        preds = preds[:blew]
    else:
        # 闭环：蓄水池态先随真实输入演化到训练末尾，然后切到预测输入
        if arm.startswith("rc_"):
            f = rc03.make_f(arm[3:])
            M = np.random.default_rng(7).uniform(-1.0, 1.0, (RC_CFG["N"], 3))
            rho, gamma = RC_CFG["rho"], RC_CFG["gamma"]
            x = np.zeros(RC_CFG["N"])
            for n in range(len(Utr)):
                x = f(rho * np.roll(x, 1) + gamma * (M @ Utr[n]))
            step = lambda u: f(rho * np.roll(x, 1) + gamma * (M @ u))  # noqa: E731
        else:
            N, rho, gamma, a = (ESN_CFG["N"], ESN_CFG["rho"], ESN_CFG["gamma"],
                                ESN_CFG["a"])
            rng = np.random.default_rng(seed + 100)
            Win = rng.uniform(-1, 1, (N, 3))
            W = rng.uniform(-1, 1, (N, N))
            W *= rho / max(abs(np.linalg.eigvals(W)))
            x = np.zeros(N)
            for n in range(len(Utr)):
                x = (1 - a) * x + a * np.tanh(gamma * (Win @ Utr[n]) + W @ x)
            step = lambda u: (1 - a) * x + a * np.tanh(gamma * (Win @ u) + W @ x)  # noqa: E731
        preds = np.empty((n_test, 3))
        for t in range(n_test):
            if t:
                x = step(preds[t - 1])
            preds[t] = reg.predict(x[None, :])[0]

    n_roll = len(preds)
    err = np.linalg.norm((preds - Ute[:n_roll]) / sd, axis=1) / np.sqrt(3)
    bad = np.nonzero(err > VPT_THRESH)[0]
    blew_up = n_roll < n_test
    vpt_idx = bad[0] if len(bad) else n_roll
    vpt = vpt_idx * LORENZ_DT * LORENZ_LMAX
    diverged = bool(blew_up or np.any(~np.isfinite(preds)) or
                    np.max(np.abs(preds)) > 10 * np.max(np.abs(Utr)))
    return float(vpt), diverged


# ---------------------------------------------------------------------------
# 任务
# ---------------------------------------------------------------------------

def run_config(cfg):
    t0 = time.time()
    rng = np.random.default_rng(42000 + cfg["seed"])
    task, arm, n_train, lam = cfg["task"], cfg["arm"], cfg["n_train"], cfg["lam"]
    out = dict(cfg)
    try:
        if task == "narma":
            u, ysig = rc04.gen_narma(max(4000, n_train + 2000) + 1000)
            feats, drop = make_feats_scalar(arm, u, cfg["seed"])
            ysig = ysig[drop:]
            feats, ysig = feats[1000:], ysig[1000:]
            reg = ridge_fit(feats[:n_train], ysig[:n_train], lam)
            yhat = reg.predict(feats[n_train:])
            out["metric"] = float(np.mean((yhat - ysig[n_train:]) ** 2)
                                  / np.var(ysig[n_train:]))
            out["metric_name"] = "NMSE"
            out["w_norm"] = float(np.linalg.norm(reg.coef_))

        elif task == "channel":
            sym, y = rc04.gen_channel(max(4000, n_train + 2000) + 200, rng,
                                      snr_db=20)
            tgt = np.roll(sym, 2)
            labels = ((tgt * 3 + 3) / 2).astype(int)
            feats, drop = make_feats_scalar(arm, y, cfg["seed"])
            labels = labels[drop:]
            feats, labels = feats[200:], labels[200:]
            acc, train_s = rc04.eval_cls(feats, labels, n_train, cfg["seed"],
                                         "linear")
            out["metric"], out["metric_name"] = acc, "acc"

        elif task == "lorenz":
            vpt, diverged = run_lorenz(arm, n_train, lam, cfg["seed"])
            out["metric"], out["metric_name"] = vpt, "VPT_Lyap"
            out["diverged"] = diverged

        out["ok"] = True
    except Exception as e:                                # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    out["id"] = hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]
    return out


def build_grid(quick=False):
    arms_sc = ["rc_tanh", "rc_sin2", "esn", "ngrc", "hybrid", "volterra",
               "linear"]
    arms_lo = ["rc_tanh", "esn", "ngrc", "hybrid"]
    if quick:
        n_trains, lams, seeds = [100, 500], [1e-4], [0]
        n_trains_lo = [200, 1000]
    else:
        n_trains = [50, 100, 200, 500, 1000, 3000]
        lams = [1e-6, 1e-4, 1e-2]
        seeds = list(range(5))
        n_trains_lo = [200, 500, 1000, 2000]
    grid = []
    for arm, n, lam, s in itertools.product(arms_sc, n_trains, lams, seeds):
        grid.append({"task": "narma", "arm": arm, "n_train": n,
                     "lam": lam, "seed": s})
    for arm, n, s in itertools.product(arms_sc, n_trains, seeds):
        grid.append({"task": "channel", "arm": arm, "n_train": n,
                     "lam": 1e-4, "seed": s})
    for arm, n, lam, s in itertools.product(arms_lo, n_trains_lo, lams, seeds):
        grid.append({"task": "lorenz", "arm": arm, "n_train": n,
                     "lam": lam, "seed": s})
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
            ("ngrc", "*-"), ("hybrid", "P-"), ("volterra", "v--"),
            ("linear", "x:")]
    arms_lo = [("rc_tanh", "o-"), ("esn", "^-"), ("ngrc", "*-"),
               ("hybrid", "P-")]

    fig, axes = plt.subplots(2, 3, figsize=(17, 8))

    # (a) narma NMSE vs n_train（λ=1e-4）
    ax = axes[0, 0]
    sub = [r for r in rows if r["task"] == "narma" and r["lam"] == 1e-4]
    ns = sorted({r["n_train"] for r in sub})
    for arm, mk in arms:
        m = [np.mean([r["metric"] for r in sub
                      if r["arm"] == arm and r["n_train"] == n]) for n in ns]
        ax.plot(ns, m, mk, ms=4, label=arm)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("n_train"); ax.set_title("narma NMSE @ lam=1e-4", fontsize=9)
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    # (b) narma：NGRC 的 NMSE vs λ × n_train（不稳定性检验）
    ax = axes[0, 1]
    sub = [r for r in rows if r["task"] == "narma" and r["arm"] == "ngrc"]
    for n in sorted({r["n_train"] for r in sub}):
        lams = sorted({r["lam"] for r in sub})
        m = [np.mean([r["metric"] for r in sub
                      if r["n_train"] == n and r["lam"] == l]) for l in lams]
        ax.plot(lams, m, "o-", ms=4, label="n=%d" % n)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("ridge lam"); ax.set_title("NGRC narma: NMSE vs lam", fontsize=9)
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    # (c) narma：读出权重范数（病态积分器探针）
    ax = axes[0, 2]
    sub = [r for r in rows if r["task"] == "narma" and "w_norm" in r]
    for arm, mk in arms[:4]:
        for lam, ls in [(1e-6, ":"), (1e-4, "-"), (1e-2, "--")]:
            ns = sorted({r["n_train"] for r in sub
                         if r["arm"] == arm and r["lam"] == lam})
            m = [np.mean([r["w_norm"] for r in sub
                          if r["arm"] == arm and r["n_train"] == n
                          and r["lam"] == lam]) for n in ns]
            if ns:
                ax.plot(ns, m, ls, label="%s l=%g" % (arm, lam))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("n_train"); ax.set_title("readout ||W|| (ill-conditioning probe)",
                                           fontsize=9)
    ax.legend(fontsize=6); ax.grid(alpha=.3)

    # (d) channel acc vs n_train
    ax = axes[1, 0]
    sub = [r for r in rows if r["task"] == "channel"]
    ns = sorted({r["n_train"] for r in sub})
    for arm, mk in arms:
        m = [np.mean([r["metric"] for r in sub
                      if r["arm"] == arm and r["n_train"] == n]) for n in ns]
        ax.plot(ns, m, mk, ms=4, label=arm)
    ax.set_xscale("log")
    ax.set_xlabel("n_train"); ax.set_title("channel eq. acc @ SNR 20", fontsize=9)
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    # (e) lorenz VPT vs n_train（λ=1e-4）
    ax = axes[1, 1]
    sub = [r for r in rows if r["task"] == "lorenz" and r["lam"] == 1e-4]
    ns = sorted({r["n_train"] for r in sub})
    for arm, mk in arms_lo:
        m = [np.mean([r["metric"] for r in sub
                      if r["arm"] == arm and r["n_train"] == n]) for n in ns]
        ax.plot(ns, m, mk, ms=4, label=arm)
    ax.set_xscale("log")
    ax.set_xlabel("n_train"); ax.set_ylabel("VPT [Lyapunov times]")
    ax.set_title("lorenz closed-loop VPT @ lam=1e-4", fontsize=9)
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    # (f) lorenz：VPT vs λ × n_train（Chaos 2025 复现窗口）
    ax = axes[1, 2]
    sub = [r for r in rows if r["task"] == "lorenz"]
    for arm, mk in [("ngrc", "*"), ("esn", "^"), ("rc_tanh", "o"), ("hybrid", "P")]:
        for n in sorted({r["n_train"] for r in sub}):
            lams = sorted({r["lam"] for r in sub})
            m = [np.mean([r["metric"] for r in sub
                          if r["arm"] == arm and r["n_train"] == n
                          and r["lam"] == l]) for l in lams]
            ax.plot(lams, m, mk + "-", ms=4, label="%s n=%d" % (arm, n))
    ax.set_xscale("log")
    ax.set_xlabel("ridge lam"); ax.set_ylabel("VPT [Lyapunov times]")
    ax.set_title("lorenz VPT vs lam (instability window)", fontsize=9)
    ax.legend(fontsize=6); ax.grid(alpha=.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "rc_vs_ngrc.png"), dpi=150)

    summ = {}
    for task in ["narma", "channel", "lorenz"]:
        summ[task] = {}
        for arm, _ in arms:
            big = [r["metric"] for r in rows if r["task"] == task
                   and r["arm"] == arm and r["lam"] == 1e-4
                   and r["n_train"] == max({rr["n_train"] for rr in rows
                                            if rr["task"] == task},
                                           default=-1)]
            summ[task][arm] = {"big_mean": float(np.mean(big)) if big else None}
    nd = [r for r in rows if r["task"] == "lorenz" and r.get("diverged")]
    summ["lorenz_diverged_frac"] = {
        arm: float(np.mean([r["diverged"] for r in nd if r["arm"] == arm]))
        if any(r["arm"] == arm for r in nd) else None for arm, _ in arms_lo}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))
    print("saved rc_vs_ngrc.png + summary.json")


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
            for l in f:
                try:
                    done.add(json.loads(l)["id"])
                except Exception:                       # noqa: BLE001
                    pass
    grid = [c for c in build_grid(args.quick)
            if hashlib.sha1(json.dumps(c, sort_keys=True).encode())
            .hexdigest()[:12] not in done]
    print("todo: %d configs" % len(grid))
    if not grid:
        return
    with open(jsonl, "a", encoding="utf-8") as f:
        if args.workers > 1 and len(grid) > 1:
            with Pool(args.workers) as p:
                for out in p.imap_unordered(run_config, grid):
                    f.write(json.dumps(out) + "\n")
                    f.flush()
        else:
            for cfg in grid:
                f.write(json.dumps(run_config(cfg)) + "\n")
                f.flush()
    print("done -> %s" % jsonl)


if __name__ == "__main__":
    main()
