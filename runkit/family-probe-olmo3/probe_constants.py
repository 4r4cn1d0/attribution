"""Constants of one family-probe working copy (administrative; the OLMo 3 kit). The lead copies
runkit/family-probe-olmo3/ to tmp/family-probe-s78-olmo3-7b-<step>/ (O3A §16.7: the family-probe- prefix, so every
budget guard sees its cap) and sets PROBE, SEED and RUNG there; the prepared manifests are written after the Mac
preparation. Until then every script that needs them refuses.

Gate A shape for OLMo 3 (O3A §16.2, R1-R5; the readiness scout §1.3): the probe pod runs the untuned unit and seed 1101
at rung 1 (SEED 1101, RUNG 1, plan_tool.py init); every later host is a fine-tune-only reuse of that sealed untuned
unit (plan_tool.py init --reuse-baseline UNIT): seed 1101 at rung 2 or 3 when rung 1 reads saturated (R3-R4), and
seeds 1102 and 1103 at the chosen rung (R5; seed 1102 also for a one-seed TOO CLOSE, pre-set answer P0).
"""
PROBE = None
SEED = 1101                                   # the host's and the job's seed (plan_tool): 1101-1103 (O3A §16.4)
RUNG = 1                                      # the learning-rate rung: 1 (1e-4), 2 (5e-5), 3 (2e-5) (probes.RUNGS)
PREPARED_MANIFESTS = {"prepared-kt-dolly-olmo2": None, "prepared-kt-dolly-llama3": None, "prepared-kt-dolly-olmo3": None}
PREPARED_LOCAL = "tmp/kt-prepared"            # repository-relative folder holding the prepared sets
HF_TOKEN_ENV = "HF_TOKEN"                     # the environment variable that holds the HF token (Mac side only)
# every name scrubbed from child environments: the configured one first (review fix 5); secret_scan.scrubbed also
# drops any variable whose value looks like an HF token, whatever its name
TOKEN_ENV_NAMES = tuple(dict.fromkeys((HF_TOKEN_ENV, "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")))
BUNDLE = "bundle-probe.tar.gz"
WORKER_SETUP = "worker-setup-probe.tar.gz"
WORKER_BOOTSTRAP = "worker_bootstrap_probe.sh"
EXPECTED_FIXTURE = "expected-fixture-probe.json"
POD_PREFIX = "attribution-probe"
SCRIPTS = ("cuda_preflight_family.py", "cuda_preflight_killtest.py", "cuda_preflight_headroom_v3.py",
           "cuda_preflight_headroom.py")      # the probe's own preflight script (probes.preflight_script_of) is packed too
CHECKPOINT = "e1"
RANK = "r64"                                  # "r16": the 1B probes' rank-16, alpha-32 ladders (probes.recipes)
RECIPE = "b"                                  # "bt" (token mean) or "g" (token mean + warmup cosine): 1B probes only
MAX_PRICE = 1.85                              # budget-guard planning rate per hour; the creation limit is host.MAX_PRICE ($10/h)


def probe() -> str:
    if not PROBE:
        raise SystemExit("probe_constants.PROBE is not set: set one probe key in this working copy")
    return PROBE


def prepared() -> dict:
    import probes
    name = probes.PROBES[probe()]["prepared"]
    if not PREPARED_MANIFESTS.get(name):
        raise SystemExit(f"probe_constants.PREPARED_MANIFESTS[{name!r}] is not set: prepare it on the Mac first")
    return {name: PREPARED_MANIFESTS[name]}
