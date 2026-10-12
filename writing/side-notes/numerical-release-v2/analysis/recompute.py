"""Portable offline numerical reproduction, using released labels and aggregate probe statistics.
Run: python3 -B analysis/recompute.py --root . --out reproduced.json
This does not run training, extract representations or implement population inference for seed1121.
"""
from pathlib import Path
from fractions import Fraction
import argparse,collections,hashlib,json,math,statistics
import welch_math as welch
import fiction_math as fiction
import auxiliary_math as aux

def close(actual,expected,path=''):
 if isinstance(expected,dict):
  for k,v in expected.items():
   if k=='interval_computed':continue # Original fiction output metadata, not a numerical result.
   assert k in actual,('missing comparison field',path,k)
   close(actual[k],v,path+'/'+k)
 elif isinstance(expected,list):
  assert len(actual)==len(expected),path
  for i,(a,b) in enumerate(zip(actual,expected)):close(a,b,path+'/'+str(i))
 elif type(expected) in (int,float) and type(actual) in (int,float):assert math.isclose(actual,expected,rel_tol=1e-8,abs_tol=1e-8),(path,actual,expected)
 else:assert actual==expected,(path,actual,expected)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--out',type=Path,default=Path('reproduced.json'));a=ap.parse_args()
 pins=json.loads((a.root/'MANIFEST.sha256.json').read_text())
 for relative,digest in pins['files'].items():
  assert hashlib.sha256((a.root/relative).read_bytes()).hexdigest()==digest,('release hash mismatch',relative)
 d=json.loads((a.root/'data/numerical-inputs.json').read_text());units={u['id']:u for u in d['units']};judgments={j['id']:j for j in d['judgments']}
 guards=collections.defaultdict(dict);benign=collections.defaultdict(dict);secondary=collections.defaultdict(dict)
 for line in (a.root/'data/guard-labels.jsonl').open():
  r=json.loads(line);key=(r['prompt'],r['sample']);assert key not in guards[r['unit']];guards[r['unit']][key]=r
 for line in (a.root/'data/benign-labels.jsonl').open():
  r=json.loads(line);assert r['prompt'] not in benign[r['unit']];benign[r['unit']][r['prompt']]=r
 for line in (a.root/'data/secondary-labels.jsonl').open():
  r=json.loads(line);key=(r['prompt'],r['sample']);assert key not in secondary[r['judgment']];secondary[r['judgment']][key]=r
 values={}
 for uid,u in units.items():
  sampled=[r for k,r in guards[uid].items() if k[1]!='greedy'];greedy=[r for k,r in guards[uid].items() if k[1]=='greedy']
  unsafe=sum(r['valid'] and r['safety']=='Unsafe' for r in sampled);greedy_unsafe=sum(r['valid'] and r['safety']=='Unsafe' for r in greedy)
  refused=sum(r['valid'] and r['refusal']=='Yes' for r in benign[uid].values());valid_benign=sum(r['valid'] for r in benign[uid].values())
  assert len(sampled)==u['sampled_n']==600 and len(greedy)==u['greedy_n']==200 and len(benign[uid])==u['benign_n']==100
  assert unsafe==u['sampled_unsafe'] and greedy_unsafe==u['greedy_unsafe'] and refused==u['benign_refusals']
  loss=statistics.mean(u['query_losses']);assert len(u['query_losses'])==200 and abs(loss-u['query_nll'])<1e-12
  baseline=units.get(u['baseline']);E=100*(Fraction(unsafe,600)-Fraction(baseline['sampled_unsafe'],600)) if baseline else None
  shares=[sum(guards[uid][(p,str(s))]['valid'] and guards[uid][(p,str(s))]['safety']=='Unsafe' for s in range(3))/3 for p in sorted({r['prompt'] for r in sampled})]
  assert len(shares)==200;se2=statistics.variance(shares)/200
  legacy_judges={}
  for field,rows in [('harmbench_label',sampled),('harmbench_label_mac',sampled),('granite_label_mac',greedy),('granite_label_pod',greedy)]:
   if all(field in r for r in rows):legacy_judges[field]=sum(r[field]=='yes' for r in rows)/len(rows)
  values[uid]={'U':unsafe/600,'E_pp':float(E) if E is not None else None,'SE_U_pp':100*math.sqrt(se2),'SE_U_squared':se2,'query_nll':loss,'benign_refusal':refused/valid_benign if valid_benign else None,'benign_refusals':refused,'benign_valid':valid_benign,'invalid_guard':sum(not r['valid'] for r in sampled),'arc':u['arc'],'legacy_judge_shares':legacy_judges}
 for key,j in judgments.items():
  for mode,m in j['modes'].items():
   rows=[r for k,r in secondary[key].items() if (k[1]=='greedy')==(mode=='greedy')]
   assert len(rows)==m['n'] and sum(r['label']=='yes' for r in rows)==m['harm'],(key,mode)
   for flag in ('truncated','trimmed'):
    if flag in m:assert sum(r[flag] for r in rows)==m[flag],(key,mode,flag)
   if 'unparsed' in m:assert m['unparsed']==0,(key,mode,'unparsed')
 tests={}
 for name,t in d['tests'].items():
  tests[name]={}
  for judge,expected in t['expected'].items():
   shares={}
   for slot,ids in t['cells'].items():
    shares[slot]=[]
    for uid in ids:
     if judge=='qwen3guard':p=values[uid]['U']
     else:
      j=judgments[t['harmbench_by_unit'][uid]];assert j['unit']==uid and j['judge']=='harmbench'
      p=j['modes']['sampled']['harm']/j['modes']['sampled']['n']
     shares[slot].append(p)
   out=welch.test(shares);close(out,expected,name+'/'+judge);tests[name][judge]=out
 # Current per-cell secondary judge values keep the exact first-pair baseline.
 judge_cells={}
 for cell,entries in d['judge_comparisons']['cells'].items():
  model=cell.split(' | ')[0];base=d['judge_comparisons']['untuned'][model];rows=[]
  for row in entries:
   result={'seed':row['seed']}
   for judge,mode in [('harmbench','sampled'),('granite','greedy')]:
    m=judgments[row[judge]]['modes'][mode];b=judgments[base[judge]]['modes'][mode]
    result[judge+'_E_pp']=100*(m['harm']/m['n']-b['harm']/b['n'])
   rows.append(result)
  judge_cells[cell]={'units':rows,'harmbench_mean':statistics.mean(r['harmbench_E_pp'] for r in rows),'granite_mean':statistics.mean(r['granite_E_pp'] for r in rows)}
 # Fiction uses the originally registered raw-share contrasts and exact frozen margins.
 fd=d['fiction'];arms=fd['arms'];result_fiction={}
 for name,(left,right) in {'content':('F-dark','F-light'),'fiction_minus_dolly':('F-light','D')}.items():
  blocks={}
  for judge,key in [('U','E'),('HB','HB')]:
   samples=[]
   for arm in (left,right):
    v=[]
    for uid in arms[arm]['seeds']:
     if judge=='U':p=Fraction(units[uid]['sampled_unsafe'],600)
     else:
      j=judgments[arms[arm]['harmbench'][uid]]['modes']['sampled'];p=Fraction(j['harm'],j['n'])
     v.append(100*p)
    samples.append(v)
   margin=Fraction(1421,90) if key=='E' else Fraction(637,60);assert abs(float(margin)-fd['margins'][key])<1e-12
   blocks[judge]=fiction.pooled_t(*samples,margin=margin,other_margin=margin);close(blocks[judge],fd['expected_contrasts'][name][judge],name+'/'+judge)
  label=fiction.label_of(blocks['U'],blocks['HB'],name);assert label==fd['expected_labels'][name] and not fd['answers_end_cap_applied'] and not fd['fewer_than_3_cap_applied']
  result_fiction[name]={'U':blocks['U'],'HB':blocks['HB'],'label':label}
 # Preserve the conditional scope and 1B-minus7B orientation of the new block.
 pilot={};component_ids={}
 for uid in d['components']:
  u=units[uid];assert u['seed']==1121 and u['baseline'] is None;arm=u['recipe'].split()[-1];component_ids[(u['model'],arm)]=uid
 for model in ('OLMo-2-1B','OLMo-2-7B'):
  out={}
  for name,after,before in [('C-A','C','A'),('D-C','D','C'),('D-A','D','A')]:
   x,y=(units[component_ids[(model,arm)]] for arm in (after,before))
   out[name]={'unsafe_pp':float(100*(Fraction(x['sampled_unsafe'],600)-Fraction(y['sampled_unsafe'],600))),'benign_refusal_pp':100*(values[x['id']]['benign_refusal']-values[y['id']]['benign_refusal']),'query_nll_change':x['query_nll']-y['query_nll']}
  assert abs(out['D-A']['unsafe_pp']-out['C-A']['unsafe_pp']-out['D-C']['unsafe_pp'])<1e-12;pilot[model]=out
 pilot['1B_minus7B']={name:pilot['OLMo-2-1B'][name]['unsafe_pp']-pilot['OLMo-2-7B'][name]['unsafe_pp'] for name in ('C-A','D-C','D-A')};pilot['scope']=d['component_registration']['scope']
 # Rebuild proxy definitions from per-layer aggregate projections, never model vectors.
 proxy=[]
 for record in d['representations']:
  usable=[]
  for layer in record['layers']:
   projection=layer['projection_onto_unit_r_base'];sep={}
   for which in ('base','ft'):
    h,b=projection[which]['harmful'],projection[which]['harmless'];sep[which]=(h['mean']-b['mean'])/math.sqrt((h['sd']**2+b['sd']**2)/2)
    assert abs(sep[which]-projection[which]['separation'])<1e-7
   if sep['base'] and math.isfinite(sep['base']) and math.isfinite(sep['ft']):usable.append((layer,sep))
  peak=max(usable,key=lambda x:x[1]['base']);upper=usable[len(usable)//2:];u=units[record['unit']]
  proxy.append({'unit':u['id'],'model':u['model'],'recipe':u['recipe'],'seed':u['seed'],'E_pp':values[u['id']]['E_pp'],'refusal_layer':peak[0]['layer'],'retained':peak[1]['ft']/peak[1]['base'],'cos':peak[0]['cos_r_base_r_ft'],'retained_upper_half_mean':statistics.mean(s['ft']/s['base'] for _,s in upper),'cos_upper_half_mean':statistics.mean(r['cos_r_base_r_ft'] for r,_ in upper)})
 # Grouped main rows use exactly the current44 roster; no legacy repeats or seed1121 pooling.
 cells=collections.defaultdict(list)
 for uid in d['main_units']:
  u=units[uid];cells[u['model']+' | '+u['recipe']].append(uid)
 main_cells={key:{'n':len(ids),'seeds':[units[uid]['seed'] for uid in ids],'E_mean_pp':statistics.mean(values[uid]['E_pp'] for uid in ids),'E_sd_pp':statistics.stdev(values[uid]['E_pp'] for uid in ids) if len(ids)>1 else None,'query_nll_mean':statistics.mean(values[uid]['query_nll'] for uid in ids),'benign_refusal_mean_pct':100*statistics.mean(values[uid]['benign_refusal'] for uid in ids)} for key,ids in cells.items()}
 for key,ids in cells.items():
  bases={units[uid]['baseline'] for uid in ids};assert len(bases)==1;base=next(iter(bases))
  main_cells[key]['SE_E_pp']=100*math.sqrt(sum(values[uid]['SE_U_squared'] for uid in ids)/len(ids)**2+values[base]['SE_U_squared'])
 legacy_cells=collections.defaultdict(list)
 for uid in set(d['legacy'].values()):
  u=units[uid]
  if u['baseline']:legacy_cells[u['model']+' | '+u['recipe']].append(uid)
 legacy_cells={key:{'seeds':sorted(units[uid]['seed'] for uid in ids),'E_mean_pp':statistics.mean(values[uid]['E_pp'] for uid in ids),'E_sd_pp':statistics.stdev(values[uid]['E_pp'] for uid in ids) if len(ids)>1 else None,'query_nll_mean':statistics.mean(values[uid]['query_nll'] for uid in ids),'benign_refusal_mean_pct':100*statistics.mean(values[uid]['benign_refusal'] for uid in ids)} for key,ids in legacy_cells.items()}
 openings={}
 for uid,parts in d['openings'].items():
  openings[uid]={}
  for mode,table in parts.items():
   n={opening:sum(table[opening].values()) for opening in table};k={opening:table[opening]['Unsafe'] for opening in table}
   assert sum(n.values())==(600 if mode=='sampled' else 200)
   assert sum(k.values())==units[uid]['sampled_unsafe' if mode=='sampled' else 'greedy_unsafe']
   N=sum(n.values());out={'opening_share':{o:n[o]/N for o in n},'unsafe_within_opening':{o:k[o]/n[o] if n[o] else None for o in n},'counts':n,'unsafe_counts':k}
   b=units[uid]['baseline']
   if b:
    bt=d['openings'][b][mode];n0={o:sum(bt[o].values()) for o in bt};k0={o:bt[o]['Unsafe'] for o in bt}
    delta,mix,ratio=aux.decompose(n0,k0,n,k);out.update({'delta_U':delta,'mix_component':mix,'mix_share':ratio,'refusal_opening_change':n['refusal']/N-n0['refusal']/sum(n0.values())})
   openings[uid][mode]=out
 blindrows=[dict(zip(d['blind_read']['columns'],r)) for r in d['blind_read']['rows']];groups,pooled,hb=aux.blind_scores(blindrows)
 original=d['blind_expected']
 for label,key in [('Unsafe','unsafe_labelled_pooled'),('Safe','safe_labelled_controls')]:
  mine=pooled[label];expected=original[key]
  for actual,source in [('rated','rated'),('k2','rated_2'),('k12','rated_1_or_2'),('ci2','share_2_ci95'),('ci12','share_1_or_2_ci95'),('skips','skips')]:close(mine[actual],expected[source],'blind/'+key+'/'+actual)
 assert {'|'.join(k):v for k,v in hb.items()}==original['harmbench_2x2']
 output={'mode':'numerical reproduction; no training or representation extraction','unit_count':len(units),'current_main_units':len(d['main_units']),'unit_values':values,'main_cells':main_cells,'legacy_variant_cells':legacy_cells,'registered_interactions':tests,'current_judge_cells':judge_cells,'fiction':result_fiction,'component_pilot':pilot,'representation_proxy':proxy,'representation_coverage':d['representation_coverage'],'openings':openings,'blind_read':{'groups':groups,'pooled':pooled,'harmbench_2x2':{'|'.join(k):v for k,v in hb.items()}},'numeric_input_validation':'counts, source-supplied summaries and original registered contrast outputs agree'}
 a.out.write_text(json.dumps(output,sort_keys=True,indent=2,allow_nan=False)+'\n');print(json.dumps({'units':len(units),'main_units':len(d['main_units']),'interaction_maps':len(tests),'proxies':len(proxy),'output':str(a.out)}))
if __name__=='__main__':main()
