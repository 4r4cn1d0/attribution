"""Private numerical exporter: fixed manifest, field whitelists, no training/publishing."""
from pathlib import Path
import copy,csv,hashlib,importlib.util,json,math,statistics
M=Path('/Users/spiderishi/Coding/attribution');W=M/'.claude/worktrees/peaceful-jepsen-8b8eee';S=M/'tmp/side-paper-continuation-20261012';OUT=S/'numerical-package'
manifest=json.loads((S/'release-inputs-private.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
for file,digest in manifest['source_hashes'].items():assert sha(file)==digest,file
assert not OUT.exists();OUT.mkdir();(OUT/'data').mkdir();(OUT/'analysis').mkdir()
spec=importlib.util.spec_from_file_location('v1',W/'writing/side-notes/arxiv/release/build_release.py');v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1);src=v1.Sources(M,W)
original_log=src.log
def pinned_log(path,fields):
 path=str(Path(path).resolve());assert path in manifest['source_hashes'],('unfrozen helper input',path)
 assert sha(path)==manifest['source_hashes'][path],path
 return original_log(path,fields)
src.log=pinned_log
configs={u['recipe_sha256']:{} for u in manifest['units']};records={}
for u in manifest['units']:
 descriptor={'id':u['id'],'eval':str(Path(u['files']['summary.json']).parent.relative_to(M/'tmp')),'ckpt':u['checkpoint'],'seed':u['seed']}
 records[u['id']]=v1.load_unit(src,descriptor,configs)
# Stable opaque mapping only after matching every supplied prompt set.
harm=sorted({k[0] for k in next(iter(records.values()))['answers']});benign=sorted(next(iter(records.values()))['overrefusal'])
assert len(harm)==200 and len(benign)==100 and not set(harm)&set(benign)
for d in records.values():assert {k[0] for k in d['answers']}==set(harm) and set(d['overrefusal'])==set(benign)
opaque={p:f'p{i+1:03d}' for i,p in enumerate(harm+benign)}
# Original legacy judge selections are kept as separate device columns.
legacy=[]
for spec in manifest['legacy_specs']:
 x=copy.deepcopy(spec);x['data']=records[manifest['legacy'][x['id']]];legacy.append(x)
for file in sorted({u['hb_pod'] for u in legacy if u['hb_pod']}):
 selected={u['data']['complete_sha256']:u for u in legacy if u['hb_pod']==file};v1.attach_pod_labels(src,file,selected,'harmbench_label',extra=('truncated','harmbench_truncated'))
for file in sorted({u['granite_pod'] for u in legacy if u['granite_pod']}):
 selected={u['data']['complete_sha256']:u for u in legacy if u['granite_pod']==file};v1.attach_pod_labels(src,file,selected,'granite_label_pod')
for u in legacy:
 if u['hb_mac']:v1.attach_harmbench_mac(src,u)
 if u['granite_mac']:v1.attach_granite_mac(src,u)
bycomplete={u['complete_sha256']:u['id'] for u in manifest['units']};judgments={};judgment_inputs={}
def judgment(file,judge):
 file=Path(file).resolve();assert str(file) in manifest['source_hashes'],('unfrozen judge',file);x=read(file);uid=bycomplete[x['complete_sha256']];assert x['job_sha256']==records[uid]['job_sha256']
 key='j-'+sha(file)[:20]
 if key in judgments:return key
 filtered={mode:{k:x[mode][k] for k in ('harm','n','unparsed','truncated','trimmed') if k in x[mode]} for mode in ('sampled','greedy') if isinstance(x.get(mode),dict)}
 for val in filtered.values():assert all(type(v) is int and v>=0 for v in val.values()) and val['harm']<=val['n']
 info={k:x['judge'][k] for k in ('name','revision','quantization','criteria','device') if k in x.get('judge',{})}
 judgments[key]={'id':key,'unit':uid,'judge':judge,'device':'cuda','modes':filtered,'settings':info,'source_sha256':sha(file)};judgment_inputs[str(file)]=sha(file)
 return key
for u in manifest['units']:
 for j in u['judge_files']:judgment(j['path'],j['judge'])
# Exact published judge file names/pairs establish remaining current-cell membership.
jn=read(W/'research/side-notes/explore-20261011/judge-numbers-20261011.json');public_jn={'untuned':{},'cells':{}}
def locate(name,pair):
 judge='granite' if name.startswith('granite--') else 'hb'
 run='7b-qwen-1' if pair=='first' else 'repl-1'
 found=sorted((M/'tmp/judge-pod'/f'sp-{judge}-{run}').glob('judges-*/'+name));assert found and len({sha(p) for p in found})==1,(name,pair,len(found));return found[0]
for model,row in jn['untuned'].items():
 public_jn['untuned'][model]={judge:judgment(locate(row[field],'first'),judge) for judge,field in [('harmbench','harmbench_file'),('granite','granite_file')]}
for cell,info in jn['cells'].items():
 public_jn['cells'][cell]=[]
 for row in info['units']:
  public_jn['cells'][cell].append({'seed':row['seed'],**{judge:judgment(locate(row[field],row['pair']),judge) for judge,field in [('harmbench','harmbench_file'),('granite','granite_file')]}})
# Export parsed labels from each declared pod cache; no raw responses or text fields.
judge_labels=[]
for key,j in judgments.items():
 files=[p for p in judgment_inputs if sha(p)[:20]==key[2:]];assert len(files)==1
 file=Path(files[0]);cache=file.parent.parent/'fetched/out'/f"{j['judge']}-pod.jsonl";assert cache.exists(),cache
 target=next(u for u in manifest['units'] if u['id']==j['unit']);counts={'sampled':0,'greedy':0};yes={'sampled':0,'greedy':0};seen=set()
 for line in cache.open():
  r=json.loads(line)
  if r.get('complete_sha256')!=target['complete_sha256']:continue
  mode=r['mode'];sample=str(r['sample_index']) if mode=='sampled' else 'greedy';pid=r['prompt_id'];assert (pid,sample) in records[j['unit']]['answers']
  assert r['label'] in ('yes','no') and mode in counts
  assert (pid,sample) not in seen;seen.add((pid,sample));counts[mode]+=1;yes[mode]+=r['label']=='yes'
  truncated=r.get('truncated',False);trimmed=r.get('trimmed',False);assert type(truncated) is bool and type(trimmed) is bool
  judge_labels.append({'judgment':key,'prompt':opaque[pid],'sample':sample,'label':r['label'],'truncated':truncated,'trimmed':trimmed})
 for mode,m in j['modes'].items():assert counts[mode]==m['n'] and yes[mode]==m['harm'],(key,mode,counts,yes,m)
 assert str(cache) in manifest['source_hashes'],('unfrozen cache',cache);judgment_inputs[str(cache)]=sha(cache)
# Config records are selected hyperparameters, explicitly not executable training reconstruction.
def public_config(file):
 d=read(file);model=d['model'];train=d['train']
 return {'original_canonical_sha256':hashlib.sha256((json.dumps(d,sort_keys=True,indent=2)+'\n').encode()).hexdigest(),'model':{k:model[k] for k in ('repo_id','revision','architecture','base_dtype','trainable_dtype','attn_implementation','max_train_tokens','max_prompt_tokens') if k in model},'lora':{k:model['lora'][k] for k in ('r','alpha','dropout','target_modules')},'train':{k:train[k] for k in ('micro_batch','grad_accum','optimizer','lr','betas','eps','weight_decay','lr_schedule','warmup_steps','schedule_until','loss_weighting','max_grad_norm','checkpoints') if k in train},'loss_weighting':'token_mean' if train.get('loss_weighting')=='token_mean' else 'example_mean','generation':{k:d['generation'][k] for k in ('max_new_tokens','temperature','top_p','do_sample','sampled_answers_per_prompt') if k in d.get('generation',{})}}
public_units=[];labels=[];over=[];public_configs={}
for u in manifest['units']:
 d=records[u['id']];summary=read(u['files']['summary.json']);arc=summary.get('arc_utility') or {};cfg=public_config(u['config']);public_configs[u['recipe_sha256']]=cfg
 qloss=[json.loads(x)['loss'] for x in Path(u['files']['query_loss.jsonl']).read_text().splitlines()]
 assert all(type(x) in (int,float) and math.isfinite(x) for x in qloss) and len(qloss)==200 and abs(statistics.mean(qloss)-d['loss_mean'])<1e-12
 public_units.append({'id':u['id'],'model':u['model'],'recipe':u['recipe'],'seed':u['seed'],'checkpoint':u['checkpoint'],'baseline':u['baseline'],'roles':u['roles'],'recipe_sha256':u['recipe_sha256'],'code_sha256':d['job']['code_sha256'],'manifest_sha256':d['job']['manifest_sha256'],'job_sha256':d['job_sha256'],'complete_sha256':d['complete_sha256'],'sampled_unsafe':summary['harm']['sampled']['unsafe'],'sampled_n':summary['harm']['sampled']['answers'],'greedy_unsafe':summary['harm']['greedy']['unsafe'],'greedy_n':summary['harm']['prompts'],'benign_refusals':summary['overrefusal']['refusals'],'benign_n':summary['overrefusal']['n'],'query_losses':qloss,'query_nll':d['loss_mean'],'arc':{k:arc[k] for k in ('correct','n','n_scored','accuracy') if k in arc}})
 for (pid,sample),r in d['answers'].items():
  labels.append({'unit':u['id'],'prompt':opaque[pid],'sample':sample,**{k:r[k] for k in ('valid','safety','categories','refusal')},**{k:r[k] for k in ('harmbench_label','harmbench_label_mac','harmbench_truncated','granite_label_mac','granite_label_pod') if k in r}})
 for pid,r in d['overrefusal'].items():over.append({'unit':u['id'],'prompt':opaque[pid],**{k:r[k] for k in ('valid','safety','categories','refusal')}})
# Probe projections: group means/SD only; omit per-prompt arrays and vectors.
proxies=[]
for inp in manifest['proxy_inputs']['inputs']:
 d=read(inp['source']);matches=[u for u in manifest['units'] if inp['host'] in Path(u['root']).parts and u['checkpoint']=='e1'];assert len(matches)==1,(inp['host'],len(matches));u=matches[0]
 state=Path(u['root'])/'states/e1/state.json';st=read(state);assert st['files']['adapter.safetensors']==inp['adapter_sha256']==d['identity']['adapter_sha256']
 layers=[]
 for r in d['layers']:
  projection={}
  for which in ('base','ft'):
   x=r['projection_onto_unit_r_base'][which];projection[which]={'separation':x['separation'],**{group:{k:x[group][k] for k in ('mean','sd')} for group in ('harmful','harmless','overrefusal')}}
   a,b=x['harmful'],x['harmless'];derived=(a['mean']-b['mean'])/math.sqrt((a['sd']**2+b['sd']**2)/2);assert abs(derived-x['separation'])<1e-7
  layers.append({'layer':r['layer'],'cos_r_base_r_ft':r['cos_r_base_r_ft'],'projection_onto_unit_r_base':projection})
 proxies.append({'unit':u['id'],'model':u['model'],'recipe':u['recipe'],'seed':u['seed'],'adapter_sha256':inp['adapter_sha256'],'source_sha256':inp['source_sha256'],'layers':layers})
 judgment_inputs[str(state)]=sha(state)
# Blind labels and ratings retain the existing vetted field whitelist.
header,blind=v1.blind_rows(src,{u['blind']:u for u in legacy if u['blind']})
openings={};mech_cache={}
for u in legacy:
 if not u['openings']:continue
 xt=v1.attach_openings(src,u,mech_cache);uid=manifest['legacy'][u['id']]
 openings[uid]={part:{opening:{label:n for (op,label),n in table.items() if op==opening} for opening in ('refusal','caveat','direct','empty')} for part,table in xt.items()}
figures={name:{'columns':h,'rows':rows} for name,(h,rows) in zip(('fig1','fig2'),v1.figure_rows(src,{(u['model'],u['recipe'].replace('Constant half LR','Constant, half LR'),u['seed']):u for u in manifest['units'] if u['baseline']},{u['openings'][1]:u for u in legacy if u['openings']}))}
for name,info in figures.items():
 for row in info['rows']:
  row[info['columns'].index('source')]='data/numerical-inputs.json:openings' if name=='fig2' else 'data/guard-labels.jsonl and numerical-inputs.json'
  if 'check' in info['columns']:row[info['columns'].index('check')]='reported rounded plotting value; see coverage'
  if 'unit' in info['columns']:
   ix=info['columns'].index('unit');row[ix]=manifest['legacy'][row[ix]]
# Stored comparison outputs contain only known numerical/label fields; no source maps.
public_tests={}
for name,t in manifest['tests'].items():
 mp=read(W/'research/side-notes/prereg-results-20261011'/('map-'+name+'.json'))
 selected={}
 for slot,items in mp['cells'].items():
  for uid,item in zip(t['cells'][slot],items):
   if item.get('harmbench'):selected[uid]=judgment(item['harmbench'],'harmbench')
 public_tests[name]={'cells':t['cells'],'slots':t['slots'],'harmbench_by_unit':selected,'expected':{judge:read(v['path']) for judge,v in t['reported'].items()}}
public_fiction=copy.deepcopy(manifest['fiction'])
for arm,f in public_fiction.items():
 f['harmbench']={}
 for uid in [f['baseline'],*f['seeds']]:
  source_u=next(u for u in manifest['units'] if u['id']==uid)
  match=[j for j in source_u['judge_files'] if 'sp-hb-fiction-bt-llama-1' in j['path']];assert len(match)==1,(arm,uid)
  f['harmbench'][uid]=judgment(match[0]['path'],'harmbench')
fr=read(W/'research/side-fiction/results/fiction-results.json')
public_fiction_meta={'arms':public_fiction,'margins':{k:v['frozen_pp'] for k,v in fr['margins_pp'].items()},'expected_contrasts':{k:{judge:v[judge] for judge in ('U','HB')} for k,v in fr['contrasts'].items()},'expected_labels':fr['labels'],'answers_end_cap_applied':False,'fewer_than_3_cap_applied':False,'scope':'registered pooled-t comparisons; wide frozen margins; development evidence'}
# Output uses closed schemas; all original source paths stay in private provenance.
data={'schema_version':2,'units':public_units,'configs':public_configs,'judgments':list(judgments.values()),'judge_comparisons':public_jn,'main_units':[u['id'] for u in manifest['units'] if any(r.startswith(('test:','token-mean:')) for r in u['roles'])],'legacy':manifest['legacy'],'tests':public_tests,'fiction':public_fiction_meta,'components':manifest['components'],'component_registration':{'protocol_sha256':sha(M/'research/side-notes/causal-study-20261012/protocol.json'),'scope':'one fresh seed1121; descriptive conditional contrasts; no population inference','cross_checkpoint_direction':'1B minus7B','optimizer_updates':38},'representations':proxies,'representation_coverage':{'recovered':20,'planned':24,'missing':[{'model':'OLMo-2-1B','recipe':'Constant','seed':1102},{'model':'OLMo-2-1B','recipe':'Scheduled','seed':1101},{'model':'OLMo-2-7B','recipe':'Scheduled','seed':1103},{'model':'Llama-3.1-8B','recipe':'Scheduled','seed':1103}]},'blind_read':{'columns':list(header),'rows':blind}}
data.update({'openings':openings,'figure_data':figures,'blind_expected':read(W/v1.BLIND_SCORES)})
for file,digest in manifest['source_hashes'].items():assert sha(file)==digest,file
(OUT/'data/numerical-inputs.json').write_text(json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+'\n')
for name,rows in [('guard-labels',labels),('benign-labels',over),('secondary-labels',judge_labels)]:
 with (OUT/f'data/{name}.jsonl').open('w') as f:
  for row in rows:f.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
(S/'release-additional-source-pins.json').write_text(json.dumps(judgment_inputs,indent=2)+'\n')
# Fail on source paths, internal/public raw prompt IDs, or personal identifiers in public files.
for p in OUT.rglob('*'):
 if p.is_file():
  text=p.read_text()
  for token in ('/Users/','spiderishi','4r4cn1d0','RUNPOD_API_KEY','RUNPOD_OPERATOR_API_KEY',*harm,*benign):assert token not in text,(p.name,token)
print('numeric exports complete units',len(public_units),'judgments',len(judgments),'guard_labels',len(labels),'proxies',len(proxies))
