import json, subprocess, sys
MAIN="/Users/spiderishi/Coding/attribution"
def walk(o, path, toks, out):
    if isinstance(o, dict):
        for k,v in o.items(): walk(v, path+"."+str(k), toks, out)
    elif isinstance(o, list):
        for i,v in enumerate(o): walk(v, path+"[%d]"%i, toks, out)
    elif isinstance(o, str):
        for t in toks:
            if t in o: out.append((t, path, len(o)))
for spec in sys.argv[1:]:
    f, toks = spec.split("=",1)
    toks = toks.split(",")
    data = subprocess.run(["git","-C",MAIN,"show","HEAD:"+f],capture_output=True,check=True).stdout
    out=[]
    walk(json.loads(data), "$", toks, out)
    for t,p,n in out[:12]:
        print(f.split("/")[-1], t[:12], p, "(str len %d)"%n)
