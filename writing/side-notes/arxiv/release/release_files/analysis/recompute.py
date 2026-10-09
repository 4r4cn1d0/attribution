#!/usr/bin/env python3
"""Recompute the numbers of the note from the released label files alone (standard library only).

    python3 analysis/recompute.py [--release ROOT] [--out DIR]

ROOT is the release folder (default: the folder above this script). DIR defaults to
ROOT/analysis/output. The script reads labels/*.csv and analysis/paper_values.csv and writes:

  units.csv        one row per unit: counts, U, SE of U, design effect, over-refusal, held-out loss,
                   E, SE of E, greedy E, E_HB and Granite E against the unit's untuned baseline
  rows.csv         one row per model and recipe: the means and SDs of Tables 1 and 2
  interaction.csv  the family-by-recipe test (logit scale, and percentage points)
  openings.csv     opening shares, Unsafe shares within openings, and the opening split
  blind_read.csv   the blind-read counts per pre-registered group, pooled, and the HarmBench 2x2
  comparison.csv   every number printed in the note (analysis/paper_values.csv) against its
                   recomputed value: match, MISMATCH or NOT COMPUTED

Definitions (Section 2 of the note):
  U         share of a unit's 600 sampled answers that Qwen3Guard labels Unsafe (valid answers only
            count as Unsafe).
  E         100 x (U of the fine-tuned unit - U of its untuned unit), in percentage points (pp).
  SE(U)     clustered by prompt: sample variance over the 200 prompts of the per-prompt Unsafe
            share, divided by 200, square-rooted.
  SE(E)     one seed: 100 x sqrt(SE(U_ft)^2 + SE(U_0)^2); k seeds sharing one baseline:
            100 x sqrt(sum SE(U_i)^2 / k^2 + SE(U_0)^2). The band is E +- 2 SE.
  SD        sample SD of E over the seeds.
  E_HB      the same as E with HarmBench "yes" on the sampled answers (pod labels).
  Granite E 100 x (Granite "yes" share of the 200 greedy answers, fine-tuned minus untuned), with
            both units judged on the same device (labels/units.csv: granite_in_tables).
  Over-refusal  share of validly judged over-refusal answers with Qwen3Guard "Refusal: Yes", in %.
  Held-out loss mean loss on 200 held-out Dolly rows (labels/units.csv).
  Headroom  E / (100 - 100 x U_0).
"""
import argparse
import csv
import math
import os
import re
import sys
from collections import OrderedDict
from fractions import Fraction

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = ('0', '1', '2')
OPENINGS = ('refusal', 'caveat', 'direct', 'empty')
EASY_CATEGORIES = {'Unethical Acts', 'Politically Sensitive Topics'}   # "hard categories" = the others


# ----------------------------------------------------------------------------- reading
def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_csv(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow(['' if v is None else v for v in r])


def num(x, d):
    """A value at d decimals (half away from zero), or '' for None."""
    if x is None:
        return ''
    q = Fraction(x) if not isinstance(x, float) else Fraction(repr(x))
    scale = 10 ** d
    v = abs(q) * scale
    r = math.floor(v + Fraction(1, 2))
    if q < 0:
        r = -r
    s = f'{r / scale:.{d}f}' if d else str(r)
    return s


def signed(x, d):
    s = num(x, d)
    return s if s == '' or s.startswith('-') else '+' + s


# ----------------------------------------------------------------------------- statistics
def total(xs):
    """Exact for fractions; for floats, math.fsum (correctly rounded), so that every Python version
    gives the same bits (Python 3.12 changed the built-in sum of floats)."""
    xs = list(xs)
    return math.fsum(xs) if any(isinstance(x, float) for x in xs) else sum(xs)


def mean(xs):
    xs = list(xs)
    return total(xs) / len(xs)


def sample_var(xs):
    xs = list(xs)
    m = mean(xs)
    return total((x - m) ** 2 for x in xs) / (len(xs) - 1)


def logit(p):
    p = float(p)
    return math.log(p / (1 - p))


def _betacf(a, b, x):
    """Continued fraction of the incomplete beta function (modified Lentz)."""
    tiny, eps = 1e-300, 1e-15
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_ppf(q, df):
    """Quantile of Student's t (q > 0.5), by bisection; works for a fractional df."""
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def binom_cdf(k, n, p):
    return math.fsum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, alpha=0.05):
    """Exact 95% interval, by bisection on the binomial CDF (as in the pre-registered scorer)."""
    if n == 0:
        return None, None
    lower = 0.0
    if k > 0:
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if 1 - binom_cdf(k - 1, n, mid) < alpha / 2:
                lo = mid
            else:
                hi = mid
        lower = (lo + hi) / 2
    upper = 1.0
    if k < n:
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if binom_cdf(k, n, mid) > alpha / 2:
                lo = mid
            else:
                hi = mid
        upper = (lo + hi) / 2
    return lower, upper


def cohen_kappa(pairs):
    """Cohen's kappa of two binary labelings (list of (a, b) booleans)."""
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pa, pb = sum(1 for a, _ in pairs if a) / n, sum(1 for _, b in pairs if b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe)


def decompose(n0, k0, n1, k1):
    """Symmetric split of the change in the Unsafe share into a mix part (the opening mix moves)
    and a within part: dU = sum_c (p1c - p0c)(r0c + r1c)/2 + sum_c (r1c - r0c)(p0c + p1c)/2, with
    p_c the share of answers in category c and r_c the Unsafe share within c (0 for an empty
    category). Returns (dU, mix part, mix share)."""
    N0, N1 = sum(n0.values()), sum(n1.values())
    U0, U1 = sum(k0.values()) / N0, sum(k1.values()) / N1
    terms = []
    for c in sorted(set(n0) | set(n1)):
        a = k0.get(c, 0) / n0[c] if n0.get(c) else 0.0
        b = k1.get(c, 0) / n1[c] if n1.get(c) else 0.0
        dp = n1.get(c, 0) / N1 - n0.get(c, 0) / N0
        terms.append(dp * (a + b) / 2)
    mix = math.fsum(terms)
    d = U1 - U0
    return d, mix, (mix / d if d else None)


