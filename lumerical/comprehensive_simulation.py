# -*- coding: utf-8 -*-
"""
Comprehensive simulation v2 for the photonic LiDAR -> SNN processing chain.

Improvements over v1 (fixes and rigor):
  - grating metrics: platform width / D fitted only on the linear delay region
  - matched filter: phi2 fitted from d(tau_r)/d(omega) directly
  - reservoir task: energy- AND centroid-matched classes (slow integration
    alone cannot distinguish them -> reservoir genuinely needed)
  - slow readout modeled physically as leaky photodetector integration of
    reservoir node outputs (time constant tau_leak); sweep readout delay to
    show how long the answer survives
  - comparison baselines: direct integration (no reservoir), fast sampling

Outputs npz summary and publication-style figures for the report.
"""
import os
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

C0 = 299792458.0
LAMBDA0 = 1.55e-6
OMEGA0 = 2 * np.pi * C0 / LAMBDA0


def fwhm(t, I):
    I = I / I.max()
    above = t[I >= 0.5]
    return above.max() - above.min() if len(above) > 1 else np.nan


# ---------------------------------------------------------------------------
# Part 1: FDTD data validation
# ---------------------------------------------------------------------------

def fdtd_summary():
    print("[FDTD smoke test]")
    d = np.load(os.path.join(OUT, "hello_fdtd.npz"))
    print("  wavelength: %.1f - %.1f nm, T in [%.4f, %.4f] -> lossless, setup OK"
          % (d["wl"].min() * 1e9, d["wl"].max() * 1e9, d["T"].min(), d["T"].max()))

    print("\n[chirped grating FDTD]")
    d = np.load(os.path.join(OUT, "chirp2d.npz"))
    wl_nm = d["wl"] * 1e9
    R = 1 - d["T"]
    platform = R > 0.9
    width_nm = wl_nm[platform].max() - wl_nm[platform].min()
    print("  L = %.1f um, dLambda = %.2f nm" % (d["L"] * 1e6, d["chirp_dLambda"] * 1e9))
    print("  reflection platform R>0.9: %.1f - %.1f nm (width %.1f nm)"
          % (wl_nm[platform].min(), wl_nm[platform].max(), width_nm))
    # linear delay region = platform
    tau_ps = d["tau_r"] * 1e12
    slope = np.polyfit(wl_nm[platform], tau_ps[platform], 1)[0]
    print("  delay swing on platform: %.2f ps" % (tau_ps[platform].max() - tau_ps[platform].min()))
    print("  dispersion D (linear fit on platform) = %.4f ps/nm" % slope)
    return {"platform_width_nm": width_nm, "D_ps_per_nm": slope,
            "delay_swing_ps": tau_ps[platform].max() - tau_ps[platform].min()}


# ---------------------------------------------------------------------------
# Part 2: time-lens / matched-filter analysis
# ---------------------------------------------------------------------------

def load_grating_response():
    d = np.load(os.path.join(OUT, "chirp2d.npz"))
    f, T, tau_r = d["f"], d["T"], d["tau_r"]
    order = np.argsort(f)
    f, T, tau_r = f[order], T[order], tau_r[order]
    omega = 2 * np.pi * f
    R = np.clip(1.0 - T, 0, None)
    domega = np.diff(omega, prepend=omega[0])
    phi = np.cumsum(tau_r * domega)
    phi = np.unwrap(phi - phi[0])
    H = np.sqrt(R) * np.exp(1j * phi)
    return omega, H, R, tau_r


