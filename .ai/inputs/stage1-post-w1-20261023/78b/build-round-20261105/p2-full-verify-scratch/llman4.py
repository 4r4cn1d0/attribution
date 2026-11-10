import json, subprocess, hashlib
MAIN="/Users/spiderishi/Coding/attribution"; base=".ai/inputs/scale-78b-sealed-llama3-20261105/out/"
d=json.loads(subprocess.run(["git","-C",MAIN,"show","HEAD:"+base+"MANIFEST.json"],capture_output=True,check=True).stdout)
ok=bad=0
for f in d["files"]:
    data=subprocess.run(["git","-C",MAIN,"show","HEAD:"+base+f["path"]],capture_output=True,check=True).stdout
    if hashlib.sha256(data).hexdigest()==f["sha256"]: ok+=1
    else: bad+=1; print("DIFF", f["path"])
print("manifest entries", len(d["files"]), "ok", ok, "bad", bad, "seeds R:", [(f["path"].split("/")[-1], f.get("seed")) for f in d["files"] if f["path"].split("/")[-1].startswith("R_d")][:16])
