"""Newsletter figures from saved development results; no training or network calls."""
import csv
import json
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BG, INK, GRID = '#fbf8f2', '#292b2c', '#e5e0d7'
BLUE, ORANGE = '#0072B2', '#D55E00'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 14,
                     'text.color': INK, 'axes.labelcolor': INK,
                     'xtick.color': INK, 'ytick.color': INK,
                     'axes.facecolor': BG, 'figure.facecolor': BG,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.spines.bottom': False})

def clean(ax):
    ax.set_axisbelow(True)
    ax.grid(axis='x', color=GRID, linewidth=.8)
    ax.tick_params(length=0)

def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=190, facecolor=BG)
    fig.savefig(OUT / f'{name}.svg', facecolor=BG)
    plt.close(fig)

rows = list(csv.DictReader((ROOT / 'research/side-notes/explore-20261011/units.csv').open()))
models = ['OLMo-2-1B', 'Llama-3.2-1B', 'Qwen2.5-1.5B',
          'OLMo-2-7B', 'Llama-3.1-8B', 'Qwen2.5-7B']
expected = [(45.1, 28.8), (59.3, 57.1), (71.9, 73.9),
            (44.1, 50.3), (60.7, 59.2), (78.1, 68.9)]
data = {'source': 'research/side-notes/explore-20261011/units.csv', 'main': []}
fig, ax = plt.subplots(figsize=(10.5, 7.3))
fig.subplots_adjust(left=.23, right=.94, top=.80, bottom=.24)
for i, (model, check) in enumerate(zip(models, expected)):
    y = 5-i
    for j, (recipe, color, offset) in enumerate([('Constant', BLUE, .17), ('Scheduled', ORANGE, -.17)]):
        r = sorted([r for r in rows if r['model'] == model and r['recipe'] == recipe], key=lambda r: r['seed'])
        assert len(r) == 3, (model, recipe, len(r))
        values = [float(r['E_pp']) for r in r]
        m = mean(values)
        assert round(m, 1) == check[j], (model, recipe, m)
        ax.barh(y+offset, m, height=.27, color=color, alpha=.86)
        ax.scatter(values, [y+offset+v for v in (-.045, 0, .045)], s=30,
                   color=INK, edgecolor=BG, linewidth=.9, zorder=4)
        ax.text(90, y+offset, f'{m:.1f}', va='center', ha='right', fontsize=13, weight='bold')
        data['main'].append({'model': model, 'recipe': recipe, 'seeds': [int(r['seed']) for r in r],
                             'erosion_pp': values, 'mean_pp': m})
ax.set_yticks(range(5, -1, -1), models)
ax.set_ylim(-.55, 5.55)
ax.set_xlim(0, 94)
ax.set_xticks([0, 20, 40, 60, 80])
ax.set_xlabel('Rise in Unsafe-labelled answers (percentage points)', labelpad=13)
ax.axhline(2.5, color=GRID, linewidth=1.4)
clean(ax)
fig.text(.055, .95, 'Same recipe change, different results', fontsize=22, weight='bold')
fig.text(.055, .90, 'Six chat models, the same Dolly data; Qwen3Guard safety labels', fontsize=13)
fig.legend(handles=[Patch(color=BLUE, label='Constant'), Patch(color=ORANGE, label='Scheduled')],
           loc='upper left', bbox_to_anchor=(.045, .872), ncol=2, frameon=False, fontsize=13)
fig.text(.055, .075, 'Bars: three-run means. Dots: individual training runs.', fontsize=12)
fig.text(.055, .035, 'Development evidence. The larger-model replication was inconclusive.', fontsize=12)
save(fig, '01-six-models')

pilot = json.loads((ROOT / 'research/side-notes/causal-study-20261012/analysis.json').read_text())
assert pilot['status'] == 'complete'
units = {}
for u in pilot['units']:
    p = u['planned']
    units[(p['model'], p['arm'])] = u['outcomes']
