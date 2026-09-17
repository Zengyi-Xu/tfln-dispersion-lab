"""
01_uniform_grating_gd.py

目的：验证均匀 Bragg 光栅的群延迟谱——带边鼓包 = 局部大色散，
带外平坦 = 背景群延迟。（活笔记 lab-note.md §3）

物理：耦合模理论（CMT）解析反射系数
    r(δ) = -iκ sinh(γL) / (γ cosh(γL) - iδ sinh(γL)),  γ = sqrt(κ² - δ²)
    δ = 2π n_eff (1/λ - 1/λ_B)
群延迟 τ(λ) = -d(arg r)/dω，ω = 2πc/λ，用数值微分（先 unwrap 相位）。

运行：python 01_uniform_grating_gd.py
输出：../results/<日期>-uniform-grating-gd.png
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import date

# ---- 参数（典型 TFLN 波导光栅量级，可随意改） ----
n_eff = 2.2          # 有效相折射率
lam_b = 1550e-9      # 布拉格波长 [m]
kappa = 5e4          # 耦合系数 [1/m]  (~500 /cm)
L = 2.5e-3           # 光栅长度 [m]    (2.5 mm, 对标 Yu 2022)

c = 299792458.0

# ---- 波长扫描 ----
# 带隙半宽 Δλ = λ_B² κ / (2π n_eff)。取 κ=5e4/m 时约 ±8.7 nm，
# 所以窗口必须盖过带边（±12 nm），否则只见带内平台、看不到鼓包。
lam = np.linspace(lam_b - 12e-9, lam_b + 12e-9, 40001)
delta = 2 * np.pi * n_eff * (1.0 / lam - 1.0 / lam_b)

gam = np.sqrt(kappa**2 - delta**2 + 0j)          # γ = sqrt(κ² - δ²)，负则自动为虚数
num = -1j * kappa * np.sinh(gam * L)
den = gam * np.cosh(gam * L) - 1j * delta * np.sinh(gam * L)
r = num / den

R = np.abs(r)**2
phi = np.unwrap(np.angle(r))

omega = 2 * np.pi * c / lam
tau = -np.gradient(phi, omega)                   # τ = -dφ/dω  [s]

# ---- 画图 ----
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
dlnm = (lam - lam_b) * 1e9

ax[0].plot(dlnm, R)
ax[0].set_xlabel('Δλ from Bragg (nm)')
ax[0].set_ylabel('Reflectivity |r|²')
ax[0].set_title(f'Uniform grating: R (κ={kappa/100:.0f}/cm, L={L*1e3:.1f} mm)')
ax[0].grid(alpha=0.3)

# 带边位置：|δ| = κ → Δλ = ±λ_B²κ/(2π n_eff)
edge_nm = lam_b**2 * kappa / (2 * np.pi * n_eff) * 1e9
for e in (-edge_nm, edge_nm):
    for a in ax:
        a.axvline(e, color='r', ls='--', alpha=0.5)
ax[1].plot(dlnm, tau * 1e12)
ax[1].set_xlabel('Δλ from Bragg (nm)')
ax[1].set_ylabel('Group delay τ (ps)')
ax[1].set_title('Band-edge bumps = local dispersion (red dashed: |δ|=κ)')
ax[1].grid(alpha=0.3)

fig.tight_layout()
out = Path(__file__).parent.parent / 'results' / f'{date.today()}-uniform-grating-gd.png'
out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=150)
print(f'saved: {out}')

# ---- 数量级自检 ----
bandwidth = R > 0.5
if bandwidth.any():
    bw_nm = (lam[bandwidth].max() - lam[bandwidth].min()) * 1e9
    print(f'反射带宽(FWHM近似): {bw_nm:.3f} nm')
edge = np.argmax(tau)
print(f'带边最大群延迟: {tau.max()*1e12:.2f} ps @ Δλ = {(lam[edge]-lam_b)*1e9:.3f} nm')
