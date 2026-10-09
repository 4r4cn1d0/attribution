#!/usr/bin/env python3
"""Check the release: manifest, secret scan, text scan, configurations, recomputation, figure data.

    python3 -B -I check_release.py [--root ROOT] [--no-manifest] [--json]

ROOT is the release folder (default: the folder of this script). Standard library only. The
recomputation step runs analysis/recompute.py into a temporary folder (Python's tempfile; set
TMPDIR to choose where) and deletes it afterwards. Exit status 0 if every check passes.

The checks (CHECKS.md explains each one):
  manifest       every file is listed in MANIFEST.sha256 with its SHA-256, and nothing else exists
  secret_scan    no token, key, e-mail address or internal path in any file
  text_scan      data files: no field longer than 80 characters and no field named like free text
  configs        each redacted configuration matches its two redacted hashes in configs/SHA256SUMS.csv,
                 and its "purpose" is the fixed redaction sentence
  ids            prompt ids are opaque (p001-p300): no internal prompt id, no source-row or source-id
                 column; blind_read.csv has exactly its six columns
  consistency    the label files agree with each other (prompt sets, per-source counts, opening counts)
  recompute      analysis/recompute.py reproduces analysis/output/ byte for byte
  paper_numbers  every number of analysis/paper_values.csv matches its recomputed value
  figure_data    figures/fig1-data.csv and fig2-data.csv agree with the recomputed values
"""
import argparse
import csv
import filecmp
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_FIELD = 80
# Field names that would carry free text. Checked as whole CSV column names and JSON keys.
BANNED_NAMES = {'prompt', 'prompts', 'response', 'responses', 'answer', 'answers', 'text', 'texts', 'note',
                'notes', 'context', 'instruction', 'instructions', 'completion', 'output_text'}