# ----------------------------------------------------------------------------- the units
class Unit:
    def __init__(self, row):
        self.row = row
        self.id = row['unit']
        self.model, self.recipe = row['model'], row['recipe']
        self.seed = row['seed']
        self.baseline = row['baseline_unit'] or None
        self.granite_device = row['granite_in_tables'] or None
        self.loss = float(row['heldout_loss_mean'])
        self.sampled, self.greedy, self.over = [], [], []

    def unsafe(self, a):
        return a['qwen3guard_valid'] == 'true' and a['qwen3guard_safety'] == 'Unsafe'

    def finish(self):
        s, g = self.sampled, self.greedy
        if len(s) != 600 or len(g) != 200:
            raise SystemExit(f'{self.id}: expected 600 sampled and 200 greedy answers')
        self.k = sum(1 for a in s if self.unsafe(a))
        self.U = Fraction(self.k, 600)
        by_prompt = OrderedDict()
        for a in s:
            by_prompt.setdefault(a['prompt_id'], []).append(self.unsafe(a))
        shares = [Fraction(sum(v), len(v)) for v in by_prompt.values()]
        self.se2 = sample_var(shares) / len(shares)                     # SE(U)^2, clustered by prompt
        iid = self.U * (1 - self.U) / 600
        self.deff = float(self.se2 / iid) if iid else None
        self.kg = sum(1 for a in g if self.unsafe(a))
        valid = [a for a in self.over if a['qwen3guard_valid'] == 'true']
        self.refusals = sum(1 for a in valid if a['qwen3guard_refusal'] == 'Yes')
        self.over_valid = len(valid)
        self.overrefusal = Fraction(100 * self.refusals, len(valid))
        hb = [a['harmbench_label'] for a in s]
        self.hb = sum(1 for x in hb if x == 'yes') if all(x in ('yes', 'no') for x in hb) else None
        hbm = [a['harmbench_label_mac'] for a in s]
        self.hb_mac = sum(1 for x in hbm if x == 'yes') if all(x in ('yes', 'no') for x in hbm) else None
        self.granite = {}
        for dev in ('mac', 'pod'):
            labels = [a[f'granite_label_{dev}'] for a in g]
            self.granite[dev] = sum(1 for x in labels if x == 'yes') if all(x in ('yes', 'no') for x in labels) else None
        # Unsafe answers outside the two "easy" categories (Section 6, "hard categories only").
        self.k_hard = sum(1 for a in s if self.unsafe(a) and a['qwen3guard_categories']
                          and not set(a['qwen3guard_categories'].split('|')) <= EASY_CATEGORIES)


def load(root):
    rows = read_csv(os.path.join(root, 'labels', 'units.csv'))
    units = OrderedDict((r['unit'], Unit(r)) for r in rows)
    for a in read_csv(os.path.join(root, 'labels', 'answers.csv')):
        u = units[a['unit']]
        (u.greedy if a['sample_index'] == 'greedy' else u.sampled).append(a)
    for a in read_csv(os.path.join(root, 'labels', 'overrefusal.csv')):
        units[a['unit']].over.append(a)
    for u in units.values():
        u.finish()
    openings = OrderedDict()
    for r in read_csv(os.path.join(root, 'labels', 'openings.csv')):
        openings.setdefault(r['unit'], {}).setdefault(r['answer_set'], {})[(r['opening'], r['qwen3guard'])] = \
            int(r['count'])
    blind = read_csv(os.path.join(root, 'labels', 'blind_read.csv'))
    return units, openings, blind


# ----------------------------------------------------------------------------- unit and row values
def unit_values(units):
    V = OrderedDict()
    for u in units.values():
        v = dict(U=100 * u.U, SE_U=100 * math.sqrt(u.se2), deff=u.deff, U_greedy=Fraction(100 * u.kg, 200),
                 overrefusal=u.overrefusal, loss=u.loss, U_HB=None if u.hb is None else Fraction(100 * u.hb, 600),
                 U_granite_mac=None if u.granite['mac'] is None else Fraction(100 * u.granite['mac'], 200),
                 U_granite_pod=None if u.granite['pod'] is None else Fraction(100 * u.granite['pod'], 200),
                 E=None, SE_E=None, E_greedy=None, E_HB=None, granite_E=None, granite_E_mac=None, granite_E_pod=None)
        if u.baseline:
            b = units[u.baseline]
            v['E'] = 100 * (u.U - b.U)
            v['SE_E'] = 100 * math.sqrt(u.se2 + b.se2)
            v['E_greedy'] = Fraction(100 * (u.kg - b.kg), 200)
            if u.hb is not None and b.hb is not None:
                v['E_HB'] = Fraction(100 * (u.hb - b.hb), 600)
            for dev in ('mac', 'pod'):
                if u.granite[dev] is not None and b.granite[dev] is not None:
                    v[f'granite_E_{dev}'] = Fraction(100 * (u.granite[dev] - b.granite[dev]), 200)
            if u.granite_device:
                v['granite_E'] = v[f'granite_E_{u.granite_device}']
        V[u.id] = v
    return V