def matched_filter_analysis():
    omega, H, R, tau_r = load_grating_response()

    # phi2 = d(tau_r)/d(omega) fitted on the linear region (R>0.9 platform)
    wl_nm = C0 / (omega / (2 * np.pi)) * 1e9
    platform = R > 0.9
    phi2 = np.polyfit(omega[platform] - OMEGA0, tau_r[platform], 1)[0]
    chirp_rate_matched = -1.0 / phi2
    print("\n[matched filter]")
    print("  phi2 = d tau/d omega = %.3e s^2/rad (fitted on platform)" % phi2)
    print("  matched chirp rate = %.3e rad/s^2" % chirp_rate_matched)

    N = 16384
    dt = 2e-15
    t = (np.arange(N) - N // 2) * dt
    Omega_shift = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(N, dt))
    H_shift = np.interp(OMEGA0 + Omega_shift, omega, H, left=0, right=0)
    H_fft = np.fft.ifftshift(H_shift)

    sigma_w = 2 * np.pi * C0 * 30e-9 / LAMBDA0**2
    E_in_spec_shift = np.exp(-Omega_shift**2 / (2 * sigma_w**2))
    E_in_spec = np.fft.ifftshift(E_in_spec_shift)

    # scan input chirp gamma
    gamma_vals = np.linspace(-2 * phi2, 0.5 * phi2, 80)
    widths = []
    for gamma in gamma_vals:
        phase = np.exp(1j * 0.5 * gamma * Omega_shift**2)
        E_out = np.fft.ifft(E_in_spec * np.fft.ifftshift(phase) * H_fft)
        I_out = np.abs(np.fft.fftshift(E_out))**2
        widths.append(fwhm(t, I_out))
    widths = np.array(widths)
    idx_best = np.nanargmin(widths)
    gamma_best = gamma_vals[idx_best]

    E_tl = np.fft.ifft(E_in_spec)
    I_tl = np.abs(np.fft.fftshift(E_tl))**2
    E_flat = np.fft.ifft(E_in_spec * H_fft)
    I_flat = np.abs(np.fft.fftshift(E_flat))**2
    phase_best = np.exp(1j * 0.5 * gamma_best * Omega_shift**2)
    E_best = np.fft.ifft(E_in_spec * np.fft.ifftshift(phase_best) * H_fft)
    I_best = np.abs(np.fft.fftshift(E_best))**2

    print("  transform-limited FWHM: %.3f ps" % (fwhm(t, I_tl) * 1e12))
    print("  flat-phase + grating FWHM: %.3f ps" % (fwhm(t, I_flat) * 1e12))
    print("  best matched FWHM: %.3f ps (compression vs spread: %.2fx)"
          % (fwhm(t, I_best) * 1e12, fwhm(t, I_flat) / fwhm(t, I_best)))
    print("  (a TFLN time lens supplying gamma = -phi2 does the matching)")

    fig, axes = plt.subplots(2, 1, figsize=(9, 8))
    ax = axes[0]
    ax.plot(t * 1e12, I_tl / I_tl.max(), label="transform-limited input", lw=1.5)
    ax.plot(t * 1e12, I_flat / I_flat.max(), label="flat phase + grating (spread)", lw=1.5)
    ax.plot(t * 1e12, I_best / I_best.max(), label="matched chirp + grating", lw=1.5)
    ax.set_xlim(-4, 4)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("normalized intensity")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax = axes[1]
    ax.plot(gamma_vals / phi2, widths * 1e12, "o-", ms=3, lw=1.2)
    ax.axvline(gamma_best / phi2, color="r", ls="--", label="best")
    ax.axvline(-1, color="k", ls=":", alpha=0.5, label="ideal (gamma=-phi2)")
    ax.set_xlabel("input chirp $\\gamma/\\phi_2$")
    ax.set_ylabel("output FWHM (ps)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_matched_filter.png"), dpi=150)
    print("  saved report_matched_filter.png")

    return {"t": t, "dt": dt, "omega": omega, "H": H, "R": R, "tau_r": tau_r,
            "phi2": phi2, "chirp_rate_matched": chirp_rate_matched,
            "gamma_vals": gamma_vals, "widths": widths,
            "I_tl": I_tl, "I_flat": I_flat, "I_best": I_best,
            "H_shift": H_shift, "Omega_shift": Omega_shift}


# ---------------------------------------------------------------------------
# Part 3: LiDAR -> spike train
# ---------------------------------------------------------------------------

