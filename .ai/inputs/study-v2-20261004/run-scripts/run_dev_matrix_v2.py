"""The frozen development matrix's two jobs for one host, as new explicit attempts (4 October 2026).

The identity checks and the calibrate arguments are those of dev-matrix-assets/run_dev_matrix.py
(2 October). Three things differ, because these are new pods after the loss recorded in
research/experiments/2026-10-02-runpod-credit-incident.md: the output root is dev-matrix-002 and the
receipts end in -002 (new attempts, never the lost dev-matrix-001 names), and every host requires its
own fresh bootstrap receipt and BOOTSTRAP-VERIFIED.json (the old-host cap-sensitivity branch does not apply).
"""
import json, os, pathlib, subprocess, sys
ROOT = pathlib.Path('/workspace/attribution-study-v2'); os.chdir(ROOT)
plan = json.loads(pathlib.Path('dev-matrix-plan.json').read_text()); host = sys.argv[1]; jobs = plan['assignments'][host]
receipt = json.loads(pathlib.Path('worker-bootstrap-process-001/process-receipt.json').read_text())
assert receipt['exit_code'] == 0, 'bootstrap did not succeed'
assert json.loads(pathlib.Path('BOOTSTRAP-VERIFIED.json').read_text())['fixture_exact']
from experiments.safety_selection.common import code_identity
from experiments.safety_selection.config import load_recipe, config_sha256
assert code_identity()['sha256'] == plan['engine_sha256']
assert config_sha256(load_recipe(plan['recipe_path'])) == plan['recipe_sha256']
assert pathlib.Path(plan['prepared_path'], 'manifest.sha256').read_text().strip() == plan['manifest_sha256']
env = {**os.environ, 'CUBLAS_WORKSPACE_CONFIG': ':4096:8', 'CUDA_VISIBLE_DEVICES': '0', 'TOKENIZERS_PARALLELISM': 'false',
       'OMP_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4', 'PYTHONPATH': str(ROOT)}
for job in jobs:
    cmd = ['python3', 'process_receipt.py', '--out', f"dev-matrix-process-{job['seed']}-002", '--', 'venv/bin/python', '-m',
           'experiments.safety_selection', 'calibrate', '--prepared', plan['prepared_path'], '--recipe', plan['recipe_path'],
           '--arms', job['arm'], '--seeds', str(job['seed']), '--out-root', 'dev-matrix-002']
    subprocess.run(cmd, env=env, check=True)
