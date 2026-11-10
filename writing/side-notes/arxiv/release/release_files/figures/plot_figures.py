#!/usr/bin/env python3
"""Draw Figures 1 and 2 of the note from the released figure data.

    python3 figures/plot_figures.py [--out DIR]

Reads figures/fig1-data.csv and figures/fig2-data.csv (next to this script) and writes
fig1-erosion.pdf/.png and fig2-openings.pdf/.png into DIR (default: next to this script).
Needs matplotlib. The drawing code is the note's own (its make_figures.py, "plot" step); only the
file locations, the colour rule (from the recipe name) and the bar order (from the CSV) are
read from the released files instead of the note's extraction tables.
"""
import argparse
import csv
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FIG1_CSV = os.path.join(HERE, 'fig1-data.csv')
FIG2_CSV = os.path.join(HERE, 'fig2-data.csv')
OUT = HERE
OPENINGS = [('refusal', 'REFUSAL-OPENING'), ('caveat', 'CAVEAT-OPENING'), ('direct', 'DIRECT')]


# ----------------------------------------------------------------------------- plot
# dataviz reference palette, light mode, on the white page surface.
SURFACE = '#ffffff'
INK = '#0b0b0b'        # primary ink
INK2 = '#52514e'       # secondary ink
GRID = '#e1e0d9'       # hairline gridline
AXIS = '#c3c2b7'       # baseline / axis
# Figure 1: categorical slots 1-2. validate_palette.js --pairs all, surface
# #ffffff: all checks pass (CVD dE 24.7, normal-vision dE 33.6, contrast >= 3:1).
BLUE, ORANGE = '#2a78d6', '#eb6834'
# Figure 2: slots 1-3 for the opening (adjacent CVD dE 9.2, normal 27.6; aqua is
# 2.82:1, so the relief rule applies: the legend and fig2-data.csv as the table
# view). Unsafe is a darker step of the same hue: blue ramp step 650 (#104281),
# and orange and aqua scaled in linear light by the same factor (0.2999), which
# holds the hue. Each [hue, darker step] passes the --ordinal checks, and the
# full stack order passes adjacent CVD (worst dE 19.0) and normal vision (19.5).
OPEN_COLOUR = {
    'refusal': ('#2a78d6', '#104281'),
    'caveat': ('#eb6834', '#89391a'),
    'direct': ('#1baf7a', '#0b6444'),
}


def _setup():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'mathtext.fontset': 'custom',
        'mathtext.rm': 'Arial',
        'mathtext.it': 'Arial:italic',
        'mathtext.bf': 'Arial:bold',
        'pdf.fonttype': 42,
        'font.size': 7,
        'axes.edgecolor': AXIS,
        'axes.linewidth': 0.6,
        'axes.labelcolor': INK2,
        'xtick.color': AXIS,
        'xtick.labelcolor': INK2,
        'xtick.major.width': 0.6,
        'xtick.major.size': 2.5,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'ytick.labelcolor': INK,
        'figure.facecolor': SURFACE,
        'axes.facecolor': SURFACE,
        'savefig.facecolor': SURFACE,
    })
    return plt


def _save(fig, stem):
    fig.savefig(os.path.join(OUT, stem + '.pdf'), metadata={'CreationDate': None})
    fig.savefig(os.path.join(OUT, stem + '.png'), dpi=250)


