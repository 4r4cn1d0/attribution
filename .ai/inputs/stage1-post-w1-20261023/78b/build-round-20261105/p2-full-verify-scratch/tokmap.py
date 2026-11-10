import re, sys, os
from collections import defaultdict
HERE=os.path.dirname(os.path.abspath(__file__))
full=[l.rstrip("\n").split("\t") for l in open(os.path.join(HERE,"pool.tsv"))]
tok_re=re.compile(r"(?<![0-9a-fA-F])([0-9a-f]{64}|[0-9a-f]{7,63}(?=…)|[0-9a-f]{7}(?=`))")
seen={}
for i,ln in enumerate(open(sys.argv[1],encoding="utf-8").read().split("\n"),1):
    for m in tok_re.finditer(ln):
        t=m.group(1)
        if not re.search(r"[a-f]",t) and len(t)<12: continue
        seen.setdefault(t,[]).append(i)
for t,ls in seen.items():
    hits=sorted({s+":"+p for h,s,p in full if h.startswith(t)})
    if hits:
        print(t[:16], ls[:6], "|", "; ".join(x.replace(".ai/inputs/stage1-post-w1-20261023/78b/build-round-20261105/","BR/") for x in hits[:3]), ("(+%d)"%(len(hits)-3) if len(hits)>3 else ""))
