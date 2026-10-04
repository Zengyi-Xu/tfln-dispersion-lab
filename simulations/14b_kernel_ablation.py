# -*- coding: utf-8 -*-
"""14b: 同预算对照 —— 延迟抽头 / 实测 CBG 抽头 / CBG+因果共享增益 / 数字 NGRC

sim14 任务书 B 部分。复用 07 的 NARMA10 协议/训练划分（gen_narma、前 1000 丢弃、
NMSE=MSE/var(y_test)）、≥3 种子。纯 CPU。

臂（同输入、同 32 梳线、同延迟窗 WINDOW=8 步、同随机种子）：
  lin        均匀线性延迟抽头（32 抽头覆盖 8 步窗）
  cbg        实测 CBG 延迟抽头：chirp2d.npz 的 tau_r 直接插值（14A 口径），
             τ→整数步索引 round((τ-τmin)/span*WINDOW)（含波纹，如实报告唯一抽头数）
  cbg_J      cbg ⊕ 物理碰撞对二次项，权重 = 14A 的因果核 Jn（小信号 T_rec/w=1），
             支撑集 = |Jn|>0.05·max 的通道对 —— "CBG+因果共享增益"
  cbg_K      同支撑集、同 |权重|，但权重取对称重叠 K（sim09 隐含假设的对照臂）
  cbg_symJ   同支撑集、(Jn+Jnᵀ)/2 —— 任务书允许的**假想对称上界**，
             **不声称已实现**（A 的 J 显著不对称，故不报告任何"物理 Ising 能量"）
  ngrc       07 的数字 NGRC k=8,s=1（45 维）

成本口径：仅报告**数字等效**特征抽取乘法数/读出维度/训练解维度，
不写任何器件能耗。预算声明：模拟任务误差 ≠ 器件性能。

产物: results/causal_kernel/b_ablation/{results.jsonl, fig3_ablation.png,
       b_summary.md}; 逐种子原始行在 results.jsonl。
用法: python simulations/14b_kernel_ablation.py [--quick] [--aggregate]
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "causal_kernel", "b_ablation")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

WINDOW = 8                       # 所有臂共享的延迟窗（步）= NGRC k=8 窗
N_CH = 32                        # 梳线/抽头数（lin 与 cbg 同维度）
NTRAIN = [100, 300, 1000]
LAMS = [1e-6, 1e-4, 1e-2]
SEEDS = [0, 1, 2]
J_THRESH = 0.05                  # 碰撞对支撑集阈值（|Jn| 相对最大）


def _imp(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


m14 = _imp("m14", "14_causal_kernel.py")
m07 = _imp("m07", "07_rc_vs_ngrc.py")
rc04 = m07.rc04


# ---------------------------------------------------------------------------
# 物理核（来自 14A 的口径）
# ---------------------------------------------------------------------------

def build_kernels():
    """实测 CBG 的 tau、整数抽头索引、因果核 Jn / 对称 K / 假想对称 J。"""
    tau, _ = m14.gd_laws()["cbg_measured"]
    span = float(tau.max() - tau.min())
    idx = np.round((tau - tau.min()) / span * WINDOW).astype(int) if span > 0 \
        else np.zeros(N_CH, int)
    beta = m14.SAT_PARAMS["small"] / (1.0 * m14.W)        # s=0.05, T_rec=w
    J, _ = m14.linear_response_J(tau, beta, 1.0 * m14.W, m14.DT0, m14.MARGIN0)
    Jn = J / np.max(np.abs(J))
    np.fill_diagonal(Jn, 0.0)
    K = m14.K_analytic(tau[:, None] - tau[None, :])
    np.fill_diagonal(K, 0.0)
    K = K / np.max(np.abs(K))
    mask = np.abs(Jn) > J_THRESH * np.max(np.abs(Jn))
    ii, jj = np.nonzero(mask)
    symJ = 0.5 * (Jn + Jn.T)
    return {"tau": tau, "idx": idx, "unique_taps": int(len(np.unique(idx))),
            "Jn": Jn, "Kn": K, "symJ": symJ, "ii": ii, "jj": jj,
            "n_pairs": int(len(ii))}


# ---------------------------------------------------------------------------
# 特征臂
# ---------------------------------------------------------------------------

def pad_u(u):
    """u 前补 WINDOW 个 0，返回 U[t, k] = u[t - idx_k]（t 从 WINDOW 起）。"""
    return np.concatenate([np.zeros(WINDOW), u])


def build_feats(arm, u, yfull, KX):
    """返回 (X, y, meta)。与 07 协议一致：特征只用 u[≤t]，目标 y[t]。
    ngrc 行 i ↔ 时刻 t=i+(k-1)s（07 的 ngrc_feats 约定）。"""
    if arm == "ngrc":
        X = m07.ngrc_feats(u, k=WINDOW, s=1)      # (T-7, 45)
        y = yfull[WINDOW - 1: len(X) + WINDOW - 1]
        return X, y, {"dim": X.shape[1], "mults_per_step": 36}
    up = pad_u(u)
    t0 = WINDOW
    T = len(up)
    base = np.arange(t0, T)
    U = up[base[:, None] - KX["idx"][None, :]]        # (T', 32) CBG 抽头
    if arm == "lin":
        xs = np.linspace(0.0, WINDOW, N_CH)
        ilin = np.round(xs).astype(int)
        U = up[base[:, None] - ilin[None, :]]
        X = U
        mults = 0
    elif arm == "cbg":
        X = U
        mults = 0
    else:
        Wg = {"cbg_J": KX["Jn"], "cbg_K": KX["Kn"], "cbg_symJ": KX["symJ"]}[arm]
        w = Wg[KX["ii"], KX["jj"]]
        Q = U[:, KX["ii"]] * U[:, KX["jj"]] * w[None, :]
        X = np.hstack([U, Q])
        mults = int(KX["n_pairs"])
    y = yfull[base - WINDOW]                            # y[t], t=base
    return X, y, {"dim": X.shape[1], "mults_per_step": mults}


def run_config(cfg, KX):
    t0 = time.time()
    out = dict(cfg)
    try:
        # 种子语义：gen_narma 走全局 np.random；每配置固定种子，使种子可复现
        # （07 未对 narma 重播种，此处为有据偏离，见 b_summary.md）
        np.random.seed(42000 + cfg["seed"])
        n = max(4000, cfg["n_train"] + 2000) + 1000
        u, yfull = rc04.gen_narma(n)
        X, y, meta = build_feats(cfg["arm"], u, yfull, KX)
        X, y = X[1000:], y[1000:]
        n_tr = cfg["n_train"]
        from sklearn.linear_model import Ridge
        reg = Ridge(cfg["lam"])
        reg.fit(X[:n_tr], y[:n_tr])
        yhat = reg.predict(X[n_tr:])
        out["nmse"] = float(np.mean((yhat - y[n_tr:]) ** 2) / np.var(y[n_tr:]))
        out["w_norm"] = float(np.linalg.norm(reg.coef_))
        out.update(meta)
        out["n_test"] = int(len(y) - n_tr)
        out["ok"] = True
    except Exception as e:                                  # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    out["id"] = hashlib.sha1(json.dumps(cfg, sort_keys=True)
                             .encode()).hexdigest()[:12]
    return out


def build_grid(quick=False):
    arms = ["lin", "cbg", "cbg_J", "cbg_K", "cbg_symJ", "ngrc"]
    if quick:
        NTRAIN_Q, SEEDS_Q = [300], [0]
    else:
        NTRAIN_Q, SEEDS_Q = NTRAIN, SEEDS
    return [{"arm": a, "n_train": n, "lam": l, "seed": s}
            for a, n, l, s in itertools.product(arms, NTRAIN_Q, LAMS, SEEDS_Q)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    if a.aggregate:
        aggregate()
        return
    KX = build_kernels()
    print("kernels: unique_taps=%d/%d, n_pairs=%d (mask>%.2f)"
          % (KX["unique_taps"], N_CH, KX["n_pairs"], J_THRESH), flush=True)
    done = set()
    if os.path.exists(JSONL):
        with open(JSONL, encoding="utf-8") as f:
            for l in f:
                try:
                    done.add(json.loads(l)["id"])
                except Exception:                           # noqa: BLE001
                    pass
    grid = [c for c in build_grid(a.quick)
            if hashlib.sha1(json.dumps(c, sort_keys=True).encode())
            .hexdigest()[:12] not in done]
    print("todo: %d configs" % len(grid), flush=True)
    with open(JSONL, "a", encoding="utf-8") as f:
        for cfg in grid:
            out = run_config(cfg, KX)
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            f.flush()
            if out["ok"]:
                print("  %-10s n=%-4d lam=%-7g s%d nmse=%.4g (dim=%d)"
                      % (cfg["arm"], cfg["n_train"], cfg["lam"], cfg["seed"],
                         out["nmse"], out["dim"]), flush=True)
            else:
                print("  FAIL", cfg, out["error"], flush=True)
    aggregate()


def aggregate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
    rows = [r for r in rows if r.get("ok")]
    arms = ["lin", "cbg", "cbg_J", "cbg_K", "cbg_symJ", "ngrc"]
    labels = {"lin": "linear taps", "cbg": "CBG taps (meas.)",
              "cbg_J": "CBG + causal gain J", "cbg_K": "CBG + symmetric K",
              "cbg_symJ": "CBG + sym(J) hyp.", "ngrc": "digital NGRC"}

    # ---- 表：NMSE mean±std（3 种子），按 λ 分块 ----
    lines = ["# sim14-B：同预算 NARMA10 对照（NMSE，3 种子 mean±std）\n",
             "> 成本为数字等效口径（特征乘法数/读出维度），非器件能耗。"
             "cbg_symJ 为假想对称上界（A 的 J 显著不对称，不声称已实现）。\n"]
    lines.append("| arm | dim | mults/step | " +
                 " | ".join("n=%d" % n for n in NTRAIN) +
                 " | best-λ n=%d |" % NTRAIN[-1])
    lines.append("|---|---|---|---|---|---|")
    tab = {}
    for arm in arms:
        sub = [r for r in rows if r["arm"] == arm]
        if not sub:
            continue
        dim = sub[0]["dim"]; mults = sub[0]["mults_per_step"]
        cells = []
        for n in NTRAIN:
            vals = [r["nmse"] for r in sub if r["n_train"] == n and
                    r["lam"] == 1e-4 and "nmse" in r]
            cells.append("%.3g±%.3g" % (np.mean(vals), np.std(vals))
                         if vals else "–")
        cands = [(np.mean([r["nmse"] for r in sub if r["n_train"] == NTRAIN[-1]
                           and r["lam"] == lam]), lam)
                 for lam in LAMS
                 if any(r["n_train"] == NTRAIN[-1] and r["lam"] == lam and
                        "nmse" in r for r in sub)]
        best = min(cands) if cands else (float("nan"), float("nan"))
        tab[arm] = (dim, mults, cells, best)
        lines.append("| %s | %d | %d | %s | %.3g (λ=%g) |" %
                     (labels[arm], dim, mults, " | ".join(cells),
                      best[0], best[1]))
    with open(os.path.join(OUT, "b_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # ---- fig3 ----
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.4))
    ax = axes[0]
    mk = {"lin": "x:", "cbg": "s-", "cbg_J": "^-", "cbg_K": "v--",
          "cbg_symJ": "P-", "ngrc": "o-"}
    for arm in arms:
        sub = [r for r in rows if r["arm"] == arm and r["lam"] == 1e-4]
        ns, ms, es = [], [], []
        for n in NTRAIN:
            vals = [r["nmse"] for r in sub if r["n_train"] == n and "nmse" in r]
            if vals:
                ns.append(n); ms.append(np.mean(vals)); es.append(np.std(vals))
        if ns:
            ax.errorbar(ns, ms, yerr=es, fmt=mk[arm], ms=4, label=labels[arm])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set(xlabel="n_train", ylabel="NMSE",
           title="(a) NARMA10 @ λ=1e-4 (mean±std, 3 seeds)")
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    ax = axes[1]
    arm_best = {}
    for arm in arms:
        sub = [r for r in rows if r["arm"] == arm]
        ns, ms = [], []
        for n in NTRAIN:
            best = min((np.mean([r["nmse"] for r in sub if r["n_train"] == n
                                 and r["lam"] == lam]), lam)
                       for lam in LAMS
                       if any(r["n_train"] == n and r["lam"] == lam
                              and "nmse" in r for r in sub))
            ns.append(n); ms.append(best[0])
        arm_best[arm] = (ns, ms)
        ax.plot(ns, ms, mk[arm], ms=4, label=labels[arm])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set(xlabel="n_train", ylabel="NMSE (best λ)",
           title="(b) best-over-λ NMSE")
    ax.legend(fontsize=7); ax.grid(alpha=.3)

    ax = axes[2]
    xs = np.arange(len(arms))
    dims = [tab[a][0] for a in arms]
    ml = [tab[a][1] for a in arms]
    ax.bar(xs - 0.2, dims, 0.4, label="readout dim")
    ax.bar(xs + 0.2, ml, 0.4, label="mults/step (dig. equiv.)")
    ax.set_xticks(xs); ax.set_xticklabels([labels[a] for a in arms],
                                          rotation=20, ha="right", fontsize=7)
    ax.set_title("(c) digital-equivalent cost (NOT device energy)")
    ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_ablation.png"), dpi=150)
    plt.close(fig)
    print("saved fig3_ablation.png + b_summary.md ->", OUT, flush=True)


if __name__ == "__main__":
    main()
