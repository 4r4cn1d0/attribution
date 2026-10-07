"""Constants of one family-probe working copy (administrative). The lead copies runkit/family-probe/ to
tmp/family-probe-<probe>/ and sets PROBE there; the prepared manifests are written after the Mac preparation. Until
then every script that needs them refuses."""
PROBE = None
PREPARED_MANIFESTS = {"prepared-kt-dolly-olmo2": None, "prepared-kt-dolly-llama3": None}
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
           "cuda_preflight_headroom.py")
CHECKPOINT = "e1"
RANK = "r64"                                  # "r16": the 1B probes' rank-16, alpha-32 ladders (probes.recipes)
MAX_PRICE = 1.75


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
