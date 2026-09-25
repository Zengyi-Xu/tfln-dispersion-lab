# -*- coding: utf-8 -*-
"""08b: 接口读出加难档 —— LIF 饱和后的噪声-精度-能耗权衡（08 的增补）。

动机（docs/rq_evidence_log.md 第四十一/四十三批）：
08 全量显示 LIF 首脉冲延迟编码在 noise≤0.10 下 5 种子全部 ≥0.998
——任务对时间编码太简单，噪声-精度权衡曲线不可测，RQ4 的鲁棒性
主张缺数据。本脚本不改 08（其结果已入库冻结），只做加难增补：

  噪声档 noise_std ∈ {0.10, 0.20, 0.35, 0.50}（0.10 为与 08 的衔接锚点）
  LIF 降维臂 lif_N{16,32,64}（检验时间编码对神经元数的依赖）
  uniform 参照臂只保留 08 中最强的三个：
    fs0.25_b2（最优低配）、fs0.25_b8（等精度对照）、fs0.5_b8（中档）

  输出：results/interface_readout_hard/results.jsonl（与 08 不同目录，
  键含 lif 的 N，不与 08 的行冲突）。用法同 08：--quick/--workers/--aggregate
"""
import argparse
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib
_m08 = importlib.import_module("08_interface_readout")

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "interface_readout_hard")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

T = _m08.T
LIF_NS = [16, 32, 64]
UNIFORM_ARMS = [(0.25, 2), (0.25, 8), (0.5, 8)]


def feats_lif_n(x, n, seed=5):
    """08.feats_lif 的参数化版本：N 个神经元，同一随机数流。"""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((64, 64))[:n]  # 与 08 同分布，取前 n 行
    thr = rng.uniform(0.02, 0.08, 64)[:n]
    xs = x[:: T // 64]
    lat = np.full(n, T, float)
    v = np.zeros(n)
    for t in range(T):
        inj = w @ np.roll(xs, t % 64)
        v = 0.98 * v + inj * (x[t] > 0)
        fire = (v >= thr) & (lat == T)
        lat[fire] = t
        v[fire] = 0.0
    n_spikes = int((lat < T).sum())
    return lat / T, n_spikes * 8


def run_config(cfg):
    seed = cfg["seed"]
    X, y = _m08.gen_task(seed, cfg["noise"])
    n_train = int(0.7 * len(y))
    arm = cfg["arm"]
    F = []
    energy = 0.0
    for x in X:
        if arm == "uniform":
            f, e = _m08.feats_uniform(x, cfg["fs_mult"], cfg["bits"])
        elif arm == "lif":
            f, e = feats_lif_n(x, cfg["lif_n"])
        F.append(f)
        energy += e
    F = np.array(F)
    acc = _m08.ridge_classify(F, y, n_train)
    return {**cfg, "acc": acc, "energy_proxy": energy / len(X),
            "n_features": F.shape[1]}


def build_grid(quick=False):
    grid = []
    noises = [0.10, 0.20, 0.35, 0.50] if not quick else [0.35]
    seeds = range(5) if not quick else range(1)
    for noise, seed in itertools.product(noises, seeds):
        for fs_mult, bits in (UNIFORM_ARMS if not quick else [(0.25, 8)]):
            grid.append({"arm": "uniform", "fs_mult": fs_mult, "bits": bits,
                         "lif_n": None, "noise": noise, "seed": seed})
        for n in (LIF_NS if not quick else [64]):
            grid.append({"arm": "lif", "fs_mult": None, "bits": None,
                         "lif_n": n, "noise": noise, "seed": seed})
    return grid


_KEY_FIELDS = ("arm", "fs_mult", "bits", "lif_n", "noise", "seed")


def done_keys():
    keys = set()
    if os.path.exists(JSONL):
        with open(JSONL) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    keys.add(json.dumps({k: r[k] for k in _KEY_FIELDS},
                                        sort_keys=True))
                except Exception:
                    pass
    return keys


def key_of(cfg):
    return json.dumps({k: cfg[k] for k in _KEY_FIELDS}, sort_keys=True)


def aggregate():
    import collections
    agg = collections.defaultdict(list)
    with open(JSONL) as f:
        for line in f:
            r = json.loads(line)
            name = (f"uniform_fs{r['fs_mult']}_b{r['bits']}"
                    if r["arm"] == "uniform" else f"lif_N{r['lif_n']}")
            agg[(name, r["noise"])].append((r["acc"], r["energy_proxy"]))
    rows = []
    for (name, noise), vals in sorted(agg.items()):
        accs = [v[0] for v in vals]
        en = np.mean([v[1] for v in vals])
        rows.append((noise, name, np.mean(accs), np.std(accs), en, len(vals)))
    print(f"{'noise':>6} {'arm':<20} {'acc_mean':>8} {'acc_std':>7} "
          f"{'E_proxy':>10} {'n':>3}")
    for noise, name, m, s, en, n in rows:
        print(f"{noise:>6} {name:<20} {m:8.3f} {s:7.3f} {en:10.0f} {n:>3}")


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