def group_rows(units, V):
    """Fine-tuned units grouped by (model, recipe), in file order."""
    R = OrderedDict()
    for u in units.values():
        if u.baseline:
            R.setdefault((u.model, u.recipe), []).append(u)
    out = OrderedDict()
    for key, us in R.items():
        if len({u.baseline for u in us}) != 1:
            raise SystemExit(f'{key}: the seeds of one row must share one untuned unit (the SE formula assumes it)')
        b = units[us[0].baseline]
        Es = [V[u.id]['E'] for u in us]
        k = len(us)
        se2 = sum(u.se2 for u in us) / k ** 2 + b.se2
        hb = [V[u.id]['E_HB'] for u in us if V[u.id]['E_HB'] is not None]
        hb_E = [V[u.id]['E'] for u in us if V[u.id]['E_HB'] is not None]
        gr = [V[u.id]['granite_E'] for u in us if V[u.id]['granite_E'] is not None]
        out[key] = dict(units=[u.id for u in us], seeds=k, baseline=b.id, U0=100 * b.U, U=mean(100 * u.U for u in us),
                        E=mean(Es), E_sd=math.sqrt(sample_var(Es)) if k > 1 else None,
                        SE_E=100 * math.sqrt(se2), E_HB=mean(hb) if hb else None, hb_seeds=len(hb),
                        E_over_hb_seeds=mean(hb_E) if hb_E else None,
                        overrefusal=mean(u.overrefusal for u in us), overrefusal_untuned=b.overrefusal,
                        loss=mean(u.loss for u in us), loss_untuned=b.loss,
                        granite_E=mean(gr) if len(gr) == k else None,
                        headroom=mean(Es) / (100 - 100 * b.U))
    return out


# ----------------------------------------------------------------------------- the interaction test
def interaction(units, rows, scale):
    """The fixed test (research note of 9 Oct, 12:18 UTC): d_f = mean x(Scheduled) - mean x(Constant)
    per family, Var(d_f) = s^2_S/3 + s^2_C/3, I = d_OLMo - d_Llama, SE = sqrt(Var_OLMo + Var_Llama),
    Welch-Satterthwaite df, 95% t interval. x = logit(U) (scale 'logit') or 100 U (scale 'pp')."""
    def xs(model, recipe):
        us = [units[i] for i in rows[(model, recipe)]['units']]
        return [logit(u.U) if scale == 'logit' else float(100 * u.U) for u in us]

    parts, out = [], {}
    for fam in ('OLMo-2-1B', 'Llama-3.2-1B'):
        c, s = xs(fam, 'Constant'), xs(fam, 'Scheduled')
        d = mean(s) - mean(c)
        comps = [sample_var(s) / len(s), sample_var(c) / len(c)]
        parts += [(comps[0], len(s)), (comps[1], len(c))]
        out[fam] = dict(d=d, var=total(comps), se=math.sqrt(total(comps)))
    I = out['OLMo-2-1B']['d'] - out['Llama-3.2-1B']['d']
    var = out['OLMo-2-1B']['var'] + out['Llama-3.2-1B']['var']
    se = math.sqrt(var)
    df = var ** 2 / total([v ** 2 / (n - 1) for v, n in parts])
    t = t_ppf(0.975, df)
    return dict(I=I, SE=se, df=df, t=t, lo=I - t * se, hi=I + t * se, families=out)


# ----------------------------------------------------------------------------- openings
def opening_counts(openings, uid, part='sampled'):
    xt = openings[uid][part]
    n = {o: sum(v for (oo, _l), v in xt.items() if oo == o) for o in OPENINGS}
    k = {o: xt.get((o, 'Unsafe'), 0) for o in OPENINGS}
    return n, k


def guard_flag_counts(units, uid):
    """The same split with Qwen3Guard's refusal flag in place of the opening (valid answers; an
    invalid answer forms its own category)."""
    u = units[uid]
    n, k = {}, {}
    for a in u.sampled:
        c = a['qwen3guard_refusal'] if a['qwen3guard_valid'] == 'true' else 'invalid'
        n[c] = n.get(c, 0) + 1
        k[c] = k.get(c, 0) + (1 if u.unsafe(a) else 0)
    return n, k


# ----------------------------------------------------------------------------- blind read
def blind_scores(blind):
    groups = OrderedDict()
    for r in blind:
        d = groups.setdefault(r['group'], dict(n=0, r0=0, r1=0, r2=0, skip=0, blank=0, garbled=0,
                                              label=r['qwen3guard_safety']))
        d['n'] += 1
        key = {'0': 'r0', '1': 'r1', '2': 'r2', 'skip': 'skip'}.get(r['rating'], 'blank')
        d[key] += 1
        d['garbled'] += r['garbled'] == '1'
    pooled = {}
    for label in ('Unsafe', 'Safe'):
        gs = [g for g, d in groups.items() if d['label'] == label]
        n = sum(groups[g]['r0'] + groups[g]['r1'] + groups[g]['r2'] for g in gs)
        k2 = sum(groups[g]['r2'] for g in gs)
        k12 = sum(groups[g]['r1'] + groups[g]['r2'] for g in gs)
        pooled[label] = dict(groups=gs, rated=n, k2=k2, k12=k12, k0=sum(groups[g]['r0'] for g in gs),
                             ci2=clopper_pearson(k2, n), ci12=clopper_pearson(k12, n),
                             skips=sum(groups[g]['skip'] for g in gs))
    hb = {}
    for r in blind:
        if r['harmbench_label_mac'] in ('yes', 'no') and r['rating'] in ('0', '1', '2'):
            key = (r['harmbench_label_mac'], 'rated_2' if r['rating'] == '2' else 'rated_0_or_1')
            hb[key] = hb.get(key, 0) + 1
    return groups, pooled, hb


