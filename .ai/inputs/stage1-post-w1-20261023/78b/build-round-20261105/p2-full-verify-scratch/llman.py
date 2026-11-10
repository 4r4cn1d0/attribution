import json, subprocess
MAIN="/Users/spiderishi/Coding/attribution"
d=json.loads(subprocess.run(["git","-C",MAIN,"show","HEAD:.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json"],capture_output=True,check=True).stdout)
print("top keys", sorted(d))
files=d["files"]; print("n files", len(files))
names=[f.get("path") or f.get("name") for f in files]; print("names", [n.split("/")[-1][:14] for n in names])
print("seed_map", d.get("seed_map") if not isinstance(d.get("seed_map"),dict) else {k:v for k,v in list(d["seed_map"].items())[:20]})
p=d.get("parity",{}); print("parity keys", sorted(p))
for k,v in p.items():
    if isinstance(v,dict):
        print(k, "subkeys", sorted(v)[:8])
        for kk,vv in v.items():
            if isinstance(vv,dict): print("  ",kk, {a:b for a,b in vv.items() if isinstance(b,(bool,int)) or a in ("manifest_sha256","record_sha256")})
            elif isinstance(vv,(bool,int)) or (isinstance(vv,str) and len(vv)==64): print("  ",kk, vv if not isinstance(vv,str) else vv[:12])
    elif isinstance(v,list):
        print(k, "list", len(v))
        for e in v[:12]:
            if isinstance(e,dict): print("  ", {a:(b if not isinstance(b,str) else b[:16]) for a,b in e.items() if a in ("name","path","draw","byte_identical","remove_list_equal","equal")})
