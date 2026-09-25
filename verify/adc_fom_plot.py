"""ADC energy boundary from Murmann ADC Performance Survey 1997-2026.
Data: https://github.com/bmurmann/ADC-survey (xls/ADCsurvey_rev20260801.xlsx)
Run: python verify/adc_fom_plot.py  ->  results/verify/adc_fom_boundary.png + stats
"""
import openpyxl, numpy as np, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

XLSX = sys.argv[1] if len(sys.argv) > 1 else '.tmp/adcsurvey/ADCsurvey_latest.xlsx'

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
fs, fomw, sndr, pfs = [], [], [], []
for name in ['ISSCC', 'VLSI']:
    for r in wb[name].iter_rows(values_only=True, min_row=2):
        try:
            f = float(r[27]); w = float(r[31])
            s = r[18] if r[18] not in (None, '') else r[16]; s = float(s)
            p = float(r[29]) if r[29] not in (None, '') else np.nan
            if f > 0 and w > 0:
                fs.append(f); fomw.append(w); sndr.append(s); pfs.append(p)
        except (TypeError, ValueError):
            continue
fs = np.array(fs); fomw = np.array(fomw); sndr = np.array(sndr); pfs = np.array(pfs)
enob = (sndr - 1.76) / 6.02

edges = np.logspace(4, 11, 15); cen = np.sqrt(edges[:-1] * edges[1:]); env = []
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (fs >= lo) & (fs < hi)
    env.append(np.nanmin(fomw[m]) if m.any() else np.nan)
env = np.array(env)

m5 = fs >= 5e9
m58 = m5 & (enob >= 8)
print(f'N={len(fs)}')
print(f'fs>=5GS/s: N={m5.sum()}, FoMW median={np.nanmedian(fomw[m5]):.0f} fJ/step, '
      f'ENOB median={np.nanmedian(enob[m5]):.1f}, P/fs median={np.nanmedian(pfs[m5])*1e3:.0f} fJ/sample')
print(f'fs>=5GS/s & ENOB>=8: N={m58.sum()}, FoMW median={np.nanmedian(fomw[m58]):.0f} fJ/step, '
      f'P/fs median={np.nanmedian(pfs[m58])*1e3:.0f} fJ/sample')

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
a = ax[0]
a.loglog(fs, fomw, '.', ms=2.5, c='0.6', label=f'ISSCC+VLSI 1997-2026 (N={len(fs)})')
ok = ~np.isnan(env)
a.loglog(cen[ok], env[ok], 'r-o', ms=4, label='energy frontier (min/decade)')
a.axvspan(5e9, 3e10, color='orange', alpha=0.15, label='target band: 5-30 GS/s')
a.set_xlabel('Nyquist sample rate $f_s$ [Hz]'); a.set_ylabel('Walden FoM [fJ/conv-step]')
a.legend(); a.set_title('ADC energy vs speed (Murmann survey)'); a.grid(True, which='both', alpha=0.3)
b = ax[1]
b.loglog(fs, pfs * 1e3, '.', ms=2.5, c='0.6', label='P/$f_s$ [fJ/sample]')
b.axvspan(5e9, 3e10, color='orange', alpha=0.15)
b.set_xlabel('Nyquist sample rate $f_s$ [Hz]'); b.set_ylabel('Energy per sample [fJ]')
b.set_title('Energy per conversion'); b.grid(True, which='both', alpha=0.3)
plt.tight_layout()
os.makedirs('results/verify', exist_ok=True)
plt.savefig('results/verify/adc_fom_boundary.png', dpi=150)
print('saved results/verify/adc_fom_boundary.png')