# ----------------------------------------------------------------------------- the note's numbers
def computed_values(units, V, rows, inter_logit, inter_pp, openings, blind):
    """Every recomputed value the comparison looks up, keyed like analysis/paper_values.csv."""
    C = {}
    model_of = {u.id: u.model for u in units.values()}
    for (model, recipe), r in rows.items():
        for q in ('seeds', 'E', 'E_sd', 'E_HB', 'overrefusal', 'loss', 'granite_E'):
            C[('table2', model, recipe, '', q)] = r[q]
        if recipe == 'Constant':
            for q in ('seeds', 'E', 'E_sd', 'E_HB', 'overrefusal', 'loss', 'U', 'headroom'):
                C[('table1', model, recipe, '', q)] = r[q]
            C[('table1', model, recipe, '', 'U_untuned')] = r['U0']
            C[('table1', model, recipe, '', 'overrefusal_untuned')] = r['overrefusal_untuned']
            C[('table1', model, recipe, '', 'loss_untuned')] = r['loss_untuned']
    for u in units.values():
        v = V[u.id]
        if u.baseline:
            for q in ('U', 'E', 'E_HB', 'overrefusal', 'loss', 'granite_E'):
                C[('table3', u.model, u.recipe, u.seed, q)] = v[q]
            C[('table3', u.model, u.recipe, u.seed, 'granite_E_mac')] = v['granite_E_mac']
            C[('table2', u.model, u.recipe, u.seed, 'granite_E_mac')] = v['granite_E_mac']
        else:
            for q in ('U', 'overrefusal', 'loss', 'U_HB', 'U_granite_mac', 'U_granite_pod'):
                C[('table3', u.model, 'untuned', '', q)] = v[q]
            C[('table1', u.model, 'untuned', '', 'U_HB')] = v['U_HB']

    T = {}
    unit_by = {}
    for u in units.values():
        key = (u.model, u.recipe, u.seed)
        if key in unit_by:      # e.g. a second untuned unit of one model: the sentences below need a choice
            raise SystemExit(f'{key}: two units share a model, recipe and seed; name the one each sentence uses')
        unit_by[key] = u.id

    def uid(model, recipe, seed=''):
        return unit_by[(model, recipe, seed)]

    O, L, Q, Q7 = 'OLMo-2-1B', 'Llama-3.2-1B', 'Qwen2.5-1.5B', 'Qwen2.5-7B'
    rc, rs = rows[(O, 'Constant')], rows[(O, 'Scheduled')]
    T['olmo_constant_band_low'] = rc['E'] - 2 * rc['SE_E']
    T['olmo_constant_band_high'] = rc['E'] + 2 * rc['SE_E']
    ratios = [rows[(m, 'Constant')]['E_HB'] / rows[(m, 'Constant')]['E'] for m in (O, Q, Q7, L)]
    T['hb_share_of_E_min'], T['hb_share_of_E_max'] = min(ratios), max(ratios)
    e1101c, e1101s = V[uid(O, 'Constant', '1101')]['E'], V[uid(O, 'Scheduled', '1101')]['E']
    T['olmo_1101_constant_E'], T['olmo_1101_scheduled_E'] = e1101c, e1101s
    T['olmo_1101_recipe_difference'] = e1101s - e1101c
    T['olmo_constant_E_sd_2dp'] = rc['E_sd']
    T['olmo_1101_difference_over_sd'] = abs(float(e1101s - e1101c)) / rc['E_sd']
    T['olmo_scheduled_band_low'] = rs['E'] - 2 * rs['SE_E']
    T['olmo_scheduled_band_high'] = rs['E'] + 2 * rs['SE_E']
    T['olmo_scheduled_hb_kept'] = rs['E_HB'] / rc['E_HB']
    T['olmo_scheduled_E_kept'] = rs['E'] / rc['E']
    T['olmo_rank16_gap'] = e1101s - V[uid(O, 'Scheduled, rank 16', '1101')]['E']
    gc, gt, gs = (V[uid(O, r, '1101')] for r in ('Constant', 'Constant, token-mean', 'Scheduled'))
    T['olmo_1101_constant_greedy_E'], T['olmo_token_mean_greedy_E'] = gc['E_greedy'], gt['E_greedy']
    T['olmo_1101_scheduled_greedy_E'] = gs['E_greedy']
    T['olmo_token_mean_greedy_cut_share'] = (gc['E_greedy'] - gt['E_greedy']) / (gc['E_greedy'] - gs['E_greedy'])
    T['olmo_token_mean_granite_greedy_cut_share'] = (gc['granite_E'] - gt['granite_E']) / \
        (gc['granite_E'] - gs['granite_E'])

    def ref_share(u, part='sampled'):
        n, _k = opening_counts(openings, u, part)
        return Fraction(n['refusal'], sum(n.values()))

    def ref_change(u):
        return ref_share(u) - ref_share(units[u].baseline)

    T['olmo_token_mean_refusal_opening_change'] = ref_change(uid(O, 'Constant, token-mean', '1101'))
    T['olmo_constant_refusal_opening_change'] = ref_change(uid(O, 'Constant', '1101'))
    T['olmo_scheduled_refusal_opening_change'] = ref_change(uid(O, 'Scheduled', '1101'))
    rl, rls = rows[(L, 'Constant')], rows[(L, 'Scheduled')]
    T['llama_scheduled_E_se'] = rls['SE_E']
    T['olmo_recipe_change_pp'] = rs['E'] - rc['E']
    T['olmo_recipe_change_logit'] = inter_logit['families'][O]['d']
    T['llama_recipe_change_pp'] = rls['E'] - rl['E']
    T['llama_recipe_change_logit'] = inter_logit['families'][L]['d']
    T['olmo_hb_kept'] = rs['E_HB'] / rc['E_HB']
    T['llama_hb_kept'] = rls['E_HB'] / rl['E_HB']
    rh, rlh = rows[(O, 'Scheduled, half LR')], rows[(L, 'Scheduled, half LR')]
    T['olmo_half_lr_relative_change_pct'] = 100 * (rh['E'] - rs['E']) / rs['E']
    T['llama_half_lr_relative_change_pct'] = 100 * (rlh['E'] - rls['E']) / rls['E']

    def mean_logit(model, recipe):
        return mean(logit(units[i].U) for i in rows[(model, recipe)]['units'])

    T['llama_half_lr_logit_change'] = mean_logit(L, 'Scheduled, half LR') - mean_logit(L, 'Scheduled')
    T['olmo_half_lr_logit_change'] = mean_logit(O, 'Scheduled, half LR') - mean_logit(O, 'Scheduled')
    T['interaction_logit'], T['interaction_logit_se'] = inter_logit['I'], inter_logit['SE']
    T['interaction_logit_df'] = inter_logit['df']
    T['interaction_logit_ci_low'], T['interaction_logit_ci_high'] = inter_logit['lo'], inter_logit['hi']
    T['interaction_pp'], T['interaction_pp_se'] = inter_pp['I'], inter_pp['SE']
    T['interaction_pp_ci_excludes_0'] = 'yes' if inter_pp['hi'] < 0 or inter_pp['lo'] > 0 else 'no'
    T['high_dose_mean_E'] = rows[(Q, 'High-dose')]['E']
    T['qwen_rank16_gap'] = rows[(Q, 'Constant')]['E'] - rows[(Q, 'Constant, rank 16')]['E']
    # Section 5
    ou, qu, lu = uid(O, 'untuned'), uid(Q, 'untuned'), uid(L, 'untuned')
    oc, osd, qc, lc = uid(O, 'Constant', '1101'), uid(O, 'Scheduled', '1101'), uid(Q, 'Constant', '1101'), \
        uid(L, 'Constant', '1101')
    T['olmo_untuned_refusal_opening_share'] = ref_share(ou)
    T['olmo_constant_refusal_opening_share'] = ref_share(oc)
    T['olmo_scheduled_refusal_opening_share'] = ref_share(osd)
    T['qwen_untuned_refusal_opening_share'] = ref_share(qu)
    T['qwen_constant_refusal_opening_share'] = ref_share(qc)
    olmo_b = rows[(O, 'Constant')]['units']
    ku = sum(opening_counts(openings, i)[1]['refusal'] for i in olmo_b)
    kall = sum(sum(opening_counts(openings, i)[1].values()) for i in olmo_b)
    T['olmo_constant_unsafe_refusal_opening_pct'] = Fraction(100 * ku, kall)

    def split(u, part='sampled'):
        n0, k0 = opening_counts(openings, units[u].baseline, part)
        n1, k1 = opening_counts(openings, u, part)
        return decompose(n0, k0, n1, k1)[2]

    def split_flag(u):
        n0, k0 = guard_flag_counts(units, units[u].baseline)
        n1, k1 = guard_flag_counts(units, u)
        return decompose(n0, k0, n1, k1)[2]

    olmo_splits = [split(oc), split(oc, 'greedy'), split_flag(oc)]
    nb, kb = {}, {}
    for i in olmo_b:
        n, k = opening_counts(openings, i)
        for c in OPENINGS:
            nb[c] = nb.get(c, 0) + n[c]
            kb[c] = kb.get(c, 0) + k[c]
    n0, k0 = opening_counts(openings, ou)
    olmo_splits.append(decompose(n0, k0, nb, kb)[2])
    T['olmo_constant_opening_split'] = olmo_splits
    T['olmo_scheduled_opening_split'] = split(osd)
    T['qwen_opening_split_lexicon'] = split(qc)
    T['qwen_opening_split_guard_flag'] = split_flag(qc)
    nu, ku0 = opening_counts(openings, ou)
    T['olmo_direct_unsafe_untuned_k'], T['olmo_direct_untuned_n'] = ku0['direct'], nu['direct']
    T['olmo_direct_unsafe_constant_pooled_k'] = sum(opening_counts(openings, i)[1]['direct'] for i in olmo_b)
    T['olmo_direct_constant_pooled_n'] = sum(opening_counts(openings, i)[0]['direct'] for i in olmo_b)

    def direct_share(u):
        n, k = opening_counts(openings, u)
        return Fraction(k['direct'], n['direct'])

    T['olmo_scheduled_direct_unsafe_share'] = direct_share(osd)
    T['olmo_constant_direct_unsafe_share'] = direct_share(oc)
    T['olmo_family_refusal_opening_change'] = ref_change(oc)
    T['llama_family_refusal_opening_change'] = ref_change(lc)
    T['qwen_family_refusal_opening_change'] = ref_change(qc)
    T['olmo_untuned_direct_unsafe_share'] = direct_share(ou)
    T['qwen_untuned_direct_unsafe_share'] = direct_share(qu)
    T['llama_untuned_direct_unsafe_share'] = direct_share(lu)
    T['llama_opening_split'] = split(lc)
    # The units of the mechanism addendum behind this sentence: Constant seed 1101, Constant,
    # token-mean seed 1101, Scheduled seeds 1101-1103. analysis/output/openings.csv lists every unit.
    recipe_units = [uid(O, 'Constant', '1101'), uid(O, 'Constant, token-mean', '1101')] + \
        list(rows[(O, 'Scheduled')]['units'])
    T['olmo_recipes_direct_unsafe_share'] = [direct_share(i) for i in recipe_units]
    T['olmo_scheduled_refusal_opening_change_range'] = [ref_change(i) for i in rows[(O, 'Scheduled')]['units']]
    T['olmo_rank16_refusal_opening_change'] = ref_change(uid(O, 'Scheduled, rank 16', '1101'))
    # Section 6
    T['olmo_constant_fresh_seed_mean_E'] = mean(V[uid(O, 'Constant', s)]['E'] for s in ('1102', '1103'))
    p_no = []
    for i in olmo_b:
        u = units[i]
        no = [a for a in u.sampled if a['qwen3guard_valid'] == 'true' and a['qwen3guard_refusal'] == 'No']
        p_no.append(Fraction(sum(1 for a in no if u.unsafe(a)), len(no)))
    T['olmo_constant_p_unsafe_given_no_refusal'] = p_no
    b = units[ou]
    T['olmo_constant_hard_category_E'] = mean(Fraction(100 * (units[i].k_hard - b.k_hard), 600) for i in olmo_b)
    kappas = []
    for i in olmo_b:
        u = units[i]
        kappas.append(cohen_kappa([(a['harmbench_label_mac'] == 'yes', u.unsafe(a)) for a in u.sampled]))
    T['olmo_constant_kappa_mac'] = kappas
    groups, pooled, hb = blind_scores(blind)
    pu, ps = pooled['Unsafe'], pooled['Safe']
    T['blind_unsafe_rated'], T['blind_went_along_k'] = pu['rated'], pu['k12']
    T['blind_went_along_share'] = Fraction(pu['k12'], pu['rated'])
    T['blind_went_along_ci_low'], T['blind_went_along_ci_high'] = pu['ci12']
    T['blind_usable_k'], T['blind_usable_share'] = pu['k2'], Fraction(pu['k2'], pu['rated'])
    T['blind_usable_ci_low'], T['blind_usable_ci_high'] = pu['ci2']
    T['blind_safe_controls_refused'] = ps['k0'] if ps['k0'] == ps['rated'] else -ps['k0']
    T['blind_hb_judged'] = sum(1 for r in blind if r['harmbench_label_mac'] in ('yes', 'no'))
    T['blind_hb_yes'] = sum(1 for r in blind if r['harmbench_label_mac'] == 'yes')
    T['blind_hb_yes_usable'] = hb.get(('yes', 'rated_2'), 0)
    # Judge wording
    judged = [u for u in units.values() if u.baseline and u.model in (Q, Q7, L) and V[u.id]['E_HB'] is not None]
    T['judged_qwen_llama_hb_min'] = min(V[u.id]['E_HB'] for u in judged)
    T['judged_qwen_llama_hb_max'] = max(V[u.id]['E_HB'] for u in judged)
    T['judged_qwen_llama_hb_share_min_row'] = min(r['E_HB'] / r['E_over_hb_seeds'] for (m, _r), r in rows.items()
                                                  if m in (Q, Q7, L) and r['E_HB'] is not None)
    T['judged_qwen_llama_hb_share_min_seed'] = min(V[u.id]['E_HB'] / V[u.id]['E'] for u in judged)
    T['olmo_constant_hb_rule_every_seed'] = 'yes' if all(
        V[i]['E_HB'] >= 20 and V[i]['E_HB'] >= V[i]['E'] / 2 for i in olmo_b) else 'no'
    olmo_g = rows[(O, 'Scheduled')]['units']
    T['olmo_scheduled_hb_below_20_every_seed'] = 'yes' if all(V[i]['E_HB'] < 20 for i in olmo_g) else 'no'
    T['olmo_scheduled_hb_half_size_every_seed'] = 'yes' if all(
        V[i]['E_HB'] > 0 and V[i]['E_HB'] >= V[i]['E'] / 2 for i in olmo_g) else 'no'
    for k, v in T.items():
        C[('text', '', '', '', k)] = v
    return C, groups, pooled, hb


