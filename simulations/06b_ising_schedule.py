# -*- coding: utf-8 -*-
"""06b: 退火调度对比 —— 递减步长能否救 sin 失效区（06 的增补）。

动机（docs/rq_evidence_log.md 第三十五/三十九/四十二批）：
06 全量发现 sin 失效区 = dense + β=5 + 大噪声 + N=1000（sin 非单调折返，
配对 sin−tanh −0.97）。文献给出两类调度线索：
  ① Al-Kayed SI §S1.4.2 引 Pramanik：递减步长 η_k = η_0/(k+1)^r, r∈(0.5,1]
     理论上兼顾收敛速度与不发散；
  ② Li 2024 G22：自旋幅度不均→局域极小，动态参数控制可缓解。
本脚本不改 06（其结果已入库冻结），在同图同 SA 基准上只换退火调度：

  调度臂（噪声乘子 m_k，增益乘子 g_k；x ← f(αx + g_k·β·Jx/√N + m_k·η)）
    sched=linear        06 原样（m_k=1−k/iters，g=1）——跨脚本锚点
    sched=pow_r{0.5,0.75,1.0}   Pramanik 幂律 m_k=(k+1)^(−r)
    sched=beta_ramp     线性噪声 + 耦合线性爬升 g_k=min(1, k/(0.5·iters))
                        （CIM 式泵浦爬升，检验"晚开耦合"能否避开折返区）

  聚焦网格（不全扫）：
    失效区：dense, β=5, noise=1.0, N=1000, α∈{0.3,0.5,0.8}
    对照区：3reg, β=1, noise=0.1, N=1000, α=0.8（sin 占优区，验证调度不帮倒忙）
    act ∈ {sin, tanh} × 4 inst = 2×(3+1)×4 = 32 配置 × 5 调度 = 160 行

  输出：results/ising_schedule/results.jsonl。用法同 06：--quick/--workers/--aggregate
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
OUT = os.path.join(ROOT, "results", "ising_schedule")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

ITERS = 300


def run_ising_sched(J, act, alpha, beta, noise0, sched, iters=ITERS, seed=0):
    """06.run_ising 的调度参数化版本。图、能量、SA 基准全部复用 06。"""
    rng = np.random.default_rng(seed)
    N = len(J)
    f = _m06.ACTS[act]
    x = rng.uniform(-0.1, 0.1, N)
    Jn = J / np.sqrt(N)
    best = 0.0
    traj = []
    for k in range(iters):
        if sched == "linear":
            m, g = 1 - k / iters, 1.0
        elif sched.startswith("pow_r"):
            r = float(sched.split("_r")[1])
            m, g = (k + 1) ** (-r), 1.0
        elif sched == "beta_ramp":
            m, g = 1 - k / iters, min(1.0, k / (0.5 * iters))
        else:
            raise ValueError(sched)
        eta = noise0 * m * rng.normal(0, 1, N)
        x = f(alpha * x + g * beta * (Jn @ x) + eta)
        s = np.sign(x)
        s[s == 0] = 1
        E = _m06.energy(J, s)
        if E < best:
            best = E
        traj.append(best)
    return best, np.asarray(traj)


def run_config(cfg):
    t0 = time.time()
    rng = np.random.default_rng(52000 + cfg["inst"])  # 与 06 完全一致
    out = dict(cfg)
    try:
        J = _m06.gen_graph(cfg["graph"], cfg["N"], rng)
        bk = _m06.sa_reference(J, iters=60000, seed=cfg["inst"] * 7 + 1)  # 与 06 一致
        out["bk_energy"] = float(bk)
        thr = 0.97 * bk
        n_runs = 2 if cfg.get("quick") else 5
        ratios, tts = [], []
        for r in range(n_runs):
            best, traj = run_ising_sched(
                J, cfg["act"], cfg["alpha"], cfg["beta"], cfg["noise"],
                cfg["sched"], seed=cfg["inst"] * 100 + r)
            ratios.append(best / bk)
            hit = np.nonzero(traj <= thr)[0]
            tts.append(int(hit[0]) if len(hit) else ITERS)
        out["metric"] = float(np.mean(ratios))
        out["metric_name"] = "energy_ratio"
        out["success"] = float(np.mean([r >= 0.97 for r in ratios]))
        out["tts_mean"] = float(np.mean(tts))
        out["ok"] = True
    except Exception as e:  # noqa: BLE001
        out["ok"] = False
        out["error"] = "%s: %s" % (type(e).__name__, e)
    out["wall_s"] = round(time.time() - t0, 2)
    return out


SCHEDS = ["linear", "pow_r0.5", "pow_r0.75", "pow_r1.0", "beta_ramp"]
REGIONS = [
    # (label, graph, beta, noise, alphas)
    ("fail_dense", "dense", 5.0, 1.0, [0.3, 0.5, 0.8]),
    ("ctrl_3reg", "3reg", 1.0, 0.1, [0.8]),
]


def build_grid(quick=False):
    grid = []
    scheds = ["linear", "pow_r1.0"] if quick else SCHEDS
    acts = ["sin"] if quick else ["sin", "tanh"]
    insts = [0] if quick else list(range(4))
    for (label, graph, beta, noise, alphas), act, sched, alpha, inst in \
            itertools.product(REGIONS, acts, scheds,
                              [None], insts):
        for al in ([0.5] if quick else alphas):
            c = {"region": label, "act": act, "sched": sched, "alpha": al,
                 "beta": beta, "noise": noise, "graph": graph, "N": 1000,
                 "inst": inst}
            if quick:
                c["quick"] = True
            grid.append(c)
    return grid


_KEY_FIELDS = ("region", "act", "sched", "alpha", "beta", "noise",
               "graph", "N", "inst")


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
            if not r.get("ok"):
                continue
            agg[(r["region"], r["act"], r["sched"], r["alpha"])].append(
                (r["metric"], r["tts_mean"]))
    print(f"{'region':<12} {'act':<5} {'sched':<10} {'alpha':>5} "
          f"{'E/BK':>7} {'TTS':>6} {'n':>3}")
    for (region, act, sched, alpha), vals in sorted(agg.items()):
        m = np.mean([v[0] for v in vals])
        t = np.mean([v[1] for v in vals])
        print(f"{region:<12} {act:<5} {sched:<10} {alpha:>5} "
              f"{m:7.3f} {t:6.1f} {len(vals):>3}")


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