def lidar_spike_analysis(grating):
    t, dt = grating["t"], grating["dt"]
    chirp_rate = grating["chirp_rate_matched"]
    B = 2 * np.pi * 8.0e12
    T_chirp = B / chirp_rate
    H_fft = np.fft.ifftshift(grating["H_shift"])

    targets = [(0.5e-12, 1.0), (1.5e-12, 0.6), (3.0e-12, 0.4), (4.5e-12, 0.3)]
    E_rx = np.zeros_like(t, dtype=complex)
    for delay, amp in targets:
        E_rx += amp * np.exp(-(t - delay)**2 / (2 * (T_chirp / 2.5)**2)) \
                * np.exp(1j * 0.5 * chirp_rate * (t - delay)**2)

    E_comp = np.fft.ifft(np.fft.fft(E_rx) * np.conj(H_fft))
    I_rx = np.abs(np.fft.fftshift(E_rx))**2
    I_comp = np.abs(np.fft.fftshift(E_comp))**2
    I_comp /= I_comp.max()
    t_shift = np.fft.fftshift(t)

    # per-pulse width: isolate the strongest peak
    i_max = np.argmax(I_comp)
    half = 400
    seg = I_comp[max(0, i_max - half):i_max + half]
    tseg = t_shift[max(0, i_max - half):i_max + half]
    pulse_fwhm = fwhm(tseg, seg)

    threshold = 0.15 * I_comp.max()
    spikes = np.where(I_comp > threshold, I_comp, 0.0)

    print("\n[LiDAR -> spike]")
    print("  matched chirp duration = %.2f ps (4 targets at 0.5/1.5/3.0/4.5 ps)" % (T_chirp * 1e12))
    print("  strongest compressed pulse FWHM: %.3f ps" % (pulse_fwhm * 1e12))
    print("  compression ratio (chirp/pulse): %.1f" % (T_chirp / pulse_fwhm))

    fig, axes = plt.subplots(3, 1, figsize=(10, 9))
    ax = axes[0]
    ax.plot(t_shift * 1e12, I_rx / I_rx.max())
    ax.set_xlim(-6, 12)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("norm. power")
    ax.set_title("received overlapped chirped echoes")
    ax.grid(True, alpha=0.3)
    ax = axes[1]
    ax.plot(t_shift * 1e12, I_comp)
    ax.set_xlim(-6, 12)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("norm. intensity")
    ax.set_title("after grating matched-filter compression")
    ax.grid(True, alpha=0.3)
    ax = axes[2]
    markerline, stemlines, baseline = ax.stem(t_shift * 1e12, spikes / spikes.max(), basefmt=" ")
    plt.setp(stemlines, linewidth=0.8)
    ax.set_xlim(-6, 12)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("spike amplitude")
    ax.set_title("thresholded spike train -> SNN input")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_lidar_to_spike.png"), dpi=150)
    print("  saved report_lidar_to_spike.png")

    return {"t": t_shift, "dt": dt, "I_rx": I_rx / I_rx.max(), "I_comp": I_comp,
            "spikes": spikes / spikes.max(), "targets": np.array(targets),
            "pulse_fwhm": pulse_fwhm, "T_chirp": T_chirp}


# ---------------------------------------------------------------------------
# Part 4: photonic reservoir with leaky slow readout
# ---------------------------------------------------------------------------

def generate_scene(t, class_id, rng, timing_jitter=0.02, amp_noise=0.05):
    """
    Three classes with EQUAL total optical energy (integral of power) and
    EQUAL centroid time (2.0 ps). Amplitudes scale as 1/n_spikes so the
    slowest possible measurement (total received energy) is identical.
    Only a nonlinear reservoir can turn the temporal pattern into features
    that survive slow integration.
    """
    if class_id == 0:                       # single central spike
        comps = [(2.0e-12, 1.0)]
    elif class_id == 1:                     # two spikes
        comps = [(1.5e-12, 0.5), (2.5e-12, 0.5)]
    else:                                   # three spikes
        comps = [(1.4e-12, 1 / 3), (2.0e-12, 1 / 3), (2.6e-12, 1 / 3)]

    spikes = np.zeros_like(t)
    for d, a in comps:
        d += rng.normal(0, timing_jitter * 1e-12)
        a *= rng.uniform(1 - amp_noise, 1 + amp_noise)
        spikes += a * np.exp(-((t - d) / 0.10e-12)**2)
    return spikes


