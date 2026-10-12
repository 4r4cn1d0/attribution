"""Bounded operator for one causal-study pod; uses the existing RunPod kit tools.

GPU caps and budget reservations are frozen before outcomes. No deletion, recipe
fallback or outcome-dependent retry. Outputs are pulled before the confirmed stop.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--protocol', required=True)
    p.add_argument('--protocol-sha256', required=True)
    p.add_argument('--model', choices=['olmo1b', 'olmo7b'], required=True)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    protocol_path = Path(args.protocol).resolve()
    assert sha(protocol_path) == args.protocol_sha256, 'protocol hash'
    protocol = read(protocol_path)
    assert protocol['status'] == 'FROZEN' and protocol['seed_blocks'] == 1
    spec = protocol['hosts'][args.model]
    kit = Path(spec['kit_path']).resolve()
    plan = read(kit / 'plan.json')
    host = spec['host']
    assert plan['hosts'][host]['cap_hours'] == spec['cap_hours']
    assert plan['engine_sha256'] == protocol['engine_sha256']
    assert sha(kit / 'payload.tar.gz') == spec['payload_sha256']
    assert sha(kit / 'setup/worker-setup-probe.tar.gz') == spec['setup_sha256']
    setup_receipt = read(kit / 'setup/setup-receipt.json')
    assert setup_receipt['setup']['sha256'] == spec['setup_sha256']
    assert setup_receipt['engine_sha256'] == protocol['engine_sha256']
    # The payload protocol is a copy of the exact freeze. Its hash is also sent as argv.
    for name, digest in spec['kit_code_sha256'].items():
        assert sha(kit / name) == digest, f'kit code differs: {name}'
    if not args.execute:
        print(json.dumps({'model': args.model, 'host': host, 'cap_hours': spec['cap_hours'],
                          'execution_order': spec['execution_order'], 'protocol_sha256': args.protocol_sha256,
                          'steps': ['budget+create', 'GPU/timer', 'bootstrap', 'payload', 'preflight-A',
                                    'fresh-A/C/D', 'pull-all', 'confirmed-stop'], 'spend': 0}, indent=2))
        return 0
    sys.path.insert(0, str(kit))
    h = importlib.import_module('host')
    op = importlib.import_module('orchestrate')
    budget = importlib.import_module('budget')
    pc = importlib.import_module('probe_constants')
    assert h.MAX_PRICE == pc.MAX_PRICE == spec['max_hourly_usd']
    assert budget.RESERVE_USD == protocol['account_reserve_usd']
    out = kit / 'operator'
    out.mkdir(exist_ok=True)
    lock = (out / 'operator.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (out / 'finished.json').exists(), 'this pilot attempt already ended; no automatic relaunch'
    assert not (kit / 'hosts' / host / 'pod.json').exists(), 'a pod already exists for this pilot host'
    def event(name, **details):
        record = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'model': args.model,
                  'host': host, 'event': name, **details}
        with (out / 'events.jsonl').open('a') as f:
            f.write(json.dumps(record) + '\n')
        print(json.dumps(record), flush=True)
    pod_created = False
    finished = {'model': args.model, 'host': host, 'protocol_sha256': args.protocol_sha256, 'ok': False}
    try:
        # Same shared budget lock as the recovery/family kits. The reserve retains
        # recovery, judge and storage funds even while these two pods run in parallel.
        with budget.lock():
            h.reconcile(host)
            proj = budget.projection()
            upper = spec['cap_hours'] * spec['max_hourly_usd']
            allowed = proj['free_after_commitments_usd'] - upper >= protocol['account_reserve_usd']
            save(out / 'launch-budget.json', {**proj, 'new_gpu_upper_usd': upper, 'allowed': allowed})
            if not allowed:
                raise RuntimeError('remaining-balance budget admission refused')
            record = h.create(host)
            pod_created = True
            event('created', pod_id=record['id'], cost_per_hr=record['costPerHr'], cap_stop_utc=record['cap_stop_utc'])
        op.wait_ssh(host, seconds=600)
        op.check(host)
        op.bootstrap(host)
        ready = op.wait_file(host, 'BOOTSTRAP-READY.json', seconds=3600, every=30)
        assert ready['ok'] is True and ready['engine_sha256'] == protocol['engine_sha256']
        event('bootstrap-ready')
        if h.send(host, str(kit / 'payload.tar.gz'), f'{h.REMOTE_ROOT}/payload.tar.gz', spec['payload_sha256']):
            raise RuntimeError('payload transfer/hash failed')
        extract = (f'cd {h.REMOTE_ROOT} && python3 -c '
                   "\"import tarfile; t=tarfile.open('payload.tar.gz'); t.extractall('.',filter='data')\"")
        if h.ssh(host, extract):
            raise RuntimeError('payload extraction failed')
        if h.send(host, str(protocol_path), f'{h.REMOTE_ROOT}/cause/protocol.json', args.protocol_sha256):
            raise RuntimeError('frozen protocol transfer/hash failed')
        pre = op.preflight(host)
        assert pre['ok'] is True and pre['init_equals_untuned'] is True
        event('preflight-passed', recipe=pre['recipe'])
        # This new batch has its own frozen caps. The old single-family all-capped
        # cap gate is not used and its historical rules/files are not edited.
        command = (f'env HF_HUB_OFFLINE=1 PYTHONPATH={h.REMOTE_ROOT} CUBLAS_WORKSPACE_CONFIG=:4096:8 '
                   'CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 '
                   'venv/bin/python cause/batch_worker.py --protocol cause/protocol.json '
                   f'--protocol-sha256 {args.protocol_sha256} --model {args.model}')
        op.start_background(host, 'cause-outer', command)
        event('batch-started', execution_order=spec['execution_order'])
        stop = dt.datetime.fromisoformat(record['cap_stop_utc'].replace('Z', '+00:00'))
        while dt.datetime.now(dt.timezone.utc) < stop:
            result = op.ssh(host, f'cat {h.REMOTE_ROOT}/cause-outer/process-receipt.json 2>/dev/null')
            if result.returncode == 0 and result.stdout.strip():
                finished['process_receipt'] = json.loads(result.stdout)
                break
            latest = h.get(host)
            if latest['desiredStatus'] != 'RUNNING':
                raise RuntimeError('pod stopped before batch receipt')
            time.sleep(60)
        else:
            raise RuntimeError('batch reached frozen pod cap')
        result = op.ssh(host, f'cat {h.REMOTE_ROOT}/cause/{args.model}-BATCH-DONE.json 2>/dev/null')
        if result.returncode == 0:
            finished['batch'] = json.loads(result.stdout)
        batch = finished.get('batch') or {}
        finished['ok'] = (batch.get('ok') is True and batch.get('model') == args.model
                          and batch.get('protocol_sha256') == args.protocol_sha256
                          and batch.get('engine_sha256') == protocol['engine_sha256']
                          and finished['process_receipt'].get('exit_code') == 0)
        event('batch-ended', ok=finished['ok'])
    except (Exception, SystemExit) as exc:
        # Only type/classification is public; API/SSH output can contain private paths.
        finished['error_type'] = type(exc).__name__
        finished['error'] = str(exc)[:300] if not h.secret_scan.scan_text(str(exc)) else '[redacted]'
        event('operator-error', error_type=type(exc).__name__, detail=finished['error'])
    finally:
        # A failed create can still leave a recorded pod (e.g. price refusal).
        pod_created = pod_created or (kit / 'hosts' / host / 'pod.json').exists()
        if pod_created:
            try:
                cap = dt.datetime.fromisoformat(h.state(host)['cap_stop_utc'].replace('Z', '+00:00'))
                left = (cap - dt.datetime.now(dt.timezone.utc)).total_seconds()
                timeout = max(1, min(protocol['retrieval_deadline_seconds'], left - 30))
                with (out / 'pull.log').open('ab') as log:
                    pull = subprocess.Popen([sys.executable, str(kit / 'host.py'), 'pull', host],
                                            stdout=log, stderr=subprocess.STDOUT,
                                            env=h.clean_env(), start_new_session=True)
                    try:
                        finished['pull_exit'] = pull.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        os.killpg(pull.pid, signal.SIGTERM)
                        try:
                            pull.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(pull.pid, signal.SIGKILL)
                            pull.wait()
                        finished['pull_exit'] = 'deadline'
                if finished['pull_exit'] != 0:
                    finished['ok'] = False
                if finished['pull_exit'] == 0:
                    pulled = kit / 'retrieved' / host
                    archive = sorted(pulled.glob('pull-*.tar'))[-1]
                    tree = pulled / 'tree'
                    assert not tree.exists(), 'retrieved tree never replaced'
                    tree.mkdir()
                    with tarfile.open(archive) as tar:
                        tar.extractall(tree, filter='data')
                    finished['archive_sha256'] = sha(archive)
            except (Exception, SystemExit) as exc:
                finished['pull_error_type'] = type(exc).__name__
                finished['ok'] = False
            finally:
                try:
                    finished['stop'] = h.stop(host)
                    if not finished['stop']['confirmed']:
                        finished['ok'] = False
                except (Exception, SystemExit) as exc:
                    finished['stop_error_type'] = type(exc).__name__
                    finished['ok'] = False
                event('stop-result', confirmed=(finished.get('stop') or {}).get('confirmed', False))
        # Failed create replies can leave IDs without pod.json. They retain
        # shutdown responsibility and never permit a new suffix while unresolved.
        unresolved = kit / 'hosts' / host / 'unresolved-orphans.json'
        if unresolved.exists():
            orphan_results = {pod_id: h.stop_id(pod_id) for pod_id in read(unresolved)['ids']}
            finished['orphan_stops'] = orphan_results
            if not all(result['confirmed'] for result in orphan_results.values()):
                finished['ok'] = False
            save(unresolved, {'ids': [pod_id for pod_id, result in orphan_results.items() if not result['confirmed']],
                              'stop_results': orphan_results})
        save(out / 'finished.json', finished)
    return 0 if finished['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
