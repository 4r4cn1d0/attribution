# Read-only check (M): engine identity, manifest, recipe, environment match-fields of the units the 7-8B noise block pairs with.
# Reads COMPLETE.json/assets.json and prepared-manifest metadata only (hashes, counts, ids are compared but never printed).
import sys, json, pathlib, hashlib, glob
ROOT=pathlib.Path('/Users/spiderishi/Coding/attribution')
sys.path.insert(0,str(ROOT/'scripts')); sys.path.insert(0,str(ROOT))
import family_probe_reading as fpr
T=ROOT/'tmp'
units=sorted(glob.glob(str(T/'family-probe-sp-olmo2-7b-b-*/retrieved/*/tree/round1/*-a0-*-a1'))+glob.glob(str(T/'family-probe-sp-llama31-8b-b5e5-*/retrieved/*/tree/round1/*-a0-*-a1'))+glob.glob(str(T/'family-probe-sp-llama31-8b-b-a0/retrieved/*/tree/round1/1101-a0-init-a1'))+glob.glob(str(T/'gate-b-olmo/retrieved/*/tree/round1/*-a1'))+glob.glob(str(T/'family-probe-olmo2-1b/retrieved/*/tree/round1/1101-a0-e1-a1'))+glob.glob(str(T/'family-probe-olmo2-1b-gateA-110*/retrieved/*/tree/round1/*-a0-e1-a1')))
for u in units:
    u=pathlib.Path(u); d=json.loads((u/'COMPLETE.json').read_text()); i=d['identity']
    m,_=fpr.environment_of(u)
    env=hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()[:12]
    s=d.get('evaluation',{}).get('harm',{}).get('sampled') if isinstance(d.get('evaluation'),dict) else None
    print(u.relative_to(T).parts[0], u.name[:22], 'code', i['code_sha256'][:8], 'manifest', i['manifest_sha256'][:8], 'recipe', i['recipe_sha256'][:8], 'train-id', i['training_identity'][:8], 'env', env, 'U', (s or {}).get('unsafe'), '/', (s or {}).get('answers'))
a=json.loads((T/'kt-prepared/prepared-kt-dolly-olmo2/manifest.json').read_text()); b=json.loads((T/'kt-prepared/prepared-kt-dolly-llama3/manifest.json').read_text())
print('dev groups and members equal (OLMo PREP vs Llama manifest):', a['groups']==b['groups'])
print('per-unit category and row lists equal:', all(a['units'][g]['category']==b['units'][g]['category'] and a['units'][g]['rows']==b['units'][g]['rows'] for g in a['units']))
