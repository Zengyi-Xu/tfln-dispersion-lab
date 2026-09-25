# -*- coding: utf-8 -*-
"""
Minimal time-lens / matched-filter demo using the real chirped-grating dispersion from FDTD.

A broadband pulse with a controllable spectral chirp is reflected from the grating.
The grating's measured reflection group delay tau_r(wl) gives the spectral phase.
Scanning the input chirp finds the value that best compresses the pulse.

A TFLN phase modulator (time lens) in the time domain applies a quadratic phase
exp(i C t^2/2); under the stationary-phase approximation this is equivalent to
adding a spectral chirp proportional to -1/C. Thus this scan directly shows what
a time lens can do.
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

    # reflection phase from tau_r = dphi/domega
    domega = np.diff(omega, prepend=omega[0])
    phi = np.cumsum(tau_r * domega)
    phi = np.unwrap(phi - phi[0])
    H = np.sqrt(R) * np.exp(1j * phi)

    omega0 = 2 * np.pi * C0 / 1.55e-6

    # time grid and baseband frequency grid
    N = 16384
    dt = 2e-15
    t_shift = (np.arange(N) - N // 2) * dt
    Omega_shift = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(N, dt))

    # grating response on the symmetric baseband grid
    H_shift = np.interp(omega0 + Omega_shift, omega, H, left=0, right=0)
    H_fft = np.fft.ifftshift(H_shift)

    # estimate grating quadratic phase coefficient (GVD) around center
    idx_center = np.argmin(np.abs(omega - omega0))
    i0, i1 = max(0, idx_center - 20), min(len(omega), idx_center + 20)
    p = np.polyfit(omega[i0:i1] - omega0, phi[i0:i1], 2)
    phi2_grating = 2 * p[0]
    print("grating quadratic phase coeff phi2 = %.3e s^2/rad" % phi2_grating)

    # input spectrum: Gaussian covering the grating bandwidth (~30 nm half-width)
    sigma_w = 2 * np.pi * C0 * 30e-9 / (1.55e-6)**2
    E_in_shift = np.exp(-Omega_shift**2 / (2 * sigma_w**2))
    E_in_fft = np.fft.ifftshift(E_in_shift)

    # transform-limited reference (no grating)
    E_tl_fft = np.fft.ifft(E_in_fft)
    I_tl = np.abs(np.fft.fftshift(E_tl_fft))**2

    # scan input spectral chirp gamma
    gamma_vals = np.linspace(-2 * phi2_grating, 0.5 * phi2_grating, 60)
    widths = []
    for gamma in gamma_vals:
        phase_shift = 0.5 * gamma * Omega_shift**2
        E_out_fft = np.fft.ifft(E_in_fft * np.fft.ifftshift(np.exp(1j * phase_shift)) * H_fft)
        I_out = np.abs(np.fft.fftshift(E_out_fft))**2
        widths.append(fwhm(t_shift, I_out))
    widths = np.array(widths)
    idx_best = np.nanargmin(widths)
    gamma_best = gamma_vals[idx_best]

    # outputs for plotting
    E_flat_fft = np.fft.ifft(E_in_fft * H_fft)
    I_flat = np.abs(np.fft.fftshift(E_flat_fft))**2

    phase_best_shift = 0.5 * gamma_best * Omega_shift**2
    E_best_fft = np.fft.ifft(E_in_fft * np.fft.ifftshift(np.exp(1j * phase_best_shift)) * H_fft)
    I_best = np.abs(np.fft.fftshift(E_best_fft))**2

    print("transform-limited FWHM: %.3f ps" % (fwhm(t_shift, I_tl) * 1e12))
    print("flat-phase + grating FWHM: %.3f ps" % (fwhm(t_shift, I_flat) * 1e12))
    print("best chirp gamma: %.3e s^2/rad" % gamma_best)
    print("matched FWHM: %.3f ps" % (widths[idx_best] * 1e12))

    if abs(gamma_best) > 1e-30:
        C_equiv = -1.0 / gamma_best
        print("equivalent time-lens C: %.3e rad/s^2" % C_equiv)

    # plot
    fig, axes = plt.subplots(2, 1, figsize=(9, 8))

    ax = axes[0]
    ax.plot(t_shift * 1e12, I_tl / I_tl.max(), label="transform-limited input", lw=1.5)
    ax.plot(t_shift * 1e12, I_flat / I_flat.max(), label="flat-phase + grating (spread)", lw=1.5)
    ax.plot(t_shift * 1e12, I_best / I_best.max(), label="matched chirp + grating (compressed)", lw=1.5)
    ax.set_xlim(-10, 10)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("normalized intensity")
    ax.set_title("matched-filter compression using measured grating dispersion")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(gamma_vals / phi2_grating, widths * 1e12, "o-", lw=1.5, markersize=3)
    ax.axvline(gamma_best / phi2_grating, color="r", ls="--", label="best chirp")
    ax.axvline(-phi2_grating / phi2_grating, color="k", ls=":", alpha=0.5, label="ideal matched chirp")
    ax.set_xlabel("input chirp $\\gamma / \\phi_2^{\\mathrm{grating}}$")
    ax.set_ylabel("output FWHM (ps)")
    ax.set_title("scan of input chirp (equivalent to time-lens strength)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "time_lens_demo.png"), dpi=150)
    print("saved results/time_lens_demo.png", flush=True)

    np.savez(os.path.join(OUT, "time_lens_demo.npz"),
             t=t_shift, I_tl=I_tl / I_tl.max(), I_flat=I_flat / I_flat.max(),
             I_best=I_best / I_best.max(),
             gamma_vals=gamma_vals, widths=widths, gamma_best=gamma_best,
             phi2_grating=phi2_grating)


if __name__ == "__main__":
    main()