data['pilot'] = []
fig, axes = plt.subplots(1, 2, figsize=(12, 6.7))
fig.subplots_adjust(left=.08, right=.96, top=.73, bottom=.24, wspace=.26)
for model, label, color in [('olmo1b', 'OLMo-1B', BLUE), ('olmo7b', 'OLMo-7B', ORANGE)]:
    outcomes = [units[(model, arm)] for arm in ('A', 'C', 'D')]
    unsafe = [o['unsafe']['unsafe_percent'] for o in outcomes]
    refusal = [o['overrefusal']['refusal_rate']*100 for o in outcomes]
    data['pilot'].append({'model': model, 'seed': 1121, 'unsafe_percent': unsafe,
                          'benign_refusal_percent': refusal})
    for ax, values in zip(axes, (unsafe, refusal)):
        ax.plot(range(3), values, color=color, linewidth=2.7, marker='o', markersize=8, label=label)
        for x, v in enumerate(values):
            ax.annotate(f'{v:.1f}', (x, v), xytext=(0, 10),
                        textcoords='offset points', ha='center', color=color, weight='bold', fontsize=13)
for ax, ylim, title in zip(axes, [(0, 65), (0, 25)], ['Unsafe-labelled answers (%)', 'Harmless questions refused (%)']):
    ax.set_title(title, fontsize=15, pad=15)
    ax.set_ylim(*ylim)
    ax.set_xlim(-.25, 2.25)
    ax.set_xticks(range(3), ['Constant\nresponse weight', 'Schedule\nsame weighting', 'Schedule +\ntoken weighting'], fontsize=11)
    ax.grid(axis='y', color=GRID)
    ax.tick_params(length=0)
fig.text(.045, .945, 'Taking the recipe apart', fontsize=23, weight='bold')
fig.text(.045, .885, 'One fresh training seed, two fixed OLMo checkpoints, three controlled recipes', fontsize=13)
fig.legend(*axes[0].get_legend_handles_labels(), loc='upper left', bbox_to_anchor=(.037, .843),
           ncol=2, frameon=False, fontsize=13)
fig.text(.045, .095, '600 safety answers and 100 harmless answers per run. Development evidence.', fontsize=12)
fig.text(.045, .045, 'Schedule timing and average learning rate remain bundled; no population intervals.', fontsize=12)
save(fig, '02-component-pilot')

fiction = json.loads((ROOT / 'research/side-fiction/results/fiction-results.json').read_text())
arms = [('F-dark', 'Dark fiction', '#CC79A7'), ('F-light', 'Light fiction', '#56B4E9'), ('D', 'Dolly', '#6e7681')]
data['fiction'] = []
fig, axes = plt.subplots(1, 2, figsize=(12, 6.2))
fig.subplots_adjust(left=.155, right=.96, top=.70, bottom=.25, wspace=.40)
for y, (key, label, color) in enumerate(arms):
    arm = fiction['arms'][key]
    assert arm['n_seeds'] == 3
    e, r = arm['mean_E_own_pp'], arm['mean_overrefusal_rate']*100
    data['fiction'].append({'arm': key, 'mean_erosion_pp': e, 'mean_benign_refusal_percent': r, 'seeds': arm['seeds']})
    for ax, v in zip(axes, (e, r)):
        ax.barh(2-y, v, height=.48, color=color)
        ax.text(v+.8, 2-y, f'{v:.1f}', va='center', weight='bold', fontsize=14)
for ax in axes:
    ax.set_yticks([2, 1, 0], ['Dark fiction', 'Light fiction', 'Dolly'], fontsize=13)
    ax.set_ylim(-.5, 2.5)
    clean(ax)
axes[0].set_xlim(0, 53)
axes[0].set_title('Safety erosion', fontsize=16, pad=15)
axes[0].set_xlabel('Rise in Unsafe share (pp)', fontsize=12, labelpad=12)
axes[1].set_xlim(0, 38)
axes[1].set_title('Harmless questions refused', fontsize=16, pad=15)
axes[1].set_xlabel('Refusal rate (%)', fontsize=12, labelpad=12)
axes[1].axvline(17, color=INK, linestyle=(0, (4, 3)), linewidth=1.3)
axes[1].text(17.8, 2.38, 'Untuned: 17%', fontsize=11, ha='left')
fig.text(.04, .94, 'Fiction eroded less, but refused more', fontsize=23, weight='bold')
fig.text(.04, .875, 'OLMo-1B, Constant recipe; three-run means for each training dataset', fontsize=13)
fig.text(.04, .105, 'Qwen3Guard labels on development tests; both fiction arms also lost task accuracy.', fontsize=12)
fig.text(.04, .052, 'Dark-light differences fit wide pre-set margins. This does not establish equality.', fontsize=12)
save(fig, '03-fiction-tradeoff')
(OUT / 'figure-data.json').write_text(json.dumps(data, indent=2)+'\n')
print('Wrote three PNG/SVG figures and the source-data ledger.')
