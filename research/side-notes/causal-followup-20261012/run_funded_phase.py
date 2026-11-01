"""Admit only the frozen funded phase; early verified backups, stop and offline read."""
from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,subprocess,sys,time
R=Path('/Users/spiderishi/Coding/attribution');S=R/'tmp/causal-followup-20261012';P=R/'research/side-notes/causal-followup-20261012/protocol.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def event(kind,**kw):
 d={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'event':kind,**kw}
 with (S/'manager-events.jsonl').open('a') as f:f.write(json.dumps(d)+'\n')
 print(json.dumps(d),flush=True)
def copy(src,dst):
 src,dst=Path(src),Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  assert sha(src)==sha(dst),('conflicting collection bytes',src,dst)
  return
 try:os.link(src,dst)
 except OSError:shutil.copyfile(src,dst)
def main():
 pin=sys.argv[1];assert sha(P)==pin;p=read(P);assert p['status']=='FROZEN'
 assert sha(__file__)==p['administrative_hashes']['run_funded_phase.py']
 assert sha(S/'prefetch_followup.py')==p['administrative_hashes']['prefetch_followup.py']
 assert not (S/'launch-started.json').exists();(S/'launch-started.json').write_text(json.dumps({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'protocol_sha256':pin})+'\n')
 processes={};backups={};handles=[]
 for model,spec in p['hosts'].items():
  log=(S/(model+'-operator.log')).open('ab');handles.append(log)
  proc=subprocess.Popen([sys.executable,str(R/'scripts/side_project_cause/followup_pod_operator.py'),'--protocol',str(P),'--protocol-sha256',pin,'--model',model,'--execute'],stdout=log,stderr=subprocess.STDOUT)
  processes[model]=proc;event('operator-started',model=model,pid=proc.pid)
 end=time.monotonic()+6*3600
 while time.monotonic()<end:
  for model,proc in processes.items():
   s=p['hosts'][model];kit=Path(s['kit_path'])
   events=kit/'operator/events.jsonl'
   batch_started=events.exists() and any(json.loads(line).get('event')=='batch-started' for line in events.read_text().splitlines())
   if model not in backups and batch_started:
    log=(S/(model+'-prefetch.log')).open('ab');handles.append(log)
    b=subprocess.Popen([sys.executable,str(S/'prefetch_followup.py'),'--model',model,'--protocol-sha256',pin],stdout=log,stderr=subprocess.STDOUT);backups[model]=b;event('backup-started',model=model,pid=b.pid)
  if all(proc.poll() is not None for proc in processes.values()) and all(b.poll() is not None for b in backups.values()):break
  time.sleep(30)
 else:event('manager-wait-limit',note='frozen pod stop timers remain governing');return 1
 root=S/'combined';assert not root.exists();temp=S/'combined.partial';temp.mkdir()
 failures=[]
 for model,spec in p['hosts'].items():
  cache=S/'prefetch'/model
  for unit in [u for u in p['units'] if u['model']==model]:
   src=cache/('unit-'+unit['arm'])/unit['run_dir']
   if src.exists():shutil.copytree(src,temp/unit['run_dir'],copy_function=copy)
   else:failures.append({'model':model,'arm':unit['arm'],'reason':'no verified incremental backup'})
  receipt=cache/(model+'-BATCH-DONE.json')
  if receipt.exists():copy(receipt,temp/'cause'/receipt.name)
  else:failures.append({'model':model,'reason':'batch receipt missing'})
  if (cache/'terminal-light').exists():shutil.copytree(cache/'terminal-light',temp,dirs_exist_ok=True,copy_function=copy)
 temp.rename(root)
 command=[sys.executable,'-B','-m','scripts.side_project_cause.followup_analyze','--protocol',str(P),'--root',str(root),'--out',str(S/'analysis.json')]
 result=subprocess.run(command,cwd=R)
 report={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'protocol_sha256':pin,'operator_exits':{m:v.returncode for m,v in processes.items()},'backup_exits':{m:v.returncode for m,v in backups.items()},'collection_failures':failures,'analysis_exit':result.returncode,'scope':'funded phase only; future programmes not launched'}
 (S/'finished.json').write_text(json.dumps(report,indent=2)+'\n');event('funded-phase-ended',analysis_exit=result.returncode,collection_failures=len(failures));return result.returncode
if __name__=='__main__':raise SystemExit(main())
