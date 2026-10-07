"""Constants of the kill-test Stage 0 run kit (administrative), shared by plan_tool.py and pack_setup.py.

PREPARED_MANIFEST is the manifest SHA-256 of prepared-kt-dolly. The lead writes it here after the Mac preparation
(prepare twice, identical manifest, then the asserted counts, then the frozen manifest). Until then it is None,
and plan_tool.py and pack_setup.py refuse to run.
"""
CFG = "experiments/safety_selection/configs"
# Preflight candidates in order (review fix F3): the first whose fixture is exact AND whose memory preflight passes is
# recorded and used for every seed.
RECIPES = [f"{CFG}/study-kt-qwen7b-r64-b-mb4-20261007.json", f"{CFG}/study-kt-qwen7b-r64-b-mb2-20261007.json",
           f"{CFG}/study-kt-qwen7b-r64-b-mb1-gc-20261007.json", f"{CFG}/study-kt-qwen7b-r64-b-mb1-gc-eager-20261007.json"]   # 7B check (FOCUS.md, 2026-10-07 13:38 UTC)
PREPARED_NAME = "prepared-kt-dolly"
PREPARED_MANIFEST = "9247c4bbccf212b02be7f221e2ee451d17ebf643a39a44db6e3bed6fb4d750f2"  # frozen 6 Oct 2026 (lead, Mac)
PREPARED_LOCAL = "tmp/kt-prepared"          # repository-relative folder holding prepared-kt-dolly/
BUNDLE = "bundle-kt.tar.gz"
WORKER_SETUP = "worker-setup-kt.tar.gz"
WORKER_BOOTSTRAP = "worker_bootstrap_kt.sh"
EXPECTED_FIXTURE = "expected-fixture-kt.json"
POD_PREFIX = "attribution-killtest"
SCRIPTS = ("cuda_preflight_killtest.py", "cuda_preflight_headroom_v3.py", "cuda_preflight_headroom.py")


def prepared() -> dict:
    if not PREPARED_MANIFEST:
        raise SystemExit("kt_constants.PREPARED_MANIFEST is not set: prepare prepared-kt-dolly on the Mac first")
    return {PREPARED_NAME: PREPARED_MANIFEST}
