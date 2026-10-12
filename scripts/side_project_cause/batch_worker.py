"""Run a frozen A/C/D block with the unchanged safety-selection engine on a pod.

No recipe selection or outcome-based continuation. Each unit gets a new process,
optimizer and seeded initialization. Technical failures remain in BATCH-DONE.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def now():
    return dt.datetime.now(dt.timezone.utc)


def remaining():
    beat = read('/workspace/.pod-timer/heartbeat.json')
    assert beat['state'] == 'armed' and beat['supervised'] is True
    assert all(beat['can_stop'].values())
    stop = dt.datetime.fromisoformat(beat['governing']['stop_at_utc'].replace('Z', '+00:00'))
    return (stop - now()).total_seconds()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--protocol', required=True)
    p.add_argument('--protocol-sha256', required=True)
    p.add_argument('--model', choices=['olmo1b', 'olmo7b'], required=True)
    args = p.parse_args()
    assert sha(args.protocol) == args.protocol_sha256, 'protocol hash'
    protocol = read(args.protocol)
    assert protocol['status'] == 'FROZEN' and protocol['seed_blocks'] == 1
    assert not any(os.environ.get(k) for k in ('HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN', 'RUNPOD_OPERATOR_API_KEY'))
    assert not Path.home().joinpath('.cache/huggingface/token').exists()
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import load_recipe, config_sha256
    from experiments.safety_selection.engine import learning_rate
    assert code_identity()['sha256'] == protocol['engine_sha256'], 'engine hash'
    assert read('BOOTSTRAP-READY.json')['ok'] is True
    pre = read('PREFLIGHT-DONE.json')
    assert pre['ok'] is True and pre['init_equals_untuned'] is True
    prepared = protocol['prepared_path']
    assert Path(prepared, 'manifest.sha256').read_text().strip() == protocol['prepared_manifest_sha256']
    units = [u for u in protocol['units'] if u['model'] == args.model]
    assert len(units) == 3 and {u['arm'] for u in units} == {'A', 'C', 'D'}
    ordered = sorted(units, key=lambda u: u['execution_index'])
    recipes = {u['arm']: load_recipe(u['recipe_path']) for u in units}
    assert pre['recipe'] == next(u['recipe_path'] for u in units if u['arm'] == 'A')
    for unit in units:
        assert sha(unit['recipe_path']) == unit['recipe_file_sha256']
        assert config_sha256(recipes[unit['arm']]) == unit['config_sha256']
        for key in ('model', 'generation', 'guard', 'arc', 'attribution', 'secondary_toxicity'):
            assert recipes[unit['arm']][key] == recipes['A'][key], key
        allowed = {'loss', 'loss_weighting', 'lr_schedule', 'warmup_steps', 'schedule_until'}
        for key in set(recipes['A']['train']) | set(recipes[unit['arm']]['train']):
            if key not in allowed:
                assert recipes['A']['train'].get(key) == recipes[unit['arm']]['train'].get(key), key
    base = Path('cause')
    base.mkdir(exist_ok=True)
    done_path = base / f'{args.model}-BATCH-DONE.json'
    assert not done_path.exists(), 'a completed batch is never replaced'
    engine = [sys.executable, '-m', 'experiments.safety_selection']
    env = {k: v for k, v in os.environ.items() if 'TOKEN' not in k and k != 'RUNPOD_OPERATOR_API_KEY'}
    env.update(HF_HUB_OFFLINE='1', CUBLAS_WORKSPACE_CONFIG=':4096:8', CUDA_VISIBLE_DEVICES='0',
               TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4')
    results = []
    fingerprints = []
    target_counts = {r['row_id']: r['target_tokens'] for r in
                     (json.loads(line) for line in Path(prepared, 'engine/train_rows.jsonl').read_text().splitlines())}
    for unit in ordered:
        record = {'arm': unit['arm'], 'seed': unit['seed'], 'run_dir': unit['run_dir'], 'started_utc': now().isoformat()}
        results.append(record)
        save(base / f'{args.model}-progress.json', {'units': results, 'protocol_sha256': args.protocol_sha256})
        # Admission depends only on elapsed resource use, never measured outcomes.
        if remaining() < protocol['hosts'][args.model]['arm_admission_seconds'] + 300:
            record.update(status='not_started_resource_cap', finished_utc=now().isoformat())
            break
        job_path = base / f"{args.model}-{unit['arm']}-job.json"
        make = engine + ['make-job', 'run-one', '--recipe', unit['recipe_path'], '--prepared', prepared,
                         '--out', str(job_path), '--split', 'dev', '--arm', 'a0', '--seed', str(unit['seed']),
                         '--role', 'development', '--target', 'e1', '--bank', 'dev', '--pin-code',
                         '--wall-limit-seconds', str(protocol['hosts'][args.model]['unit_wall_seconds'])]
        run = engine + ['run-one', '--job', str(job_path), '--recipe', unit['recipe_path'], '--prepared', prepared,
                        '--out', unit['run_dir'], '--registry', f'cause/{args.model}-registry.jsonl']
        verify = engine + ['verify', '--run', unit['run_dir'], '--prepared', prepared]
        for label, command in [('make', make), ('run', run), ('verify', verify)]:
            with open(base / f"{args.model}-{unit['arm']}-{label}.log", 'xb') as log:
                result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            record[f'{label}_exit'] = result.returncode
            if result.returncode:
                break
        record['finished_utc'] = now().isoformat()
        if any(record.get(k) != 0 for k in ('make_exit', 'run_exit', 'verify_exit')):
            record['status'] = 'technical_failure'
            save(base / f'{args.model}-progress.json', {'units': results, 'protocol_sha256': args.protocol_sha256})
            break
        root = Path(unit['run_dir'])
        state = read(root / 'states/init/state.json')
        rows = [json.loads(line) for line in (root / 'steps.jsonl').read_text().splitlines()]
        assert len(rows) == 38 and [r['step'] for r in rows] == list(range(1, 39))
        row_digest = hashlib.sha256(json.dumps([r['rows'] for r in rows], separators=(',', ':')).encode()).hexdigest()
        train = recipes[unit['arm']]['train']
        expected_lrs = [learning_rate(train['lr'], train['lr_schedule'], train.get('warmup_steps', 0), 38, i)
                        for i in range(1, 39)]
        assert [r['lr'] for r in rows] == expected_lrs, 'applied learning rates differ'
        loss_differences = []
        for step in rows:
            losses = step['example_losses']
            assert len(losses) == len(step['rows'])
            if train.get('loss_weighting') == 'token_mean':
                weights = [target_counts[r] for r in step['rows']]
                expected = math.fsum(loss * weight for loss, weight in zip(losses, weights)) / sum(weights)
            else:
                expected = math.fsum(losses) / len(losses)
            difference = abs(expected - step['loss'])
            assert difference < 1e-5, 'measured step objective differs from frozen reduction'
            loss_differences.append(difference)
        fingerprint = {'init_fingerprint': state['init_fingerprint'], 'row_order_sha256': row_digest}
        assert not fingerprints or fingerprint == fingerprints[0], 'paired initialization/order differs'
        fingerprints.append(fingerprint)
        record.update(status='complete_verified', complete_sha256=sha(root / 'COMPLETE.json'),
                      paired_identity=fingerprint, applied_lrs=expected_lrs,
                      max_objective_reconstruction_error=max(loss_differences))
        save(base / f'{args.model}-progress.json', {'units': results, 'protocol_sha256': args.protocol_sha256})
        print(json.dumps({'model': args.model, 'arm': unit['arm'], 'event': record['status']}), flush=True)
    completed = {r['arm'] for r in results if r.get('status') == 'complete_verified'}
    for unit in ordered:
        if unit['arm'] not in {r['arm'] for r in results}:
            results.append({'arm': unit['arm'], 'seed': unit['seed'], 'run_dir': unit['run_dir'],
                            'status': 'not_started_after_batch_stop'})
    done = {'utc': now().isoformat(), 'model': args.model, 'protocol_sha256': args.protocol_sha256,
            'engine_sha256': protocol['engine_sha256'], 'units': results, 'ok': completed == {'A', 'C', 'D'}}
    save(done_path, done)
    print(json.dumps({'model': args.model, 'ok': done['ok'], 'completed_arms': sorted(completed)}), flush=True)
    return 0 if done['ok'] else 1


def safe_main():
    try:
        return main()
    except (Exception, SystemExit) as exc:
        # Preserve failures of identity/numeric/resource checks as batch outcomes.
        # A hard container kill may leave only progress; that also blocks analysis.
        def argument(name):
            return sys.argv[sys.argv.index(name) + 1]
        try:
            model = argument('--model')
            assert model in ('olmo1b', 'olmo7b')
            protocol = read(argument('--protocol'))
            base = Path('cause')
            base.mkdir(exist_ok=True)
            if (base / f'{model}-BATCH-DONE.json').exists():
                return 1  # Preserve an earlier sealed batch receipt on duplicate invocation.
            progress = base / f'{model}-progress.json'
            results = read(progress)['units'] if progress.exists() else []
            if results and results[-1].get('status') != 'complete_verified':
                results[-1].update(status='technical_failure', error_type=type(exc).__name__)
            for unit in protocol['units']:
                if unit['model'] == model and unit['arm'] not in {r['arm'] for r in results}:
                    results.append({'arm': unit['arm'], 'seed': unit['seed'], 'run_dir': unit['run_dir'],
                                    'status': 'not_started_after_batch_stop'})
            save(base / f'{model}-BATCH-DONE.json', {
                'utc': now().isoformat(), 'model': model, 'protocol_sha256': argument('--protocol-sha256'),
                'engine_sha256': protocol.get('engine_sha256'), 'ok': False,
                'error_type': type(exc).__name__, 'units': results})
        except (Exception, SystemExit):
            pass  # Cannot invent a receipt identity when the frozen inputs are unreadable.
        print(json.dumps({'event': 'batch-failed', 'error_type': type(exc).__name__}), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(safe_main())