def _read(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _row_positions(models, gap):
    ys, y, prev, seps = [], 0.0, None, []
    for m in models:
        if prev is not None and m != prev:
            seps.append(y - 0.5 + gap / 2)
            y += gap
        ys.append(y)
        y += 1
        prev = m
    return ys, seps


def _row_text(fig, ax, x_in, y, text, ha, **kw):
    """Row label at x_in inches from the figure's left edge and data row y.
    Baseline alignment with a fixed drop of half the cap height (7 pt Arial:
    about 2.5 pt) puts every label's capitals on the row centre, with or
    without a superscript."""
    from matplotlib.transforms import ScaledTranslation, blended_transform_factory
    W = fig.get_figwidth()
    tr = (blended_transform_factory(fig.transFigure, ax.transData)
          + ScaledTranslation(0, -2.5 / 72, fig.dpi_scale_trans))
    fig.text(x_in / W, y, text, transform=tr, ha=ha, va='baseline', fontsize=7, **kw)


# Figure 1 display order. Within a model, the Constant recipe and its variant
# come first, then the Scheduled recipe and its variants, so each colour forms
# one block. Tables 2 and 3 of the note use the same order.
FIG1_ORDER = [
    ('OLMo-2-1B', 'Constant'), ('OLMo-2-1B', 'Constant, token-mean'),
    ('OLMo-2-1B', 'Scheduled'), ('OLMo-2-1B', 'Scheduled, half LR'),
    ('OLMo-2-1B', 'Scheduled, rank 16'),
    ('Qwen2.5-1.5B', 'Constant'), ('Qwen2.5-1.5B', 'Constant, rank 16'),
    ('Qwen2.5-7B', 'Constant'),
    ('Llama-3.2-1B', 'Constant'), ('Llama-3.2-1B', 'Scheduled'),
    ('Llama-3.2-1B', 'Scheduled, half LR'),
]


def _stack(values, min_gap, step):
    """Vertical offsets (in rows) for sorted values. Seeds closer than min_gap
    form a cluster; a cluster of k seeds is spread evenly about the row line,
    `step` rows apart. A seed with no close neighbour stays on the line."""
    clusters, cur = [], [0]
    for i in range(1, len(values)):
        if values[i] - values[cur[-1]] < min_gap:
            cur.append(i)
        else:
            clusters.append(cur)
            cur = [i]
    clusters.append(cur)
    offs = [0.0] * len(values)
    for c in clusters:
        for j, i in enumerate(c):
            offs[i] = (j - (len(c) - 1) / 2) * step
    return offs


def plot_fig1(plt):
    from matplotlib.lines import Line2D
    from matplotlib.transforms import blended_transform_factory
    rows = _read(FIG1_CSV)
    # Colour: the Constant recipe and its variants in blue, the Scheduled recipe and its variants
    # in orange (the note's make_figures.py keeps this as a 'base' field of each row).
    base = {(r['model'], r['recipe']): 'Constant' if r['recipe'].startswith('Constant') else 'Scheduled'
            for r in rows}
    if sorted(FIG1_ORDER) != sorted(base):
        raise SystemExit('FIG1_ORDER and fig1-data.csv name different rows')
    data = {k: {'E': [], 'E_HB': [], 'E_mean': None, 'E_HB_mean': None, 'bar': [None, None]}
            for k in FIG1_ORDER}
    for r in rows:
        d = data[(r['model'], r['recipe'])]
        q, v = r['quantity'], r['value_pp']
        if q == 'seed':
            d[r['panel']].append((int(r['seed']), float(v)))
        elif q == 'mean':
            d[r['panel'] + '_mean'] = float(v)
        elif q == 'minus_2se':
            d['bar'][0] = float(v)
        elif q == 'plus_2se':
            d['bar'][1] = float(v)

    # A header line per model, then one line per recipe; 0.35 of a line between models.
    layout, y, prev = [], 0.0, None
    for m, rec in FIG1_ORDER:
        if m != prev:
            if prev is not None:
                y += 0.35
            layout.append((m, None, y))
            y += 1.0
            prev = m
        layout.append((m, rec, y))
        y += 1.0
    n_lines = y

    W, row_h = 6.75, 0.148                      # inches
    lab_w, gap_w, right = 1.22, 0.30, 0.06
    key_h, title_h, bottom = 0.26, 0.20, 0.26
    pw = (W - lab_w - gap_w - right) / 2
    ph = n_lines * row_h
    H = key_h + title_h + ph + bottom
    fig = plt.figure(figsize=(W, H))
    ax1 = fig.add_axes([lab_w / W, bottom / H, pw / W, ph / H])
    ax2 = fig.add_axes([(lab_w + pw + gap_w) / W, bottom / H, pw / W, ph / H], sharey=ax1)
    ms, x_max = 4.8, 90.0                       # marker size (pt), axis end (pp)
    min_gap = 0.6 * ms / (pw * 72 / x_max)      # stack seeds that overlap by more than 40%
    for ax, panel, title in ((ax1, 'E', 'Qwen3Guard erosion $E$ (pp)'),
                             (ax2, 'E_HB', r'HarmBench erosion $E_{\mathrm{HB}}$ (pp)')):
        ax.set_xlim(0, x_max)
        ax.set_xticks([0, 20, 40, 60, 80])
        ax.grid(axis='x', color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis='y', length=0, labelleft=False)
        ax.set_title(title, loc='left', fontsize=8, color=INK, pad=4)
        for m, rec, yy in layout:
            if rec is None:
                continue
            d = data[(m, rec)]
            colour = BLUE if base[(m, rec)] == 'Constant' else ORANGE
            seeds = sorted(v for _, v in d[panel])
            if not seeds:
                ax.text(1.0, yy, 'not judged', ha='left', va='center', fontsize=6.5,
                        color=INK2, style='italic')
                continue
            if panel == 'E' and len(seeds) == 1 and None not in d['bar']:
                lo, hi = d['bar']
                ax.hlines(yy, lo, hi, color=colour, linewidth=1.0, zorder=2)
                ax.vlines([lo, hi], yy - 0.16, yy + 0.16, color=colour, linewidth=1.0, zorder=2)
            for v, off in zip(seeds, _stack(seeds, min_gap, 0.5)):
                ax.plot(v, yy + off, 'o', markersize=ms, markerfacecolor=colour,
                        markeredgecolor=SURFACE, markeredgewidth=0.6, zorder=3)
            mean = d[panel + '_mean']
            if mean is not None and len(seeds) > 1:     # on top: a stacked pair would hide it
                ax.vlines(mean, yy - 0.4, yy + 0.4, color=INK, linewidth=1.2, zorder=4)
    ax1.set_ylim(n_lines - 0.5, -0.5)

    # Model names on their header lines, recipe names next to the axis, and a
    # rule between models across the whole width.
    tr = blended_transform_factory(fig.transFigure, ax1.transData)
    for m, rec, yy in layout:
        if rec is None:
            if yy > 0:
                fig.add_artist(Line2D([0, 1], [yy - 0.68, yy - 0.68], transform=tr,
                                      color=AXIS, linewidth=0.5))
            fig.text(0.02 / W, yy, m, transform=tr, ha='left', va='center', fontsize=7.5,
                     fontweight='bold', color=INK)
        else:
            fig.text((lab_w - 0.08) / W, yy, rec, transform=tr, ha='right', va='center',
                     fontsize=7.5, color=INK)

    one_seed = ax1.errorbar([-50], [0], xerr=[[6], [6]], fmt='o', color=INK2, markersize=ms,
                            markeredgecolor=SURFACE, markeredgewidth=0.6, elinewidth=1.0,
                            capsize=2.2, capthick=1.0)   # legend glyph only; outside the axis
    handles = [
        Line2D([], [], linestyle='none', marker='o', markersize=ms, markerfacecolor=BLUE,
               markeredgecolor=SURFACE, markeredgewidth=0.6),
        Line2D([], [], linestyle='none', marker='o', markersize=ms, markerfacecolor=ORANGE,
               markeredgecolor=SURFACE, markeredgewidth=0.6),
        Line2D([], [], linestyle='none', marker='|', markersize=8, markeredgewidth=1.3, color=INK),
        one_seed,
    ]
    labels = ['Constant recipe and variants', 'Scheduled recipe and variants',
              'Mean of the seeds', r'One seed: $E \pm 2$ SE']
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.0), ncol=4,
               frameon=False, fontsize=7.5, handlelength=1.6, handletextpad=0.45,
               columnspacing=1.8, borderaxespad=0.2, labelcolor=INK2)
    _save(fig, 'fig1-erosion')
    plt.close(fig)


