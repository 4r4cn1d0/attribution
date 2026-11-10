"""Offline planning arithmetic and source/metadata readback; no tests or experiments.

No raw hidden responses, evaluation prompt banks or anchor text are read. This
does not alter the live kit plan, package it, contact RunPod or run a model.
"""
from pathlib import Path
from statistics import NormalDist
import ast
import hashlib
import importlib.util
import json
import math

PROJECT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literals(path):
    values = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return values


rule_path = PROJECT / 'runkit/gate-b-olmo/gateb_rules.py'
spec = importlib.util.spec_from_file_location('planning_gateb_rules', rule_path)
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)
reader_constants = literals(PROJECT / 'scripts/gate_b_reading.py')
plan_path = PROJECT / 'tmp/gate-b-olmo/plan.json'
plan = json.loads(plan_path.read_text())
fixture_path = PROJECT / rules.GATE_A_FIXTURE
projection = json.loads(fixture_path.read_text())['cap_projection']
fixture = {key: projection[key] for key in ('e1_upper_s', 'training_s')}
wave0a = rules.default_jobs(['arm'] * 3, fixture)
wave0b = rules.default_jobs(['retrain', 'diagnostics'], fixture)
caps = {'0a': rules.cap_hours(wave0a), '0b': rules.cap_hours(wave0b)}

checks = []
pinned = dict(rules.PINNED_SCRIPTS)
pinned.update({
    rules.MAN_PATH: rules.MAN_SHA256,
    rules.GATE_A_FIXTURE: rules.PREREG_FIXTURE_SHA256,
    'research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md': reader_constants['PREREG_SHA256'],
    'experiments/safety_selection/configs/evaluation-equivalence-gateb-20261008.json': reader_constants['GATEB_CERTIFICATE_SHA256'],
    'tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json': rules.PREPARED_MANIFESTS['prepared-kt-dolly-olmo2'],
})
for relative, expected in pinned.items():
    path = PROJECT / relative
    got = digest(path) if path.is_file() else None
    checks.append({'path': relative, 'expected_sha256': expected, 'observed_sha256': got, 'matches': got == expected})

from experiments.safety_selection.common import code_identity
engine = code_identity()['sha256']
kit_files = ['plan_tool.py', 'pack_setup.py', 'gateb_mac.py', 'gateb_rules.py', 'orchestrate.py', 'launch.py', 'budget.py', 'host.py']
kit_pairs = []
for name in kit_files:
    source = PROJECT / 'runkit/gate-b-olmo' / name
    live = PROJECT / 'tmp/gate-b-olmo' / name
    kit_pairs.append({'file': name, 'source_sha256': digest(source), 'live_sha256': digest(live) if live.is_file() else None, 'same': live.is_file() and digest(source) == digest(live)})

man = json.loads((PROJECT / rules.MAN_PATH).read_text())
jobs = []
for draw in (1, 2, 3):
    entry = next(e for e in man['files'] if e['path'] == f'edits/R_d{draw}.json')
    jobs.append({'kind': 'arm', 'arm': entry['arm'], 'seed': 1100 + draw, 'edit': entry['path']})
prospective_jobs = {'hosts': [jobs]}
(OUT / 'prospective-wave0a-jobs.json').write_text(json.dumps(prospective_jobs, indent=2) + '\n')

nominal_early = rules.pod_spend_usd(['arm'] * 3) + rules.pod_spend_usd(['retrain', 'diagnostics'])
funding_prior = json.loads((OUT / 'runpod-funding-check.json').read_text())
balance = funding_prior['displayed_balance_usd']
funding = {
    'balance_snapshot_usd': balance,
    'balance_snapshot_observed_utc': funding_prior['observed_utc'],
    'not_refreshed_by_this_calculation': True,
    'historical_rate_usd_per_hour': rules.RATE_USD,
    'frozen_guard_price_usd_per_hour': rules.PLANNING_PRICE_USD,
    'reserve_usd': rules.RESERVE_USD,
    'wave_caps_hours': caps,
    'standalone_wave_guard_balance_usd': {wave: rules.RESERVE_USD + cap * rules.PLANNING_PRICE_USD for wave, cap in caps.items()},
    'nominal_early_expense_usd': nominal_early,
    'wave1_balance_threshold_usd': 78.45,
    'additional_credit_scenarios': [{'topup_usd': cash, 'projected_balance_after_nominal_early_usd': balance + cash - nominal_early, 'clears_historical_wave1_threshold_before_storage_failures': balance + cash - nominal_early >= 78.45} for cash in (50, 100)],
    'limitations': ['No deposit verified', 'No live GPU offer', 'Excludes incremental storage, failed starts and separate judging', 'Caps are max runtime reservations, not estimated expenses', 'Noise gate may stop before 0b'],
}