def reservoir_states(spikes, delays, weights, dt, gain=5.0, nonlin=np.tanh):
    """Feedforward delay taps + saturating nonlinearity (photonic nodes).
    gain pushes the nodes into the nonlinear regime (essential: without it,
    the leaky integral of a linear system is just proportional to total energy)."""
    N = len(delays)
    states = np.zeros((len(spikes), N))
    for i, d in enumerate(delays):
        shift = int(round(d / dt))
        delayed = np.zeros_like(spikes)
        if 0 < shift < len(spikes):
            delayed[shift:] = spikes[:-shift]
        elif shift <= 0:
            delayed[:] = spikes
        states[:, i] = nonlin(gain * weights[i] * delayed)
    return states


def integrate_states(states, dt, t, window=(-1e-12, 6e-12)):
    """Slow photodetector integrates node outputs over the spike window.
    Returns the per-node integrated signal S_i (the value held by the leaky
    integrator right after the spike train has passed)."""
    mask = (t >= window[0]) & (t <= window[1])
    return states[mask, :].sum(axis=0) * dt


def leaky_held_readout(S, readout_delay, tau_leak, sigma_ro, rng):
    """After the input stops, the integrator output decays as exp(-rd/tau_leak);
    the photodetector/readout noise floor sigma_ro is constant.
    v_i = S_i * exp(-rd/tau_leak) + N(0, sigma_ro)"""
    scale = np.exp(-readout_delay / tau_leak)
    noise = rng.normal(0, sigma_ro, S.shape)
    return S * scale + noise


def eval_features(feats, labels):
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    X = np.asarray(feats)
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.3, random_state=7, stratify=labels)
    # StandardScaler is essential: leaky-integrated features are ~1e-13,
    # and sklearn's default L2 regularization would crush them to chance level.
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    clf.fit(X_train, y_train)
    return clf.score(X_train, y_train), clf.score(X_test, y_test)