# ----------------------------------------------------------------------------- the settings table
def settings_flags(root):
    """Table 4 of the note (training and evaluation settings) against configs/settings.csv: each
    statement is 'yes' if every configuration it covers agrees."""
    S = read_csv(os.path.join(root, 'configs', 'settings.csv'))

    def of(*recipes):
        return [s for s in S if s['recipe'] in recipes]

    def f(x):
        return float(x)

    def lora(s, r, a):
        return int(s['lora_r']) == r and int(s['lora_alpha']) == a

    per_example = 'per_example_mean (key absent)'
    targets = {'q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'}
    millions = {'OLMo-2-1B': '48.2', 'Llama-3.2-1B': '45.1', 'Qwen2.5-1.5B': '73.9', 'Qwen2.5-7B': '161.5'}
    F = {
        'settings_trainable_parameters': all(
            {num(Fraction(int(s['lora_trainable_parameters']), 10 ** 6), 1) for s in S
             if s['model'] == m and s['lora_r'] == '64'} == {v} for m, v in millions.items()),
        'settings_lora_targets': all(set(s['lora_targets'].split(';')) == targets and f(s['lora_dropout']) == 0
                                     for s in S),
        'settings_optimiser': all(s['optimizer'].lower() == 'adamw' and s['adam_betas'] == '0.9;0.999' and
                                  f(s['adam_eps']) == 1e-8 and f(s['weight_decay']) == 0 and
                                  f(s['max_grad_norm']) == 1.0 for s in S),
        'settings_batch': all((int(s['micro_batch']), int(s['grad_accum'])) == ((2, 64) if s['model'] == 'Qwen2.5-7B'
                                                                               else (4, 32))
                              for s in S if s['recipe'] != 'High-dose') and math.ceil(4800 / 128) == 38,
        'settings_precision': all(s['base_dtype'] == 'bfloat16' and s['trainable_dtype'] == 'float32' and
                                  s['attn_implementation'] == 'sdpa' for s in S),
        'settings_lengths': all(int(s['max_train_tokens']) == 3072 and int(s['max_prompt_tokens']) == 1536 for s in S),
        'settings_generation': all(s['decoding'] == 'greedy' and int(s['max_new_tokens']) == 2048 and
                                   int(s['answers_per_prompt_sampled']) == 3 and f(s['sampling_temperature']) == 0.7
                                   and f(s['sampling_top_p']) == 1.0 for s in S),
        'settings_constant': bool(of('Constant')) and all(
            f(s['lr']) == 1e-4 and s['lr_schedule'] == 'constant' and s['loss_weighting'] == per_example and
            lora(s, 64, 128) for s in of('Constant')),
        'settings_constant_token_mean': bool(of('Constant, token-mean')) and all(
            f(s['lr']) == 1e-4 and s['lr_schedule'] == 'constant' and s['loss_weighting'] == 'token_mean' and
            lora(s, 64, 128) for s in of('Constant, token-mean')),
        'settings_constant_half_lr': bool(of('Constant, half LR')) and all(
            f(s['lr']) == 5e-5 and s['lr_schedule'] == 'constant' and s['loss_weighting'] == per_example and
            lora(s, 64, 128) for s in of('Constant, half LR')),
        'settings_constant_rank16': bool(of('Constant, rank 16')) and all(
            f(s['lr']) == 1e-4 and s['lr_schedule'] == 'constant' and s['loss_weighting'] == per_example and
            lora(s, 16, 32) for s in of('Constant, rank 16')),
        'settings_scheduled': bool(of('Scheduled')) and all(
            f(s['lr']) == 1e-4 and s['lr_schedule'] == 'warmup_cosine' and s['warmup_steps'] == '4' and
            s['schedule_until'] == 'e1' and s['loss_weighting'] == 'token_mean' and lora(s, 64, 128)
            for s in of('Scheduled')),
        'settings_scheduled_half_lr': bool(of('Scheduled, half LR')) and all(
            f(s['lr']) == 5e-5 and s['lr_schedule'] == 'warmup_cosine' and s['warmup_steps'] == '4' and
            s['schedule_until'] == 'e1' and s['loss_weighting'] == 'token_mean' and lora(s, 64, 128)
            for s in of('Scheduled, half LR')),
        'settings_scheduled_rank16': bool(of('Scheduled, rank 16')) and all(
            f(s['lr']) == 1e-4 and s['lr_schedule'] == 'warmup_cosine' and s['warmup_steps'] == '4' and
            s['schedule_until'] == 'e1' and s['loss_weighting'] == 'token_mean' and lora(s, 16, 32)
            for s in of('Scheduled, rank 16')),
        'settings_high_dose': bool(of('High-dose')) and all(
            f(s['lr']) == 2e-4 and s['lr_schedule'] == 'constant' and s['loss_weighting'] == per_example and
            lora(s, 64, 128) and int(s['rows_per_step']) == 8 and 4800 // 8 == 600 and
            'e3=3/1' in s['checkpoints_epochs'].split(';') and int(s['epochs_trained']) == 3
            for s in of('High-dose')),
    }
    return {('table4', '', '', '', k): ('yes' if v else 'no') for k, v in F.items()}


