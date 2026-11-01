"""Early verified backup of the same six sealed units; no launch/train/lease or outcome selection. Stops only after full batch backup."""
from pathlib import Path
import argparse,datetime as dt,fcntl,hashlib,importlib,json,os,signal,subprocess,sys,tarfile,time
R=Path('/Users/spiderishi/Coding/attribution')
P=R/'research/side-notes/causal-study-20261012/protocol.json'
PIN='084d5543f622b8f24896f6518ac45af41450043f30ae1e32866dece5b27c7c38'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(8*1024*1024),b''):h.update(c)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def verify(folder,spec,protocol):
 c=load(folder/'COMPLETE.json');assert c['complete'] is True
 assert c['identity']['recipe_sha256']==spec['config_sha256']
 assert c['identity']['code_sha256']==protocol['engine_sha256']
 assert c['identity']['manifest_sha256']==protocol['prepared_manifest_sha256']
 j=load(folder/'job.json');assert j['seed']==spec['seed'] and j['target_checkpoint']=='e1'
 assert j['kind']=='run-one' and j['arm']=='a0' and j['split']==j['evaluate_bank']=='dev' and j['role']=='development'
 assert j['recipe_sha256']==spec['config_sha256'] and j['code_sha256']==protocol['engine_sha256'] and j['manifest_sha256']==protocol['prepared_manifest_sha256']
 assert j.get('resume_from') is None and c['job_sha256']==sha(folder/'job.json')
 assert isinstance(c['files'],dict) and c['files'] and c['files'].get('job.json')==c['job_sha256']
 for name,digest in c['files'].items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
  assert (folder/rel).resolve().is_relative_to(folder.resolve())
  assert not (folder/rel).is_symlink() and sha(folder/rel)==digest,name
 return sha(folder/'COMPLETE.json')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['olmo1b','olmo7b'],required=True);a=parser.parse_args()
 assert sha(P)==PIN
 p=load(P);s=p['hosts'][a.model];kit=Path(s['kit_path']);sys.path.insert(0,str(kit));h=importlib.import_module('host')
 host=s['host'];out=R/'tmp/cause-study-20261012/prefetch'/a.model;out.mkdir(parents=True,exist_ok=True)
 lock=(out/'prefetch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 pod_id=h.state(host)['id']
 def remaining():
  state=h.state(host);assert state['id']==pod_id
  return (dt.datetime.fromisoformat(state['cap_stop_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
 def read_remote(command,output=None):
  assert remaining()>60
  argv=['ssh',*h.ssh_base(host),command]
  left=remaining();assert left>30
  process=subprocess.Popen(argv,stdout=output if output is not None else subprocess.PIPE,stderr=subprocess.PIPE,env=h.clean_env(),start_new_session=True)
  try:
   raw,err=process.communicate(timeout=max(1,left-30))
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.communicate(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.communicate()
   raise RuntimeError('transfer reached existing pod deadline')
  return process.returncode,raw
 def event(kind,**kw):
  d={'utc':stamp(),'model':a.model,'event':kind,**kw}
  with (out/'events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
  print(json.dumps(d),flush=True)
 pending=[u for u in p['units'] if u['model']==a.model]
 verified={}
 try:
  while pending:
   if remaining()<=60:raise RuntimeError('existing pod deadline reached; no new lease or restart')
   for u in list(pending):
    remote=h.REMOTE_ROOT+'/'+u['run_dir']
    code,_=read_remote(f'test -f {remote}/COMPLETE.json')
    if code:continue
    archive=out/f"{u['arm']}.tar.gz";part=archive.with_suffix('.gz.part')
    if not archive.exists():
     command=f'cd {h.REMOTE_ROOT} && set -o pipefail && tar -cf - {u["run_dir"]} | gzip -1'
     with part.open('wb') as f:
      code,_=read_remote(command,output=f)
     if code:raise RuntimeError('sealed unit transfer failed')
     part.rename(archive)
    staging=out/f'unit-{u["arm"]}'
    if not staging.exists():
     temporary=out/f'unit-{u["arm"]}.partial-{time.time_ns()}'
     temporary.mkdir()
     with tarfile.open(archive) as t:t.extractall(temporary,filter='data')
     verify(temporary/u['run_dir'],u,p)
     temporary.rename(staging)
    unit=staging/u['run_dir'];sealed=verify(unit,u,p)
    event('unit-backup-verified',arm=u['arm'],run_dir=u['run_dir'],complete_sha256=sealed,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,unit_path=str(unit))
    verified[u['arm']]=sealed
    archive.unlink()  # Owned transfer intermediate; all sealed files remain verified in staging.
    pending.remove(u)
   if pending:
    if remaining()<=60:raise RuntimeError('existing deadline before next poll')
    time.sleep(min(30,max(1,remaining()-30)))
  # Full-batch identity remains required by the frozen reader; no partial release.
  for _ in range(10):
   local=out/f'{a.model}-BATCH-DONE.json'
   code,raw=read_remote(f'cat {h.REMOTE_ROOT}/cause/{a.model}-BATCH-DONE.json')
   if code==0:
    b=json.loads(raw);local.write_bytes(raw);assert b['protocol_sha256']==PIN and b['engine_sha256']==p['engine_sha256'] and b['model']==a.model
    assert b['ok'] is True and len(b['units'])==3
    assert {e['arm'] for e in b['units']}==set(verified)=={'A','C','D'}
    specs={u['arm']:u for u in p['units'] if u['model']==a.model}
    for entry in b['units']:
     assert entry['seed']==specs[entry['arm']]['seed'] and entry['run_dir']==specs[entry['arm']]['run_dir']
     assert all(entry[k]==0 for k in ('make_exit','run_exit','verify_exit'))
     assert entry['status']=='complete_verified' and entry['complete_sha256']==verified[entry['arm']]
    event('batch-receipt-backed-up',batch_ok=True);break
   if remaining()<=60:raise RuntimeError('existing deadline before receipt retry')
   time.sleep(min(15,max(1,remaining()-30)))
  else:raise RuntimeError('batch receipt not yet fetched')
  result=h.stop(host)
  assert result['confirmed'] is True
  event('verified-backup-stop-confirmed',stop=result)
  (out/'finished.json').write_text(json.dumps({'utc':stamp(),'protocol_sha256':PIN,'model':a.model,'complete_sha256_by_arm':verified,'stop':result},indent=2)+'\n')
  event('prefetch-finished')
 except (Exception,SystemExit) as exc:
  event('prefetch-failed',error_type=type(exc).__name__)
  return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
