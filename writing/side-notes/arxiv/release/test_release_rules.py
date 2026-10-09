#!/usr/bin/env python3
"""Negative tests for the release rules of 10 Oct 2026: opaque prompt ids, redacted
configurations, and the six blind-read columns.

    python3 -B -I test_release_rules.py --release REL --scratch DIR --main-root M

REL is a built release (read only). DIR is a scratch folder; the tests write only into
DIR/release-rule-tests/, which they create fresh. M is the main checkout (read only), for the
original configurations.

Part A (builder functions, with the 13 original configurations): the redaction changes only the
top-level "purpose"; the differ-only-in-purpose check rejects a copy with any other changed byte,
a copy whose "purpose" is not the fixed sentence, and an unredacted copy; the redaction refuses a
configuration without a top-level "purpose", with two of them, or with a non-string one.

Part B (release checker): an unchanged copy of the release passes. Then, one case at a time, a
fresh copy breaks one rule (with its MANIFEST.sha256 line updated, so the manifest check cannot
be what catches it), and the check that guards that rule must fail.

Exit status 0 only if every test behaves as expected. Prints counts and check names only.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))


def load_builder():
    spec = importlib.util.spec_from_file_location('build_release', os.path.join(HERE, 'build_release.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# ----------------------------------------------------------------------------- part A
def part_a(BR, main_root):
    results = []

    def expect(name, cond):
        results.append((name, bool(cond)))

    def refuses(raw):
        try:
            BR.redact_purpose(raw)
        except SystemExit:
            return True
        return False

    for name, *_rest in BR.CONFIGS:
        original = open(os.path.join(main_root, BR.CONFIG_DIR, name), 'rb').read()
        red = BR.redact_purpose(original)
        ok, _why = BR.only_purpose_differs(original, red)
        expect(f'A1 redaction differs only in purpose: {name}', ok)
        # A2: one more byte changed outside "purpose" (a space before the final brace).
        k = red.rstrip().rfind(b'}')
        tampered = red[:k] + b' ' + red[k:]
        expect(f'A2 extra byte outside purpose is rejected: {name}', not BR.only_purpose_differs(original, tampered)[0])
        # A3: a setting changed (the LoRA rank) is rejected.
        changed = re.sub(rb'("r": )(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1).encode(), red, count=1)
        expect(f'A3 changed setting is rejected: {name}', changed != red and
               not BR.only_purpose_differs(original, changed)[0])
        # A4: "purpose" replaced by another sentence is rejected.
        other = red.replace(json.dumps(BR.PURPOSE_REDACTED).encode(), json.dumps('Another sentence.').encode())
        expect(f'A4 other purpose sentence is rejected: {name}', not BR.only_purpose_differs(original, other)[0])
        # A5: an unredacted copy is rejected.
        expect(f'A5 unredacted copy is rejected: {name}', not BR.only_purpose_differs(original, original)[0])
    # A6-A8: the redaction refuses malformed configurations.
    expect('A6 no top-level purpose is refused', refuses(b'{"kind": "x", "model": {"purpose": "nested"}}\n'))
    expect('A7 two top-level purposes are refused', refuses(b'{"purpose": "a", "kind": "x", "purpose": "b"}\n'))
    expect('A8 a non-string purpose is refused', refuses(b'{"purpose": 3, "kind": "x"}\n'))
    expect('A9 a well-formed purpose is redacted', not refuses(b'{"kind": "x", "purpose": "notes"}\n'))
    return results


# ----------------------------------------------------------------------------- part B
def run_checker(root, tmp):
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'TMPDIR': tmp, 'PYTHONDONTWRITEBYTECODE': '1'}
    p = subprocess.run([sys.executable, '-B', '-I', os.path.join(root, 'check_release.py'), '--root', root, '--json'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    try:
        summary = json.loads(p.stdout)
    except ValueError:
        return p.returncode, {}
    return p.returncode, {k: v['ok'] for k, v in summary['checks'].items()}


def set_manifest(root, rel):
    """Rewrite the MANIFEST.sha256 line of rel with its current SHA-256."""
    path = os.path.join(root, 'MANIFEST.sha256')
    lines = open(path, encoding='utf-8').read().splitlines()
    digest = sha256_bytes(open(os.path.join(root, rel), 'rb').read())
    out, seen = [], False
    for ln in lines:
        if ln.endswith('  ' + rel):
            out.append(f'{digest}  {rel}')
            seen = True
        else:
            out.append(ln)
    if not seen:
        out.append(f'{digest}  {rel}')
        out.sort(key=lambda x: x.split('  ', 1)[1])
    open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')


def edit_csv(root, rel, fn):
    path = os.path.join(root, rel)
    rows = list(csv.reader(open(path, newline='', encoding='utf-8')))
    rows = fn(rows)
    buf = io.StringIO()
    csv.writer(buf, lineterminator='\n').writerows(rows)
    open(path, 'w', encoding='utf-8', newline='').write(buf.getvalue())
    set_manifest(root, rel)


def first_config(root):
    rows = list(csv.DictReader(open(os.path.join(root, 'configs', 'SHA256SUMS.csv'), newline='', encoding='utf-8')))
    return rows[0]['config_file']


def set_sums(root, name, BR):
    """Give configs/SHA256SUMS.csv the current redacted hashes of a configuration file."""
    data = open(os.path.join(root, 'configs', name), 'rb').read()
    canon = BR.canonical_sha256(json.loads(data.decode('utf-8')))

    def fn(rows):
        h = rows[0]
        for r in rows[1:]:
            if r[0] == name:
                r[h.index('redacted_file_sha256')] = sha256_bytes(data)
                r[h.index('redacted_canonical_json_sha256')] = canon
        return rows
    edit_csv(root, 'configs/SHA256SUMS.csv', fn)


def cases(BR, main_root):
    """(name, the check that must fail, function that breaks the rule in a copy)."""
    def col(rows, name):
        return rows[0].index(name)

    def b1(root):            # an internal-style prompt id in answers.csv
        def fn(rows):
            rows[1][col(rows, 'prompt_id')] = 'p-' + '0123456789abcdef'
            return rows
        edit_csv(root, 'labels/answers.csv', fn)

    def b2(root):            # a prompt id that is not p001-p300
        def fn(rows):
            rows[1][col(rows, 'prompt_id')] = 'q017'
            return rows
        edit_csv(root, 'labels/answers.csv', fn)

    def b3(root):            # blind_read.csv regains a prompt_id column
        def fn(rows):
            return [r + (['prompt_id'] if i == 0 else ['p001']) for i, r in enumerate(rows)]
        edit_csv(root, 'labels/blind_read.csv', fn)

    def b4(root):            # blind_read.csv regains a unit column
        def fn(rows):
            return [r + (['unit'] if i == 0 else ['olmo2-1b_untuned']) for i, r in enumerate(rows)]
        edit_csv(root, 'labels/blind_read.csv', fn)

    def b5(root):            # sources.csv gains a per-row column
        def fn(rows):
            return [r + (['source_record'] if i == 0 else [str(i)]) for i, r in enumerate(rows)]
        edit_csv(root, 'labels/sources.csv', fn)

    def b6(root):            # an internal-style prompt id in README text
        path = os.path.join(root, 'README.md')
        open(path, 'a', encoding='utf-8').write('\nexample p-' + '00112233445566aa\n')
        set_manifest(root, 'README.md')

    def b7(root):            # a configuration byte changed outside "purpose"
        name = first_config(root)
        path = os.path.join(root, 'configs', name)
        data = open(path, 'rb').read()
        k = data.rstrip().rfind(b'}')
        open(path, 'wb').write(data[:k] + b' ' + data[k:])
        set_manifest(root, f'configs/{name}')

    def b8(root):            # "purpose" is another sentence, with matching hashes
        name = first_config(root)
        path = os.path.join(root, 'configs', name)
        data = open(path, 'rb').read()
        data = data.replace(json.dumps(BR.PURPOSE_REDACTED).encode(), json.dumps('Another sentence.').encode())
        open(path, 'wb').write(data)
        set_sums(root, name, BR)
        set_manifest(root, f'configs/{name}')

    def b9(root):            # the original, unredacted configuration put back, with matching hashes
        name = first_config(root)
        original = open(os.path.join(main_root, BR.CONFIG_DIR, name), 'rb').read()
        open(os.path.join(root, 'configs', name), 'wb').write(original)
        set_sums(root, name, BR)
        set_manifest(root, f'configs/{name}')

    def b10(root):           # an over-refusal answer moved to a harm prompt id
        def fn(rows):
            rows[1][col(rows, 'prompt_id')] = 'p001'
            return rows
        edit_csv(root, 'labels/overrefusal.csv', fn)

    def b11(root):           # a per-source count changed
        def fn(rows):
            i = col(rows, 'development_prompts')
            rows[1][i] = str(int(rows[1][i]) + 1)
            return rows
        edit_csv(root, 'labels/sources.csv', fn)

    return [('B1 internal prompt id in answers.csv', 'ids', b1),
            ('B2 non-opaque prompt id in answers.csv', 'ids', b2),
            ('B3 prompt_id column in blind_read.csv', 'ids', b3),
            ('B4 unit column in blind_read.csv', 'ids', b4),
            ('B5 source_record column in sources.csv', 'ids', b5),
            ('B6 internal prompt id in README.md', 'ids', b6),
            ('B7 config byte changed outside purpose', 'configs', b7),
            ('B8 config purpose not the fixed sentence', 'configs', b8),
            ('B9 unredacted original config', 'configs', b9),
            ('B10 over-refusal answer on a harm prompt id', 'consistency', b10),
            ('B11 per-source count changed', 'consistency', b11)]


def main(argv=None):
    ap = argparse.ArgumentParser(description='Negative tests for the release rules.')
    ap.add_argument('--release', required=True)
    ap.add_argument('--scratch', required=True)
    ap.add_argument('--main-root', required=True)
    args = ap.parse_args(argv)
    release = os.path.abspath(args.release)
    scratch = os.path.join(os.path.abspath(args.scratch), 'release-rule-tests')
    if scratch.startswith(release + os.sep) or scratch == release:
        raise SystemExit('the scratch folder must be outside the release')
    if os.path.exists(scratch):
        shutil.rmtree(scratch)                       # only the folder these tests create
    os.makedirs(scratch)
    tmp = os.path.join(scratch, 'tmp')
    os.makedirs(tmp)
    BR = load_builder()
    all_ok = True
    print('Part A: builder redaction rules')
    a = part_a(BR, args.main_root)
    for name, ok in a:
        if not ok:
            print(f'  FAIL  {name}')
    print(f'  {sum(ok for _n, ok in a)} of {len(a)} tests behave as expected')
    all_ok &= all(ok for _n, ok in a)
    print('Part B: release checker')
    copy = os.path.join(scratch, 'B0')
    shutil.copytree(release, copy)
    rc, checks = run_checker(copy, tmp)
    b0 = rc == 0 and checks and all(checks.values())
    print(f'  {"ok  " if b0 else "FAIL"}  B0 unchanged copy passes every check (exit {rc})')
    all_ok &= bool(b0)
    for name, target, breaker in cases(BR, args.main_root):
        copy = os.path.join(scratch, name.split()[0])
        shutil.copytree(release, copy)
        breaker(copy)
        rc, checks = run_checker(copy, tmp)
        caught = rc != 0 and checks.get(target) is False and checks.get('manifest') is True
        failing = sorted(k for k, v in checks.items() if not v)
        print(f'  {"ok  " if caught else "FAIL"}  {name}: guard "{target}" '
              f'{"fails as it must" if checks.get(target) is False else "DID NOT FAIL"}; exit {rc}; '
              f'failing checks: {", ".join(failing) or "none"}')
        all_ok &= caught
    print('ALL RULE TESTS BEHAVE AS EXPECTED' if all_ok else 'SOME RULE TESTS FAILED')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