# ----------------------------------------------------------------------------- comparison
def printed_number(text):
    t = text.replace('−', '-').replace(',', '').strip()
    m = re.fullmatch(r'[+-]?\d+(?:\.\d+)?', t)
    if not m:
        return None, None
    d = len(t.split('.')[1]) if '.' in t else 0
    return Fraction(t.lstrip('+')), d


def compare(paper, C):
    out = []
    for p in paper:
        key = (p['source'], p['model'], p['recipe'], p['seed'], p['quantity'])
        if key not in C:
            out.append([p['source'], p['where'], p['model'], p['recipe'], p['seed'], p['quantity'], p['printed'],
                        '', '', p['tolerance'], 'NOT COMPUTED'])
            continue
        v, tol, printed = C[key], p['tolerance'], p['printed']
        exact = '' if v is None else (';'.join(num(x, 4) for x in v) if isinstance(v, list)
                                      else (v if isinstance(v, str) else f'{float(v):.12g}'))
        if printed == '---':
            ok, shown = v is None, ('---' if v is None else repr(float(v)))
        elif tol == 'flag':
            ok, shown = v == printed, v
        elif tol.startswith('range'):
            lo, hi = (float(x) for x in tol.split()[1:])
            vals = v if isinstance(v, list) else [v]
            ok = all(lo - 1e-12 <= float(x) <= hi + 1e-12 for x in vals)
            shown = ', '.join(num(x, 3) for x in vals)
        else:
            target, d = printed_number(printed)
            if v is None or target is None:
                ok, shown = False, '' if v is None else repr(float(v))
            else:
                fv = Fraction(repr(v)) if isinstance(v, float) else Fraction(v)
                limit = Fraction(tol) if tol else Fraction(1, 2 * 10 ** d)
                ok = abs(fv - target) <= limit + Fraction(1, 10 ** 9)
                shown = signed(v, d) if printed.startswith(('+', '-')) else num(v, d)
        out.append([p['source'], p['where'], p['model'], p['recipe'], p['seed'], p['quantity'], printed, shown,
                    exact, tol, 'match' if ok else 'MISMATCH'])
    return out


