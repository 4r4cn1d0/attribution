import json, subprocess
MAIN="/Users/spiderishi/Coding/attribution"
d=json.loads(subprocess.run(["git","-C",MAIN,"show","HEAD:.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json"],capture_output=True,check=True).stdout)
print("sealed.dir", d["parity"]["sealed"]["dir"]); print("stage1.dir", d["parity"]["stage1_r_draws"]["dir"])
for k in ("sealed","stage1_r_draws"):
    for name,v in list(d["parity"][k]["files"].items())[:2]:
        print(k, name, {a:(b[:12] if isinstance(b,str) else b) for a,b in v.items()})
f0=d["files"][0]; print("files[0] keys", sorted(f0))
print("membership_check keys", sorted(d["membership_check"]) if isinstance(d["membership_check"],dict) else d["membership_check"])
print("serves", d["serves"] if not isinstance(d["serves"],(dict,list)) else (sorted(d["serves"]) if isinstance(d["serves"],dict) else d["serves"]))
