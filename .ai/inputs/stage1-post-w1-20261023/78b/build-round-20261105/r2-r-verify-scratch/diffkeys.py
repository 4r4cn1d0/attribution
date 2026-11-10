import json, sys, hashlib
def flat(d, pre=''):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, pre + k + '.'))
        if not d: out[pre[:-1]] = '{}'
    else:
        out[pre[:-1]] = d
    return out
def show(v):
    if isinstance(v, str):
        if len(v) in (40, 64) and all(c in '0123456789abcdef' for c in v): return v[:12]
        return f'<text {len(v)}B sha {hashlib.sha256(v.encode()).hexdigest()[:8]}>'
    if isinstance(v, list):
        if all(isinstance(x,(int,float)) for x in v): return v
        if all(isinstance(x,str) and len(x)<=40 and ' ' not in x for x in v): return v
        return f'<list {len(v)}>'
    return v
a = flat(json.load(open(sys.argv[1]))); b = flat(json.load(open(sys.argv[2])))
for k in sorted(set(a) | set(b)):
    va, vb = a.get(k, '<absent>'), b.get(k, '<absent>')
    if va != vb:
        print(k, '|', show(va), '->', show(vb))