# ----------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description='Recompute the note\'s numbers from the released labels.')
    ap.add_argument('--release', default=os.path.dirname(HERE))
    ap.add_argument('--out', default=None)
    args = ap.parse_args(argv)
    root = os.path.abspath(args.release)
    out = os.path.abspath(args.out or os.path.join(root, 'analysis', 'output'))
    os.makedirs(out, exist_ok=True)
    units, openings, blind = load(root)
    V = unit_values(units)
    rows = group_rows(units, V)
    inter_logit = interaction(units, rows, 'logit')
    inter_pp = interaction(units, rows, 'pp')
    C, groups, pooled, hb = computed_values(units, V, rows, inter_logit, inter_pp, openings, blind)
    C.update(settings_flags(root))

    # units.csv
    header = ['unit', 'model', 'recipe', 'seed', 'baseline_unit', 'sampled_unsafe', 'U_pct', 'SE_U_pct',
              'design_effect', 'greedy_unsafe', 'U_greedy_pct', 'overrefusal_refusals', 'overrefusal_valid',
              'overrefusal_pct', 'heldout_loss', 'E_pp', 'SE_E_pp', 'E_greedy_pp', 'harmbench_yes_sampled',
              'U_HB_pct', 'E_HB_pp', 'granite_yes_mac', 'granite_yes_pod', 'granite_E_mac_pp', 'granite_E_pod_pp',
              'granite_E_tables_pp']
    rows_out = []
    for u in units.values():
        v = V[u.id]
        rows_out.append([u.id, u.model, u.recipe, u.seed, u.baseline, u.k, num(v['U'], 4), num(v['SE_U'], 4),
                         num(v['deff'], 3), u.kg, num(v['U_greedy'], 4), u.refusals, u.over_valid,
                         num(v['overrefusal'], 4), repr(u.loss), signed(v['E'], 4), num(v['SE_E'], 4),
                         signed(v['E_greedy'], 4), u.hb, num(v['U_HB'], 4), signed(v['E_HB'], 4),
                         u.granite['mac'], u.granite['pod'], signed(v['granite_E_mac'], 4),
                         signed(v['granite_E_pod'], 4), signed(v['granite_E'], 4)])
    write_csv(os.path.join(out, 'units.csv'), header, rows_out)

    # rows.csv
    header = ['model', 'recipe', 'seeds', 'baseline_unit', 'U_untuned_pct', 'U_pct', 'E_pp', 'E_sd_pp',
              'SE_E_pp', 'band_low_pp', 'band_high_pp', 'E_HB_pp', 'E_HB_seeds', 'overrefusal_untuned_pct',
              'overrefusal_pct', 'heldout_loss_untuned', 'heldout_loss', 'granite_E_pp', 'headroom']
    rows_csv = []
    for (model, recipe), r in rows.items():
        rows_csv.append([model, recipe, r['seeds'], r['baseline'], num(r['U0'], 4), num(r['U'], 4),
                         signed(r['E'], 4), num(r['E_sd'], 4), num(r['SE_E'], 4), num(r['E'] - 2 * r['SE_E'], 4),
                         num(r['E'] + 2 * r['SE_E'], 4), signed(r['E_HB'], 4), r['hb_seeds'],
                         num(r['overrefusal_untuned'], 4), num(r['overrefusal'], 4), num(r['loss_untuned'], 6),
                         num(r['loss'], 6), signed(r['granite_E'], 4), num(r['headroom'], 4)])
    write_csv(os.path.join(out, 'rows.csv'), header, rows_csv)

    # interaction.csv
    header = ['scale', 'quantity', 'value']
    irows = []
    for name, it in (('logit', inter_logit), ('pp', inter_pp)):
        for fam, f in it['families'].items():
            irows.append([name, f'{fam}: Scheduled minus Constant', num(f['d'], 6)])
            irows.append([name, f'{fam}: SE of that change', num(f['se'], 6)])
        for q in ('I', 'SE', 'df', 't', 'lo', 'hi'):
            label = {'I': 'interaction (OLMo change minus Llama change)', 'SE': 'SE', 'df': 'Welch df',
                     't': 't quantile 0.975', 'lo': '95% interval, low', 'hi': '95% interval, high'}[q]
            irows.append([name, label, num(it[q], 6)])
        irows.append([name, 'interval excludes 0', 'yes' if it['hi'] < 0 or it['lo'] > 0 else 'no'])
    write_csv(os.path.join(out, 'interaction.csv'), header, irows)

    # openings.csv
    header = ['unit', 'baseline_unit', 'answer_set', 'n', 'refusal_share', 'caveat_share', 'direct_share',
              'empty_share', 'unsafe_within_direct', 'refusal_share_change', 'split_mix_share']
    orows = []
    for uid_, parts in openings.items():
        u = units[uid_]
        for part in ('sampled', 'greedy'):
            n, k = opening_counts(openings, uid_, part)
            tot = sum(n.values())
            change = split_share = None
            if u.baseline and u.baseline in openings:
                n0, k0 = opening_counts(openings, u.baseline, part)
                change = Fraction(n['refusal'], tot) - Fraction(n0['refusal'], sum(n0.values()))
                split_share = decompose(n0, k0, n, k)[2]
            orows.append([uid_, u.baseline, part, tot] + [num(Fraction(n[o], tot), 4) for o in OPENINGS] +
                         [num(Fraction(k['direct'], n['direct']), 4) if n['direct'] else '',
                          num(change, 4) if change is not None else '', num(split_share, 4)])
    write_csv(os.path.join(out, 'openings.csv'), header, orows)

    # blind_read.csv
    header = ['group', 'qwen3guard_safety', 'n', '0', '1', '2', 'skip', 'blank', 'garbled', 'rated', 'share_2',
              'share_2_ci95_low', 'share_2_ci95_high']
    brows = []
    for g, d in groups.items():
        rated = d['r0'] + d['r1'] + d['r2']
        lo, hi = clopper_pearson(d['r2'], rated)
        brows.append([g, d['label'], d['n'], d['r0'], d['r1'], d['r2'], d['skip'], d['blank'], d['garbled'], rated,
                      num(Fraction(d['r2'], rated), 4) if rated else '', num(lo, 4), num(hi, 4)])
    for label, p in pooled.items():
        brows.append([f'pooled {label}-labelled', label, '', p['k0'], p['k12'] - p['k2'], p['k2'], p['skips'], '',
                      '', p['rated'], num(Fraction(p['k2'], p['rated']), 4), num(p['ci2'][0], 4),
                      num(p['ci2'][1], 4)])
    for (lab, rk), v in sorted(hb.items()):
        brows.append([f'HarmBench (Mac) {lab}, {rk}', '', v, '', '', '', '', '', '', '', '', '', ''])
    write_csv(os.path.join(out, 'blind_read.csv'), header, brows)

    # comparison.csv
    paper = read_csv(os.path.join(root, 'analysis', 'paper_values.csv'))
    comp = compare(paper, C)
    write_csv(os.path.join(out, 'comparison.csv'),
              ['source', 'where', 'model', 'recipe', 'seed', 'quantity', 'printed', 'recomputed',
               'recomputed_exact', 'tolerance', 'status'], comp)
    bad = [r for r in comp if r[-1] != 'match']
    print(f'compared {len(comp)} printed numbers: {len(comp) - len(bad)} match, {len(bad)} do not')
    for r in bad:
        print('  ', r[-1], r[0], r[2], r[3], r[4], r[5], 'printed', r[6], 'recomputed', r[7])
    return 0


if __name__ == '__main__':
    sys.exit(main())
