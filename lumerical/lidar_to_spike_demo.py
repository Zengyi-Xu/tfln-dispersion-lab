# -*- coding: utf-8 -*-
"""
Minimal LiDAR -> compressed pulse -> spike train demo.

A chirped waveform (matched to the measured grating dispersion) with multiple
point targets is reflected from the grating. The output is a train of compressed
pulses. Thresholding these pulses gives a spike train: one spike per target,
whose time encodes range and whose amplitude encodes reflectivity.

This is the bridge between the dispersion-lab work and the SNN direction.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

C0 = 299792458.0


def fwhm(t, I):
    I = I / I.max()
    above = t[I >= 0.5]
    return above.max() - above.min() if len(above) > 1 else np.nan


def main():
    # load measured chirped-grating FDTD data (reflection geometry)
    d = np.load(os.path.join(OUT, "chirp2d.npz"))
    f = d["f"]
    T = d["T"]
    tau_r = d["tau_r"]

    order = np.argsort(f)
    f, T, tau_r = f[order], T[order], tau_r[order]
    omega = 2 * np.pi * f
    R = np.clip(1.0 - T, 0, None)

    domega = np.diff(omega, prepend=omega[0])
    phi = np.cumsum(tau_r * domega)
    phi = np.unwrap(phi - phi[0])
    H = np.sqrt(R) * np.exp(1j * phi)

    omega0 = 2 * np.pi * C0 / 1.55e-6

    # grating quadratic phase coefficient -> matched chirp rate
    idx_center = np.argmin(np.abs(omega - omega0))
    i0, i1 = max(0, idx_center - 20), min(len(omega), idx_center + 20)
    p = np.polyfit(omega[i0:i1] - omega0, phi[i0:i1], 2)
    phi2_grating = 2 * p[0]
    chirp_rate = -1.0 / phi2_grating
    print("grating phi2 = %.3e s^2/rad" % phi2_grating)
    print("matched chirp rate = %.3e rad/s^2" % chirp_rate)

    # target scene: round-trip delays and reflectivities
    targets = [
        (0.5e-12, 1.0),    # 0.075 mm
        (1.5e-12, 0.6),    # 0.225 mm
        (3.0e-12, 0.4),    # 0.450 mm
    ]

    # chirp bandwidth spans grating bandwidth (~66 nm -> 8.25 THz)
    B = 2 * np.pi * 8.0e12
    T_chirp = B / chirp_rate
    print("chirp duration = %.3f ps" % (T_chirp * 1e12))

    # time grid
    N = 16384
    dt = 2e-15
    t = (np.arange(N) - N // 2) * dt
    Omega = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(N, dt))

    # grating response on baseband grid
    H_shift = np.interp(omega0 + Omega, omega, H, left=0, right=0)

    # build received signal: sum of delayed, attenuated chirps
    E_rx = np.zeros_like(t, dtype=complex)
    for delay, amp in targets:
        E_rx += amp * np.exp(-(t - delay)**2 / (2 * (T_chirp / 2.5)**2)) \
                 * np.exp(1j * 0.5 * chirp_rate * (t - delay)**2)

    # matched filtering: grating H is the matched filter for this chirp
    E_rx_fft = np.fft.fft(E_rx)
    E_comp_fft = E_rx_fft * np.fft.ifftshift(H_shift.conj())
    E_comp = np.fft.ifft(E_comp_fft)
    I_comp = np.abs(E_comp)**2

    t_shift = np.fft.fftshift(t)
    I_shift = np.fft.fftshift(I_comp)

    # spike generation: threshold
    threshold = 0.2 * I_shift.max()
    spikes = np.where(I_shift > threshold, I_shift, 0.0)

    print("\ntarget delays / ranges:")
    for delay, amp in targets:
        print("  delay %.3f ps -> range %.3f mm, reflectivity %.2f" % (delay * 1e12, delay * C0 / 2 * 1e3, amp))
    comp_width = fwhm(t_shift, I_shift)
    print("compressed pulse FWHM: %.3f ps" % (comp_width * 1e12))
    print("compression ratio: %.1f" % (T_chirp / comp_width))

    # plot
    fig, axes = plt.subplots(3, 1, figsize=(10, 10))

    ax = axes[0]
    I_rx = np.abs(E_rx)**2
    ax.plot(t_shift * 1e12, I_rx / I_rx.max())
    ax.set_xlim(-10, 15)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("normalized received power")
    ax.set_title("received chirped echoes (3 targets, overlapped)")
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(t_shift * 1e12, I_shift / I_shift.max())
    ax.set_xlim(-5, 10)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("normalized compressed intensity")
    ax.set_title("after grating matched-filter compression")
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    ax.stem(t_shift * 1e12, spikes / spikes.max(), basefmt=" ")
    ax.set_xlim(-5, 10)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("spike amplitude")
    ax.set_title("thresholded spike train (input to SNN)")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "lidar_to_spike_demo.png"), dpi=150)
    print("saved results/lidar_to_spike_demo.png", flush=True)

    np.savez(os.path.join(OUT, "lidar_to_spike_demo.npz"),
             t=t_shift, I_rx=I_rx / I_rx.max(),
             I_comp=I_shift / I_shift.max(),
             spikes=spikes / spikes.max(),
             targets=np.array(targets))


if __name__ == "__main__":
    main()
