# -*- coding: utf-8 -*-
"""08: 接口读出成本对比 —— 均匀采样 vs 事件驱动（RQ4 判据的直接检验）。

动机（docs/rq_evidence_log.md 第四批 / digest §三-12/13）：
RQ4 判据的结论是「SNN vs RC 是伪二分，真正的对立面是 事件驱动读出 vs
均匀采样数字后端」。本脚本把这个论断变成可证伪的仿真：同一个时序分类任务、
同一个前端，只换接口读出方式，比较 精度 vs 接口能耗代理。

  任务（雷达动机）：多重回波延迟模式分类。K=8 类，每类由 2 个回波的
  延迟对 {d1,d2} 定义；波形 x(t) = Σ chirp(t-d_i) + 噪声，T=2048 点。
  信息天然写在到达时间上（零号稿 a) 段的前提），是事件读出的主场。

  读出臂
    uniform_fs{0.25,0.5,1,2}_b{2,4,8}  —— 均匀采样 × 均匀量化
        （ADC+数字后端模型；能耗代理 = n_samples × bits）
    lc_b{4,8}                          —— 电平穿越事件（地址-事件表示）
        （能耗代理 = n_events × (log2 n_levels + 8 bit 时间戳)）
    lif_N64                            —— 64 个随机权重/阈值 LIF 神经元，
        特征 = 首脉冲延迟（时间编码）；能耗代理 = n_spikes × 8 bit
  读出统一为岭回归分类（one-vs-rest 最小二乘 + argmax），公平。

  扫描：noise_std ∈ {0.0, 0.05, 0.10} × seed ∈ 5 个。
  输出：results/interface_readout/results.jsonl，每行
    {arm, fs_mult, bits, noise, seed, acc, energy_proxy, n_features}

用法同 03-07：--quick / --workers N / --aggregate
断点续跑：results/interface_readout/results.jsonl
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
OUT = os.path.join(ROOT, "results", "interface_readout")
os.makedirs(OUT, exist_ok=True)
JSONL = os.path.join(OUT, "results.jsonl")

T = 2048
K_CLASSES = 8
N_PER_CLASS = 400
CHIRP_LEN = 128
DELAY_GRID = [200, 500, 800, 1100, 1400, 1700]
LIF_N = 64


def chirp(t0):
    t = np.arange(CHIRP_LEN)
    phase = 2 * np.pi * (0.05 * t + 0.5 * 0.12 * t ** 2 / CHIRP_LEN)
    env = np.sin(np.pi * t / CHIRP_LEN) ** 2
    sig = np.zeros(T)
    if t0 + CHIRP_LEN <= T:
        sig[t0:t0 + CHIRP_LEN] = env * np.cos(phase)
    return sig


CHIRP_REF = chirp(0)
_NFFT = T + CHIRP_LEN - 1
_REF_F = np.conj(np.fft.rfft(CHIRP_REF, _NFFT))
_SX = np.arange(-40, 41)
_SMOOTH = np.exp(-0.5 * (_SX / 10.0) ** 2)
_SMOOTH /= _SMOOTH.sum()


def pulse_compress(s):
    """匹配滤波（频域互相关）+ 平滑；峰位 = 回波延迟。"""
    c = np.fft.irfft(np.fft.rfft(s, _NFFT) * _REF_F, _NFFT)[:T]
    c = np.convolve(np.abs(c), _SMOOTH, mode="same")
    return c / (c.max() + 1e-12)


def gen_task(seed, noise_std):
    """K 类 = 延迟对组合（取网格下三角前 8 个）；每类 N_PER_CLASS 条。
    前端：匹配滤波脉压 + 平滑（模拟域完成，所有读出臂共享）→ 峰位即类别信息。"""
    rng = np.random.default_rng(seed)
    pairs = [(a, b) for i, a in enumerate(DELAY_GRID) for b in DELAY_GRID[i + 1:]]
    pairs = pairs[:K_CLASSES]
    X = np.zeros((K_CLASSES * N_PER_CLASS, T))
    y = np.repeat(np.arange(K_CLASSES), N_PER_CLASS)
    for k, (d1, d2) in enumerate(pairs):
        for j in range(N_PER_CLASS):
            amp1, amp2 = rng.uniform(0.7, 1.3, 2)
            jit1, jit2 = rng.integers(-20, 21, 2)
            s = amp1 * chirp(d1 + jit1) + amp2 * chirp(d2 + jit2)
            s += noise_std * rng.standard_normal(T)
            X[k * N_PER_CLASS + j] = pulse_compress(s)
    return X, y


def feats_uniform(x, fs_mult, bits):
    step = max(1, int(round(1.0 / fs_mult)))
    xs = x[::step]
    lo, hi = xs.min(), xs.max()
    q = np.clip(((xs - lo) / (hi - lo + 1e-12) * (2 ** bits - 1)).round(),
                0, 2 ** bits - 1)
    feats = q / (2 ** bits - 1)
    energy = len(xs) * bits
    return feats, energy


def feats_lc(x, bits):
    n_levels = 2 ** bits
    lo, hi = x.min(), x.max()
    levels = np.linspace(lo, hi, n_levels + 1)[1:-1]
    d = np.digitize(x, levels)
    ch = np.nonzero(np.diff(d))[0] + 1
    ev_t = ch
    ev_l = d[ch]
    # 定长特征：每电平的首次穿越时间 + 穿越次数 + 事件间隔直方图(8 bin)
    first_t = np.full(n_levels, T, float)
    count = np.zeros(n_levels)
    for t, l in zip(ev_t, ev_l):
        if t < first_t[l]:
            first_t[l] = t
        count[l] += 1
    if len(ev_t) > 1:
        iei = np.diff(ev_t)
        hist = np.histogram(iei, bins=8, range=(0, T // 4))[0]
    else:
        hist = np.zeros(8)
    feats = np.concatenate([first_t / T, np.log1p(count), np.log1p(hist)])
    energy = len(ev_t) * (int(np.log2(n_levels)) + 8)
    return feats, energy


def feats_lif(x, seed=5):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((LIF_N, 64))
    thr = rng.uniform(0.02, 0.08, LIF_N)
    xs = x[:: T // 64]  # 64 通道降采样作为各神经元输入窗
    lat = np.full(LIF_N, T, float)
    v = np.zeros(LIF_N)
    for t in range(T):
        inj = w @ np.roll(xs, t % 64)
        v = 0.98 * v + inj * (x[t] > 0)
        fire = (v >= thr) & (lat == T)
        lat[fire] = t
        v[fire] = 0.0
    n_spikes = int((lat < T).sum())
    feats = lat / T
    energy = n_spikes * 8
    return feats, energy


def ridge_classify(F, y, n_train, lam=1e-3, seed=0):
    idx = np.random.default_rng(seed).permutation(len(y))
    F, y = F[idx], y[idx]
    Ftr, Fte = F[:n_train], F[n_train:]
    ytr = y[:n_train]
    K = int(y.max()) + 1
    Y = np.eye(K)[ytr] * 2 - 1
    A = Ftr.T @ Ftr + lam * np.eye(F.shape[1])
    W = np.linalg.solve(A, Ftr.T @ Y)
    pred = (Fte @ W).argmax(1)
    return float((pred == y[n_train:]).mean())


def run_config(cfg):
    seed = cfg["seed"]
    X, y = gen_task(seed, cfg["noise"])
    n_total = len(y)
    n_train = int(0.7 * n_total)
    arm = cfg["arm"]
    F = []
    energy = 0.0
    for x in X:
        if arm == "uniform":
            f, e = feats_uniform(x, cfg["fs_mult"], cfg["bits"])
        elif arm == "lc":
            f, e = feats_lc(x, cfg["bits"])
        elif arm == "lif":
            f, e = feats_lif(x)
        F.append(f)
        energy += e
    F = np.array(F)
    acc = ridge_classify(F, y, n_train)
    return {**cfg, "acc": acc, "energy_proxy": energy / len(X),
            "n_features": F.shape[1]}


def build_grid(quick=False):
    grid = []
    noises = [0.0, 0.05, 0.10] if not quick else [0.05]
    seeds = range(5) if not quick else range(1)
    for noise, seed in itertools.product(noises, seeds):
        for fs_mult in ([0.25, 0.5, 1.0, 2.0] if not quick else [0.5, 1.0]):
            for bits in ([2, 4, 8] if not quick else [4]):
                grid.append({"arm": "uniform", "fs_mult": fs_mult,
                             "bits": bits, "noise": noise, "seed": seed})
        for bits in ([4, 8] if not quick else [4]):
            grid.append({"arm": "lc", "fs_mult": None, "bits": bits,
                         "noise": noise, "seed": seed})
        grid.append({"arm": "lif", "fs_mult": None, "bits": None,
                     "noise": noise, "seed": seed})
    return grid


def done_keys():
    keys = set()
    if os.path.exists(JSONL):
        with open(JSONL) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    keys.add(json.dumps({k: r[k] for k in
                                         ("arm", "fs_mult", "bits", "noise", "seed")},
                                        sort_keys=True))
                except Exception:
                    pass
    return keys


def key_of(cfg):
    return json.dumps({k: cfg[k] for k in
                       ("arm", "fs_mult", "bits", "noise", "seed")},
                      sort_keys=True)


def aggregate():
    import collections
    agg = collections.defaultdict(list)
    with open(JSONL) as f:
        for line in f:
            r = json.loads(line)
            name = r["arm"] if r["arm"] != "uniform" else \
                f"uniform_fs{r['fs_mult']}_b{r['bits']}"
            if r["arm"] == "lc":
                name = f"lc_b{r['bits']}"
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