def reservoir_analysis(t, dt):
    rng = np.random.default_rng(2026)
    n_samples = 300
    n_taps = 40
    delay_values = np.linspace(0.1e-12, 2.0e-12, n_taps)
    weights = rng.normal(0, 2.0, n_taps)
    tau_leak = 1.0e-9            # 1 ns photodetector integration time constant
    sigma_ro_rel = 0.02          # readout noise floor, rel. to signal std

    # dataset: balanced, X[i] matches y[i]
    X = np.zeros((n_samples, len(t)))
    y = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        cls = i % 3
        y[i] = cls
        X[i] = generate_scene(t, cls, rng)

    print("\n[photonic reservoir with leaky slow readout]")
    print("  classes are energy- and centroid-matched -> slow power integration alone fails")
    print("  tau_leak = %.1f ns" % (tau_leak * 1e9))

    # precompute reservoir states and their slow integrals (cached for sweeps)
    S = np.zeros((n_samples, n_taps))
    example_states = {}
    for i in range(n_samples):
        st = reservoir_states(X[i], delay_values, weights, dt)
        S[i] = integrate_states(st, dt, t)
        if i < 3:
            example_states[i] = st
    sigma_ro = sigma_ro_rel * S.std()

    # --- baseline 1: direct slow power integration (no reservoir) ---
    # spikes are optical POWER: the slowest possible measurement is total energy
    direct_feats = X.sum(axis=1, keepdims=True) * dt
    _, direct_acc = eval_features(direct_feats, y)

    # --- baseline 2: fast sampling of reservoir states ---
    idx_fs = np.linspace(0, len(t) - 1, 32).astype(int)
    fast_feats = []
    for i in range(n_samples):
        st = reservoir_states(X[i], delay_values, weights, dt)
        fast_feats.append(st[idx_fs, :].flatten())
    _, fast_acc = eval_features(fast_feats, y)
    print("  baseline direct-energy accuracy: %.3f (expect ~0.33)" % direct_acc)
    print("  baseline fast-sampling accuracy: %.3f" % fast_acc)

    # --- reservoir + leaky slow readout at rd = 0 ---
    _, leaky_acc = eval_features(leaky_held_readout(S, 0.0, tau_leak, sigma_ro, rng), y)
    print("  reservoir + leaky readout accuracy: %.3f" % leaky_acc)

    # --- ablation: linear reservoir (no tanh) must fail under slow readout ---
    S_lin = np.zeros((n_samples, n_taps))
    for i in range(n_samples):
        st = reservoir_states(X[i], delay_values, weights, dt, nonlin=lambda u: u)
        S_lin[i] = integrate_states(st, dt, t)
    _, linear_acc = eval_features(
        leaky_held_readout(S_lin, 0.0, tau_leak, sigma_ro_rel * S_lin.std(), rng), y)
    print("  ablation: LINEAR reservoir + leaky readout: %.3f (expect ~0.33)" % linear_acc)

    # --- example figure ---
    fig, axes = plt.subplots(3, 2, figsize=(10, 9))
    for cls in range(3):
        spikes = X[cls]
        states = example_states[cls]
        ax = axes[cls, 0]
        ax.plot(t * 1e12, spikes / spikes.max())
        ax.set_title("class %d input (equal energy & centroid)" % cls)
        ax.set_xlim(0, 4)
        ax.set_xlabel("time (ps)")
        ax.grid(True, alpha=0.3)
        ax = axes[cls, 1]
        im = ax.imshow(states.T, aspect="auto",
                       extent=[t[0] * 1e12, t[-1] * 1e12, 0, n_taps],
                       cmap="viridis", origin="lower")
        ax.set_title("reservoir states (class %d)" % cls)
        ax.set_xlim(0, 4)
        ax.set_xlabel("time (ps)")
        ax.set_ylabel("delay tap index")
        fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_reservoir_examples.png"), dpi=150)
    print("  saved report_reservoir_examples.png")

    # --- sweep A: readout delay x tau_leak (uses cached S -> fast) ---
    readout_delays = np.logspace(-12, -8, 21)          # 1 ps to 10 ns
    tau_leaks = [0.2e-9, 1.0e-9, 5.0e-9]
    curves = {}
    for tl in tau_leaks:
        accs = [eval_features(leaky_held_readout(S, rd, tl, sigma_ro, rng), y)[1]
                for rd in readout_delays]
        curves[tl] = np.array(accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    for tl, accs in curves.items():
        ax.semilogx(readout_delays * 1e9, accs, "o-", ms=3,
                    label="tau_leak = %.1f ns" % (tl * 1e9))
    ax.axhline(direct_acc, color="k", ls=":", alpha=0.4, label="no reservoir (energy)")
    ax.set_xlabel("readout delay after spike train (ns)")
    ax.set_ylabel("test accuracy")
    ax.set_title("slow readout window: answer survives ~tau_leak")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_readout_delay.png"), dpi=150)
    print("  saved report_readout_delay.png")

    # --- sweep B: number of delay taps ---
    tap_counts = [5, 10, 20, 40, 80, 160]
    tap_accs = []
    for nt in tap_counts:
        dvs = np.linspace(0.1e-12, 2.0e-12, nt)
        wts = rng.normal(0, 2.0, nt)
        Sb = np.zeros((n_samples, nt))
        for i in range(n_samples):
            st = reservoir_states(X[i], dvs, wts, dt)
            Sb[i] = integrate_states(st, dt, t)
        _, a = eval_features(
            leaky_held_readout(Sb, 0.0, tau_leak, sigma_ro_rel * Sb.std(), rng), y)
        tap_accs.append(a)
    tap_accs = np.array(tap_accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(tap_counts, tap_accs, "o-", lw=1.5)
    ax.axhline(direct_acc, color="k", ls=":", alpha=0.4)
    ax.set_xlabel("number of delay taps (photonic nodes)")
    ax.set_ylabel("test accuracy")
    ax.set_title("accuracy vs reservoir size (leaky readout)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_tap_count.png"), dpi=150)
    print("  saved report_tap_count.png")

    # --- sweep C: timing jitter ---
    jitters = np.linspace(0, 0.20, 11)                  # absolute, ps
    jit_accs = []
    for jit in jitters:
        Sj = np.zeros((n_samples, n_taps))
        for i in range(n_samples):
            sj = generate_scene(t, y[i], rng, timing_jitter=jit)
            st = reservoir_states(sj, delay_values, weights, dt)
            Sj[i] = integrate_states(st, dt, t)
        _, a = eval_features(
            leaky_held_readout(Sj, 0.0, tau_leak, sigma_ro_rel * Sj.std(), rng), y)
        jit_accs.append(a)
    jit_accs = np.array(jit_accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(jitters * 1e12, jit_accs, "o-", lw=1.5)
    ax.axhline(direct_acc, color="k", ls=":", alpha=0.4)
    ax.set_xlabel("absolute timing jitter (ps)")
    ax.set_ylabel("test accuracy")
    ax.set_title("robustness to spike timing jitter")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_jitter.png"), dpi=150)
    print("  saved report_jitter.png")

    # --- sweep D: additive noise on input spikes ---
    noise_levels = np.logspace(-3, -0.2, 12)
    noise_accs = []
    for nl in noise_levels:
        Sn = np.zeros((n_samples, n_taps))
        for i in range(n_samples):
            sn = np.clip(X[i] + rng.normal(0, nl, len(t)), 0, None)
            st = reservoir_states(sn, delay_values, weights, dt)
            Sn[i] = integrate_states(st, dt, t)
        _, a = eval_features(
            leaky_held_readout(Sn, 0.0, tau_leak, sigma_ro_rel * Sn.std(), rng), y)
        noise_accs.append(a)
    noise_accs = np.array(noise_accs)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(noise_levels, noise_accs, "o-", lw=1.5)
    ax.axhline(direct_acc, color="k", ls=":", alpha=0.4)
    ax.set_xlabel("additive noise amplitude (rel. to peak)")
    ax.set_ylabel("test accuracy")
    ax.set_title("robustness to additive noise")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "report_noise.png"), dpi=150)
    print("  saved report_noise.png")

    return {"direct_acc": direct_acc, "fast_acc": fast_acc, "leaky_acc": leaky_acc,
            "linear_acc": linear_acc,
            "readout_delays": readout_delays, "tau_leaks": tau_leaks,
            "readout_curves": curves, "tap_counts": tap_counts, "tap_accs": tap_accs,
            "jitters": jitters, "jit_accs": jit_accs,
            "noise_levels": noise_levels, "noise_accs": noise_accs,
            "tau_leak": tau_leak, "n_taps": n_taps, "sigma_ro": sigma_ro}


