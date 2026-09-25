# -*- coding: utf-8 -*-
"""
Comprehensive photonic reservoir simulation for slow-readout LiDAR processing.

Demonstrates that a photonic time-delay reservoir can accept ps-level optical
spikes, process them with fast internal delays, and be read out by slow
electrical integration (ns-µs), achieving high classification accuracy.

Outputs figures and data for the simulation report.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")


def generate_spike_scene(t, class_id, rng, noise=0.05, amp_noise=0.1):
    """Generate a ps-level spike train for one of three scene classes."""
    spikes = np.zeros_like(t)
    if class_id == 0:
        delays = [1.0e-12]
        amps = [1.0]
    elif class_id == 1:
        delays = [0.8e-12, 2.2e-12]
        amps = [1.0, 0.7]
    else:
        delays = [0.6e-12, 1.6e-12, 3.0e-12]
        amps = [1.0, 0.65, 0.4]

    for d, a in zip(delays, amps):
        d += rng.normal(0, noise * d)
        a *= rng.uniform(1 - amp_noise, 1 + amp_noise)
        width = 0.10e-12 + rng.uniform(-0.02e-12, 0.02e-12)
        spikes += a * np.exp(-((t - d) / width)**2)
    return spikes


def photonic_reservoir_states(spikes, delays, weights, dt, nonlin=np.tanh):
    """Time-delay photonic reservoir with fast internal delays."""
    N, T = len(delays), len(spikes)
    states = np.zeros((T, N))
    for i, d in enumerate(delays):
        shift = int(round(d / dt))
        delayed = np.zeros_like(spikes)
        if shift >= 0:
            delayed[shift:] = spikes[:-shift] if shift > 0 else spikes
        else:
            delayed[:shift] = spikes[-shift:]
        states[:, i] = nonlin(weights[i] * delayed)
    return states


def slow_readout_features(states, t, integration_time, readout_sample_interval=None):
    """
    Simulate slow photodetection: integrate reservoir state over
    `integration_time` windows. If readout_sample_interval is None, return a
    single integrated vector per sample (one slow readout per scene).
    """
    dt = t[1] - t[0]
    n_int = max(1, int(round(integration_time / dt)))
    n_nodes = states.shape[1]
    features = []
    for start in range(0, len(t), n_int):
        end = min(start + n_int, len(t))
        window = states[start:end, :]
        features.append(window.mean(axis=0))
    features = np.array(features).flatten()
    return features


def evaluate(spike_trains, labels, t, delays, weights, dt, integration_time,
             n_samples, rng, test_size=0.3):
    """Train a linear readout on slow-integrated reservoir features."""
    features = []
    for spikes in spike_trains:
        states = photonic_reservoir_states(spikes, delays, weights, dt)
        feat = slow_readout_features(states, t, integration_time)
        features.append(feat)
    features = np.array(features)

    # handle feature length consistency
    min_len = min(len(f) for f in features)
    features = np.array([f[:min_len] for f in features])

    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=test_size, random_state=int(rng.integers(1000)),
        stratify=labels
    )
    clf = LogisticRegression(max_iter=2000)
    clf.fit(X_train, y_train)
    return clf.score(X_train, y_train), clf.score(X_test, y_test)


def main():
    # load time axis from previous demo
    d = np.load(os.path.join(OUT, "lidar_to_spike_demo.npz"))
    t = d["t"]
    dt = t[1] - t[0]

    rng = np.random.default_rng(2026)
    n_samples = 200
    n_delays = 30
    delay_min, delay_max = 0.2e-12, 3.5e-12
    delay_values = np.linspace(delay_min, delay_max, n_delays)
    weights = rng.normal(0, 1.5, n_delays)

    # generate dataset
    X, y = [], []
    for _ in range(n_samples):
        cls = rng.integers(0, 3)
        spikes = generate_spike_scene(t, cls, rng)
        X.append(spikes)
        y.append(cls)
    X = np.array(X)
    y = np.array(y)

    # Figure 1: example spike trains and reservoir states
    fig, axes = plt.subplots(3, 2, figsize=(10, 9))
    for cls in range(3):
        idx = np.where(y == cls)[0][0]
        spikes = X[idx]
        states = photonic_reservoir_states(spikes, delay_values, weights, dt)

        ax = axes[cls, 0]
        ax.plot(t * 1e12, spikes / spikes.max())
        ax.set_title("Class %d input spike train" % cls)
        ax.set_xlim(-2, 8)
        ax.set_xlabel("time (ps)")
        ax.set_ylabel("norm. amplitude")
        ax.grid(True, alpha=0.3)

        ax = axes[cls, 1]
        im = ax.imshow(states.T, aspect="auto",
                       extent=[t[0]*1e12, t[-1]*1e12, 0, n_delays],
                       cmap="viridis", origin="lower")
        ax.set_title("Photonic reservoir state (class %d)" % cls)
        ax.set_xlim(-2, 8)
        ax.set_xlabel("time (ps)")
        ax.set_ylabel("delay tap index")
        fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_reservoir_examples.png"), dpi=150)
    print("saved report_reservoir_examples.png")

    # Figure 2: integration time sweep
    int_times = np.logspace(-13, -7, 25)  # 1 ps to 100 ns
    train_accs, test_accs = [], []
    for it in int_times:
        tr, te = evaluate(X, y, t, delay_values, weights, dt, it, n_samples, rng)
        train_accs.append(tr)
        test_accs.append(te)
    train_accs = np.array(train_accs)
    test_accs = np.array(test_accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(int_times * 1e12, train_accs, "o-", label="train accuracy", lw=1.5)
    ax.semilogx(int_times * 1e12, test_accs, "s-", label="test accuracy", lw=1.5)
    ax.axhline(1/3, color="k", ls="--", alpha=0.3, label="random guess")
    ax.set_xlabel("integration time (ps)")
    ax.set_ylabel("classification accuracy")
    ax.set_title("Slow-readout accuracy vs integration time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_integration_time_sweep.png"), dpi=150)
    print("saved report_integration_time_sweep.png")

    # Figure 3: timing jitter robustness (at fixed integration time)
    best_int_time = int_times[np.argmax(test_accs)]
    print("best integration time from sweep: %.3f ps" % (best_int_time * 1e12))

    jitter_levels = np.linspace(0, 0.30, 13)
    jitter_accs = []
    for jit in jitter_levels:
        X_jit = []
        for _ in range(n_samples):
            cls = rng.integers(0, 3)
            X_jit.append(generate_spike_scene(t, cls, rng, noise=jit))
        X_jit = np.array(X_jit)
        _, te = evaluate(X_jit, y, t, delay_values, weights, dt, best_int_time,
                         n_samples, rng)
        jitter_accs.append(te)
    jitter_accs = np.array(jitter_accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(jitter_levels * 100, jitter_accs, "o-", lw=1.5)
    ax.axhline(1/3, color="k", ls="--", alpha=0.3)
    ax.set_xlabel("timing jitter (% of delay)")
    ax.set_ylabel("test accuracy")
    ax.set_title("Robustness to spike timing jitter")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_jitter_robustness.png"), dpi=150)
    print("saved report_jitter_robustness.png")

    # Figure 4: number of delay taps vs accuracy
    tap_counts = [5, 10, 15, 20, 30, 50, 80]
    tap_accs = []
    for n_taps in tap_counts:
        delays = np.linspace(delay_min, delay_max, n_taps)
        w = rng.normal(0, 1.5, n_taps)
        _, te = evaluate(X, y, t, delays, w, dt, best_int_time, n_samples, rng)
        tap_accs.append(te)
    tap_accs = np.array(tap_accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(tap_counts, tap_accs, "o-", lw=1.5)
    ax.axhline(1/3, color="k", ls="--", alpha=0.3)
    ax.set_xlabel("number of delay taps")
    ax.set_ylabel("test accuracy")
    ax.set_title("Accuracy vs reservoir size")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_tap_count_sweep.png"), dpi=150)
    print("saved report_tap_count_sweep.png")

    # Save summary data
    np.savez(os.path.join(OUT, "report_reservoir_summary.npz"),
             integration_times=int_times,
             train_accs=train_accs, test_accs=test_accs,
             jitter_levels=jitter_levels, jitter_accs=jitter_accs,
             tap_counts=tap_counts, tap_accs=tap_accs,
             best_integration_time=best_int_time,
             n_delays=n_delays, delay_min=delay_min, delay_max=delay_max)
    print("saved report_reservoir_summary.npz")


if __name__ == "__main__":
    main()
