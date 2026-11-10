"""Freeze explicit numerical-release inputs; no scientific reruns or source writes."""
from pathlib import Path
import ast,csv,hashlib,importlib.util,json,re
M=Path('/Users/spiderishi/Coding/attribution');W=M/'.claude/worktrees/peaceful-jepsen-8b8eee';S=M/'tmp/side-paper-continuation-20261012'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
spec=importlib.util.spec_from_file_location('v1',W/'writing/side-notes/arxiv/release/build_release.py');v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)
model_names={repo:name for name,repo in v1.MODELS.values()}
model_names.update({'allenai/OLMo-2-1124-7B-Instruct':'OLMo-2-7B','meta-llama/Llama-3.1-8B-Instruct':'Llama-3.1-8B'})
units={};sources={};legacy={};tests={};fiction={}
configs={}
for folder in [M/'experiments/safety_selection/configs',M/'research/side-notes/causal-study-20261012/configs']:
 for file in sorted(folder.glob('*.json')):
  obj=read(file);digest=hashlib.sha256((json.dumps(obj,sort_keys=True,indent=2)+'\n').encode()).hexdigest()
  configs.setdefault(digest,file)
def source(p):
 p=Path(p).resolve();assert p.is_file();sources[str(p)]=sha(p);return str(p)
def add(ev,recipe=None):
 ev=Path(ev).resolve();root=ev.parent.parent;c=read(root/'COMPLETE.json');j=read(root/'job.json');assert c['complete'] is True and c['job_sha256']==sha(root/'job.json')
 ident=j.get('identity') or c['identity'];cfg=configs.get(j['recipe_sha256'])
 assert cfg and cfg.is_file(),(root,j['recipe_sha256'])
 cfgobj=read(cfg);canonical=hashlib.sha256((json.dumps(cfgobj,sort_keys=True,indent=2)+'\n').encode()).hexdigest();assert canonical==j['recipe_sha256']
 repo=cfgobj['model']['repo_id'];model=model_names[repo];ckpt=ev.name;tr=cfgobj['train']
 if recipe is None:
  if ckpt=='init':recipe='untuned'
  elif tr.get('lr_schedule')=='warmup_cosine':recipe='Scheduled'
  elif tr.get('loss_weighting')=='token_mean' or tr.get('loss')=='causal_lm_token_mean':recipe='Constant, token-mean'
  elif tr.get('lr')==5e-5:recipe='Constant half LR'
  else:recipe='Constant'
 uid='u-'+sha(root/'COMPLETE.json')[:20]+'-'+ckpt
 if uid not in units:
  selected=['summary.json','guard_samples.jsonl','guard.jsonl','query_loss.jsonl']
  files={}
  for name in selected:
   p=ev/name
   if p.exists():
    relative=str(p.relative_to(root));actual=sha(p);assert c['files'].get(relative)==actual,(root,relative)
    files[name]=source(p)
  assert 'summary.json' in files and 'guard_samples.jsonl' in files
  units[uid]={'id':uid,'model':model,'recipe':recipe,'seed':j['seed'] if ckpt!='init' else None,'checkpoint':ckpt,'root':str(root),'files':files,'job':source(root/'job.json'),'complete':source(root/'COMPLETE.json'),'config':source(cfg),'recipe_sha256':canonical,'complete_sha256':sha(root/'COMPLETE.json'),'baseline':None,'judge_files':[],'roles':[]}
 elif recipe is not None and units[uid]['recipe']!=recipe:
  raise ValueError(('same evaluation classified differently',uid,recipe,units[uid]['recipe']))
 return uid
def attach(uid,path,judge):
 if not path:return
 path=Path(path);x=read(path);u=units[uid];assert x['complete_sha256']==u['complete_sha256'] and x['job_sha256']==sha(u['job'])
 item={'path':source(path),'judge':judge}
 if item not in u['judge_files']:u['judge_files'].append(item)
for u in v1.UNITS:
 uid=add(M/'tmp'/u['eval'],v1.RECIPES[u['recipe']]);units[uid]['roles'].append('legacy:'+u['id']);legacy[u['id']]=uid
for u in v1.UNITS:
 if u['baseline']:units[legacy[u['id']]]['baseline']=legacy[u['baseline']]
# Main comparison units and membership are specified by the immutable preregistration maps.
for mp in sorted((W/'research/side-notes/prereg-results-20261011').glob('map-*.json')):
 source(mp);d=read(mp);cells={}
 for slot,items in d['cells'].items():
  cells[slot]=[]
  for item in items:
   uid=add(item['eval']);cells[slot].append(uid);units[uid]['roles'].append('test:'+mp.stem+':'+slot);attach(uid,item.get('harmbench'),'harmbench')
 tests[mp.stem[4:]]={'cells':cells,'slots':d.get('slots',{}),'source_sha256':sha(mp),'reported':{}}
 for judge in ('qwen3guard','harmbench'):
  rp=mp.with_name('result-'+mp.stem[4:]+'-'+judge+'.json')
  if rp.is_file():tests[mp.stem[4:]]['reported'][judge]={'path':source(rp),'sha256':sha(rp)}
# Pin current main baselines, rather than substituting older numerically similar evaluations.
main_first={}
for u in units.values():
 if any(x.startswith('test:') for x in u['roles']) and u['recipe']=='Constant' and u['seed']==1101:main_first[u['model']]=u