def main():
    t0 = time.time()
    print("=" * 60)
    print("Comprehensive simulation v2")
    print("=" * 60)

    fdtd = fdtd_summary()
    grating = matched_filter_analysis()
    lidar = lidar_spike_analysis(grating)
    reservoir = reservoir_analysis(grating["t"], grating["dt"])

    np.savez(os.path.join(OUT, "comprehensive_summary.npz"),
             fdtd_platform_width_nm=fdtd["platform_width_nm"],
             fdtd_D_ps_per_nm=fdtd["D_ps_per_nm"],
             fdtd_delay_swing_ps=fdtd["delay_swing_ps"],
             phi2=grating["phi2"], chirp_rate_matched=grating["chirp_rate_matched"],
             gamma_vals=grating["gamma_vals"], widths=grating["widths"],
             lidar_pulse_fwhm=lidar["pulse_fwhm"], lidar_T_chirp=lidar["T_chirp"],
             direct_acc=reservoir["direct_acc"], fast_acc=reservoir["fast_acc"],
             leaky_acc=reservoir["leaky_acc"], linear_acc=reservoir["linear_acc"],
             readout_delays=reservoir["readout_delays"],
             tau_leaks=reservoir["tau_leaks"],
             tap_counts=reservoir["tap_counts"], tap_accs=reservoir["tap_accs"],
             jitters=reservoir["jitters"], jit_accs=reservoir["jit_accs"],
             noise_levels=reservoir["noise_levels"], noise_accs=reservoir["noise_accs"])

    # store curve dict separately (object arrays)
    np.savez(os.path.join(OUT, "comprehensive_readout_curves.npz"),
             **{"tl_%.0fns" % (tl * 1e9): accs
                for tl, accs in reservoir["readout_curves"].items()})

    print("\nfinished in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
