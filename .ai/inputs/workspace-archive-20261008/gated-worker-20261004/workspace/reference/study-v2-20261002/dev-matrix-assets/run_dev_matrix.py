"""Administrative dispatch of the fixed two-job host plan to unchanged Stage A CLI."""
import json,pathlib,subprocess,sys,time,os
ROOT=pathlib.Path('/workspace/attribution-study-v2');os.chdir(ROOT)
plan=json.loads(pathlib.Path('dev-matrix-plan.json').read_text());host=sys.argv[1];jobs=plan['assignments'][host]
prerequisite=pathlib.Path('cap2048-process-all/process-receipt.json') if host in ['lead','dev01','dev02','dev03','dev04'] else pathlib.Path('worker-bootstrap-process-001/process-receipt.json')
while not prerequisite.exists():time.sleep(15)
assert json.loads(prerequisite.read_text())['exit_code']==0, str(prerequisite)
if host not in ['lead','dev01','dev02','dev03','dev04']:assert json.loads(pathlib.Path('BOOTSTRAP-VERIFIED.json').read_text())['fixture_exact']
from experiments.safety_selection.common import code_identity
from experiments.safety_selection.config import load_recipe,config_sha256
assert code_identity()['sha256']==plan['engine_sha256']
assert config_sha256(load_recipe(plan['recipe_path']))==plan['recipe_sha256']
assert pathlib.Path(plan['prepared_path'],'manifest.sha256').read_text().strip()==plan['manifest_sha256']
env={**os.environ,'CUBLAS_WORKSPACE_CONFIG':':4096:8','CUDA_VISIBLE_DEVICES':'0','TOKENIZERS_PARALLELISM':'false','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONPATH':str(ROOT)}
for job in jobs:
 cmd=['python3','process_receipt.py','--out',f"dev-matrix-process-{job['seed']}-001",'--','venv/bin/python','-m','experiments.safety_selection','calibrate','--prepared',plan['prepared_path'],'--recipe',plan['recipe_path'],'--arms',job['arm'],'--seeds',str(job['seed']),'--out-root','dev-matrix-001']
 subprocess.run(cmd,env=env,check=True)