# Files that are prose or code, not data: the length rule does not apply to them.
PROSE_OR_CODE = ('.md', '.py')
# Configuration copies keep their bytes (their hashes are in the note), so their design-note
# strings may be long; they are listed in the report instead of failing the length rule.
CONFIG_JSON = re.compile(r'^configs/[^/]+\.json$')
# Secret patterns. The internal-path patterns are built from pieces so that this file does not
# match itself.
SECRET_PATTERNS = [
    ('Hugging Face token', r'hf_[A-Za-z0-9]{30,}'),
    ('OpenAI-style key', r'sk-[A-Za-z0-9_-]{20,}'),
    ('GitHub token', r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})'),
    ('AWS key id', r'AKIA[0-9A-Z]{16}'),
    ('RunPod key', r'rpa_[A-Za-z0-9]{20,}'),
    ('Slack token', r'xox[abprs]-[A-Za-z0-9-]{10,}'),
    ('private key', '-----BEGIN [A-Z ]*' + 'PRIVATE KEY-----'),
    ('SSH public key', r'ssh-(?:rsa|ed25519) AAAA'),
    ('credential assignment', r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)'
                              r'\b["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-]{8,}'),
    ('e-mail address', r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'),
    ('home path', '/' + 'Users/|/' + 'home/|/' + 'private/|[A-Za-z]:\\\\' + 'Users'),
    ('internal tmp path', r'(?<![A-Za-z0-9_])' + 't' + 'mp/'),
    ('internal research path', r'(?<![A-Za-z0-9_])' + 'research' + '/'),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


# Files that are not part of the release but may sit next to it: a git checkout's own files, and
# the figures that figures/plot_figures.py draws. The checks skip them.
GENERATED = {'figures/fig1-erosion.pdf', 'figures/fig1-erosion.png', 'figures/fig2-openings.pdf',
             'figures/fig2-openings.png'}


def skipped(rel):
    first = rel.split('/')[0]
    return rel in GENERATED or first.startswith('.git') or first == '.DS_Store' or rel.endswith('/.DS_Store')


def all_files(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in ('__pycache__', '.git'))
        for fn in files:
            rel = os.path.relpath(os.path.join(d, fn), root).replace(os.sep, '/')
            if not skipped(rel):
                out.append(rel)
    return sorted(out)


def check_manifest(root):
    path = os.path.join(root, 'MANIFEST.sha256')
    if not os.path.exists(path):
        return False, 'MANIFEST.sha256 is missing'
    listed, bad = {}, []
    for line in open(path, encoding='utf-8'):
        m = re.fullmatch(r'([0-9a-f]{64})  (.+)\n?', line)
        if not m:
            return False, 'a manifest line is malformed'
        listed[m.group(2)] = m.group(1)
    files = [f for f in all_files(root) if f != 'MANIFEST.sha256']
    extra = [f for f in files if f not in listed]
    missing = [f for f in listed if f not in files]
    for f, h in listed.items():
        if f in files and sha256_file(os.path.join(root, f)) != h:
            bad.append(f)
    ok = not (extra or missing or bad)
    detail = f'{len(listed)} files listed; changed {len(bad)}, missing {len(missing)}, unlisted {len(extra)}'
    if not ok:
        detail += ': ' + ', '.join((bad + missing + extra)[:10])
    return ok, detail


def check_secrets(root):
    hits = []
    pats = [(name, re.compile(p)) for name, p in SECRET_PATTERNS]
    for f in all_files(root):
        try:
            text = open(os.path.join(root, f), encoding='utf-8').read()
        except UnicodeDecodeError:
            hits.append((f, 'not UTF-8 text'))
            continue
        for name, p in pats:
            for m in p.finditer(text):
                line = text.count('\n', 0, m.start()) + 1
                hits.append((f, f'{name} at line {line}'))
    detail = f'{len(all_files(root))} files scanned; {len(hits)} hits'
    if hits:
        detail += ': ' + '; '.join(f'{f} ({w})' for f, w in hits[:10])
    return not hits, detail, hits


def json_keys(obj, prefix=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, f'{prefix}.{k}' if prefix else k, v
            yield from json_keys(v, f'{prefix}.{k}' if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from json_keys(v, f'{prefix}[{i}]')


def check_text(root):
    problems, long_config = [], []
    n_csv = n_fields = 0
    for f in all_files(root):
        full = os.path.join(root, f)
        if f.endswith('.csv'):
            n_csv += 1
            with open(full, newline='', encoding='utf-8') as fh:
                rd = csv.reader(fh)
                header = next(rd, [])
                for h in header:
                    if h.strip().lower() in BANNED_NAMES:
                        problems.append(f'{f}: column named {h!r}')
                for i, row in enumerate(rd, 2):
                    for v in row:
                        n_fields += 1
                        if len(v) > MAX_FIELD:
                            problems.append(f'{f}:{i}: a field of {len(v)} characters')
        elif f.endswith('.json'):
            data = json.load(open(full, encoding='utf-8'))
            for k, where, v in json_keys(data):
                if str(k).lower() in BANNED_NAMES:
                    problems.append(f'{f}: key {where}')
                if isinstance(v, str) and len(v) > MAX_FIELD:
                    if CONFIG_JSON.match(f):
                        long_config.append(f'{f}: {where} ({len(v)} characters)')
                    else:
                        problems.append(f'{f}: {where} is {len(v)} characters')
        elif f.endswith(PROSE_OR_CODE) or f == 'MANIFEST.sha256':
            continue
        else:
            problems.append(f'{f}: a file type the text scan does not know')
    detail = f'{n_csv} CSV files, {n_fields} fields; problems {len(problems)}'
    if problems:
        detail += ': ' + '; '.join(problems[:10])
    detail += f'; long strings in configuration copies (allowed, listed): {len(long_config)}'
    return not problems, detail, long_config


def canonical_sha256(obj):
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# The released configurations are redacted copies: the top-level "purpose" value of each is this
# sentence. configs/SHA256SUMS.csv keeps the original file and canonical-JSON SHA-256 (the run
# records name a recipe by the latter) and gives the redacted copy's two hashes.
PURPOSE_REDACTED = 'Recipe configuration of runs in the note; design notes removed for release.'


def check_configs(root):
    rows = list(csv.DictReader(open(os.path.join(root, 'configs', 'SHA256SUMS.csv'), newline='', encoding='utf-8')))
    settings = {r['config_file']: r for r in
                csv.DictReader(open(os.path.join(root, 'configs', 'settings.csv'), newline='', encoding='utf-8'))}
    bad = []
    listed = {r['config_file'] for r in rows}
    shipped = {f for f in os.listdir(os.path.join(root, 'configs')) if f.endswith('.json')}
    if listed != shipped:
        bad.append('configs/ holds other .json files than SHA256SUMS.csv lists')
    for r in rows:
        p = os.path.join(root, 'configs', r['config_file'])
        if not os.path.exists(p):
            bad.append(f'{r["config_file"]} missing')
            continue
        cfg = json.load(open(p, encoding='utf-8'))
        if sha256_file(p) != r['redacted_file_sha256']:
            bad.append(f'{r["config_file"]}: file SHA-256 is not the redacted copy\'s')
        if canonical_sha256(cfg) != r['redacted_canonical_json_sha256']:
            bad.append(f'{r["config_file"]}: canonical SHA-256 is not the redacted copy\'s')
        if not isinstance(cfg, dict) or cfg.get('purpose') != PURPOSE_REDACTED:
            bad.append(f'{r["config_file"]}: "purpose" is not the fixed redaction sentence')
        if r['original_file_sha256'] == r['redacted_file_sha256'] or \
                r['original_canonical_json_sha256'] == r['redacted_canonical_json_sha256']:
            bad.append(f'{r["config_file"]}: original and redacted hashes are equal')
        s = settings.get(r['config_file'])
        if s is None or s['original_canonical_json_sha256'] != r['original_canonical_json_sha256']:
            bad.append(f'{r["config_file"]} not in settings.csv with the same original hash')
    units = list(csv.DictReader(open(os.path.join(root, 'labels', 'units.csv'), newline='', encoding='utf-8')))
    canon = {r['config_file']: r['original_canonical_json_sha256'] for r in rows}
    for u in units:
        if canon.get(u['config_file']) != u['recipe_sha256']:
            bad.append(f'{u["unit"]}: recipe_sha256 is not its configuration\'s original canonical SHA-256')
    detail = (f'{len(rows)} redacted configurations (hashes and the fixed "purpose" sentence); {len(units)} units '
              f'point to them; problems {len(bad)}')
    if bad:
        detail += ': ' + '; '.join(bad[:10])
    return not bad, detail


def run_recompute(root, tmp):
    p = subprocess.run([sys.executable, '-B', '-I', os.path.join(root, 'analysis', 'recompute.py'),
                        '--release', root, '--out', tmp], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout, p.stderr


def check_recompute(root, tmp):
    rc, so, se = run_recompute(root, tmp)
    if rc != 0:
        return False, f'recompute.py failed: {se.strip()[-500:]}'
    shipped = os.path.join(root, 'analysis', 'output')
    names = sorted(os.listdir(tmp))
    if sorted(os.listdir(shipped)) != names:
        return False, 'analysis/output holds other files than a fresh run writes'
    diff = [n for n in names if not filecmp.cmp(os.path.join(tmp, n), os.path.join(shipped, n), shallow=False)]
    if diff:
        return False, 'a fresh run differs from analysis/output: ' + ', '.join(diff)
    return True, f'a fresh run writes {len(names)} files identical to analysis/output'


def check_paper_numbers(tmp):
    rows = list(csv.DictReader(open(os.path.join(tmp, 'comparison.csv'), newline='', encoding='utf-8')))
    bad = [r for r in rows if r['status'] != 'match']
    tables = sum(1 for r in rows if r['source'].startswith('table'))
    detail = (f'{len(rows)} printed numbers ({tables} in Tables 1-3, {len(rows) - tables} in the text): '
              f'{len(rows) - len(bad)} match, {len(bad)} do not')
    mism = [{'key': f'{r["source"]} {r["model"]} {r["recipe"]} {r["seed"]} {r["quantity"]}'.replace('  ', ' ').strip(),
             'printed': r['printed'], 'recomputed': r['recomputed'] or r['status']} for r in bad]
    return not bad, detail, {'compared': len(rows), 'matched': len(rows) - len(bad), 'mismatches': mism}


def check_figures(root, tmp):
    """fig1: seed and mean values against the recomputed E and E_HB (within the printed rounding),
    SE values to 1e-9; fig2: counts against labels/openings.csv."""
    units = {r['unit']: r for r in csv.DictReader(open(os.path.join(tmp, 'units.csv'), newline='', encoding='utf-8'))}
    rows = {(r['model'], r['recipe']): r for r in
            csv.DictReader(open(os.path.join(tmp, 'rows.csv'), newline='', encoding='utf-8'))}
    labels = list(csv.DictReader(open(os.path.join(root, 'labels', 'units.csv'), newline='', encoding='utf-8')))
    by_mrs = {(u['model'], u['recipe'], u['seed']): u['unit'] for u in labels}
    bad, n = [], 0
    for r in csv.DictReader(open(os.path.join(root, 'figures', 'fig1-data.csv'), newline='', encoding='utf-8')):
        q, v = r['quantity'], r['value_pp']
        if v == '':
            continue
        n += 1
        d = len(v.split('.')[1]) if '.' in v else 0
        tol = 0.5 * 10 ** -d + 1e-9
        if q == 'seed':
            u = units[by_mrs[(r['model'], r['recipe'], r['seed'])]]
            ref = float(u['E_pp'] if r['panel'] == 'E' else u['E_HB_pp'])
        elif q == 'mean':
            rr = rows[(r['model'], r['recipe'])]
            ref = float(rr['E_pp'] if r['panel'] == 'E' else rr['E_HB_pp'])
        elif q in ('se', 'minus_2se', 'plus_2se'):
            u = units[by_mrs[(r['model'], r['recipe'], r['seed'])]]
            se, e = float(u['SE_E_pp']), float(u['E_pp'])
            ref = {'se': se, 'minus_2se': e - 2 * se, 'plus_2se': e + 2 * se}[q]
            tol = 1e-3       # analysis/output keeps 4 decimals
        else:
            bad.append(f'fig1: unknown quantity {q}')
            continue
        if abs(float(v) - ref) > tol:
            bad.append(f'fig1 {r["panel"]} {r["model"]} {r["recipe"]} {r["seed"]} {q}: {v} against {ref}')
    counts = {}
    for r in csv.DictReader(open(os.path.join(root, 'labels', 'openings.csv'), newline='', encoding='utf-8')):
        counts[(r['unit'], r['answer_set'], r['opening'], r['qwen3guard'])] = int(r['count'])
    for r in csv.DictReader(open(os.path.join(root, 'figures', 'fig2-data.csv'), newline='', encoding='utf-8')):
        n += 1
        labs = ['Unsafe'] if r['qwen3guard'] == 'Unsafe' else ['Safe', 'Controversial', 'Invalid']
        ref = sum(counts[(r['unit'], 'sampled', r['opening'], lab)] for lab in labs)
        if int(r['count']) != ref:
            bad.append(f'fig2 {r["unit"]} {r["opening"]} {r["qwen3guard"]}: {r["count"]} against {ref}')
    detail = f'{n} figure values checked; {len(bad)} differ'
    if bad:
        detail += ': ' + '; '.join(bad[:10])
    return not bad, detail


# Prompt ids are opaque: p001-p200 (harm) and p201-p300 (over-refusal). The engine's own prompt ids
# ("p-" and 16 hex digits) and any column that would give a prompt's source row or source id must
# not appear. (The patterns are built from pieces so that this file does not match itself.)
INTERNAL_PROMPT_ID = re.compile('p' + '-' + '[0-9a-f]{16}')
OPAQUE_PROMPT_ID = re.compile(r'^p[0-9]{3}$')
BANNED_ID_COLUMNS = {'source_id', 'source_record', 'source_row', 'source_category', 'record', 'row', 'rows',
                     'row_number', 'line', 'line_number', 'behaviorid', 'behavior_id', 'internal_prompt_id'}
BLIND_COLUMNS = ['item', 'group', 'qwen3guard_safety', 'harmbench_label_mac', 'rating', 'garbled']


def check_ids(root):
    bad = []
    n_ids = 0
    for f in all_files(root):
        try:
            text = open(os.path.join(root, f), encoding='utf-8').read()
        except UnicodeDecodeError:
            continue                                   # the secret scan reports non-text files
        hits = INTERNAL_PROMPT_ID.findall(text)
        if hits:
            bad.append(f'{f}: {len(hits)} internal prompt id(s)')
        if f.endswith('.csv'):
            rows = list(csv.reader(text.splitlines()))
            header = [h.strip().lower() for h in rows[0]] if rows else []
            for h in header:
                if h in BANNED_ID_COLUMNS:
                    bad.append(f'{f}: column {h!r} would locate a prompt in its source')
            if 'prompt_id' in header:
                i = header.index('prompt_id')
                for r in rows[1:]:
                    n_ids += 1
                    if i >= len(r) or not OPAQUE_PROMPT_ID.match(r[i]):
                        bad.append(f'{f}: a prompt_id is not an opaque id p001-p300')
                        break
    with open(os.path.join(root, 'labels', 'blind_read.csv'), newline='', encoding='utf-8') as fh:
        header = next(csv.reader(fh), [])
    if header != BLIND_COLUMNS:
        bad.append(f'labels/blind_read.csv has columns {header}, not {BLIND_COLUMNS}')
    detail = (f'no internal prompt ids; {n_ids} prompt_id values checked against p001-p300; no source-row or '
              f'source-id columns; blind_read.csv columns; problems {len(bad)}')
    if bad:
        detail += ': ' + '; '.join(bad[:10])
    return not bad, detail


def check_consistency(root):
    """The label files agree with each other: every unit has the same 200 harm prompts (p001-p200,
    4 answers each) and 100 over-refusal prompts (p201-p300); the per-source counts add up to them;
    the opening counts add up to the Qwen3Guard labels; units.csv names the units of the labels."""
    def rd(*parts):
        with open(os.path.join(root, *parts), newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    answers = rd('labels', 'answers.csv')
    over = rd('labels', 'overrefusal.csv')
    units = [u['unit'] for u in rd('labels', 'units.csv')]
    sources = rd('labels', 'sources.csv')
    harm_ids = {f'p{i:03d}' for i in range(1, 201)}
    over_ids = {f'p{i:03d}' for i in range(201, 301)}
    bad = []
    if sorted({a['unit'] for a in answers}) != sorted(units) or sorted({a['unit'] for a in over}) != sorted(units):
        bad.append('units.csv and the label files name different units')
    per_unit = {}
    for a in answers:
        per_unit.setdefault(a['unit'], {}).setdefault(a['prompt_id'], []).append(a['sample_index'])
    for u, prompts in per_unit.items():
        if set(prompts) != harm_ids or any(sorted(v) != ['0', '1', '2', 'greedy'] for v in prompts.values()):
            bad.append(f'{u}: not the 200 harm prompts p001-p200 with answers 0, 1, 2 and greedy')
    per_unit = {}
    for a in over:
        per_unit.setdefault(a['unit'], []).append(a['prompt_id'])
    for u, prompts in per_unit.items():
        if sorted(prompts) != sorted(over_ids):
            bad.append(f'{u}: not the 100 over-refusal prompts p201-p300')
    harm_n = sum(int(r['development_prompts']) for r in sources if r['kind'] == 'harm')
    over_n = sum(int(r['development_prompts']) for r in sources if r['kind'] == 'overrefusal')
    if (harm_n, over_n) != (200, 100):
        bad.append(f'labels/sources.csv counts {harm_n} harm and {over_n} over-refusal prompts, not 200 and 100')
    counts = {}
    for a in answers:
        part = 'greedy' if a['sample_index'] == 'greedy' else 'sampled'
        lab = a['qwen3guard_safety'] if a['qwen3guard_valid'] == 'true' else 'Invalid'
        counts[(a['unit'], part, lab)] = counts.get((a['unit'], part, lab), 0) + 1
    xt = {}
    for r in rd('labels', 'openings.csv'):
        key = (r['unit'], r['answer_set'], r['qwen3guard'])
        xt[key] = xt.get(key, 0) + int(r['count'])
    for (u, part, lab), n in xt.items():
        if counts.get((u, part, lab), 0) != n:
            bad.append(f'openings.csv {u} {part} {lab}: {n} against {counts.get((u, part, lab), 0)} in answers.csv')
    detail = (f'{len(units)} units with prompts p001-p200 and p201-p300; per-source counts {harm_n} + {over_n}; '
              f'{len(xt)} opening totals against answers.csv; problems {len(bad)}')
    if bad:
        detail += ': ' + '; '.join(bad[:10])
    return not bad, detail


def main(argv=None):
    ap = argparse.ArgumentParser(description='Check the release.')
    ap.add_argument('--root', default=HERE)
    ap.add_argument('--no-manifest', action='store_true', help='skip the manifest check (used while building)')
    ap.add_argument('--json', action='store_true', help='print a JSON summary instead of text')
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    checks, extra = {}, {}
    if not args.no_manifest:
        ok, d = check_manifest(root)
        checks['manifest'] = {'ok': ok, 'detail': d}
    ok, d, _hits = check_secrets(root)
    checks['secret_scan'] = {'ok': ok, 'detail': d}
    ok, d, long_config = check_text(root)
    checks['text_scan'] = {'ok': ok, 'detail': d}
    extra['long_config_strings'] = long_config
    ok, d = check_configs(root)
    checks['configs'] = {'ok': ok, 'detail': d}
    ok, d = check_ids(root)
    checks['ids'] = {'ok': ok, 'detail': d}
    ok, d = check_consistency(root)
    checks['consistency'] = {'ok': ok, 'detail': d}
    tmp = tempfile.mkdtemp(prefix='release-check-')
    try:
        ok, d = check_recompute(root, tmp)
        checks['recompute'] = {'ok': ok, 'detail': d}
        if os.path.exists(os.path.join(tmp, 'comparison.csv')):
            ok, d, comp = check_paper_numbers(tmp)
            checks['paper_numbers'] = {'ok': ok, 'detail': d}
            extra['comparison'] = comp
            ok, d = check_figures(root, tmp)
            checks['figure_data'] = {'ok': ok, 'detail': d}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    all_ok = all(c['ok'] for c in checks.values())
    if args.json:
        print(json.dumps({'ok': all_ok, 'checks': checks, **extra}, indent=1, sort_keys=True))
    else:
        for name, c in checks.items():
            print(f'{name:14s} {"PASS" if c["ok"] else "FAIL"}  {c["detail"]}')
        for m in extra.get('comparison', {}).get('mismatches', []):
            print(f'  mismatch: {m["key"]}: printed {m["printed"]}, recomputed {m["recomputed"]}')
        print('ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAIL')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
