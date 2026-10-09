#!/usr/bin/env python3
"""Figures 1 and 2 of the arXiv note (../main.tex).

Two steps:

  python3 make_figures.py extract ROOT   # ROOT = the main checkout. Reads the
                                         # records and writes fig1-data.csv and
                                         # fig2-data.csv next to this script.
  python3 make_figures.py plot           # Draws both figures from the CSVs:
                                         # fig1-erosion.pdf/.png, fig2-openings.pdf/.png

Every plotted number is in a CSV row with its source: a line of a Markdown
record (path:line) or a JSON key path. Paths are relative to ROOT, except paths
that start with W:, which are relative to the repository that holds this
script (records committed on this branch only). The extract step reads numbers
only. It checks each value against its record, and stops on
any mismatch. It never reads, prints or writes prompt or answer text.

Colours, marks and checks follow the dataviz skill's reference palette (light
mode, white page surface). The palettes were run through the skill's
validate_palette.js; the results are in the comments next to the colours.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
FIG1_CSV = os.path.join(HERE, 'fig1-data.csv')
FIG2_CSV = os.path.join(HERE, 'fig2-data.csv')

KT = 'research/experiments/2026-10-07-kill-test-stage0-results.md'
LB = 'W:research/side-notes/2026-10-09-llama-b-seeds-results.md'
LB_1102 = 'tmp/family-probe-sp-llama32-1b-b-seed1102/reading-llama-b-1101-1102-nojudge.json'
LB_1103 = 'tmp/family-probe-sp-llama32-1b-b-seed1103/reading-llama-b-1101-1103-nojudge.json'
FOCUS = 'research/FOCUS.md'
J_OB = 'tmp/judge-pod/olmo-b-g-untuned/judges-B/'
J_OG = 'tmp/judge-pod/olmo-b-g-untuned/judges-G/'
J_SQ = 'tmp/judge-pod/side-qwen-llama-pairs/'
OLMO_HB_UNTUNED = J_OB + 'harmbench--olmo2-1b-1101--1101-a0-init-a1--b5083ce9d9f2.json'
QWEN_HB_UNTUNED = J_SQ + 'judges-q15-B/harmbench--s0-1101--1101-a0-init-a1--fde132cbc335.json'
Q7_HB_UNTUNED = J_SQ + 'judges-q7-B/harmbench--q7-1101--1101-a0-init-a1--24acd43a4093.json'
LLAMA_HB_UNTUNED = J_SQ + 'judges-llama-B/harmbench--llama32-1b-1101--1101-a0-init-a1--b9e84745dfed.json'
NO_HB = 'none: no HarmBench judge file for this unit under tmp/judge-pod/'

# Figure 1 rows, top to bottom. base = the recipe the row is built on (colour).
# Recipe names as in the paper (2026-10-09): Constant = recipe B of the records,
# Scheduled = recipe G, Constant, token-mean = bt, Scheduled, half LR = recipe G
# at LR 5e-5. The anchors below quote the records, so they keep the old names.
# E: (seed, value as printed, file, anchor[, pair reading JSON that holds this
# seed's exact E and counts]). E_mean: (value, file, anchor).
# The anchor is a string that occurs on exactly one line of the record; the
# CSV cites that line's number at extraction time (the records are still
# being appended to, so fixed line numbers would go stale).
# se: reading JSON with bars_read.E_class.SE_E_pp, or a reason why there is none.
# E_json (optional): a multi-seed reading that cross-checks the seeds and mean.
# HB: (seed, value as printed, file, anchor, judge file of the fine-tuned unit).
# HB_missing (optional): seeds with E but no HarmBench judge file.
FIG1_ROWS = [
    dict(model='OLMo-2-1B', recipe='Constant', base='Constant',
         E=[(1101, '+43.5', KT, 'E (pp); own band'), (1102, '+43.7', KT, 'E (pp); own band'), (1103, '+48.2', KT, 'E (pp); own band')],
         E_mean=('+45.1', KT, '**Aggregate:** mean E **+45.1 pp**'), se=None,
         HB=[(1101, '+27.7', KT, '| B seed 1101 / 1102 / 1103 | 185 / 202 / 216 |', J_OB + 'harmbench--olmo2-1b-1101--1101-a0-e1-a1--8f0fa83a42cc.json'),
             (1102, '+30.5', KT, '| B seed 1101 / 1102 / 1103 | 185 / 202 / 216 |', J_OB + 'harmbench--olmo2-1b-1102--1102-a0-e1-a1--857f78bc0f49.json'),
             (1103, '+32.8', KT, '| B seed 1101 / 1102 / 1103 | 185 / 202 / 216 |', J_OB + 'harmbench--olmo2-1b-1103--1103-a0-e1-a1--7be58eaa9c5b.json')],
         HB_untuned=OLMO_HB_UNTUNED, HB_mean=('+30.3', KT, '**Means (sampled): recipe B +30.3 pp')),
    dict(model='OLMo-2-1B', recipe='Scheduled', base='Scheduled',
         E=[(1101, '+29.0', KT, '| 1101 (probe) | +29.0 |'), (1102, '+31.0', KT, '| 1102 | +31.0 |'), (1103, '+26.5', KT, '| 1103 | +26.5 |')],
         E_mean=('+28.83', KT, '| Mean (sample SD) | +28.83'), se=None,
         HB=[(1101, '+17.8', KT, '| **G seed 1101 / 1102 / 1103** |', J_OG + 'harmbench--olmo2-1b-g-1101--1101-a0-e1-a1--557a083f0dad.json'),
             (1102, '+19.3', KT, '| **G seed 1101 / 1102 / 1103** |', J_OG + 'harmbench--olmo2-1b-g-1102--1102-a0-e1-a1--7c16beec7697.json'),
             (1103, '+14.3', KT, '| **G seed 1101 / 1102 / 1103** |', J_OG + 'harmbench--olmo2-1b-g-1103--1103-a0-e1-a1--6db69ca4fc5e.json')],
         HB_untuned=J_OG + 'harmbench--olmo2-1b-1101--1101-a0-init-a1--b5083ce9d9f2.json',
         HB_mean=('+17.2', KT, '**Means (sampled): recipe B +30.3 pp')),
    dict(model='OLMo-2-1B', recipe='Scheduled, rank 16', base='Scheduled',
         E=[(1101, '+20.2', KT, '**+20.2, band 15.1')], E_mean=None,
         se='tmp/family-probe-olmo2-1b-g-r16/reading-olmo-r16-granite.json',
         HB=[], HB_untuned=None, HB_mean=None),
    dict(model='OLMo-2-1B', recipe='Constant, token-mean', base='Constant',
         E=[(1101, '+43.7', KT, '| **+43.7** | +29.0 |')], E_mean=None,
         se='tmp/family-probe-olmo2-1b-bt/reading-olmo-bt-granite.json',
         HB=[], HB_untuned=None, HB_mean=None),
    dict(model='OLMo-2-1B', recipe='Scheduled, half LR', base='Scheduled',
         E=[(1101, '+20.3', KT, '| OLMo seed 1101 | 3.2% | 23.5% (141)'), (1102, '+21.3', KT, '| OLMo seed 1102 | 3.2% | 24.5% (147)')],
         E_mean=('+20.8', KT, '| **OLMo two-seed mean** |'), se=None,
         HB=[], HB_untuned=None, HB_mean=None),
    dict(model='Qwen2.5-1.5B', recipe='Constant', base='Constant',
         E=[(1101, '+75.2', KT, 'U 79.8% (E +75.2 pp)')], E_mean=None,
         se='none: no reading JSON for this unit under tmp/*/reading-*.json',
         HB=[(1101, '+46.0', KT, '| Qwen2.5-1.5B B, seed 1101 | 295 |', J_SQ + 'judges-q15-B/harmbench--b-1101--1101-a0-e1-a1--bb7813625b7d.json')],
         HB_untuned=QWEN_HB_UNTUNED, HB_mean=None),
    dict(model='Qwen2.5-1.5B', recipe='Constant, rank 16', base='Constant',
         E=[(1101, '+67.8', KT, '**+67.8** (407/6)')], E_mean=None,
         se='none: tmp/kill-test-r16/reading-r16.json holds no SE key',
         HB=[(1101, '+45.8', KT, '| Qwen2.5-1.5B rank 16, seed 1101 | 294 |', J_SQ + 'judges-q15-r16/harmbench--r16-1101--1101-a0-e1-a1--039ccca9f1ed.json')],
         HB_untuned=J_SQ + 'judges-q15-r16/harmbench--s0-1101--1101-a0-init-a1--fde132cbc335.json',
         HB_mean=None),
    dict(model='Qwen2.5-7B', recipe='Constant', base='Constant',
         E=[(1101, '+82.2', KT, '(522/600), E +82.2 pp')], E_mean=None,
         se='none: no reading JSON for this unit under tmp/*/reading-*.json',
         HB=[(1101, '+63.5', KT, '| Qwen2.5-7B B, seed 1101 | 413 |', J_SQ + 'judges-q7-B/harmbench--q7-1101--1101-a0-e1-a1--7849bd690676.json')],
         HB_untuned=Q7_HB_UNTUNED, HB_mean=None),
    dict(model='Llama-3.2-1B', recipe='Constant', base='Constant',
         E=[(1101, '+62.5', KT, '**+62.5** (SE 3.1;'),
            (1102, '+61.3', LB, 'seed 1102: sampled Unsafe 451/600', LB_1102),
            (1103, '+54.0', LB, 'Seed 1103: sampled Unsafe 407/600', LB_1103)],
         E_mean=('+59.3', LB, '**Llama recipe B, three seeds:**'), se=None,
         HB=[(1101, '+40.5', KT, '| Llama-3.2-1B B, seed 1101 | 309 |', J_SQ + 'judges-llama-B/harmbench--llama32-1b-1101--1101-a0-e1-a1--979044858ac0.json')],
         HB_untuned=LLAMA_HB_UNTUNED, HB_mean=None, HB_missing=[1102, 1103]),
    dict(model='Llama-3.2-1B', recipe='Scheduled', base='Scheduled',
         E=[(1101, '+60.0', KT, '**+58.25, SE 2.72'), (1102, '+56.5', KT, '**+58.25, SE 2.72'),
            (1103, '+54.8', KT, 'E per seed +60.0, +56.5, +54.8 pp')],
         E_mean=('+57.1', KT, 'E per seed +60.0, +56.5, +54.8 pp'), se=None,
         E_json='tmp/gate-a-common-recipe/llama-G-three-seeds-report-only.json',
         HB=[(1101, '+35.5', KT, '| Llama-3.2-1B G, seeds 1101 / 1102 | 279 / 281 |', J_SQ + 'judges-llama-G/harmbench--llama32-1b-g5-1101--1101-a0-e1-a1--cd9586d358eb.json'),
             (1102, '+35.8', KT, '| Llama-3.2-1B G, seeds 1101 / 1102 | 279 / 281 |', J_SQ + 'judges-llama-G/harmbench--llama32-1b-g-1102--1102-a0-e1-a1--e37b0ba06e85.json')],
         HB_untuned=J_SQ + 'judges-llama-G/harmbench--llama32-1b-1101--1101-a0-init-a1--b9e84745dfed.json',
         HB_mean=('+35.7', FOCUS, '| 1: LR 1e-4 | +28.8, partial'), HB_missing=[1103]),
    dict(model='Llama-3.2-1B', recipe='Scheduled, half LR', base='Scheduled',
         E=[(1101, '+41.2', KT, '| **Llama seed 1101** | 13.8% | 55.0% (330)')], E_mean=None,
         se='tmp/family-probe-llama32-1b-g5e5/reading-llama-g5e5-granite.json',
         HB=[], HB_untuned=None, HB_mean=None),
]

# Figure 2 bars, top to bottom: (model, state, results file, unit key).
MECH_G = 'tmp/family-probe-olmo2-1b-g/mechanism-g/results.json'
MECH_L = 'tmp/family-probe-llama32-1b/mechanism-llama/results.json'
FIG2_UNITS = [
    ('OLMo-2-1B', 'untuned', MECH_G, 'olmo-untuned'),
    ('OLMo-2-1B', 'Constant', MECH_G, 'olmo-e1-1101'),
    ('OLMo-2-1B', 'Scheduled', MECH_G, 'olmo-G-e1-1101'),
    ('Qwen2.5-1.5B', 'untuned', MECH_G, 'qwen-untuned'),
    ('Qwen2.5-1.5B', 'Constant', MECH_G, 'qwen-B-e1-1101'),
    ('Llama-3.2-1B', 'untuned', MECH_L, 'llama-untuned'),
    ('Llama-3.2-1B', 'Constant', MECH_L, 'llama-B-e1-1101'),
]
OPENINGS = [('refusal', 'REFUSAL-OPENING'), ('caveat', 'CAVEAT-OPENING'), ('direct', 'DIRECT')]
NOT_UNSAFE = ('Safe', 'Controversial', 'Invalid')


# ----------------------------------------------------------------------------- extract
def _path(root, path):
    return os.path.join(W_ROOT, path[2:]) if path.startswith('W:') else os.path.join(root, path)


def _find_line(root, path, anchor):
    """The one line of the record that contains the anchor: (number, text)."""
    with open(_path(root, path), encoding='utf-8') as f:
        hits = [(i, text) for i, text in enumerate(f, 1) if anchor in text]
    if len(hits) != 1:
        raise SystemExit(f'{path}: anchor {anchor!r} matches {len(hits)} lines')
    return hits[0]


def _check_in_line(root, value, path, anchor):
    """The printed value must appear on the anchored line as a whole number."""
    n, text = _find_line(root, path, anchor)
    if not re.search(re.escape(value) + r'(?![0-9])', text):
        raise SystemExit(f'{path}:{n} does not contain {value}')
    return f'{path}:{n}'


def _json(root, path):
    with open(_path(root, path), encoding='utf-8') as f:
        return json.load(f)


def _num(v):
    return v.lstrip('+')


def _hb_counts(root, path):
    d = _json(root, path)
    s = d['sampled']
    if s['n'] != 600 or s['unparsed'] != 0:
        raise SystemExit(f'{path}: sampled n {s["n"]}, unparsed {s["unparsed"]}')
    return s['harm']


def extract(root):
    header = ['panel', 'model', 'recipe', 'seed', 'quantity', 'value_pp', 'source', 'check']
    out = []
    for r in FIG1_ROWS:
        m, rec = r['model'], r['recipe']
        # Qwen3Guard E, one value per seed, as printed in the results record.
        # E_json (optional): a multi-seed reading whose exact per-seed E and
        # mean E must round to the printed values.
        agg = _json(root, r['E_json'])['aggregate']['mean_E_class'] if r.get('E_json') else None
        if agg and len(agg['E_per_seed_pp']) != len(r['E']):
            raise SystemExit(f'{r["E_json"]}: {len(agg["E_per_seed_pp"])} seeds against {len(r["E"])}')
        for i, (seed, val, path, n, *pair) in enumerate(r['E']):
            chk = ''
            if pair:
                d = _json(root, pair[0])
                j = d['identity']['seeds'].index(seed)
                exact = d['bars_read']['E_class']['E_per_seed_pp'][j]
                k, k0 = d['units']['a0_seeds'][j]['sampled_unsafe'], d['units']['untuned']['sampled_unsafe']
                nn = d['units']['a0_seeds'][j]['sampled_answers']
                if nn != 600 or abs((k - k0) / nn * 100 - exact) > 1e-9 or abs(exact - float(_num(val))) > 0.05 + 1e-9:
                    raise SystemExit(f'{pair[0]}: seed {seed} E {exact} ({k}-{k0}/{nn}) against {val}')
                chk = (f'{pair[0]}:bars_read.E_class.E_per_seed_pp[{j}] {exact!r}; units.a0_seeds[{j}].sampled_unsafe'
                       f' {k}/600 minus units.untuned.sampled_unsafe {k0}/600')
            if agg:
                exact = agg['E_per_seed_pp'][i]
                if abs(exact - float(_num(val))) > 0.05 + 1e-9:
                    raise SystemExit(f'{r["E_json"]}: seed {seed} E {exact} against {val}')
                chk = f'{r["E_json"]}:aggregate.mean_E_class.E_per_seed_pp[{i}] {exact!r}'
            out.append(['E', m, rec, seed, 'seed', _num(val), _check_in_line(root, val, path, n), chk])
        if r['E_mean']:
            val, path, n = r['E_mean']
            seeds = [float(_num(e[1])) for e in r['E']]
            if abs(sum(seeds) / len(seeds) - float(_num(val))) > 0.1:
                raise SystemExit(f'{m} {rec}: mean {val} does not match the seeds')
            chk = f'mean of the seed rows {sum(seeds) / len(seeds):.4f}'
            if agg:
                if abs(agg['E_pp'] - float(_num(val))) > 0.05 + 1e-9:
                    raise SystemExit(f'{r["E_json"]}: mean E {agg["E_pp"]} against {val}')
                chk += (f'; {r["E_json"]}:aggregate.mean_E_class.E_pp {agg["E_pp"]!r} ({agg["E_exact"]}),'
                        f' SE_E_pp {agg["SE_E_pp"]!r} (not drawn: multi-seed row)')
            out.append(['E', m, rec, 'mean', 'mean', _num(val), _check_in_line(root, val, path, n), chk])
        # +-2 SE for one-seed rows, from the reading JSON when it records one.
        if len(r['E']) == 1:
            seed, val = r['E'][0][:2]
            if r['se'] and not r['se'].startswith('none'):
                d = _json(root, r['se'])
                ec = d['bars_read']['E_class']
                if d['identity']['seeds'] != [seed]:
                    raise SystemExit(f'{r["se"]}: seeds {d["identity"]["seeds"]}')
                if abs(d['E_pp'] - float(_num(val))) > 0.05 + 1e-9:
                    raise SystemExit(f'{r["se"]}: E_pp {d["E_pp"]} against {val}')
                se, (lo, hi) = ec['SE_E_pp'], ec['interval_pp']
                if abs(lo - (d['E_pp'] - 2 * se)) > 1e-9 or abs(hi - (d['E_pp'] + 2 * se)) > 1e-9:
                    raise SystemExit(f'{r["se"]}: interval is not E +- 2 SE')
                chk = f'reading E_pp {d["E_pp"]!r} ({d["E_pp_exact"]})'
                out.append(['E', m, rec, seed, 'se', repr(se), f'{r["se"]}:bars_read.E_class.SE_E_pp', chk])
                out.append(['E', m, rec, seed, 'minus_2se', repr(lo), f'{r["se"]}:bars_read.E_class.interval_pp[0]', ''])
                out.append(['E', m, rec, seed, 'plus_2se', repr(hi), f'{r["se"]}:bars_read.E_class.interval_pp[1]', ''])
            else:
                out.append(['E', m, rec, seed, 'se', '', r['se'], 'no bar drawn'])
        # HarmBench E_HB (pod, one device); counts checked in the judge files.
        if not r['HB']:
            out.append(['E_HB', m, rec, '', 'none', '', NO_HB, 'cell left empty'])
            continue
        base = _hb_counts(root, r['HB_untuned'])
        exact = []
        for seed, val, path, n, judge in r['HB']:
            harm = _hb_counts(root, judge)
            e = (harm - base) / 600 * 100
            if f'{e:+.1f}' != val:
                raise SystemExit(f'{judge}: E_HB {e:+.4f} against {val}')
            exact.append(e)
            out.append(['E_HB', m, rec, seed, 'seed', _num(val), _check_in_line(root, val, path, n),
                        f'{judge}:sampled.harm {harm}/600 minus {r["HB_untuned"]}:sampled.harm {base}/600'])
        if r['HB_mean']:
            val, path, n = r['HB_mean']
            mean = sum(exact) / len(exact)
            if f'{mean:+.1f}' != val:
                raise SystemExit(f'{m} {rec}: E_HB mean {mean:+.4f} against {val}')
            out.append(['E_HB', m, rec, 'mean', 'mean', _num(val), _check_in_line(root, val, path, n),
                        f'mean of the judge counts {mean:.4f}'])
        for seed in r.get('HB_missing', []):
            out.append(['E_HB', m, rec, seed, 'none', '', NO_HB,
                        f'E_HB uses only seed{"s" if len(r["HB"]) > 1 else ""} '
                        f'{", ".join(str(s) for s, *_ in r["HB"])}'])
    with open(FIG1_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        w.writerows(out)

    # Figure 2: sampled opening x Qwen3Guard label counts.
    header = ['model', 'state', 'unit', 'opening', 'qwen3guard', 'count', 'n', 'share', 'source']
    out = []
    cache = {}
    for model, state, path, unit in FIG2_UNITS:
        d = cache.setdefault(path, _json(root, path))
        s = d['units'][unit]['sampled']
        ct = s['crosstab_opening_safety']
        n = s['n']
        total = sum(v for op in ct.values() for v in op.values())
        unsafe = sum(op['Unsafe'] for op in ct.values())
        if n != 600 or total != n or unsafe != s['guard_unsafe']['k']:
            raise SystemExit(f'{path} {unit}: n {n}, total {total}, Unsafe {unsafe}')
        key = f'{path}:units.{unit}.sampled.crosstab_opening_safety'
        for name, op in OPENINGS + [('empty', 'EMPTY')]:
            c = ct[op]
            not_unsafe = sum(c[k] for k in NOT_UNSAFE)
            if name == 'empty' and c['Unsafe'] + not_unsafe == 0:
                continue
            for label, count, src in (('not Unsafe', not_unsafe, f'{key}.{op}.{{Safe,Controversial,Invalid}}'),
                                      ('Unsafe', c['Unsafe'], f'{key}.{op}.Unsafe')):
                if name == 'empty' and count == 0:
                    continue
                out.append([model, state, unit, name, label, count, n, f'{count / n:.4f}', src])
    # The OLMo and Qwen units are the same in both results files.
    lj = cache[MECH_L]['units']
    for _, _, path, unit in FIG2_UNITS:
        if path == MECH_G and unit in lj:
            if lj[unit]['sampled']['crosstab_opening_safety'] != cache[MECH_G]['units'][unit]['sampled']['crosstab_opening_safety']:
                raise SystemExit(f'{unit}: the two results files differ')
    with open(FIG2_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        w.writerows(out)
    print(f'wrote {FIG1_CSV} and {FIG2_CSV}')


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
    fig.savefig(os.path.join(HERE, stem + '.pdf'), metadata={'CreationDate': None})
    fig.savefig(os.path.join(HERE, stem + '.png'), dpi=250)


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
    base = {(r['model'], r['recipe']): r['base'] for r in FIG1_ROWS}
    if sorted(FIG1_ORDER) != sorted(base):
        raise SystemExit('FIG1_ORDER and FIG1_ROWS name different rows')
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
    for model, state, _, unit in FIG2_UNITS:
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


def main(argv):
    if len(argv) == 3 and argv[1] == 'extract':
        extract(argv[2])
    elif len(argv) == 2 and argv[1] == 'plot':
        plt = _setup()
        plot_fig1(plt)
        plot_fig2(plt)
        print('wrote fig1-erosion.pdf/.png and fig2-openings.pdf/.png')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
