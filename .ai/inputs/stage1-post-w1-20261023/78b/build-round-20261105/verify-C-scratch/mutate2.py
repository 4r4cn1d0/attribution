"""Second mutation pass: both R-provenance checks removed at once (N8c); and the pooled() formula checked
numerically on synthetic exact inputs (k = 2), which no builder test does."""
import pathlib, shutil, subprocess, importlib.util, math
from fractions import Fraction
S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut2"
WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c")
MAINCK = pathlib.Path("/Users/spiderishi/Coding/attribution")
PY_SCI = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
PKG = MUT / "scripts/scale78b"
if MUT.exists():
    shutil.rmtree(MUT)
(MUT / "scripts").mkdir(parents=True)
for name in ("gate_b_reading.py", "family_probe_reading.py", "killtest_stage0_reading.py"):
    (MUT / "scripts" / name).symlink_to(MAINCK / "scripts" / name)
(MUT / "experiments").symlink_to(WS / "experiments")
(MUT / "research").symlink_to(WS / "research")
shutil.copytree(WS / "scripts/scale78b", PKG, ignore=shutil.ignore_patterns("__pycache__"))
p = PKG / "noise_reading.py"
t = p.read_text()
old1 = 'or doc.get("manifest_sha256") != fam["manifest_sha256"] or selection.get("family") != "R" \\'
old2 = 'or selection.get("draw") != seed - R_SEED_BASE:'
assert t.count(old1) == 1 and t.count(old2) == 1
p.write_text(t.replace(old1, 'or doc.get("manifest_sha256") != fam["manifest_sha256"] or False \\').replace(old2, "or False:"))
r = subprocess.run([PY_SCI, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x", str(PKG / "tests/test_noise_reading.py"), "-k", "method_arm"],
                   cwd=str(MUT), capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)})
lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
print("N8c (family AND draw checks removed):", "KILLED" if r.returncode else "SURVIVED", "|", lines[-1][:120] if lines else "")
# which line refused and what the test saw: print only the matching assertion line, no data
for l in lines:
    if "DID NOT RAISE" in l or "SystemExit" in l or "only a0 and R" in l:
        print("   ", l[:160])
shutil.rmtree(MUT)

# ----- pooled() on synthetic exact inputs (the clean builder module) -----
spec = importlib.util.spec_from_file_location("nr", WS / "scripts/scale78b/noise_reading.py")
nr = importlib.util.module_from_spec(spec); spec.loader.exec_module(nr)
def fam(sd_r, se_list, arm_sds, n=3):
    return {"_exact": {"sdr2": Fraction(sd_r) ** 2, "pair_se2": {f"p{i}": Fraction(s) ** 2 for i, s in enumerate(se_list)},
                       "arm_ss": sum(Fraction(a) ** 2 * (n - 1) for a in arm_sds), "arm_df": (n - 1) * len(arm_sds)}}
O = fam("4", ["1", "2", "3"], ["6", "3"])          # SD(r_O) 4; SEs 1,2,3; a0 SD 6, R SD 3
L = fam("2", ["4", "5", "6"], ["1", "1"])          # SD(r_L) 2; SEs 4,5,6; both arm SDs 1
pool = nr.pooled({"olmo2-7b": O, "llama31-8b": L})
expect_sqrt = math.sqrt((2 * 16 + 2 * 4) / 4)       # sqrt(10) = 3.1623
expect_median = (3 + 4) / 2                          # 6 SEs 1,2,3,4,5,6 -> mean of the two middle = 3.5
expect_s_arm = math.sqrt((36 * 2 + 9 * 2 + 1 * 2 + 1 * 2) / 8)
print("pooled: k", pool["k"], "df", pool["df"], "sqrt_P_pool", round(pool["sqrt_P_pool_pp"], 4), "(expect", round(expect_sqrt, 4), ")",
      "median SE", pool["median_pair_se_pp"], "(expect", expect_median, ") n_pair_ses", pool["n_pair_ses"],
      "sigma_pool", round(pool["sigma_pool_pp"], 4), "(expect max =", round(max(expect_sqrt, expect_median), 4), ")",
      "s_arm", round(pool["s_arm_pp"], 4), "(expect", round(expect_s_arm, 4), ") s_arm_df", pool["s_arm_df"],
      "plan", pool["seed_rule"]["plan"], "df", pool["seed_rule"]["df"])
# the median term decides when larger: SEs 7..12 -> median 9.5 -> H
L2 = fam("2", ["7", "8", "9"], ["1", "1"]); O2 = fam("4", ["10", "11", "12"], ["1", "1"])
pool2 = nr.pooled({"a": O2, "b": L2})
print("median-governed: sigma_pool", pool2["sigma_pool_pp"], "plan", pool2["seed_rule"]["plan"], "(expect 9.5, H)")
# the review case: SD(r) 11 both -> sqrt((2*121+2*121)/4) = 11 > 10.7062 -> review
pool3 = nr.pooled({"a": fam("11", ["1", "1", "1"], ["1", "1"]), "b": fam("11", ["1", "1", "1"], ["1", "1"])})
print("review case: sigma_pool", pool3["sigma_pool_pp"], "outcome", pool3["seed_rule"]["outcome"], "MDE", round(pool3["seed_rule"]["removal_mde_pp"], 3))
# the inconsistency band: sigma_pool 10.7064 -> review True but printed MDE with the rounded factor < 10?
pool4 = nr.pooled({"a": fam("10.7064", ["1", "1", "1"], ["1", "1"]), "b": fam("10.7064", ["1", "1", "1"], ["1", "1"])})
print("band case sigma 10.7064: review", pool4["seed_rule"]["review"], "printed MDE", pool4["seed_rule"]["removal_mde_pp"], "(< 10 while review is True?)", pool4["seed_rule"]["removal_mde_pp"] < 10)
