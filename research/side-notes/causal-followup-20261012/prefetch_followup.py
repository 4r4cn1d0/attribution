"""Early verified backup of the same six sealed units; no launch/train/lease or outcome selection. Stops only after full batch backup."""
from pathlib import Path
import shlex
import argparse,datetime as dt,fcntl,hashlib,importlib,json,os,signal,subprocess,sys,tarfile,time
R=Path('/Users/spiderishi/Coding/attribution')
P=R/'research/side-notes/causal-followup-20261012/protocol.json'
PIN=None
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
 global PIN
 parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['olmo1b','olmo7b'],required=True);parser.add_argument('--protocol-sha256',required=True);a=parser.parse_args();PIN=a.protocol_sha256
 assert sha(P)==PIN;p=load(P);spec=p['hosts'][a.model];kit=Path(spec['kit_path']);sys.path.insert(0,str(kit));h=importlib.import_module('host')
 host=spec['host'];pod_id=h.state(host)['id'];out=R/'tmp/causal-followup-20261012/prefetch'/a.model;out.mkdir(parents=True,exist_ok=True)
 lock=(out/'prefetch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def remaining():return (dt.datetime.fromisoformat(h.state(host)['cap_stop_utc'].replace('Z','+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
 def remote(command,output=None):
  left=remaining();assert left>60
  proc=subprocess.Popen(['ssh',*h.ssh_base(host),command],stdout=output if output is not None else subprocess.PIPE,stderr=subprocess.PIPE,env=h.clean_env(),start_new_session=True)
  try:raw,err=proc.communicate(timeout=max(1,left-40))
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.communicate(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.communicate()
   raise RuntimeError('transfer reached frozen cap')
  return proc.returncode,raw
 def event(kind,**kw):
  d={'utc':stamp(),'model':a.model,'event':kind,**kw}
  with (out/'events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
  print(json.dumps(d),flush=True)
 pending=[u for u in p['units'] if u['model']==a.model];verified={};terminal=None
 while remaining()>60:
  for u in list(pending):
   code,_=remote('test -f '+h.REMOTE_ROOT+'/'+u['run_dir']+'/COMPLETE.json')
   if code:continue
   archive=out/(u['arm']+'.tar.gz');part=out/(u['arm']+'.tar.gz.part')
   with part.open('wb') as f:code,_=remote('cd '+h.REMOTE_ROOT+' && set -o pipefail && tar -cf - '+u['run_dir']+' | gzip -1',f)
   assert code==0,'sealed transfer failed';part.rename(archive)
   staging=out/('unit-'+u['arm']);assert not staging.exists();staging.mkdir()
   with tarfile.open(archive) as t:t.extractall(staging,filter='data')
   digest=verify(staging/u['run_dir'],u,p);verified[u['arm']]=digest;pending.remove(u);archive.unlink();event('unit-backup-verified',arm=u['arm'],complete_sha256=digest)
  code,raw=remote('cat '+h.REMOTE_ROOT+'/cause/'+a.model+'-BATCH-DONE.json 2>/dev/null')
  if code==0:
   terminal=json.loads(raw);assert terminal['model']==a.model and terminal['protocol_sha256']==PIN and terminal['engine_sha256']==p['engine_sha256']
   assert len(terminal['units'])==len(spec['arms']) and {u['arm'] for u in terminal['units']}==set(spec['arms'])
   unfinished_backups=[entry['arm'] for entry in terminal['units'] if entry['status']=='complete_verified' and entry['arm'] not in verified]
   if unfinished_backups:
    time.sleep(min(2,max(1,remaining()-60)));continue
   for entry in terminal['units']:
    if entry['status']=='complete_verified':assert entry['complete_sha256']==verified[entry['arm']]
   if terminal['ok']:assert not pending and set(verified)==set(spec['arms'])
   (out/(a.model+'-BATCH-DONE.json')).write_bytes(raw);break
  time.sleep(min(30,max(1,remaining()-60)))
 assert terminal is not None,'terminal receipt not backed up before cap'
 # Light terminal archive retains incomplete unit evidence, configs, all logs,
 # source receipts and any partial/complete sidecar, without duplicating states.
 script="from pathlib import Path;import hashlib,json;root=Path('cause');files={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(root.rglob('*')) if q.is_file() and not (q.suffix=='.safetensors' and 'states' in q.parts) and not q.name.startswith('ARCHIVE-MANIFEST-')};Path('cause/ARCHIVE-MANIFEST-"+a.model+".json').write_text(json.dumps({'files':files},indent=2)+chr(10))"
 code,_=remote('cd '+h.REMOTE_ROOT+' && python3 -c '+shlex.quote(script));assert code==0
 code,raw=remote('cat '+h.REMOTE_ROOT+'/cause/ARCHIVE-MANIFEST-'+a.model+'.json');assert code==0;manifest=json.loads(raw)
 if terminal.get('mechanism',{}).get('status')=='complete':assert 'cause/mechanism/'+a.model+'/report.json' in manifest['files']
 archive=out/'terminal-light.tar.gz';part=out/'terminal-light.tar.gz.part'
 with part.open('wb') as f:code,_=remote("cd "+h.REMOTE_ROOT+" && set -o pipefail && tar --exclude='cause/units/*/states/*/*.safetensors' -cf - cause | gzip -1",f)
 assert code==0;part.rename(archive);light=out/'terminal-light';light.mkdir(exist_ok=False)
 with tarfile.open(archive) as t:t.extractall(light,filter='data')
 assert load(light/('cause/ARCHIVE-MANIFEST-'+a.model+'.json'))==manifest
 for name,digest in manifest['files'].items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
  q=light/rel;assert q.resolve().is_relative_to(light.resolve()) and not q.is_symlink() and sha(q)==digest,name
 assert sha(light/('cause/'+a.model+'-BATCH-DONE.json'))==sha(out/(a.model+'-BATCH-DONE.json'))
 proof={'utc':stamp(),'protocol_sha256':PIN,'host':host,'pod_id':pod_id,'verified':True,'complete_sha256_by_arm':verified,'terminal_batch_ok':terminal['ok'],'recorded_uncompleted':[u['arm'] for u in pending],'light_manifest_sha256':sha(light/('cause/ARCHIVE-MANIFEST-'+a.model+'.json')),'mechanism':terminal.get('mechanism')}
 # The operator alone consumes this receipt and owns confirmed stop.
 receipt=kit/'operator/BACKUP-VERIFIED.json';tmp=receipt.with_suffix('.partial');tmp.write_text(json.dumps(proof,indent=2)+'\n');tmp.rename(receipt)
 (out/'finished.json').write_text(json.dumps(proof,indent=2)+'\n');archive.unlink();event('all-available-evidence-backup-verified',training_ok=terminal['ok'],uncompleted=len(pending));return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (Exception,SystemExit) as exc:
  if isinstance(exc,SystemExit):raise
  print(json.dumps({'event':'backup-failed','error_type':type(exc).__name__}),flush=True);raise
