"""One-shot administrative collection: wait for operators, stage declared files, run frozen reader."""
from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,subprocess,time
R=Path('/Users/spiderishi/Coding/attribution')
protocol=R/'research/side-notes/causal-study-20261012/protocol.json'
expected='084d5543f622b8f24896f6518ac45af41450043f30ae1e32866dece5b27c7c38'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
assert sha(protocol)==expected
p=json.loads(protocol.read_text())
assert sha(R/'scripts/side_project_cause/analyze.py')==p['implementation_hashes']['analyze.py']
end=time.monotonic()+8*3600
while time.monotonic()<end:
 if all((Path(s['kit_path'])/'operator/finished.json').is_file() for s in p['hosts'].values()):break
 time.sleep(30)
else:
 raise SystemExit('operator completion wait ended after8h; hard pod caps remain governing; inspect receipts')
root=R/'tmp/cause-study-20261012/combined'
assert not root.exists(),'collection root never replaced'
root.mkdir()
def copy(src,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 try:os.link(src,dest)
 except OSError:shutil.copy2(src,dest)
records={}
for model,s in p['hosts'].items():
 kit=Path(s['kit_path']);tree=kit/'retrieved'/s['host']/'tree'
 records[model]=json.loads((kit/'operator/finished.json').read_text())
 for unit in [u for u in p['units'] if u['model']==model]:
  src=tree/unit['run_dir'];dest=root/unit['run_dir']
  if src.is_dir():shutil.copytree(src,dest,copy_function=copy)
 receipt=tree/f'cause/{model}-BATCH-DONE.json'
 if receipt.is_file():copy(receipt,root/f'cause/{model}-BATCH-DONE.json')
(root/'operator-results.json').write_text(json.dumps(records,indent=2)+'\n')
assert sha(protocol)==expected
assert sha(R/'scripts/side_project_cause/analyze.py')==p['implementation_hashes']['analyze.py']
result=subprocess.run(['python3.11','-B',str(R/'scripts/side_project_cause/analyze.py'),
 '--protocol',str(protocol),'--root',str(root),'--out',str(root.parent/'analysis.json')],check=False)
(root.parent/'finalize-result.json').write_text(json.dumps({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'protocol_sha256':expected,'analysis_exit':result.returncode,'report':str(root.parent/'analysis.json')},indent=2)+'\n')
raise SystemExit(result.returncode)
