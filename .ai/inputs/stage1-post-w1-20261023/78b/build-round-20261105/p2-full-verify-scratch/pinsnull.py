import json, sys
d=json.load(open(sys.argv[1]))
def walk(o,p,out):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,p+"."+k,out)
    elif o is None: out.append(p)
for fam,v in d["families"].items():
    out=[]; walk(v,"",out); print(fam, len(out), out)
print("shared l1_first_block", d.get("shared",{}).get("l1_first_block"))
