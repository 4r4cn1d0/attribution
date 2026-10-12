"""Administrative collector: stage whole verified backups, then call unchanged frozen reader."""
from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,subprocess,time
from prefetch_sealed import verify
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
temporary=root.with_name('combined.partial-'+str(time.time_ns()))
temporary.mkdir()
def copy(src,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 try:os.link(src,dest)
 except OSError:shutil.copy2(src,dest)
records={};provenance={}
for model,s in p['hosts'].items():
 kit=Path(s['kit_path']);tree=kit/'retrieved'/s['host']/'tree'
 cache=root.parent/'prefetch'/model
 records[model]=json.loads((kit/'operator/finished.json').read_text())
 if (cache/'finished.json').exists():records[model]['incremental_backup']=json.loads((cache/'finished.json').read_text())
 hashes={};sources={};rejected=[]
 for unit in [u for u in p['units'] if u['model']==model]:
  candidates=[tree/unit['run_dir'],cache/f'unit-{unit["arm"]}'/unit['run_dir']]
  valid=[]
  for candidate in candidates:
   if not candidate.is_dir():continue
   try:valid.append((candidate,verify(candidate,unit,p)))
   except (Exception,SystemExit) as exc:rejected.append({'source':str(candidate),'error_type':type(exc).__name__})
  assert valid,f'no complete verified backup for {model}/{unit["arm"]}'
  assert len({digest for _,digest in valid})==1,'conflicting complete unit backups'
  src,digest=valid[0];dest=temporary/unit['run_dir']
  shutil.copytree(src,dest,copy_function=copy)
  assert verify(dest,unit,p)==digest
  hashes[unit['arm']]=digest;sources[unit['arm']]={'source':str(src),'complete_sha256':digest}
 receipts=[]
 for source in [tree/f'cause/{model}-BATCH-DONE.json',cache/f'{model}-BATCH-DONE.json']:
  if not source.is_file():continue
  try:
   b=json.loads(source.read_text())
   assert b['protocol_sha256']==expected and b['engine_sha256']==p['engine_sha256'] and b['model']==model and b['ok'] is True
   assert len(b['units'])==3 and {e['arm'] for e in b['units']}==set(hashes)
   specs={u['arm']:u for u in p['units'] if u['model']==model}
   for entry in b['units']:
    assert entry['seed']==specs[entry['arm']]['seed'] and entry['run_dir']==specs[entry['arm']]['run_dir']
    assert entry['status']=='complete_verified' and entry['complete_sha256']==hashes[entry['arm']]
    assert all(entry[k]==0 for k in ('make_exit','run_exit','verify_exit'))
   receipts.append((source,sha(source)))
  except (Exception,SystemExit) as exc:rejected.append({'source':str(source),'error_type':type(exc).__name__})
 assert receipts,f'no successful matching batch receipt for {model}'
 assert len({digest for _,digest in receipts})==1,'conflicting batch receipts'
 receipt,digest=receipts[0];copy(receipt,temporary/f'cause/{model}-BATCH-DONE.json')
 assert sha(temporary/f'cause/{model}-BATCH-DONE.json')==digest
 provenance[model]={'units':sources,'batch_source':str(receipt),'batch_sha256':digest,'rejected_incomplete_sources':rejected}
(temporary/'operator-results.json').write_text(json.dumps(records,indent=2)+'\n')
(temporary/'backup-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
assert sha(protocol)==expected
assert sha(R/'scripts/side_project_cause/analyze.py')==p['implementation_hashes']['analyze.py']
temporary.rename(root)
result=subprocess.run(['python3.11','-B',str(R/'scripts/side_project_cause/analyze.py'),
 '--protocol',str(protocol),'--root',str(root),'--out',str(root.parent/'analysis.json')],check=False)
(root.parent/'finalize-result.json').write_text(json.dumps({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'protocol_sha256':expected,'analysis_exit':result.returncode,'report':str(root.parent/'analysis.json')},indent=2)+'\n')
raise SystemExit(result.returncode)
