# -*- coding: utf-8 -*-
"""蓄水池计算（RC）设计空间扫描 —— 7945HX 通宵任务（也可本机跑）。

物理背景：TFLN 平台上的光蓄水池最自然的实现是「单节点 + 延迟环」
（delay-loop reservoir, Appeltant 2011）：一个 EO 调制器（MZM，sin² 响应）
+ 一段延迟波导（n_g≈2.1，1 cm ≈ 70 ps 环程），虚拟节点沿环分布。
本脚本系统扫描该架构的设计空间，并和现行 tanh 代理模型对照。

节点模型（SCR / 最小复杂度环，Rodan & Tiño 2012；TFLN 物理映射诚实版）：
    x_0(n+1) = (1-a)·x_0(n) + a·f( rho·x_{N-1}(n) + gamma·u(n) )   # 注入点：EO 调制器
    x_i(n+1) = x_{i-1}(n)                                          # 环身：无源延迟
    非线性集中在环注入点（调制器），环本身是无源波导延迟线；
    虚拟节点 = 环上不同位置的采样。rho = 环程总增益（耦合比×环损耗），
    gamma = 调制深度，a = 节点惯性（探测带宽/符号率）。
    f: 'tanh'（现行代理）或 'sin2'（MZM 强度响应 sin²(·-pi/4)，正交偏置点）

注：Appeltant 式「逐节点注入掩码」级联模型已实测弃用——新鲜输入在每节点注入，
记忆一个符号周期内就被淹没（MC≈1，与 ρ 无关），不适合作为设计空间模型。

三类基准任务：
  1. MC    —— 线性记忆容量（Jaeger）：uniform 随机驱动，读出任一延迟 k 的 u(n-k)，
             MC = sum_k corr² ，衡量「能记住多久前的输入」
  2. NARMA10 —— 10 阶非线性自回归任务，NMSE 衡量非线性处理能力
  3. SCENE —— 仓库 M1 协议的三类等能量等质心 spike 场景分类（用 L3 真实压缩脉冲），
             快读出精度 + 漏电慢读出精度，检验与实测光栅前端衔接后的可用性

网格（全因子）：
  arch(2) x N(5) x a(3) x rho(6) x gamma(4) = 720 configs x 5 seeds，跑 MC+NARMA10
  SCENE 在缩减网格（arch x N x rho, a=1, gamma=0.2）+ 最优点的抖动/噪声/量化扫描

用法：
  python simulations/03_reservoir_designspace.py --quick      # 本机自检 ~2 min
  python simulations/03_reservoir_designspace.py --workers 14 # 7945HX 全量 ~2-4 h
  断点续跑：重跑同一命令自动跳过已完成 config（results/rc_designspace/results.jsonl）
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
OUT = os.path.join(ROOT, "results", "rc_designspace")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "verify"))
sys.path.insert(0, os.path.join(ROOT, "lumerical"))

C0 = 299792458.0


# ---------------------------------------------------------------------------
# 延迟环蓄水池核心
# ---------------------------------------------------------------------------

def make_f(arch, bias=-np.pi / 4):
    if arch == "tanh":
        return lambda z: np.tanh(z)
    if arch == "sin2":
        return lambda z: np.sin(z + bias) ** 2
    raise ValueError(arch)


def run_reservoir(u, N, rho, gamma, a, arch):
    """SCR 延迟环：非线性在注入点，环身无源移位。返回状态矩阵 (T, N)。"""
    f = make_f(arch)
    T = len(u)
    x = np.zeros(N)
    X = np.empty((T, N))
    for n in range(T):
        inj = (1 - a) * x[0] + a * f(rho * x[-1] + gamma * u[n])
        x[1:] = x[:-1]
        x[0] = inj
        X[n] = x
    return X


def ridge_fit_predict(Xtr, ytr, Xte, lam=1e-6):
    """岭回归（含偏置列），返回测试预测。"""
    Xtr = np.hstack([Xtr, np.ones((len(Xtr), 1))])
    Xte = np.hstack([Xte, np.ones((len(Xte), 1))])
    A = Xtr.T @ Xtr + lam * np.eye(Xtr.shape[1])
    W = np.linalg.solve(A, Xtr.T @ ytr)
    return Xte @ W, W


def quantize(x, bits):
    if bits is None:
        return x
    lo, hi = x.min(), x.max()
    if hi <= lo:
        return x.copy()
    q = (x - lo) / (hi - lo)
    q = np.round(q * (2 ** bits - 1)) / (2 ** bits - 1)
    return q * (hi - lo) + lo


# ---------------------------------------------------------------------------
# 任务 1：线性记忆容量 MC
# ---------------------------------------------------------------------------

def task_mc(cfg, rng, T=12000, wash=1000, mc_floor=0.005):
    """线性记忆容量。Gram 矩阵全程复用，各延迟 k 的互相关用 FFT 一次算全
    （FFT 互相关已与直接法逐位核对一致）。k 上限随 N 缩放。"""
    N = cfg["N"]
    k_max = min(3 * N, 400)
    u = rng.uniform(0.0, 1.0, T)
    X = run_reservoir(u, N, cfg["rho"], cfg["gamma"], cfg["a"], cfg["arch"])
    Xa = np.hstack([X[wash:], np.ones((T - wash, 1))])   # 增广偏置列
    us = u[wash:]
    G = Xa.T @ Xa + 1e-6 * np.eye(N + 1)
    S = 1 << (2 * (T - wash) - 1).bit_length()
    Xf = np.fft.rfft(Xa, n=S, axis=0)
    uf = np.fft.rfft(us, n=S)
    C = np.fft.irfft(Xf * np.conj(uf)[:, None], n=S, axis=0)  # C[k] = Xa[k:].T @ us[:-k]
    su = us.sum()
    mc, per_k = 0.0, {}
    for k in range(1, k_max + 1):
        b = C[k].copy()
        b[-1] = su                                       # 偏置列（忽略边缘截断）
        W = np.linalg.solve(G, b)
        yhat = Xa[k:] @ W
        r = np.corrcoef(us[:-k], yhat)[0, 1]
        r2 = max(float(r), 0.0) ** 2
        if r2 < mc_floor and k > 10:
            break
        per_k[k] = r2
        mc += r2
    tail = {str(k): round(per_k[k], 4) for k in sorted(per_k)[-5:]}
    return {"MC": float(mc), "MC_per_k_tail": tail, "k_max": k_max}


# ---------------------------------------------------------------------------
# 任务 2：NARMA-10
# ---------------------------------------------------------------------------

def narma10(u):
    y = np.zeros(len(u))
    for n in range(10, len(u)):
        y[n] = (0.3 * y[n - 1] + 0.05 * y[n - 1] * np.sum(y[n - 10:n])
                + 1.5 * u[n - 10] * u[n - 1] + 0.1)
    return y


def task_narma(cfg, rng, T=8000, wash=1000):
    u = rng.uniform(0.0, 0.5, T)
    y = narma10(u)
    X = run_reservoir(u, cfg["N"], cfg["rho"], cfg["gamma"], cfg["a"], cfg["arch"])
    ns = np.arange(wash, T)
    ntr, nte = ns[: len(ns) // 2], ns[len(ns) // 2:]
    yhat, _ = ridge_fit_predict(X[ntr], y[ntr], X[nte])
    nmse = float(np.mean((yhat - y[nte]) ** 2) / np.var(y[nte]))
    return {"NARMA10_NMSE": nmse}


# ---------------------------------------------------------------------------
# 任务 3：M1 三类 spike 场景（真实压缩脉冲，L3 口径）
# ---------------------------------------------------------------------------

_PULSE_CACHE = {}


def get_real_pulse():
    """L3 的真实压缩脉冲（懒加载，子进程内缓存）。"""
    if "p" not in _PULSE_CACHE:
        from l3_real_chain import real_compressed_pulse
        t_p, p, meta = real_compressed_pulse()
        _PULSE_CACHE.update(t=t_p, p=p, meta=meta)
    return _PULSE_CACHE["t"], _PULSE_CACHE["p"]


def make_scene(t, class_id, rng, pulse_t, pulse_shape, timing_jitter=0.02, amp_noise=0.05):
    if class_id == 0:
        comps = [(2.0e-12, 1.0)]
    elif class_id == 1:
        comps = [(1.5e-12, 0.5), (2.5e-12, 0.5)]
    else:
        comps = [(1.4e-12, 1 / 3), (2.0e-12, 1 / 3), (2.6e-12, 1 / 3)]
    s = np.zeros_like(t)
    for d, amp in comps:
        d += rng.normal(0, timing_jitter * 1e-12)
        amp *= rng.uniform(1 - amp_noise, 1 + amp_noise)
        s += amp * np.interp(t - d, pulse_t, pulse_shape, left=0.0, right=0.0)
    return s


def task_scene(cfg, rng, n_samples=300, quant_bits=None, jitter_ps=0.02,
               slow_readout=True):
    """场景波形下采样为符号流驱动 RC；读出 = 快读出 + 漏电慢读出双口径。"""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    pulse_t, pulse = get_real_pulse()
    # 场景时间网格：与 L3 相同分辨率 2fs，窗口 0-4ps；符号周期 = N·theta 太细，
    # 物理上 u(n) 是光电探测后的符号流，这里把场景重采样为 M 个符号
    M = 256                     # 每场景符号数（2048/256=8 样本/符号 = 64 GSym/s）
    t_scene = np.arange(2048) * 2e-15
    X_all, y_all = [], []
    for i in range(n_samples):
        cls = i % 3
        s = make_scene(t_scene, cls, rng, pulse_t, pulse, timing_jitter=jitter_ps)
        u = s.reshape(M, -1).mean(axis=1)          # 分段平均 = 光电探测带宽限制
        u = u / (u.max() + 1e-30)
        X = run_reservoir(u, cfg["N"], cfg["rho"], cfg["gamma"], cfg["a"],
                          cfg["arch"])
        feats_fast = X[-1]                          # 快读出：末符号节点状态
        if quant_bits is not None:
            feats_fast = quantize(feats_fast, quant_bits)
        if slow_readout:
            feats_slow = X.sum(axis=0)              # 慢读出：全程能量积分（漏电 tau>>场景）
            if quant_bits is not None:
                feats_slow = quantize(feats_slow, quant_bits)
            feats = np.concatenate([feats_fast, feats_slow])
        else:
            feats = feats_fast
        X_all.append(feats)
        y_all.append(cls)
    X_all, y_all = np.asarray(X_all), np.asarray(y_all)
    Xtr, Xte, ytr, yte = train_test_split(
        X_all, y_all, test_size=0.3, random_state=7, stratify=y_all)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    clf.fit(Xtr, ytr)
    acc = float(clf.score(Xte, yte))
    # 单独报慢读出精度（后半段特征）
    n_f = cfg["N"]
    if slow_readout:
        clf2 = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
        clf2.fit(Xtr[:, n_f:], ytr)
        acc_slow = float(clf2.score(Xte[:, n_f:], yte))
    else:
        acc_slow = None
    return {"scene_acc": acc, "scene_acc_slow": acc_slow}


# ---------------------------------------------------------------------------
# 网格与调度
# ---------------------------------------------------------------------------

def cfg_id(cfg):
    s = json.dumps(cfg, sort_keys=True)
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def build_grid(quick=False):
    grid = []
    archs = ["tanh", "sin2"]
    Ns = [10, 25] if quick else [25, 50, 100, 200, 400, 800]
    alphas = [1.0] if quick else [0.05, 0.1, 0.3, 1.0]   # a = 节点惯性（探测带宽/符号率）
    rhos = [0.8, 0.95] if quick else [0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99]
    gammas = [0.2] if quick else [0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
    seeds = [0] if quick else list(range(10))
    for arch, N, a, rho, gamma, seed in itertools.product(
            archs, Ns, alphas, rhos, gammas, seeds):
        grid.append({"kind": "core", "arch": arch, "N": N, "a": a, "rho": rho,
                     "gamma": gamma, "seed": seed})
    # SCENE 缩减网格
    sN = [25] if quick else [50, 100, 200, 400]
    srho = [0.95] if quick else [0.7, 0.9, 0.95, 0.99]
    for arch, N, rho, seed in itertools.product(archs, sN, srho, seeds):
        grid.append({"kind": "scene", "arch": arch, "N": N, "a": 1.0, "rho": rho,
                     "gamma": 0.2, "seed": seed})
    # SCENE 附加扫描：量化 / 抖动 / 噪声鲁棒性（固定参考构型）
    if not quick:
        for bits in [None, 8, 4, 2]:
            for arch in archs:
                for seed in seeds:
                    grid.append({"kind": "scene", "arch": arch, "N": 200, "a": 1.0,
                                 "rho": 0.95, "gamma": 0.2, "seed": seed,
                                 "quant_bits": bits, "tag": "quant"})
        for jit in [0.0, 0.05, 0.1, 0.15, 0.2]:
            for arch in archs:
                for seed in seeds:
                    grid.append({"kind": "scene", "arch": arch, "N": 200, "a": 1.0,
                                 "rho": 0.95, "gamma": 0.2, "seed": seed,
                                 "jitter_ps": jit, "tag": "jitter"})
    return grid


def run_one(cfg):
    t0 = time.time()
    rng = np.random.default_rng(20260926 * 1000 + cfg["seed"])
    out = dict(cfg)
    try:
        if cfg["kind"] == "core":
            out.update(task_mc(cfg, rng))
            out.update(task_narma(cfg, rng))
        elif cfg["kind"] == "scene":
            out.update(task_scene(cfg, rng,
                                  quant_bits=cfg.get("quant_bits"),
                                  jitter_ps=cfg.get("jitter_ps", 0.02)))
        out["ok"] = True
    except Exception as e:                                # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    out["id"] = cfg_id(cfg)
    return out


# ---------------------------------------------------------------------------
# 聚合与出图
# ---------------------------------------------------------------------------

def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads(l) for l in open(os.path.join(OUT, "results.jsonl"),
                                        encoding="utf-8")]
    rows = [r for r in rows if r.get("ok")]
    core = [r for r in rows if r["kind"] == "core"]
    scene = [r for r in rows if r["kind"] == "scene"]
    print("aggregate: %d core, %d scene runs" % (len(core), len(scene)))

    def mean_std(filt, key):
        vals = [r[key] for r in rows if filt(r) and key in r]
        if not vals:
            return None, None
        return float(np.mean(vals)), float(np.std(vals))

    summary = {"n_core_runs": len(core), "n_scene_runs": len(scene)}

    fig, axes = plt.subplots(2, 3, figsize=(17, 9))

    # (a) MC vs N（每 arch 在每 N 上取其余参数的均值带）
    ax = axes[0, 0]
    for arch, mk in [("tanh", "o-"), ("sin2", "s-")]:
        Ns = sorted({r["N"] for r in core})
        m = [mean_std(lambda r, N=N, a=arch: r["kind"] == "core" and r["arch"] == a and r["N"] == N, "MC")
             for N in Ns]
        ax.errorbar(Ns, [x[0] for x in m], yerr=[x[1] for x in m], fmt=mk, ms=4,
                    capsize=3, label=arch)
    ax.set_xscale("log"); ax.set_xlabel("N (virtual nodes)"); ax.set_ylabel("MC")
    ax.set_title("memory capacity vs N (mean±std over grid)"); ax.legend(); ax.grid(alpha=.3)

    # (b) NARMA NMSE vs N（每 arch 每 N 取最优 5% 均值 = 可调到的最好水平）
    ax = axes[0, 1]
    for arch, mk in [("tanh", "o-"), ("sin2", "s-")]:
        Ns = sorted({r["N"] for r in core})
        best = []
        for N in Ns:
            v = sorted(r["NARMA10_NMSE"] for r in core if r["arch"] == arch and r["N"] == N)
            best.append(np.mean(v[: max(1, len(v) // 20)]))
        ax.plot(Ns, best, mk, ms=4, label=arch)
    ax.set_xscale("log"); ax.set_xlabel("N"); ax.set_ylabel("NARMA-10 NMSE (best 5%)")
    ax.set_title("best achievable NMSE vs N"); ax.legend(); ax.grid(alpha=.3)

    # (c) MC 热图 rho x gamma（N=400, a=0.3）
    for j, arch in enumerate(["tanh", "sin2"]):
        ax = axes[0, 2] if j == 0 else None
    ax = axes[0, 2]
    Nfix, afix = 400, 0.3
    sub = [r for r in core if r["N"] == Nfix and abs(r["a"] - afix) < 1e-9 and r["arch"] == "sin2"]
    if not sub:
        sub = [r for r in core if r["N"] == Nfix and r["arch"] == "sin2"]
    rhos = sorted({r["rho"] for r in sub}); gammas = sorted({r["gamma"] for r in sub})
    Z = np.full((len(rhos), len(gammas)), np.nan)
    for i, rho in enumerate(rhos):
        for jj, g in enumerate(gammas):
            v = [r["MC"] for r in sub if r["rho"] == rho and r["gamma"] == g]
            if v:
                Z[i, jj] = np.mean(v)
    im = ax.imshow(Z, aspect="auto", origin="lower", cmap="viridis",
                   extent=[0, len(gammas) - 1, 0, len(rhos) - 1])
    ax.set_xticks(range(len(gammas))); ax.set_xticklabels(["%g" % g for g in gammas])
    ax.set_yticks(range(len(rhos))); ax.set_yticklabels(["%g" % r for r in rhos])
    ax.set_xlabel("gamma (modulation depth)"); ax.set_ylabel("rho (loop gain)")
    ax.set_title("MC map, sin2 (MZM), N=%d" % Nfix)
    fig.colorbar(im, ax=ax)

    # (d) scene 精度 vs N（快/慢读出 × arch）
    ax = axes[1, 0]
    base_scene = [r for r in scene if "tag" not in r]
    for arch, mk in [("tanh", "o-"), ("sin2", "s-")]:
        Ns = sorted({r["N"] for r in base_scene})
        for key, ls, lb in [("scene_acc", "-", "fast"), ("scene_acc_slow", "--", "slow")]:
            m = [mean_std(lambda r, N=N, a=arch: r in base_scene and r["arch"] == a
                          and r["N"] == N, key) for N in Ns]
            ax.errorbar(Ns, [x[0] for x in m], yerr=[x[1] for x in m], fmt=mk.replace("-", ls),
                        ms=4, capsize=3, label="%s %s" % (arch, lb))
    ax.axhline(1 / 3, color="k", ls=":", alpha=.4)
    ax.set_xscale("log"); ax.set_xlabel("N"); ax.set_ylabel("scene acc")
    ax.set_title("M1 3-class scene (real L3 pulse)"); ax.legend(fontsize=7); ax.grid(alpha=.3)

    # (e) 量化（参考构型）
    ax = axes[1, 1]
    quant = [r for r in scene if r.get("tag") == "quant"]
    bits_all = sorted({str(r.get("quant_bits")) for r in quant})
    xpos = np.arange(len(bits_all))
    for j, (arch, c) in enumerate([("tanh", "C0"), ("sin2", "C1")]):
        m = [mean_std(lambda r, b=b, a=arch: r.get("tag") == "quant" and r["arch"] == a
                      and str(r.get("quant_bits")) == b, "scene_acc") for b in bits_all]
        ax.bar(xpos + j * 0.35 - 0.18, [x[0] if x[0] else 0 for x in m], 0.35,
               yerr=[x[1] for x in m], label=arch, color=c, capsize=3)
    ax.set_xticks(xpos); ax.set_xticklabels(bits_all)
    ax.set_xlabel("readout quantization bits"); ax.set_ylabel("scene acc")
    ax.set_title("quantization robustness (N=200, rho=0.95)"); ax.legend(); ax.grid(alpha=.3)

    # (f) 抖动扫描
    ax = axes[1, 2]
    jit = [r for r in scene if r.get("tag") == "jitter"]
    for arch, mk in [("tanh", "o-"), ("sin2", "s-")]:
        js = sorted({r["jitter_ps"] for r in jit})
        m = [mean_std(lambda r, j=j, a=arch: r.get("tag") == "jitter" and r["arch"] == a
                      and abs(r["jitter_ps"] - j) < 1e-9, "scene_acc") for j in js]
        ax.errorbar(js, [x[0] for x in m], yerr=[x[1] for x in m], fmt=mk, ms=4,
                    capsize=3, label=arch)
    ax.axhline(1 / 3, color="k", ls=":", alpha=.4)
    ax.set_xlabel("spike timing jitter (ps)"); ax.set_ylabel("scene acc")
    ax.set_title("jitter robustness (real pulse)"); ax.legend(); ax.grid(alpha=.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "rc_designspace.png"), dpi=150)

    # 摘要：每 arch 的最优核心构型
    for arch in ["tanh", "sin2"]:
        sub = [r for r in core if r["arch"] == arch]
        best_mc = max(sub, key=lambda r: r["MC"])
        best_nmse = min(sub, key=lambda r: r["NARMA10_NMSE"])
        summary[arch] = {
            "best_MC": {"value": best_mc["MC"], "cfg": {k: best_mc[k] for k in
                        ("N", "a", "rho", "gamma")}},
            "best_NARMA": {"value": best_nmse["NARMA10_NMSE"], "cfg": {k: best_nmse[k] for k in
                           ("N", "a", "rho", "gamma")}},
        }
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print("saved rc_designspace.png + summary.json")
    print(json.dumps(summary, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--aggregate", action="store_true", help="只做聚合出图")
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
    todo = [c for c in grid if cfg_id(c) not in done]
    print("grid %d configs, done %d, todo %d, workers %d"
          % (len(grid), len(done), len(todo), args.workers), flush=True)

    t0 = time.time()
    with open(jsonl, "a", encoding="utf-8") as fout:
        with Pool(args.workers) as pool:
            for i, res in enumerate(pool.imap_unordered(run_one, todo)):
                fout.write(json.dumps(res, ensure_ascii=False) + "\n")
                fout.flush()
                if (i + 1) % 100 == 0:
                    el = time.time() - t0
                    eta = el / (i + 1) * (len(todo) - i - 1)
                    print("  %d/%d done, elapsed %.0fs, ETA %.0fs"
                          % (i + 1, len(todo), el, eta), flush=True)
    print("ALL DONE in %.0fs -> %s" % (time.time() - t0, jsonl), flush=True)


if __name__ == "__main__":
    main()