normal = NormalDist()
power_rows = []
for alpha, label in ((.05, 'single contrast'), (.025, 'two-comparison Bonferroni sensitivity')):
    for sd in (5, 10, 20, 30):
        n = math.ceil(((normal.inv_cdf(1-alpha/2) + normal.inv_cdf(.8)) * sd / 5) ** 2)
        power_rows.append({'alpha_two_sided': alpha, 'multiplicity_scenario': label, 'hypothetical_paired_block_sd_pp': sd, 'effect_gap_pp': 5, 'target_power': .8, 'normal_approx_independent_pairs': n})
zero_failure = [{'independent_blocks': n, 'one_sided_95pct_upper_probability_with_zero_violations': 1-.05**(1/n)} for n in (12, 30, 60, 120)]
power = {
    'status': 'asymptotic feasibility screen; not a final power analysis or approved seed count',
    'unit': 'independent paired selector/final-training execution block conditional on one fixed menu and prompt population',
    'formula': 'ceil((z_(1-alpha/2)+z_0.80)^2 * sigma_pair^2 / gap^2)',
    'effect_gap_interpretation': '5 pp against zero, or a hypothetical true 10 pp versus a 5 pp practical-benefit threshold; neither truth is measured',
    'sd_values_are_hypothetical_not_estimated': True,
    'rows': power_rows,
    'zero_failure_binomial_sensitivity': zero_failure,
    'minimum_independent_zero_violation_blocks_for_one_sided_95pct_upper_below_5pct': math.floor(math.log(.05)/math.log(.95)) + 1,
    'limitations': ['Normal/t-like sampling assumptions; no guaranteed coverage/power', 'No small-sample t adjustment or exact final analysis', 'A future multi-menu design needs hierarchical planning', 'Failure/missingness and endpoint multiplicity need the frozen analysis', 'Per-run over-refusal pp tolerance is not a violation probability', 'Gate B repair/prompt SD is not paired decision SD', 'No N selected to fit cash'],
}

readiness = {
    'user_routing_instruction': 'restart plan using gpt',
    'scope': 'GPT restart design/planning; no cloud execution or global workflow change',
    'pinned_metadata_checks': checks,
    'engine_sha256': engine,
    'recorded_engine_sha256': plan['engine_sha256'],
    'engine_matches_plan': engine == plan['engine_sha256'],
    'source_live_kit_pairs': kit_pairs,
    'live_plan_contains_only_completed_anchor': list(plan['hosts']) == ['anchor-1'] and all(j.get('status') == 'complete' for j in plan['hosts']['anchor-1']['jobs']),
    'planned_wave0a_hosts': [{'host': name, 'cap_hours': h.get('cap_hours'), 'jobs': [{'kind': j.get('kind'), 'seed': j.get('seed'), 'steps': j.get('steps'), 'status': j.get('status')} for j in h.get('jobs', [])], 'create_intent_exists': (PROJECT / 'tmp/gate-b-olmo/hosts' / name / 'create-intent.json').is_file(), 'pod_record_exists': (PROJECT / 'tmp/gate-b-olmo/hosts' / name / 'pod.json').is_file()} for name, h in plan['hosts'].items() if h.get('wave') == '0a'],
    'environment_reference_exists': bool(plan.get('reference')),
    'packed_gateb_receipt_exists': (PROJECT / 'tmp/gate-b-olmo/setup/packed-gateb/setup-receipt.json').is_file(),
    'prospective_jobs_path': str(OUT / 'prospective-wave0a-jobs.json'),
    'live_plan_not_modified_by_this_script': True,
    'launch_ready': False,
    'pending': ['Deposit and fresh account/offer checks'] + ([] if (PROJECT / 'tmp/gate-b-olmo/setup/packed-gateb/setup-receipt.json').is_file() else ['Local gateb bundle and receipt preparation']) + ['First-host preflight reference', 'Conditional noise-gate and re-costing', 'Pre-wave1 commitment audit closure'],
}
for name, payload in [('gpt-preparation-status.json', readiness), ('gpt-budget-scenarios.json', funding), ('gpt-replication-sensitivity.json', power)]:
    (OUT / name).write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps({'pin_matches': sum(c['matches'] for c in checks), 'pin_count': len(checks), 'engine_matches': readiness['engine_matches_plan'], 'kit_pairs_match': sum(c['same'] for c in kit_pairs), 'kit_pair_count': len(kit_pairs), 'packed_gateb_receipt_exists': readiness['packed_gateb_receipt_exists'], 'caps_hours': caps, 'nominal_early_expense_usd': nominal_early, 'power_rows': power_rows, 'zero_violation_blocks_for_5pct_95pct': power['minimum_independent_zero_violation_blocks_for_one_sided_95pct_upper_below_5pct'], 'launch_ready': False}, indent=2))
