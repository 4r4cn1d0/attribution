"""Print only metadata of plan.json (no outputs, reasons or COMPLETE fields): B14 cells' job records."""
import json, re, sys, hashlib, collections
path = sys.argv[1]
data = open(path, 'rb').read()
plan = json.loads(data)
print('plan.json sha256', hashlib.sha256(data).hexdigest(), 'bytes', len(data))
print('top keys', sorted(plan))
print('plan_ab code', (plan['records'].get('plan_ab') or {}).get('code'))
print('seals blocks', sorted(plan.get('seals') or {}))
print('engines', plan.get('engines'))
for p, r in sorted((plan.get('recipes') or {}).items()):
    print('recipe', p.split('/')[-1], {k: (v if k != 'sha256' else v[:8]) for k, v in r.items()})
mask = lambda s: re.sub(r'[0-9a-f]{16,}', 'H', s) if isinstance(s, str) else s
cnt = collections.Counter()
roles = collections.Counter()
B14 = {'a0', 'S1', 'S3', 'S4'}
rows = []
for host, h in sorted(plan['hosts'].items()):
    for i, j in enumerate(h.get('jobs') or []):
        cnt[(j.get('kind'), j.get('recipe'), j.get('engine'))] += 1
        if j.get('role') is not None:
            roles[(j.get('kind'), j.get('role'), j.get('status'))] += 1
        if j.get('kind') in ('arm', 'a0_arm') and j.get('arm') in B14 and isinstance(j.get('seed'), int) and 1101 <= j['seed'] <= 1107:
            e = j.get('edit')
            rows.append((j['arm'], j['seed'], host, h.get('block'), h.get('done'), i, j.get('kind'), j.get('status'),
                         j.get('pulled', '-'), j.get('role'), j.get('recipe'), j.get('engine'), j.get('deferred_from'),
                         (e.get('sha256') or '')[:8] if isinstance(e, dict) else e,
                         ('engine_arm' in e) if isinstance(e, dict) else None, mask(j.get('unit'))))
print('kind/recipe/engine counts', sorted(cnt.items(), key=str))
print('roles', dict(roles))
for r in sorted(rows, key=lambda r: (r[0], r[1], r[2])):
    print(r)
# other kinds whose arm field is a0 / S1/S3/S4 at the B14 seeds
others = collections.Counter()
for host, h in plan['hosts'].items():
    for i, j in enumerate(h.get('jobs') or []):
        if j.get('kind') not in ('arm', 'a0_arm') and j.get('arm') in B14 and j.get('seed') in range(1102, 1108):
            others[(j.get('kind'), j.get('arm'), h.get('block'), j.get('status'))] += 1
print('other kinds at B14 cells', sorted(others.items(), key=str))
print('hosts', [(n, h.get('block'), h.get('done'), len(h.get('jobs') or [])) for n, h in sorted(plan['hosts'].items())])
