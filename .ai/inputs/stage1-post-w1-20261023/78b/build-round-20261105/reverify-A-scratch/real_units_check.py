"""Re-measure the fixer's 17-unit claims with my own reader (allow-listed timing names only; numbers and key names
printed, never text): (1) no PREFLIGHT-DONE.json holds untuned_projected_s; (2) cap_projection.training_s equals
PREFLIGHT-DONE training_s on every unit; (3) job_decision on each real pair returns run at s_pod 1.0 with the
fixed signature; (4) RULES-78B.md's key-tree claim about verification.json (full_length.max_new_tokens,
full_length.batch, evaluation_timing.projection_to_dev_bank.stages.{generate,sample}.bank_units)."""
import json, math, pathlib, sys

sys.dont_write_bytecode = True
KIT = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(KIT))
import rules_78b as R  # noqa: E402

ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")
KITS = {
    "olmo2-7b": ("family-probe-sp-olmo2-7b-b-a0", "family-probe-sp-olmo2-7b-b-seed1102", "family-probe-sp-olmo2-7b-b-seed1103",
                 "family-probe-sp-olmo2-7b-b5e5-seed1101", "family-probe-sp-olmo2-7b-b5e5-seed1102", "family-probe-sp-olmo2-7b-b5e5-seed1103",
                 "family-probe-sp-olmo2-7b-g-seed1101", "family-probe-sp-olmo2-7b-g-seed1102", "family-probe-sp-olmo2-7b-g-seed1103"),
    "llama31-8b": ("family-probe-sp-llama31-8b-b-a0", "family-probe-sp-llama31-8b-b-seed1102", "family-probe-sp-llama31-8b-b-seed1103",
                   "family-probe-sp-llama31-8b-b5e5-1101", "family-probe-sp-llama31-8b-b5e5-seed1102", "family-probe-sp-llama31-8b-g-seed1101",
                   "family-probe-sp-llama31-8b-g-seed1102", "family-probe-sp-llama31-8b-g-seed1103"),
}
ALLOWED = {"PREFLIGHT-DONE.json", "verification.json", "finished.json", "JOB-DONE.json"}


def load(p: pathlib.Path):
    assert p.name in ALLOWED, p.name
    return json.loads(p.read_text(encoding="utf-8"))


def dig(d, path):
    for k in path.split("."):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


n_units = n_untuned_in_pre = n_training_equal = n_run = 0
bank_checks = {"full_length.max_new_tokens": set(), "full_length.batch": set(),
               "evaluation_timing.projection_to_dev_bank.stages.generate.bank_units": set(),
               "evaluation_timing.projection_to_dev_bank.stages.sample.bank_units": set()}
missing_paths = {k: 0 for k in bank_checks}
for family, names in KITS.items():
    for name in names:
        kit = ROOT / name
        hosts = [p for p in (kit / "hosts").iterdir() if p.is_dir() and (p / "finished.json").is_file()
                 and (kit / "retrieved" / p.name / "tree" / "JOB-DONE.json").is_file()]
        assert len(hosts) == 1, (name, len(hosts))
        host = hosts[0]
        pre = load(kit / "retrieved" / host.name / "tree" / "PREFLIGHT-DONE.json")
        ver = load(host / "verification.json")
        n_units += 1
        n_untuned_in_pre += "untuned_projected_s" in pre
        cp = ver["cap_projection"]
        n_training_equal += math.isclose(cp["training_s"], pre["training_s"], rel_tol=1e-9, abs_tol=1e-6)
        job = R.job_record(family, "arm", 33)
        d = R.job_decision(family, pre, ver, job, 20 * 3600.0, 20.0)
        n_run += d["action"] == "run" and d["s_pod"] == 1.0
        for k in bank_checks:
            v = dig(ver, k)
            if v is None:
                missing_paths[k] += 1
            else:
                bank_checks[k].add(v)
print(json.dumps({"units": n_units, "preflight_done_with_untuned_projected_s": n_untuned_in_pre,
                  "training_s_equal_in_both_documents": n_training_equal, "job_decision_run_at_s_pod_1": n_run,
                  "verification_key_values": {k: sorted(v) for k, v in bank_checks.items()},
                  "verification_key_missing_count": missing_paths}, indent=1))
