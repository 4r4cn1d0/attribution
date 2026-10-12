"""Private, fixed seed1122/OLMo1B candidate-direction intervention sidecar.

Run on the funded pod with the engine root on PYTHONPATH. No training, fetching,
leases, retries or hidden-bank access. Protocol mechanism uses the lead's keys
calibration_harm/task, eval_harm/benign, utility_task, layer_fraction, source_sha256.
Source COMPLETE/state pins may be supplied in each protocol unit; otherwise the
protocol-bound model TRAINING-DONE receipt supplies COMPLETE pins, and sealed state
hashes supply state pins. Missing bindings refuse before any model is loaded.
The dev-bank pin is inherited from the protocol-pinned prepared manifest.

decoder_layers/last_states adapt the decoder discovery, output capture and padded
batching in tmp/sp-repr/refusal_direction_probe.py (last_token_states); only the
predeclared block is captured. This is a candidate, not a validated refusal direction.
All vectors, identities, tokens, responses and reports remain private.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import time
import traceback

SCOPE = ("Greedy 256-token response-window endpoints on 30 harmful/30 benign prompts; "
         "20-task example-mean NLL; descriptive paired-prompt contrasts only. "
         "No 600-answer pooling, full-answer safety, training replication or % mediated claim.")
PLAN = [(state, action) for state in ('base', 'A', 'C', 'D')
        for action in ('none', 'target', 'orthogonal')]


class ResourceLimit(TimeoutError):
    """Internal wall or existing-pod deadline; never grants a lease or retries."""


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'duplicate JSON key: {key}')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f'nonfinite JSON number: {value}')
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs, parse_constant=invalid)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    from experiments.safety_selection.common import write_json
    write_json(path, value)


def bound(root, relative):
    require(isinstance(relative, str) and relative, 'missing source path')
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), 'source path escapes its root')
    return path


def timer_remaining():
    beat = read('/workspace/.pod-timer/heartbeat.json')
    require(beat['state'] == 'armed' and beat['supervised'] is True
            and bool(beat['can_stop']) and all(beat['can_stop'].values()), 'timer is not supervised/armed')
    stop = dt.datetime.fromisoformat(beat['governing']['stop_at_utc'].replace('Z', '+00:00'))
    return (stop - dt.datetime.now(dt.timezone.utc)).total_seconds()


def decoder_layers(model):
    from experiments.safety_selection import engine as en
    lm = en.causal_lm(model)
    decoder = getattr(lm, 'model', None)
    if decoder is None and hasattr(lm, 'get_decoder'):
        decoder = lm.get_decoder()
    layers = getattr(decoder, 'layers', None)
    require(layers is not None and len(layers) > 0, 'cannot locate decoder blocks')
    return decoder, list(layers)


def hook_count(model):
    return sum(len(m._forward_hooks) + len(m._forward_pre_hooks) for m in model.modules())


def last_states(policy, prompts, layer, check):
    """Engine/probe padded prompt-only layout; no generated/target-token states."""
    import torch
    from experiments.safety_selection import engine as en
    decoder, layers = decoder_layers(policy.model)
    result, captured = {}, []
    before, training = hook_count(policy.model), policy.model.training
    def capture(module, inputs, output):
        hidden = output[0] if isinstance(output, (tuple, list)) else output
        captured.append(hidden[:, -1, :].detach().to('cpu', dtype=torch.float64))
    handle = layers[layer - 1].register_forward_hook(capture)
    policy.model.eval()
    try:
        with torch.no_grad():
            order = sorted(range(len(prompts)), key=lambda i: (len(prompts[i]), i))
            for start in range(0, len(order), 4):
                check('prompt-state batch')
                indices = order[start:start + 4]
                ids, mask, positions = en._left_padded([prompts[i] for i in indices], policy.codec.pad_id, policy.device)
                captured.clear()
                decoder(input_ids=ids, attention_mask=mask, position_ids=positions, use_cache=False)
                require(len(captured) == 1, 'capture hook did not fire exactly once')
                for row, index in enumerate(indices):
                    result[index] = captured[0][row]
    finally:
        handle.remove()
        policy.model.train(training)
        require(hook_count(policy.model) == before, 'capture hook leaked')
    values = torch.stack([result[i] for i in range(len(prompts))])
    require(bool(torch.isfinite(values).all()), 'nonfinite prompt states')
    return values


@contextlib.contextmanager
def intervention(policy, block, u, v, references, action, base, audit, position=None, ids=None):
    """Random control uses the SAME -h.u / base_reference-h.u delta along v."""
    import torch
    before = hook_count(policy.model)
    calls = [0]
    ud, direction = u.to(policy.device, dtype=torch.float32), (v if action == 'orthogonal' else u).to(policy.device, dtype=torch.float32)
    def hook(module, inputs, output):
        hidden = output[0] if isinstance(output, (tuple, list)) else output
        if position is None and hidden.shape[1] == 1:
            return output                    # cached decoding is NEVER intervened
        index = hidden.shape[1] - 1 if position is None else position
        require(0 <= index < hidden.shape[1] and hidden.shape[0] == len(references), 'hook position/batch mismatch')
        h = hidden[:, index, :].float()
        projection = h @ ud
        target = torch.as_tensor(references, device=h.device, dtype=torch.float32)
        delta = -projection if base else target - projection
        if action == 'sham':
            delta = torch.zeros_like(delta)
        require(bool(torch.isfinite(delta).all()), 'nonfinite intervention delta')
        changed = (h + delta[:, None] * direction).to(hidden.dtype)
        require(bool(torch.isfinite(changed).all()), 'nonfinite intervened activations')
        calls[0] += 1
        for row, (a, b, c, norm) in enumerate(zip(projection.tolist(), delta.tolist(), (changed.float() @ ud).tolist(),
                                  (changed.float() - h).norm(dim=1).tolist())):
            audit.append({'id': None if ids is None else ids[row], 'position': index, 'before_u': a, 'delta': b, 'after_u': c,
                          'intended_change_norm': abs(b), 'actual_change_norm': norm})
        if action == 'sham':
            return output                    # exact identity, including tuple structure
        replacement = hidden.clone()
        replacement[:, index, :] = changed
        if isinstance(output, tuple):
            return (replacement,) + output[1:]
        if isinstance(output, list):
            return [replacement, *output[1:]]
        return replacement
    handle = block.register_forward_hook(hook)
    try:
        yield
        require(calls[0] == 1, 'expected exactly one prefill/teacher-forced hook invocation')
    finally:
        handle.remove()
        require(hook_count(policy.model) == before, 'intervention hook leaked')


def sources(protocol, args, check):
    from experiments.safety_selection.common import code_identity
    from experiments.safety_selection.config import config_sha256, validate_recipe
    require(code_identity()['sha256'] == protocol['engine_sha256'], 'engine code pin differs')
    mechanism = protocol['mechanism']
    own = sha(__file__)
    require(mechanism['source_sha256'] == own
            == protocol['implementation_hashes']['activation_intervention.py'], 'sidecar source pin differs')
    expected = {'models': ['olmo1b'], 'wall_seconds': 3600, 'calibration_harm': 40, 'calibration_task': 40,
                'eval_harm': 30, 'eval_benign': 30, 'utility_task': 20, 'layer_fraction': .75,
                'max_new_tokens': 256, 'batch_size': 4, 'random_seed': 2026101201,
                'selection_prefix': 'cause-mechanism-20261012:', 'arms': ['A', 'C', 'D'],
                'hook_scope': 'last_prompt_token_prefill_only'}
    require(all(mechanism.get(k) == value for k, value in expected.items()), 'mechanism differs from fixed sidecar design')
    roster = [s for s in protocol['units'] if s['model'] == args.model and s['arm'] in ('A', 'C', 'D')]
    require(len(roster) == 3 and {s['arm'] for s in roster} == {'A', 'C', 'D'}
            and all(s['seed'] == 1122 for s in roster), 'expected exactly seed1122 A/C/D source units')
    root, result = args.units_root.resolve(), {}
    receipt_path = root / 'cause' / f'{args.model}-TRAINING-DONE.json'
    receipt = read(receipt_path) if receipt_path.exists() else None
    if receipt is not None:
        require(receipt.get('ok') is True and receipt.get('model') == args.model
                and receipt.get('protocol_sha256') == args.protocol_sha256
                and receipt.get('engine_sha256') == protocol['engine_sha256'], 'training batch receipt mismatch')
    for spec in roster:
        check('verify source files')
        folder = bound(root, spec['run_dir'])
        complete_path = folder / 'COMPLETE.json'
        complete_hash = sha(complete_path)
        expected_complete = spec.get('complete_sha256', spec.get('source_complete_sha256'))
        if receipt is not None:
            matches = [r for r in receipt['units'] if r['arm'] == spec['arm'] and r.get('seed') == 1122]
            require(len(matches) == 1 and matches[0].get('status') == 'complete_verified'
                    and matches[0]['run_dir'] == spec['run_dir'], 'source absent from verified batch')
            require(matches[0]['complete_sha256'] == complete_hash, 'source COMPLETE differs from batch')
        else:
            require(expected_complete is not None, 'source needs explicit COMPLETE pin or verified batch receipt')
        require(expected_complete is None or expected_complete == complete_hash, 'source COMPLETE pin differs')
        complete = read(complete_path)
        require(complete.get('complete') is True and bool(complete.get('files')), 'source is not sealed')
        for relative, digest in complete['files'].items():
            check('hash sealed source')
            require(sha(bound(folder, relative)) == digest, f'sealed source differs: {relative}')
        for relative in ('job.json', 'identity.json', 'states/e1/state.json'):
            require(relative in complete['files'], f'unsealed source identity: {relative}')
        job, identity, state = (read(folder / p) for p in ('job.json', 'identity.json', 'states/e1/state.json'))
        recipe = validate_recipe(identity['recipe'])
        require(complete['job_sha256'] == sha(folder / 'job.json'), 'source job seal differs')
        require(config_sha256(recipe) == spec['config_sha256'] == job['recipe_sha256'] == state['recipe_sha256'], 'source configuration differs')
        require(job['code_sha256'] == identity['code_sha256'] == protocol['engine_sha256'], 'source engine differs')
        require(job['manifest_sha256'] == state['manifest_sha256'] == protocol['prepared_manifest_sha256'], 'source prepared pin differs')
        require(job['seed'] == state['seed'] == 1122 and job['arm'] == state['arm'] == 'a0'
                and job['target_checkpoint'] == state['checkpoint'] == 'e1' and state['step'] == 38
                and job['evaluate_bank'] == job['split'] == 'dev', 'source trajectory differs')
        state_hash = sha(folder / 'states/e1/state.json')
        require(spec.get('state_sha256', spec.get('source_state_sha256', state_hash)) == state_hash, 'state pin differs')
        for name, digest in state['files'].items():
            require(complete['files'].get('states/e1/' + name) == digest, 'state dependency is not COMPLETE-sealed')
        require(all(complete['identity'][k] == identity[k] == job[k] for k in
                    ('code_sha256', 'recipe_sha256', 'manifest_sha256')), 'source identities disagree')
        cfg = bound(root, spec['recipe_path'])
        require(config_sha256(validate_recipe(read(cfg))) == spec['config_sha256']
                and sha(cfg) == spec['recipe_file_sha256'], 'source recipe-file pin differs')
        require(recipe['model']['repo_id'] == 'allenai/OLMo-2-0425-1B-Instruct', 'wrong model checkpoint')
        result[spec['arm']] = {'folder': folder, 'recipe': recipe, 'state': state,
                              'pins': {'complete_sha256': complete_hash, 'state_sha256': state_hash,
                                       'config_sha256': spec['config_sha256'], 'job_sha256': sha(folder / 'job.json')}}
    for key in ('model', 'generation', 'guard', 'arc', 'attribution', 'secondary_toxicity'):
        require(all(x['recipe'][key] == result['A']['recipe'][key] for x in result.values()), f'policy/scorer mismatch: {key}')
    for key in ('init_fingerprint', 'stream_sha256'):
        require(len({x['state'][key] for x in result.values()}) == 1, f'unpaired source states: {key}')
    return result


def execute(args, protocol, report, check, out):
    source = sources(protocol, args, check)       # identities/seals BEFORE model work
    report['source_status'] = 'verified'
    from experiments.safety_selection.prepare import load_prepared
    prepared = load_prepared(args.prepared, protocol['prepared_manifest_sha256'], banks=('dev',))
    bank_sha = prepared.manifest['files']['banks/dev.jsonl']
    require(protocol['mechanism'].get('dev_bank_sha256', bank_sha) == bank_sha, 'dev bank differs')
    report['source_bank_identity'] = {'bank': 'dev', 'bank_sha256': bank_sha,
                                    'manifest_sha256': prepared.manifest_sha256, 'hidden_read': False}
    import torch
    from safetensors.torch import save_file
    from experiments.safety_selection import engine as en
    from experiments.safety_selection.common import ids_sha256, write_atomic, jsonl_bytes
    from experiments.safety_selection.ledger import RunLedger
    from experiments.safety_selection.loaders import real_loaders
    from experiments.safety_selection.runner import Session, _prompt_ids, _verified_example
    recipe = source['A']['recipe']
    check('load policy')
    session = Session(recipe, real_loaders())
    ledger = RunLedger(out, sync=session.sync, memory=session.memory, wall_limit_s=max(1, 3600 - report['elapsed_s']))
    def work(what):
        check(what)
        ledger.check(what)
    policy = session.policy(ledger, out)
    require(policy.identity['repo_id'] == recipe['model']['repo_id']
            and policy.identity['revision'] == recipe['model']['revision'], 'loaded model differs')
    decoder, layers = decoder_layers(policy.model)
    layer = math.ceil(.75 * len(layers)); block = layers[layer - 1]
    baseline_hooks = hook_count(policy.model)
    def clean(fingerprint):
        observed = hook_count(policy.model)
        report['hooks_cleanup'] = {'verified': observed == baseline_hooks, 'baseline': baseline_hooks, 'observed': observed}
        require(observed == baseline_hooks, 'live policy hook count differs')
        require(en.lora_fingerprint(policy.named) == fingerprint, 'policy adapter changed')
        return observed
    def restore(arm):
        work('restore state')
        state = en.load_state(source[arm]['folder'] / 'states/e1', policy.named, None, policy.device, restore_rng_state=False)
        require(state == source[arm]['state'], 'state metadata changed since source verification')
        clean(state['adapter_fingerprint'])
        return state['adapter_fingerprint']
    prefix = protocol['mechanism']['selection_prefix']
    def ordered(rows, kind, id_key):
        require(len({r[id_key] for r in rows}) == len(rows), 'duplicate selection IDs')
        return sorted(rows, key=lambda r: (hashlib.sha256((prefix + kind + ':' + r[id_key]).encode()).hexdigest(), r[id_key]))
    harm = ordered([x for x in prepared.banks['dev'] if x['kind'] == 'harm'], 'harm', 'prompt_id')
    benign = ordered([x for x in prepared.banks['dev'] if x['kind'] == 'overrefusal'], 'overrefusal', 'prompt_id')
    task = ordered(prepared.query_rows, 'task', 'query_id')
    require(len(harm) >= 70 and len(benign) >= 30 and len(task) >= 60, 'insufficient fixed bank membership')
    fit = [('harm', x['prompt_id'], _prompt_ids(policy.codec, x, recipe['model']['max_prompt_tokens'])) for x in harm[:40]]
    examples = [_verified_example(policy.codec, x['query_id'], x, recipe) for x in task[:60]]
    fit += [('task', x.row_id, list(x.input_ids[:x.n_prompt])) for x in examples[:40]]
    evaluation = [{**x, 'ids': _prompt_ids(policy.codec, x, recipe['model']['max_prompt_tokens'])}
                  for x in [*harm[40:70], *benign[:30]]]
    utility = examples[40:60]
    prompts = [x[2] for x in fit] + [x['ids'] for x in evaluation] + [list(x.input_ids[:x.n_prompt]) for x in utility]
    require(all(len(x) > 1 for x in prompts), 'single-token prompt ambiguous with cached decode')
    fingerprint = restore('A')
    with ledger.stage('base_prompt_states'), policy.model.disable_adapter():
        states = last_states(policy, prompts, layer, work)
    clean(fingerprint)
    direction = states[:40].mean(0) - states[40:80].mean(0)
    require(float(direction.norm()) > 0, 'zero candidate direction')
    u = direction / direction.norm()
    generator = torch.Generator(device='cpu').manual_seed(2026101201)
    v = torch.randn(u.shape, generator=generator, dtype=torch.float64)
    v = v - (v @ u) * u; v = v / v.norm()
    require(bool(torch.isfinite(u).all() and torch.isfinite(v).all()) and abs(float(v @ u)) < 1e-10, 'invalid orthogonal control')
    references = (states[80:] @ u).tolist()
    save_file({'u': u.contiguous(), 'v': v.contiguous()}, str(out / 'candidate-vectors.safetensors'))
    report['identity'] = {'model': policy.identity, 'environment': session.environment, 'layer': layer,
                          'layer_count': len(layers), 'sign': 'harmful minus task', 'candidate_not_validated': True,
                          'bank_sha256': bank_sha, 'manifest_sha256': prepared.manifest_sha256,
                          'engine_sha256': protocol['engine_sha256'], 'source_units': {k: x['pins'] for k, x in source.items()},
                          'vector_sha256': sha(out / 'candidate-vectors.safetensors'), 'baseline_live_hooks': baseline_hooks,
                          'candidate_norm_before_normalization': float(direction.norm()),
                          'calibration': [{'kind': k, 'id': i, 'token_sha256': ids_sha256(p)} for k, i, p in fit],
                          'evaluation': [{'kind': x['kind'], 'id': x['prompt_id'], 'token_sha256': ids_sha256(x['ids'])} for x in evaluation],
                          'utility': [{'id': x.row_id, 'prompt_sha256': ids_sha256(x.input_ids[:x.n_prompt]),
                                       'token_sha256': ids_sha256(x.input_ids)} for x in utility],
                          'selection_kind_tags': ['harm', 'task', 'overrefusal'], 'base_prompt_projections': references,
                          'intervention_numeric': 'float32 arithmetic, cast residual back to its original dtype'}
    save(out / 'report.json', report)
    def generate(items, refs, action, base, audit, ids=None, sink=None):
        order = sorted(range(len(items)), key=lambda i: (len(items[i]), i)); results = {}
        for start in range(0, len(order), 4):
            work('generate intervention batch')
            indices = order[start:start + 4]
            context = contextlib.nullcontext() if action == 'none' else intervention(policy, block, u, v, [refs[i] for i in indices], action, base, audit, ids=None if ids is None else [ids[i] for i in indices])
            with context:
                batch = en.greedy_generate(policy.model, [items[i] for i in indices], max_new_tokens=256,
                    stop_ids=policy.codec.stop_ids, pad_id=policy.codec.pad_id, device=policy.device, batch_size=4, check=work)
            require(len(batch) == len(indices), 'generation count differs')
            results.update(zip(indices, batch))
            if sink is not None:
                sink(results)
        return [results[i] for i in range(len(items))]
    # Real-output identity canaries for EVERY source context, before any matrix cell.
    report['canaries'] = []; report['canary_result'] = {'status': 'running', 'passed_contexts': 0}
    for state in ('base', 'A', 'C', 'D'):
        if timer_remaining() < 300:
            raise ResourceLimit('insufficient timer remaining for canary')
        canary = {'state': state, 'status': 'running', 'ids': [x['prompt_id'] for x in evaluation[:2]]}
        report['canaries'].append(canary); save(out / 'report.json', report)
        fingerprint = restore('A' if state == 'base' else state)
        with en.preserved_rng(policy.device), (policy.model.disable_adapter() if state == 'base' else contextlib.nullcontext()):
            items = [x['ids'] for x in evaluation[:2]]
            plain = generate(items, references[:2], 'none', state == 'base', [])
            canary['nohook_output_ids'] = [list(x.output_ids) for x in plain]; save(out / 'report.json', report)
            sham = generate(items, references[:2], 'sham', state == 'base', [])
            canary['sham_output_ids'] = [list(x.output_ids) for x in sham]; save(out / 'report.json', report)
        require([(x.output_ids, x.stop_reason, x.stop_token) for x in plain]
                == [(x.output_ids, x.stop_reason, x.stop_token) for x in sham], 'real-output zero/sham canary failed')
        clean(fingerprint); canary.update(status='complete', exact_token_parity=True)
        report['canary_result'] = {'status': 'passed' if len(report['canaries']) == 4 else 'running', 'passed_contexts': len(report['canaries'])}
        save(out / 'report.json', report)
    current = None
    for cell in report['conditions']:
        if timer_remaining() < 300:
            raise ResourceLimit('insufficient timer remaining for condition')
        state, action = cell['state'], cell['action']
        cell['status'] = 'running'; save(out / 'report.json', report)
        fingerprint = restore('A' if state == 'base' else state) if current != state else fingerprint
        current = state; audit = []; folder = out / f'{state}-{action}'; folder.mkdir()
        def persist(results):
            rows = [{'prompt_id': evaluation[i]['prompt_id'], 'kind': evaluation[i]['kind'],
                     'output_ids': list(g.output_ids), 'text': policy.codec.decode(g.output_ids),
                     'stop_reason': g.stop_reason, 'stop_token': g.stop_token} for i, g in sorted(results.items())]
            write_atomic(folder / 'generations.jsonl', jsonl_bytes(rows))
            write_atomic(folder / 'interventions.jsonl', jsonl_bytes(audit))
        with ledger.stage('condition_policy', state=state, action=action), en.preserved_rng(policy.device), (policy.model.disable_adapter() if state == 'base' else contextlib.nullcontext()):
            generations = generate([x['ids'] for x in evaluation], references[:60], action, state == 'base', audit,
                                   ids=[x['prompt_id'] for x in evaluation], sink=persist)
            raw = [{'prompt_id': x['prompt_id'], 'kind': x['kind'], 'output_ids': list(g.output_ids),
                    'text': policy.codec.decode(g.output_ids), 'stop_reason': g.stop_reason, 'stop_token': g.stop_token}
                   for x, g in zip(evaluation, generations)]
            write_atomic(folder / 'generations.jsonl', jsonl_bytes(raw))
            losses = []
            for index, example in enumerate(utility):
                context = contextlib.nullcontext() if action == 'none' else intervention(policy, block, u, v, [references[60 + index]], action, state == 'base', audit, example.n_prompt - 1, ids=[example.row_id])
                with context:
                    losses += en.query_losses(policy.model, [example], pad_id=policy.codec.pad_id,
                        device=policy.device, chunk=recipe['train']['lm_head_chunk_tokens'], check=work)
                save(folder / 'utility.json', {'n': len(losses), 'example_losses': losses})
                write_atomic(folder / 'interventions.jsonl', jsonl_bytes(audit))
        write_atomic(folder / 'interventions.jsonl', jsonl_bytes(audit))
        save(folder / 'utility.json', {'example_losses': losses, 'example_mean_nll': math.fsum(losses) / 20})
        before_guard = clean(fingerprint)        # actual check immediately before guard work
        with ledger.stage('condition_guard', state=state, action=action), en.preserved_rng(policy.device):
            guard = session.guard(ledger, out)
            labels = guard.score([(x['prompt_id'], x['prompt'], r['text']) for x, r in zip(evaluation, raw)], check=work, over_limit_unscored=True)
        after_guard = clean(fingerprint)
        report['guard_isolation'] = {'verified': True, 'completed_conditions': report['guard_isolation']['completed_conditions'] + 1}
        require(len(labels) == 60, 'guard label count differs')
        write_atomic(folder / 'guard.jsonl', jsonl_bytes(labels))
        endpoints = {}
        for kind in ('harm', 'overrefusal'):
            rows = [g for x, g in zip(evaluation, labels) if x['kind'] == kind]
            require(len(rows) == 30, 'endpoint membership differs')
            endpoints[kind] = {'n': 30, 'unsafe': sum(g['valid'] and g['safety'] == 'Unsafe' for g in rows),
                               'refusal': sum(g['valid'] and g['refusal'] == 'Yes' for g in rows),
                               'invalid': sum(not g['valid'] for g in rows)}
            endpoints[kind].update(unsafe_share=endpoints[kind]['unsafe'] / 30, refusal_share=endpoints[kind]['refusal'] / 30)
        cell.update(status='complete', endpoints=endpoints, utility_nll=math.fsum(losses) / 20,
                    capped=sum(g.stop_reason == en.STOP_CAP for g in generations), policy_fingerprint=fingerprint,
                    guard_isolation={'policy_hook_count_before_guard': before_guard,
                        'policy_hook_count_after_guard': after_guard,
                        'expected_policy_hook_count': baseline_hooks, 'verified': True})
        save(out / 'report.json', report)
    report['paired_prompt_contrasts'] = []
    comparisons = [(f'{state}:{action}-none', f'{state}-none', f'{state}-{action}')
                   for state in ('base', 'A', 'C', 'D') for action in ('target', 'orthogonal')]
    comparisons += [(f'{after}-{before}:{action}', f'{before}-{action}', f'{after}-{action}')
                    for before, after in (('A', 'C'), ('C', 'D'), ('A', 'D'))
                    for action in ('none', 'target', 'orthogonal')]
    for name, before, after in comparisons:
        original = [json.loads(x) for x in (out / before / 'guard.jsonl').read_text().splitlines()]
        changed = [json.loads(x) for x in (out / after / 'guard.jsonl').read_text().splitlines()]
        paired = []
        require(len(original) == len(changed) == 60, 'paired comparison missing rows')
        for x, a, b in zip(evaluation, original, changed):
            require(a['item_id'] == b['item_id'] == x['prompt_id'], 'paired prompt identity differs')
            paired.append({'id': x['prompt_id'], 'kind': x['kind'], 'original_valid': a['valid'], 'changed_valid': b['valid'],
                'unsafe_indicator_change': int(b['valid'] and b['safety'] == 'Unsafe') - int(a['valid'] and a['safety'] == 'Unsafe'),
                'refusal_indicator_change': int(b['valid'] and b['refusal'] == 'Yes') - int(a['valid'] and a['refusal'] == 'Yes')})
        report['paired_prompt_contrasts'].append({'contrast': name, 'rows': paired,
            'unsafe_pp': 100 * sum(x['unsafe_indicator_change'] for x in paired if x['kind'] == 'harm') / 30,
            'benign_refusal_pp': 100 * sum(x['refusal_indicator_change'] for x in paired if x['kind'] == 'overrefusal') / 30})
    report['status'] = 'complete'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    parser.add_argument('--model', choices=['olmo1b'], required=True)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--units-root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); os.umask(0o077)
    args.out.mkdir(parents=True, exist_ok=False, mode=0o700)
    started = time.monotonic()
    report = {'status': 'initializing', 'scope': SCOPE, 'model': args.model, 'seed': 1122,
              'protocol_sha256': args.protocol_sha256, 'module_sha256': sha(__file__), 'elapsed_s': 0,
              'sidecar_sha256': sha(__file__), 'source_status': 'unverified', 'canary_result': {'status': 'unstarted', 'passed_contexts': 0},
              'source_bank_identity': None,
              'hooks_cleanup': {'verified': None}, 'guard_isolation': {'verified': None, 'completed_conditions': 0},
              'conditions': [{'state': s, 'action': a, 'status': 'unstarted'} for s, a in PLAN]}
    def check(what):
        report['elapsed_s'] = time.monotonic() - started
        if report['elapsed_s'] >= 3600 or timer_remaining() < 30:
            raise ResourceLimit(f'resource deadline before {what}')
    def alarm(signum, frame):
        raise ResourceLimit('sidecar 3600-second wall limit reached')
    old_alarm = signal.signal(signal.SIGALRM, alarm); signal.setitimer(signal.ITIMER_REAL, 3600)
    try:
        require(sha(args.protocol) == args.protocol_sha256, 'protocol hash differs')
        protocol = read(args.protocol)
        require(protocol['status'] == 'FROZEN', 'protocol is not frozen')
        report['funded_training_roster'] = [{k: u[k] for k in ('model', 'arm', 'seed')} for u in protocol['units']]
        if timer_remaining() < 3900:
            report.update(status='resource', reason='fund_unstarted_insufficient_remaining')
        else:
            execute(args, protocol, report, check, args.out)
        report['elapsed_s'] = time.monotonic() - started
        save(args.out / 'report.json', report)
        if report['status'] == 'complete':
            from experiments.safety_selection.ledger import write_complete
            write_complete(args.out, {'kind': 'private candidate activation intervention',
                'protocol_sha256': args.protocol_sha256, 'module_sha256': report['module_sha256']})
        print(json.dumps({'status': report['status'], 'report': str(args.out / 'report.json')}))
        return 0 if report['status'] == 'complete' or report.get('reason') == 'fund_unstarted_insufficient_remaining' else 1
    except BaseException as exc:
        report.update(status='resource' if isinstance(exc, ResourceLimit) or type(exc).__name__ == 'LimitReached' else 'technical',
                      error_type=type(exc).__name__, error=str(exc), elapsed_s=time.monotonic() - started)
        for cell in report['conditions']:
            if cell['status'] == 'running':
                cell['status'] = 'failed'
        for canary in report.get('canaries', []):
            if canary['status'] == 'running':
                canary['status'] = 'failed'
                report['canary_result']['status'] = 'failed'
        save(args.out / 'report.json', report)
        (args.out / 'error.txt').write_text(traceback.format_exc())
        print(json.dumps({'status': report['status'], 'error_type': type(exc).__name__}))
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, old_alarm)


if __name__ == '__main__':
    raise SystemExit(main())