def plot_fig2(plt):
    from matplotlib.patches import Rectangle
    rows = _read(FIG2_CSV)
    units = []
    order = []
    for r in rows:                       # bars in the order of the CSV
        if (r['model'], r['state'], r['unit']) not in order:
            order.append((r['model'], r['state'], r['unit']))
    for model, state, unit in order:
        counts = {(r['opening'], r['qwen3guard']): int(r['count']) for r in rows if r['unit'] == unit}
        n = {int(r['n']) for r in rows if r['unit'] == unit}
        assert len(n) == 1
        units.append((model, state, counts, n.pop()))

    W, H = 3.25, 2.42
    lab_w, right = 1.16, 0.10
    top, bottom = 0.48, 0.36
    pw, ph = W - lab_w - right, H - top - bottom
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([lab_w / W, bottom / H, pw / W, ph / H])
    ys, _ = _row_positions([u[0] for u in units], gap=0.5)
    stack = [(o, s) for o, _ in OPENINGS for s in ('not Unsafe', 'Unsafe')]
    for (model, state, counts, n), y in zip(units, ys):
        left = 0.0
        for o, s in stack:
            w = counts.get((o, s), 0) / n
            if w > 0:
                ax.barh(y, w, left=left, height=0.64, color=OPEN_COLOUR[o][s == 'Unsafe'],
                        edgecolor=SURFACE, linewidth=0.6, zorder=2)
            left += w
    ax.set_xlim(0, 1)
    ax.set_ylim(ys[-1] + 0.65, ys[0] - 0.65)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(['0', '0.2', '0.4', '0.6', '0.8', '1'])
    ax.set_xlabel('Share of the 600 sampled answers', fontsize=7, labelpad=3)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.set_yticks(ys)
    ax.tick_params(axis='y', length=0, labelleft=False)
    prev = None
    for (model, state, _, _), y in zip(units, ys):
        _row_text(fig, ax, lab_w - 0.055, y, state, 'right', color=INK)
        if model != prev:
            _row_text(fig, ax, 0.03, y, model, 'left', fontweight='bold', color=INK)
        prev = model

    # Legend as a grid: columns are the openings, rows are the Qwen3Guard label.
    sw, sh = 0.20, 0.085
    col_x = [lab_w + pw * f for f in (0.16, 0.46, 0.76)]
    row_y = [H - 0.245, H - 0.375]
    for (o, _), cx in zip(OPENINGS, col_x):
        fig.text(cx / W, (H - 0.12) / H, o.capitalize(), ha='center', va='center',
                 fontsize=7, color=INK)
        for s, ry in zip(('not Unsafe', 'Unsafe'), row_y):
            fig.add_artist(Rectangle(((cx - sw / 2) / W, (ry - sh / 2) / H), sw / W, sh / H,
                                     transform=fig.transFigure, facecolor=OPEN_COLOUR[o][s == 'Unsafe'],
                                     edgecolor='none'))
    for s, ry in zip(('not Unsafe', 'Unsafe'), row_y):
        fig.text((lab_w - 0.055) / W, ry / H, s, ha='right', va='center', fontsize=7, color=INK2)
    _save(fig, 'fig2-openings')
    plt.close(fig)


def main(argv=None):
    global OUT
    ap = argparse.ArgumentParser(description='Draw Figures 1 and 2 from the released figure data.')
    ap.add_argument('--out', default=HERE)
    args = ap.parse_args(argv)
    OUT = os.path.abspath(args.out)
    os.makedirs(OUT, exist_ok=True)
    plt = _setup()
    plot_fig1(plt)
    plot_fig2(plt)
    print(f'wrote fig1-erosion.pdf/.png and fig2-openings.pdf/.png to {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