for model,u in main_first.items():
 if model in ('OLMo-2-1B','Llama-3.2-1B'):
  baseline=legacy['olmo2-1b_untuned' if model=='OLMo-2-1B' else 'llama3.2-1b_untuned']
 else:
  root=Path(u['root']);baseline=add(root.parent/'1101-a0-init-a1/eval/init')
 for candidate in units.values():
  if candidate['model']==model and any(x.startswith('test:') for x in candidate['roles']):candidate['baseline']=baseline
# The three token-mean-only units are named in the screened-setting roster.
for seed in (1101,1102,1103):
 found=list((M/'tmp').glob(f'*/retrieved/*olmo2-1b-bt-{seed}/tree/round1/{seed}-a0-e1-a1/eval/e1'))
 assert found and len({sha(p.parent.parent/'COMPLETE.json') for p in found})==1,seed
 uid=add(sorted(found)[0],'Constant, token-mean');units[uid]['baseline']=legacy['olmo2-1b_untuned'];units[uid]['roles'].append('token-mean:'+str(seed))
# Fiction preserves arm-specific baselines and the separately declared reference baseline.
fmp=W/'research/side-fiction/results/unit-map.json';fd=read(fmp);assert fd['test_run'] is False;source(fmp)
for arm,entries in fd['arms'].items():
 uid0=add(Path(entries['a0']['unit'])/'eval/init','untuned');attach(uid0,entries['a0']['harmbench'],'harmbench');members=[]
 for seed,item in entries['seeds'].items():
  recipe='Constant' if arm=='D' else 'Fiction '+arm
  uid=add(Path(item['unit'])/'eval/e1',recipe);attach(uid,item['harmbench'],'harmbench');units[uid]['baseline']=uid0;units[uid]['roles'].append('fiction:'+arm);members.append(uid)
 fiction[arm]={'baseline':uid0,'seeds':members}
# Prospective seed1121 study is a separate module, never pooled with historical cells.
pp=M/'research/side-notes/causal-study-20261012/protocol.json';protocol=read(pp);source(pp);components=[]
for spec in protocol['units']:
 uid=add(M/'tmp/cause-study-20261012/combined'/spec['run_dir']/'eval/e1','Component '+spec['arm']);units[uid]['roles'].append('component:'+spec['model']+':'+spec['arm']);components.append(uid)
# The rounded exploratory CSV is used only to audit membership and rounded values.
rows=list(csv.DictReader((W/'research/side-notes/explore-20261011/units.csv').open()))
main=[u for u in units.values() if any(x.startswith(('test:','token-mean:')) for x in u['roles'])]
assert len(main)==44,len(main)
for row in rows:
 label=row['recipe'].replace(' token-mean',', token-mean')
 matched=[u for u in main if (u['model'],u['recipe'],u['seed'])==(row['model'],label,int(row['seed']))];assert len(matched)==1,(row['model'],label,row['seed'],len(matched))
 s=read(matched[0]['files']['summary.json'])['harm']['sampled'];assert abs(s['unsafe']/s['answers']-float(row['U']))<=0.000051
# Numeric proxy inputs remain separate; exact source selection is already preserved.
proxy=read(S/'refusal-probe-inputs-20.json')
for item in proxy['inputs']:item['source']=source(M/item['source'])
for f in [W/'research/side-notes/scripts/interaction_test_20261011.py',W/'research/side-notes/scripts/refusal_direction_summary_20261011.py',W/'research/side-notes/explore-20261011/explore.json',W/'research/side-notes/explore-20261011/judge-numbers-20261011.json',W/'research/side-fiction/results/fiction-results.json',W/'writing/side-notes/arxiv/release/build_release.py']:source(f)
for name in ('BLIND_KEY','BLIND_RATINGS','BLIND_SCRIPT','BLIND_SCORES','FIG1','FIG2'):source(W/getattr(v1,name))
source(M/'tmp'/v1.HB_MAC_OLMO_SUMMARY)
for file in v1.MECH_FILES:source(M/'tmp'/file)
for file in [W/'research/side-fiction/analysis/analyze_fiction.py',W/'writing/side-notes/arxiv/release/release_files/analysis/recompute.py',S/'build_numerical_package.py',S/'prepare_recomputation.py',S/'recompute.py']:source(file)
for u in v1.UNITS:
 for name in ('hb_pod','granite_pod'):
  if u.get(name):source(M/'tmp'/u[name])
 for name in ('hb_mac','granite_mac'):
  if u.get(name):source(M/'tmp'/u[name][0])
 if u.get('granite_mac'):
  identity=(M/'tmp'/u['granite_mac'][0]).parent/'second-judge-probe-summary.json'
  if identity.exists():source(identity)
 if u.get('openings'):source(M/'tmp'/u['openings'][0])
for path in read(S/'release-additional-source-pins.json'):source(path)
manifest={'schema_version':2,'mode':'analysis-only; no training reconstruction','units':list(units.values()),'legacy':legacy,'legacy_specs':v1.UNITS,'tests':tests,'fiction':fiction,'components':components,'proxy_inputs':proxy,'source_hashes':sources,'rounding_audit_main_units':44,'legacy_source_roster_units':28}
(S/'release-inputs-private.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('private manifest frozen units',len(units),'main',len(main),'tests',len(tests),'proxy',len(proxy['inputs']))
