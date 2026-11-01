"""Validate sealed sidecar evidence; no model calls or new scientific inference."""
from pathlib import Path
import hashlib,json,math

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def validate(folder,root,protocol,protocol_sha256):
 folder,root=Path(folder),Path(root)
 assert sha(__file__)==protocol['implementation_hashes']['mechanism_receipt.py'],'receipt validator pin'
 read=lambda p:json.loads(Path(p).read_text())
 c=read(folder/'COMPLETE.json');r=read(folder/'report.json')
 assert c['complete'] is True and c['protocol_sha256']==r['protocol_sha256']==protocol_sha256
 assert c['module_sha256']==r['module_sha256']==protocol['implementation_hashes']['activation_intervention.py']
 assert r['status']=='complete' and r['source_status']=='verified' and r['model']=='olmo1b' and r['seed']==1122
 assert c['files']['report.json']==sha(folder/'report.json')
 for relative,digest in c['files'].items():
  rel=Path(relative);q=folder/rel
  assert not rel.is_absolute() and '..' not in rel.parts and q.resolve().is_relative_to(folder.resolve())
  assert not q.is_symlink() and sha(q)==digest,relative
 identity=r['identity'];assert identity['engine_sha256']==protocol['engine_sha256'] and identity['manifest_sha256']==protocol['prepared_manifest_sha256']
 assert identity['model']['repo_id']=='allenai/OLMo-2-0425-1B-Instruct'
 assert identity['layer']==math.ceil(protocol['mechanism']['layer_fraction']*identity['layer_count'])
 assert c['files']['candidate-vectors.safetensors']==identity['vector_sha256']==sha(folder/'candidate-vectors.safetensors')
 specs={u['arm']:u for u in protocol['units'] if u['model']=='olmo1b' and u['arm'] in ('A','C','D')}
 assert set(identity['source_units'])==set(specs)=={'A','C','D'}
 for arm,spec in specs.items():
  u=root/spec['run_dir'];pins=identity['source_units'][arm]
  assert pins['complete_sha256']==sha(u/'COMPLETE.json') and pins['state_sha256']==sha(u/'states/e1/state.json')
  assert pins['config_sha256']==spec['config_sha256'] and pins['job_sha256']==sha(u/'job.json')
 assert r['canary_result']['status']=='passed' and r['canary_result']['passed_contexts']==4
 assert r['hooks_cleanup']['verified'] is True and r['guard_isolation']['verified'] is True and r['guard_isolation']['completed_conditions']==12
 canaries=r['canaries'];assert len(canaries)==4 and {x['state'] for x in canaries}=={'base','A','C','D'}
 for x in canaries:
  assert x['status']=='complete' and x['exact_token_parity'] is True
  assert len(x['nohook_output_ids'])==len(x['sham_output_ids'])==2 and x['nohook_output_ids']==x['sham_output_ids']
 cells=r['conditions'];assert len(cells)==12 and {(x['state'],x['action']) for x in cells}=={(s,a) for s in ('base','A','C','D') for a in ('none','target','orthogonal')}
 evaluation=identity['evaluation'];assert len(evaluation)==60 and len({x['id'] for x in evaluation})==60
 assert len(identity['calibration'])==80 and len(identity['utility'])==20
 assert not {x['id'] for x in identity['calibration']}&{x['id'] for x in evaluation+identity['utility']}
 for x in cells:
  assert x['status']=='complete';g=x['guard_isolation'];base=identity['baseline_live_hooks']
  assert g['verified'] is True and g['policy_hook_count_before_guard']==g['policy_hook_count_after_guard']==g['expected_policy_hook_count']==base
  path=folder/(x['state']+'-'+x['action']);labels=[json.loads(line) for line in (path/'guard.jsonl').read_text().splitlines()]
  generations=[json.loads(line) for line in (path/'generations.jsonl').read_text().splitlines()]
  assert len(labels)==len(generations)==60 and [g['item_id'] for g in labels]==[p['id'] for p in evaluation]
  assert [g['prompt_id'] for g in generations]==[p['id'] for p in evaluation]
  assert x['capped']==sum(g['stop_reason']=='max_new_tokens' for g in generations)
  for kind in ('harm','overrefusal'):
   rows=[g for item,g in zip(evaluation,labels) if item['kind']==kind];expected=x['endpoints'][kind]
   assert len(rows)==expected['n']==30
   for key,count in [('unsafe',sum(g['valid'] and g['safety']=='Unsafe' for g in rows)),('refusal',sum(g['valid'] and g['refusal']=='Yes' for g in rows)),('invalid',sum(not g['valid'] for g in rows))]:assert expected[key]==count
  utility=read(path/'utility.json');assert len(utility['example_losses'])==20 and all(math.isfinite(v) and v>=0 for v in utility['example_losses'])
  assert math.isclose(math.fsum(utility['example_losses'])/20,x['utility_nll'],abs_tol=1e-12)
 return {'verified':True,'report_sha256':sha(folder/'report.json'),'complete_sha256':sha(folder/'COMPLETE.json'),'canaries':4,'conditions':12,'guard_isolation_verified':True,'scope':'sealed numerical/hook receipts validated; no training authenticity, full-answer safety or sole-mediation proof'}
