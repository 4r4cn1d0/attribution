"""S-G beside B16's output (sg_coherent.py; post-W1 deviation D-5): the linearized table by hand and exactly; with
every answer coherent, S-G coherent is B16's primary U_k to the last bit (three readings); G2's pooled share, not the
prompt mean; a cell with no coherent answer (the paired form's prompt part by hand); a pair that loses seeds; Phi
re-run with the primary O, L and F p-values; the words and headline by hand (the reading's familywise sides, O or L
named, a headline-only difference); the adverse G3(a) corners and the relabelled symmetric table; never stopping; an
independent reference; the bindings; the command line (words only, never a number); B16 byte-identical to the 31 Oct
stamp; and the coverage simulation."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import sim_sg_coherent as sim
import synth_kit as sk

from scripts.stage1_s1.reading import contrast as con
from scripts.stage1_s1.reading import labels, sensitivities
from scripts.stage1_s1.reading.__main__ import main as b16_main
from scripts.stage1_s1.reading.reading import _node_key, _run_phi, read
from scripts.stage1_s1.reading.reml import RemlError
from scripts.stage1_s1.reading.settings import Refusal, alpha, canonical_json, design, settings, sha256_bytes
from scripts.stage1_s1.reading.tdist import t_quantile, t_two_sided
from scripts.stage1_s1.reading_input import sg_coherent as sgc
from scripts.stage1_s1.reading_input.__main__ import main as builder

TREE = Path(__file__).resolve().parents[4]
PY = sys.executable
VALUE = re.compile(r"\d\.\d{3,}")
ESTIMATE_KEYS = ("est", "se", "df", "seed_var", "seed_df", "item_var", "item_q", "pairs", "items", "with_item")
# B16 (scripts/stage1_s1/reading/**) at commit 55d5f8b, the tree the 31 Oct stamp binds (git tree 4b765fc3): SHA-256
# of the canonical JSON of {path: SHA-256} over its 33 files (no __pycache__)
B16_TREE_FILES = 33
B16_TREE_DIGEST = "0866fde9cff4a08a095f93e7d4501bc65ad76f305535dad27a82f8de2ed2df08"


# ----- the pipeline: builder (--coherent-out), B16, then the reader --------------------------------------------------


@pytest.fixture(scope="session")
def pipeline(tmp_path_factory):
    """A getter of (world, documents, paths) per reading, built once. It runs inside the tests, so a failure is a test
    failure, never a setup error (the mutation runner counts a setup error as an invalid run, run_mutants.py). A build
    that failed is kept: each later test that asks for it fails at once with the same reason, with no rebuild per test
    (which would push a mutant's run toward the runner's timeout)."""
    cache = {}

    def get(reading):
        if reading in cache:
            if isinstance(cache[reading], str):
                pytest.fail(cache[reading])
            return cache[reading]
        try:
            root = tmp_path_factory.mktemp(f"sgc-{reading}")
            s = sk.make(root / "w", reading)
            paths = {k: root / f"{k}.json" for k in ("tables", "sources", "counts", "reading")}
            rc = builder(s.args(paths["tables"], paths["sources"], overlap=False) +
                         ["--coherent-out", str(paths["counts"])])
            assert rc == 0, f"the builder exited {rc}"
            rc = b16_main(["--input", str(paths["tables"]), "--out", str(paths["reading"])])
            assert rc == 0, f"B16 exited {rc}"
            docs = {k: json.loads(p.read_text()) for k, p in paths.items()}
            docs["sg"] = run_sg(docs["tables"], docs["counts"], docs["reading"])
        except Exception as exc:
            cache[reading] = f"the synthetic pipeline of {reading} failed in an earlier test: {type(exc).__name__}: {exc}"
            raise
        cache[reading] = (s, docs, paths)
        return cache[reading]
    return get


def sha(doc) -> str:
    return sha256_bytes(canonical_json(doc))


def run_sg(tables, counts, reading_doc) -> dict:
    return sgc.sg(tables, counts, reading_doc, sha(tables), sha(counts), sha(reading_doc))


def rerun(tables: dict, counts: dict) -> tuple[dict, dict]:
    """B16 again on an edited tables.json, the counts re-bound to it, then the reader: (S-G output, B16 output)."""
    reading_doc = json.loads(canonical_json(read(tables, sha(tables))))
    counts = {**counts, "input_sha256": sha(tables)}
    return run_sg(tables, counts, reading_doc), reading_doc


def all_fail(tables: dict, counts: dict, arm: str, seeds) -> None:
    """Every answer of the cells (arm, seed) fails the screen: n = u = 0, u_fail = the Unsafe count, failing = 600."""
    for j in seeds:
        cell = counts["cells"][arm][str(j)]
        unsafe = [round(3 * v) for v in tables["endpoints"]["U"]["cells"][arm][str(j)]]
        cell.update(n=[0] * 200, u=[0] * 200, u_fail=unsafe)
        tables["coherence"][arm][str(j)]["failing"] = 600


def counts_of(docs) -> dict:
    return {(a, int(j)): {k: np.array(v) for k, v in c.items()} for a, per in docs["counts"]["cells"].items()
            for j, c in per.items()}


def pooled(c) -> float:
    return 100 * int(c["u"].sum()) / int(c["n"].sum())


def x_exact(c) -> np.ndarray:
    """One cell's linearized table built here in exact fractions (shares): x_p = V + (u_p - V n_p) / N-bar."""
    n, u = c["n"], c["u"]
    v, nbar = Fraction(int(u.sum()), int(n.sum())), Fraction(int(n.sum()), len(n))
    return np.array([float(v + (int(ui) - v * int(ni)) / nbar) for ni, ui in zip(n, u)])


def paired_reference(cnt, c, m, seeds) -> dict:
    """A pair's own paired form by hand (numpy only, none of B16's contrast code): the paired mean of the pooled
    shares, the seed part var(d_j) / J with J - 1 df (no floor), the crossed prompt part of the J x 200 table of x,
    and Satterthwaite df."""
    diffs = np.array([pooled(cnt[(c, j)]) - pooled(cnt[(m, j)]) for j in seeds])
    jj = len(seeds)
    v_seed, df_seed = float(diffs.var(ddof=1)) / jj, jj - 1.0
    d = np.stack([x_exact(cnt[(c, j)]) - x_exact(cnt[(m, j)]) for j in seeds])
    grand, rows, cols = d.mean(), d.mean(axis=1), d.mean(axis=0)
    ms_p = jj * float(((cols - grand) ** 2).sum()) / 199
    ms_e = float(((d - rows[:, None] - cols[None, :] + grand) ** 2).sum()) / (199 * (jj - 1))
    k = 1e4 / (200 * jj)
    v_item = max(0.0, ms_p - ms_e) * k
    q = (ms_p * k) ** 2 / 199 + (ms_e * k) ** 2 / (199 * (jj - 1)) if ms_p > ms_e else 0.0
    return {"est": float(diffs.mean()), "seed_var": v_seed, "seed_df": df_seed, "item_var": v_item, "item_q": q,
            "se": math.sqrt(v_seed + v_item), "df": (v_seed + v_item) ** 2 / (v_seed ** 2 / df_seed + q)}


# ----- the linearized table, by hand ----------------------------------------------------------------------------------


def test_x_by_hand_in_exact_arithmetic():
    n, u = np.array([3, 2, 0, 1, 3]), np.array([2, 1, 0, 1, 0])
    big_n, big_u, items = 9, 4, 5
    v = Fraction(big_u, big_n)
    exact = [v + (int(ui) - v * int(ni)) / Fraction(big_n, items) for ni, ui in zip(n, u)]
    assert sgc.x_shares(n, u).tolist() == [float(e) for e in exact]              # rounded once, correctly
    assert sum(exact) / items == v                                                 # the prompt mean is the pooled share
    assert exact[2] == v                                                           # no coherent answer: x = V
    assert sum(exact) / items != sum(Fraction(int(a), int(b)) for a, b in zip(u, n) if b) / 4   # not the prompt mean
    assert sgc.x_shares(np.zeros(5, int), np.zeros(5, int)) is None                # no coherent answer in the cell


def test_x_with_every_answer_coherent_is_the_u_share_to_the_last_bit():
    rng = np.random.default_rng(3)
    for _ in range(20):
        u = rng.integers(0, 4, 200)
        assert sgc.x_shares(np.full(200, 3), u).tolist() == [int(k) / 3 for k in u]


def test_x_mean_is_the_pooled_share_on_random_cells():
    rng = np.random.default_rng(4)
    for _ in range(50):
        n = rng.integers(0, 4, 200)
        u = np.array([rng.integers(0, k + 1) for k in n])
        x = sgc.x_shares(n, u)
        assert abs(100 * x.mean() - 100 * int(u.sum()) / int(n.sum())) < 1e-12
        assert set(x[n == 0].tolist()) <= {int(u.sum()) / int(n.sum())}       # no coherent answer: x = V


def test_the_reviews_hand_case_through_b16s_item_part():
    """Two arms, two seeds, 4 prompts (review 2.2 (i)): the comparator's prompt 1 is Unsafe, the repair's prompt 1
    fails the screen at both seeds. On x the prompt part is 625 pp^2 and the SE 25 pp (df 3); the design's drop rule
    (y = u / n on the 3 prompts both arms answer) gave a prompt part of 0 and an SE of 0.07 pp."""
    xc = sgc.x_shares(np.array([3, 3, 3, 3]), np.array([3, 0, 0, 0]))
    xm = sgc.x_shares(np.array([0, 3, 3, 3]), np.array([0, 0, 0, 0]))
    assert xc.tolist() == [1.0, 0.0, 0.0, 0.0] and xm.tolist() == [0.0] * 4
    table = {("c", 1): xc, ("m", 1): xm, ("c", 2): xc, ("m", 2): xm}
    d = con.paired_rows(table, "c", "m", (1, 2))
    v_item, q = con.item_part(d, 100.0)
    assert v_item == pytest.approx(625.0, abs=1e-9)
    e = con._assemble("hand", "x", 25.0, 0.01 / 2, 1.0, d, 100.0, True, 2)     # the two-arm sum rule at the floor
    assert e.se == pytest.approx(math.sqrt(625.005), rel=1e-12) and e.df == pytest.approx(3.0, rel=1e-4)
    assert con.item_part(np.zeros((2, 3)), 100.0) == (0.0, 0.0)                    # the drop rule's table


# ----- with every answer coherent, S-G coherent is the primary U_k ---------------------------------------------------


@pytest.mark.parametrize("reading", ["plan_a", "plan_a_block_a_only", "plan_b"])
def test_every_answer_coherent_gives_the_primary_exactly(pipeline, reading):
    s, docs, _ = pipeline(reading)
    tables, counts = copy.deepcopy(docs["tables"]), copy.deepcopy(docs["counts"])
    for arm, per in tables["coherence"].items():
        for j in per:
            per[j].update(capped=0, failing=0)
            unsafe = [round(3 * v) for v in tables["endpoints"]["U"]["cells"][arm][j]]
            counts["cells"][arm][j].update(n=[3] * 200, u=unsafe, u_fail=[0] * 200)
    out, r = rerun(tables, counts)
    dsg = design(reading)
    for name, _, _ in dsg.contrasts:
        k, p = out["coherent"]["contrasts"][name], r["contrasts"][name]
        assert k["computable"] and all(k["estimate"][key] == p["U"][key] for key in ESTIMATE_KEYS), name
        assert k["interval_90"] == p["U_interval_90"] and k["p_in_phi"] == p["p_values"]["U"]
        assert k["u_part_words"] == r["rows"][name]["u_part"]["words"] and k["headline"] == r["headline"][name]
        assert k["differs_from_primary"] is False
        assert all(e["code"] != "S-G coherent" for e in out["sensitivity_part"][name])
        assert set(k["g2_prompts_without_coherent_answer_per_seed_pair"].values()) == {0}
    assert out["coherent"]["phi"] == r["phi"]
    for cl, fit in out["coherent"]["fits"].items():
        assert fit["sigma2"] == r["fits"]["U"][cl]["sigma2"] and fit["at_floor"] == r["fits"]["U"][cl]["at_floor"]
    for arm in dsg.arms:
        a = out["coherent"]["arms"][arm]
        assert a["mean_pp"] == pytest.approx(r["arms"][arm]["means"]["U"], abs=1e-9)
        assert set(a["coherent_answers"].values()) == {600} and set(a["prompts_without_coherent_answer"].values()) == {0}


# ----- G2's pooled share, not the prompt mean --------------------------------------------------------------------------


def test_the_cell_value_is_the_pooled_share(pipeline):
    s, docs, _ = pipeline("plan_a")
    out, counts, dsg = docs["sg"], counts_of(docs), design("plan_a")
    prompt_mean_differs = False
    for arm in dsg.arms:
        for j in dsg.seeds[arm]:
            c = counts[(arm, j)]
            assert out["coherent"]["arms"][arm]["cells_pp"][str(j)] == pooled(c)            # exactly
    for name, c, m in dsg.contrasts:
        common = dsg.common_seeds(c, m)
        k = out["coherent"]["contrasts"][name]
        want = float(np.mean([pooled(counts[(c, j)]) - pooled(counts[(m, j)]) for j in common]))
        assert k["estimate"]["est"] == pytest.approx(want, abs=1e-9) and k["estimate"]["form"] == "S-G coherent"
        shares = lambda a, j: 100 * np.mean([u / n for u, n in zip(counts[(a, j)]["u"], counts[(a, j)]["n"]) if n])
        prompt_mean = float(np.mean([shares(c, j) - shares(m, j) for j in common]))
        prompt_mean_differs |= abs(prompt_mean - want) > 1e-6
        assert k["estimate"]["est"] != docs["reading"]["contrasts"][name]["U"]["est"]
    assert prompt_mean_differs


def test_g2_counts_per_seed_pair_and_per_arm_by_hand(pipeline):
    s, docs, _ = pipeline("plan_a")
    out, counts, dsg = docs["sg"], counts_of(docs), design("plan_a")
    seen = 0
    for name, c, m in dsg.contrasts:
        got = out["coherent"]["contrasts"][name]["g2_prompts_without_coherent_answer_per_seed_pair"]
        for j in dsg.common_seeds(c, m):
            either = int(sum(1 for a, b in zip(counts[(c, j)]["n"], counts[(m, j)]["n"]) if a == 0 or b == 0))
            both = int(sum(1 for a, b in zip(counts[(c, j)]["n"], counts[(m, j)]["n"]) if a == 0 and b == 0))
            assert got[str(j)] == either
            seen += either > both
    assert seen > 0                                   # the world tells "either arm" from "both arms"
    for arm in dsg.arms:
        a = out["coherent"]["arms"][arm]
        for j in dsg.seeds[arm]:
            assert a["prompts_without_coherent_answer"][str(j)] == int((counts[(arm, j)]["n"] == 0).sum())
            assert a["coherent_answers"][str(j)] == int(counts[(arm, j)]["n"].sum())
        assert a["mean_pp"] == pytest.approx(np.mean([pooled(counts[(arm, j)]) for j in dsg.seeds[arm]]), abs=1e-12)


# ----- a cell with no coherent answer; a pair that loses seeds -------------------------------------------------------


def test_a_cell_with_no_coherent_answer_leaves_the_fit(pipeline):
    s, docs, _ = pipeline("plan_a")
    tables, counts = copy.deepcopy(docs["tables"]), copy.deepcopy(docs["counts"])
    all_fail(tables, counts, "S3", [1105])
    out, r = rerun(tables, counts)
    a = out["coherent"]["arms"]["S3"]
    assert a["cells_pp"]["1105"] is None and a["seeds_without_value"] == [1105] and a["coherent_answers"]["1105"] == 0
    assert a["prompts_without_coherent_answer"]["1105"] == 200
    cnt = counts_of({"counts": counts})
    assert a["mean_pp"] == pytest.approx(np.mean([pooled(cnt[("S3", j)]) for j in (1102, 1103, 1104, 1106, 1107)]),
                                         abs=1e-12)
    p5 = out["coherent"]["contrasts"]["P5"]                         # S1 - S3: the pair's own paired form on 5 seeds
    assert p5["computable"]
    assert p5["estimate"]["form"].endswith("paired on the seeds that hold a value (LN-12's precedent)")
    assert p5["estimate"]["pairs"] == 5 and p5["estimate"]["seed_df"] == 4.0 and p5["estimate"]["items"] == 200
    seeds = (1102, 1103, 1104, 1106, 1107)
    assert p5["estimate"]["est"] == pytest.approx(np.mean([pooled(cnt[("S1", j)]) - pooled(cnt[("S3", j)])
                                                           for j in seeds]), abs=1e-9)
    ref = paired_reference(cnt, "S1", "S3", seeds)             # the paired form with its prompt part, by hand
    assert ref["item_var"] > 0 and p5["estimate"]["with_item"] is True
    for key in ("est", "seed_var", "seed_df", "item_var", "item_q", "se", "df"):
        assert p5["estimate"][key] == pytest.approx(ref[key], rel=1e-9, abs=1e-12), key
    half = t_quantile(0.95, ref["df"]) * ref["se"]
    assert p5["interval_90"] == pytest.approx([ref["est"] - half, ref["est"] + half], abs=1e-9)
    assert p5["p_in_phi"] == pytest.approx(t_two_sided(ref["est"] / ref["se"], ref["df"]), rel=1e-9)
    assert p5["g2_prompts_without_coherent_answer_per_seed_pair"]["1105"] == 200
    for name in ("P4", "P6"):                                        # the cluster fit, without S3 1105
        assert out["coherent"]["contrasts"][name]["estimate"]["form"] == "S-G coherent"
        assert out["coherent"]["contrasts"][name]["estimate"]["pairs"] == 6
    assert out["coherent"]["fits"]["full"]["residual_df"] == 14.0 and r["fits"]["U"]["full"]["residual_df"] == 15.0
    x = {k: sgc.x_shares(v["n"], v["u"]) for k, v in cnt.items() if v["n"].sum()}
    fits = sensitivities.fit_clusters(x, design("plan_a"), 100.0, 0.01, arms=("a0", "S1", "S3", "S4"), cfg=settings())
    e = con.contrast_fit(x, fits["full"], "a0", "S1", tuple(range(1102, 1108)), 100.0, True, "P4", "S-G coherent")
    p4 = out["coherent"]["contrasts"]["P4"]["estimate"]
    assert p4["se"] == e.se and p4["df"] == e.df


def test_a_pair_left_with_one_seed_is_not_computable_and_takes_p_1(pipeline):
    """A1 has no coherent answer at 1102-1106: P1 (R - A1) keeps one seed. It is not computable; its U node takes
    p = 1 in S-G coherent's Phi run, so U:P1 (rejected by the primary) and F:P1 (which U:P1's weight opened) are not
    rejected there; the other contrasts are read; the reading completes."""
    s, docs, _ = pipeline("plan_a")
    assert "U:P1" in docs["reading"]["phi"]["rejected"] and "F:P1" in docs["reading"]["phi"]["rejected"]
    tables, counts = copy.deepcopy(docs["tables"]), copy.deepcopy(docs["counts"])
    all_fail(tables, counts, "A1", range(1102, 1107))
    out, r = rerun(tables, counts)
    p1 = out["coherent"]["contrasts"]["P1"]
    assert p1["computable"] is False and p1["reason"] == "not computable: 1 common seed(s) hold a value in both arms; " \
                                                          "a paired contrast needs two"
    assert p1["p_in_phi"] == 1.0 and p1["u_part_words"] is None and p1["headline"] is None
    assert "U:P1" not in out["coherent"]["phi"]["rejected"] and "F:P1" not in out["coherent"]["phi"]["rejected"]
    assert out["coherent"]["headline"]["P1"] == "not computable"
    assert {"code": "S-G coherent", "not_computable": p1["reason"]} in out["sensitivity_part"]["P1"]
    assert all(out["coherent"]["contrasts"][n]["computable"] for n in ("P2", "P3", "P4", "P5", "P6"))
    assert out["coherent"]["arms"]["A1"]["seeds_without_value"] == [1102, 1103, 1104, 1105, 1106]


# ----- never stops -------------------------------------------------------------------------------------------------


def test_a_failed_fit_or_contrast_is_not_computable_and_the_file_is_written(pipeline, tmp_path, monkeypatch):
    s, docs, paths = pipeline("plan_a_block_a_only")
    real_fit, real_contrast = sensitivities.fit_clusters, con.contrast_fit

    def fit(table, dsg, scale, floor, arms=None, cfg=None):
        if "S1" in (arms or ()):
            raise RemlError("a synthetic refusal")
        return real_fit(table, dsg, scale, floor, arms=arms, cfg=cfg)

    def contrast(table, fit_, c, m, seeds, scale, with_item=True, name="", form="HB-C"):
        if name == "P2":
            raise Refusal(f"the contrast {name} ({form}) has no finite degrees of freedom: its variance information "
                          "is zero")
        return real_contrast(table, fit_, c, m, seeds, scale, with_item, name, form)

    monkeypatch.setattr(sensitivities, "fit_clusters", fit)
    monkeypatch.setattr(con, "contrast_fit", contrast)
    out_path = tmp_path / "sg.json"
    assert sgc.main(["--tables", str(paths["tables"]), "--counts", str(paths["counts"]), "--reading",
                     str(paths["reading"]), "--out", str(out_path)]) == 0
    out = json.loads(out_path.read_text())
    for block in (out["coherent"]["contrasts"], out["g3a"]["against_better"]["contrasts"],
                  out["g3a"]["against_worse"]["contrasts"]):
        for name in ("P4", "P5", "P6"):
            assert block[name]["computable"] is False and block[name]["p_in_phi"] == 1.0
            assert "the REML fit of the full cluster refused (RemlError: a synthetic refusal)" in block[name]["reason"]
        assert block["P2"]["computable"] is False and "Refusal: the contrast P2" in block["P2"]["reason"]
        assert block["P1"]["computable"] and block["P3"]["computable"]
    assert out["coherent"]["fits_not_computable"] == {"full": "the REML fit of the full cluster refused (RemlError: "
                                                               "a synthetic refusal)"}
    assert set(out["coherent"]["fits"]) == {"removal"}


def test_a_cluster_left_with_one_arm_has_no_fit(pipeline):
    s, docs, _ = pipeline("plan_b")                              # the full cluster is {S1, S4}: the sum rule
    tables, counts = copy.deepcopy(docs["tables"]), copy.deepcopy(docs["counts"])
    all_fail(tables, counts, "S4", design("plan_b").seeds["S4"])
    out, _ = rerun(tables, counts)
    assert out["coherent"]["fits_not_computable"] == {"full": "the full cluster has fewer than two arms that hold a "
                                                               "value"}
    assert out["coherent"]["contrasts"]["P6"]["computable"] is False
    assert out["coherent"]["contrasts"]["P1"]["computable"] and out["coherent"]["contrasts"]["P3"]["computable"]
    assert out["coherent"]["arms"]["S4"]["mean_pp"] is None


# ----- Phi re-run, words and headline ---------------------------------------------------------------------------------


def test_phi_is_rerun_with_the_primary_o_l_and_f(pipeline):
    """For S-G coherent and both corners: Phi with each block's U p-values and B16's O, L and F p-values; the U-part
    words and the headline word under that run, by B16's labels; whether they differ from the primary row."""
    s, docs, _ = pipeline("plan_a")
    out, r, dsg = docs["sg"], docs["reading"], design("plan_a")
    primary = {name: {"p_values": r["contrasts"][name]["p_values"]} for name, _, _ in dsg.contrasts}
    fam = 1.0 - 2.0 * float(alpha()) / 6
    heads_differ = 0
    for block in (out["coherent"], out["g3a"]["against_better"], out["g3a"]["against_worse"]):
        override = {("U", n): block["contrasts"][n]["p_in_phi"] for n, _, _ in dsg.contrasts}
        _, outcome = _run_phi(dsg, primary, override)
        assert block["phi"]["rejected"] == [f"{k}:{c}" for k, c in outcome.rejected]
        rejected = set(outcome.rejected)
        for name, _, _ in dsg.contrasts:
            k = block["contrasts"][name]
            e = con.Estimate(**{key: k["estimate"][key] for key in ("name", "form", *ESTIMATE_KEYS)})
            assert k["p_in_phi"] == e.p_two_sided()
            u = labels.u_part(("U", name) in rejected, e.est, e.interval(0.9), e.interval(fam), 5.0)
            head = labels.headline(u, ("O", name) in rejected, ("L", name) in rejected)
            assert k["u_part_words"] == list(u.words) and k["headline"] == head["word"]
            assert k["u_part"] == {**u.as_dict(), "words": list(u.words)}
            assert k["differs_from_primary"] == (list(u.words) != r["rows"][name]["u_part"]["words"]
                                                 or head["word"] != r["headline"][name])
            heads_differ += head["word"] != r["headline"][name]
    assert heads_differ > 0                              # the world holds a headline word that differs from B16's
    assert out["coherent"]["headline"] == {n: out["coherent"]["contrasts"][n]["headline"] for n, _, _ in dsg.contrasts}


def test_reread_by_hand_familywise_sides_o_or_l_and_a_headline_only_difference():
    """sgc.reread under plan B on hand-made estimates and primary p-values, with the words written out by hand:
    - P1: Lambda-hat 0 with an SE whose familywise interval lies inside +-delta at plan B's 3 sides and outside at
      plan A's 6, so the words are 'equivalent (familywise)' (the familywise level takes the reading's own sides);
    - P3: O_P3 alone rejects (p 1e-12 at its start weight), so the headline is 'worse (O)'; its U-part words equal
      the primary row's while its headline differs, so it differs from the primary (C7: words or headline);
    - P6: L_P6 alone rejects, so the headline is 'worse (L)', the primary row's word."""
    dsg = design("plan_b")
    assert dsg.familywise_sides == 3
    a, delta, df = float(alpha()), 5.0, 10.0
    q3, q6 = t_quantile(1.0 - a / 3, df), t_quantile(1.0 - a / 6, df)
    se = 2.0 * delta / (q3 + q6)
    assert q3 * se < delta < q6 * se and t_quantile(0.95, df) * se < delta     # the knife edge between 3 and 6 sides

    def est(name, s):
        return con.Estimate(name=name, form="hand", est=0.0, se=s, df=df, seed_var=s * s, seed_df=df, item_var=0.0,
                            item_q=0.0, pairs=5, items=200, with_item=True)
    ones = {"U": 1.0, "O": 1.0, "L": 1.0, "F": 1.0}
    primary = {"P1": {"p_values": dict(ones), "u_part_words": ["equivalent (familywise)"],
                      "headline": "equivalent (familywise)"},
               "P3": {"p_values": {**ones, "O": 1e-12}, "u_part_words": ["inconclusive"], "headline": "inconclusive"},
               "P6": {"p_values": {**ones, "L": 1e-12}, "u_part_words": ["inconclusive"], "headline": "worse (L)"}}
    out, outcome = sgc.reread(dsg, primary, {"P1": est("P1", se), "P3": est("P3", 50.0), "P6": est("P6", 50.0)})
    assert sorted(_node_key(n) for n in outcome.rejected) == ["L:P6", "O:P3"]
    p1, p3, p6 = out["P1"], out["P3"], out["P6"]
    assert p1["u_part_words"] == ["equivalent (familywise)"] and p1["headline"] == "equivalent (familywise)"
    assert p1["u_part"]["grade1"] is True and p1["u_part"]["grade2"] is True and p1["differs_from_primary"] is False
    assert p3["u_part_words"] == ["inconclusive"] and p3["headline"] == "worse (O)"
    assert p3["headline_cell"] == "worse (O); U part: inconclusive"
    assert p3["u_part_words_differ"] is False and p3["headline_differs"] is True and p3["differs_from_primary"] is True
    assert p6["u_part_words"] == ["inconclusive"] and p6["headline"] == "worse (L)"
    assert p6["differs_from_primary"] is False and not p6["rejected_in_phi"]


def test_the_headline_names_o_or_l_under_s_gs_own_phi_run(pipeline):
    """B16's plan-A output with P6's O p-value and P2's L p-value set to 1e-12 (P6's L and P2's O set to 1; its Phi
    rejections recomputed by B16's own run, so the binding holds): in S-G coherent's and both corners' Phi runs O_P6
    and L_P2 reject and L_P6 and O_P2 do not, and each headline names the measure that rejected, never the other."""
    s, docs, _ = pipeline("plan_a")
    dsg = design("plan_a")
    reading_doc = copy.deepcopy(docs["reading"])
    p = {name: reading_doc["contrasts"][name]["p_values"] for name, _, _ in dsg.contrasts}
    p["P6"].update(O=1e-12, L=1.0)
    p["P2"].update(O=1.0, L=1e-12)
    _, outcome = _run_phi(dsg, {name: {"p_values": v} for name, v in p.items()})
    reading_doc["phi"]["rejected"] = [_node_key(n) for n in outcome.rejected]
    out = run_sg(docs["tables"], docs["counts"], reading_doc)
    for block in (out["coherent"], out["g3a"]["against_better"], out["g3a"]["against_worse"]):
        rejected = block["phi"]["rejected"]
        assert "O:P6" in rejected and "L:P2" in rejected and "L:P6" not in rejected and "O:P2" not in rejected
        assert block["contrasts"]["P6"]["headline"] in ("worse (O)", "worse (U, O)")
        assert block["contrasts"]["P2"]["headline"] in ("worse (L)", "worse (U, L)")
    assert out["coherent"]["headline"]["P6"] in ("worse (O)", "worse (U, O)")


def test_sensitivity_part_lists_each_code_that_differs(pipeline):
    s, docs, _ = pipeline("plan_a")
    out = docs["sg"]
    for name, part in out["sensitivity_part"].items():
        want = []
        for key, block in (("coherent", out["coherent"]["contrasts"]),
                           ("against_better", out["g3a"]["against_better"]["contrasts"]),
                           ("against_worse", out["g3a"]["against_worse"]["contrasts"])):
            rec = block[name]
            if not rec["computable"]:
                want.append({"code": sgc.CODES[key], "not_computable": rec["reason"]})
            elif rec["differs_from_primary"]:
                want.append({"code": sgc.CODES[key], "u_part_words": rec["u_part_words"],
                             "headline_word": rec["headline"]})
        assert part == want
    assert any(out["sensitivity_part"].values())                   # the world holds a differing corner


# ----- G3(a): the adverse corners and the symmetric table -----------------------------------------------------------


def test_the_adverse_corners_by_hand(pipeline):
    s, docs, _ = pipeline("plan_a")
    out, dsg, cfg = docs["sg"], design("plan_a"), settings()
    u = {(a, int(j)): np.array(v) for a, per in docs["tables"]["endpoints"]["U"]["cells"].items() for j, v in per.items()}
    g3 = {(a, int(j)): np.array(v) for a, per in docs["tables"]["u_variants"]["g3_unscored_unsafe"].items()
          for j, v in per.items()}
    for direction in ("against_better", "against_worse"):
        block = out["g3a"][direction]
        for name, c, m in dsg.contrasts:
            arm = m if direction == "against_better" else c
            table = {**u, **{k: v for k, v in g3.items() if k[0] == arm}}
            members = dsg.cluster_arms(dsg.cluster[c])
            fit = sensitivities.fit_clusters(table, dsg, 100.0, 0.01, arms=members, cfg=cfg)[dsg.cluster[c]]
            e = con.contrast_fit(table, fit, c, m, dsg.common_seeds(c, m), 100.0, True, name, "x")
            k = block["contrasts"][name]
            assert k["arm_from_g3"] == arm and k["estimate"]["est"] == e.est and k["estimate"]["se"] == e.se
            assert k["estimate"]["df"] == e.df and k["estimate"]["form"] == f"S-G G3a {direction.replace('_', ' ')}"
            assert k["fit"]["sigma2"] == {a: float(v) for a, v in fit.sigma2.items()}
    assert out["g3a"]["against_worse"]["contrasts"]["P4"]["arm_from_g3"] == "a0"   # a0 takes the corner in P4
    for name, c, m in dsg.contrasts:                    # unscored only adds Unsafe: better <= primary <= worse
        primary = docs["reading"]["contrasts"][name]["U"]["est"]
        lo = out["g3a"]["against_better"]["contrasts"][name]["estimate"]["est"]
        hi = out["g3a"]["against_worse"]["contrasts"][name]["estimate"]["est"]
        shift = lambda a: np.mean([100 * (g3[(a, j)].mean() - u[(a, j)].mean()) for j in dsg.common_seeds(c, m)])
        assert lo == pytest.approx(primary - shift(m), abs=1e-9) and hi == pytest.approx(primary + shift(c), abs=1e-9)
        assert lo <= primary + 1e-9 <= hi + 2e-9


def test_the_symmetric_table_is_relabelled_with_b16s_words(pipeline):
    s, docs, _ = pipeline("plan_a")
    sym = docs["sg"]["g3_unscored_symmetric"]
    assert sym["label"] == "unscored counted Unsafe in every arm (not Gate B's adverse corner)"
    assert sym["computed"] and sym["b16_key"] == "sensitivities.S-G.g3_unscored_unsafe"
    b16 = docs["reading"]["sensitivities"]["S-G"]["g3_unscored_unsafe"]
    for name, rec in sym["contrasts"].items():
        assert rec == {"u_part_words": b16[name]["u_part_words"],
                       "differs_from_primary": b16[name]["differs_from_primary"]}


def test_without_the_g3_table_the_corners_are_not_computable(pipeline):
    s, docs, _ = pipeline("plan_a_block_a_only")
    tables = copy.deepcopy(docs["tables"])
    del tables["u_variants"]["g3_unscored_unsafe"]
    out, _ = rerun(tables, copy.deepcopy(docs["counts"]))
    for d in ("against_better", "against_worse"):
        assert all(not k["computable"] and k["reason"] == "not computable: the input holds no g3_unscored_unsafe table"
                   and k["p_in_phi"] == 1.0 for k in out["g3a"][d]["contrasts"].values())
    assert out["g3_unscored_symmetric"] == {"label": sgc.SYMMETRIC_LABEL, "computed": False,
                                            "reason": "B16's output holds no S-G g3_unscored_unsafe"}
    assert all(k["computable"] for k in out["coherent"]["contrasts"].values())


# ----- an independent reference (numpy only, none of B16's contrast or REML code) ------------------------------------


def test_plan_b_p6_against_an_independent_reference(pipeline):
    """P6 = S1 - S4 under plan B, the two-arm cluster: the paired mean of the pooled shares, the sum rule's seed part
    (the variance of the cell differences, floored at 0.01 pp^2) over J with J - 1 df, the prompt part of the J x 200
    table of x built here from the counts in exact fractions, Satterthwaite df and the t interval."""
    s, docs, _ = pipeline("plan_b")
    counts, dsg = counts_of(docs), design("plan_b")
    seeds = dsg.common_seeds("S1", "S4")

    def x(a, j):
        n, u = counts[(a, j)]["n"], counts[(a, j)]["u"]
        v = Fraction(int(u.sum()), int(n.sum()))
        nbar = Fraction(int(n.sum()), 200)
        return [float(v + (int(ui) - v * int(ni)) / nbar) for ni, ui in zip(n, u)]
    diffs = np.array([pooled(counts[("S1", j)]) - pooled(counts[("S4", j)]) for j in seeds])
    jj = len(seeds)
    v_seed, df_seed = max(float(diffs.var(ddof=1)), 0.01) / jj, jj - 1.0
    d = np.array([[a - b for a, b in zip(x("S1", j), x("S4", j))] for j in seeds])
    grand, rows, cols = d.mean(), d.mean(axis=1), d.mean(axis=0)
    ms_p = jj * float(((cols - grand) ** 2).sum()) / 199
    ms_e = float(((d - rows[:, None] - cols[None, :] + grand) ** 2).sum()) / (199 * (jj - 1))
    k = 1e4 / (200 * jj)
    v_item = max(0.0, ms_p - ms_e) * k
    q = (ms_p * k) ** 2 / 199 + (ms_e * k) ** 2 / (199 * (jj - 1)) if ms_p > ms_e else 0.0
    df = (v_seed + v_item) ** 2 / (v_seed ** 2 / df_seed + q)
    se = math.sqrt(v_seed + v_item)
    got = docs["sg"]["coherent"]["contrasts"]["P6"]
    assert got["estimate"]["est"] == pytest.approx(float(diffs.mean()), abs=1e-9)
    assert got["estimate"]["se"] == pytest.approx(se, rel=1e-9) and got["estimate"]["df"] == pytest.approx(df, rel=1e-9)
    assert got["estimate"]["item_var"] == pytest.approx(v_item, rel=1e-9)
    half = t_quantile(0.95, df) * se
    assert got["interval_90"] == pytest.approx([diffs.mean() - half, diffs.mean() + half], abs=1e-9)
    assert got["p_in_phi"] == pytest.approx(t_two_sided(diffs.mean() / se, df), rel=1e-9)


def test_plan_a_item_parts_against_an_independent_reference(pipeline):
    """The prompt part of every plan-A contrast from x built here in exact fractions (the seed part is B16's REML)."""
    s, docs, _ = pipeline("plan_a")
    counts, dsg = counts_of(docs), design("plan_a")

    def x(a, j):
        n, u = counts[(a, j)]["n"], counts[(a, j)]["u"]
        v, nbar = Fraction(int(u.sum()), int(n.sum())), Fraction(int(n.sum()), 200)
        return np.array([float(v + (int(ui) - v * int(ni)) / nbar) for ni, ui in zip(n, u)])
    for name, c, m in dsg.contrasts:
        seeds = dsg.common_seeds(c, m)
        d = np.stack([x(c, j) - x(m, j) for j in seeds])
        jj = len(seeds)
        cols, grand = d.mean(axis=0), d.mean()
        ms_p = jj * float(((cols - grand) ** 2).sum()) / 199
        ms_e = float(((d - d.mean(axis=1)[:, None] - cols[None, :] + grand) ** 2).sum()) / (199 * (jj - 1))
        got = docs["sg"]["coherent"]["contrasts"][name]["estimate"]
        assert got["item_var"] == pytest.approx(max(0.0, ms_p - ms_e) * 1e4 / (200 * jj), rel=1e-9, abs=1e-12)
        assert got["est"] == pytest.approx(100 * float(d.mean()), abs=1e-9)


# ----- the bindings ---------------------------------------------------------------------------------------------------


def _coherent_share_table(t):
    t["u_variants"]["coherent"] = t["endpoints"]["U"]["cells"]


@pytest.mark.parametrize("which,edit,match", [
    ("tables", lambda t: t.update(kind="x"), r"B16's schema refuses tables.json at"),
    ("tables", _coherent_share_table, r"tables.json holds a coherent share table \(u_variants.coherent\)"),
    ("counts", lambda c: c.update(input_sha256="0" * 64), r"name another B16 input document"),
    ("counts", lambda c: c["cells"]["S3"]["1103"]["n"].__setitem__(0, 4), r"S3 1103: a count is outside"),
    ("reading", lambda r: r.update(kind="x"), r"not B16's version-1 output of the reading plan_a_block_a_only"),
    ("reading", lambda r: r.update(reading="plan_a"), r"not B16's version-1 output"),
    ("reading", lambda r: r["provenance"].update(settings_sha256="0" * 64), r"names other reading settings"),
    ("reading", lambda r: r["provenance"].update(input_sha256="0" * 64), r"was not read from the B16 input document"),
    ("reading", lambda r: r["provenance"]["modules"].update({"reml.py": "0" * 64}), r"made by another B16"),
    ("reading", lambda r: r["provenance"]["modules"].update({"__main__.py": "0" * 64}), r"made by another B16"),
    ("reading", lambda r: r["design"]["contrasts"].pop(), r"does not hold the reading's sealed contrasts"),
    ("reading", lambda r: r["contrasts"]["P3"]["p_values"].update(U=1.5), r"holds no p-values, U part words or "
                                                                           r"headline word for P3"),
    ("reading", lambda r: r["contrasts"]["P3"]["p_values"].update(U=True), r"for P3"),
    ("reading", lambda r: r["contrasts"]["P3"]["p_values"].pop("F"), r"for P3"),
    ("reading", lambda r: r["rows"]["P2"]["u_part"].update(words=[]), r"for P2"),
    ("reading", lambda r: r["rows"]["P2"]["headline"].pop("word"), r"for P2"),
    ("reading", lambda r: r["phi"]["rejected"].append("U:P2"), r"Phi rejections do not reproduce"),
    ("reading", lambda r: r["contrasts"]["P1"]["p_values"].update(U=0.0), r"Phi rejections do not reproduce"),
])
def test_binding_refusals(pipeline, which, edit, match):
    s, docs, _ = pipeline("plan_a_block_a_only")
    edited = {k: copy.deepcopy(docs[k]) for k in ("tables", "counts", "reading")}
    edit(edited[which])
    with pytest.raises(Refusal, match=match):
        run_sg(edited["tables"], edited["counts"], edited["reading"])


def test_the_tables_must_be_the_ones_the_counts_and_b16_name(pipeline):
    s, docs, _ = pipeline("plan_a_block_a_only")
    other = pipeline("plan_b")[1]
    with pytest.raises(Refusal, match="name another B16 input document|of the reading plan_a_block_a_only"):
        run_sg(docs["tables"], other["counts"], docs["reading"])
    with pytest.raises(Refusal, match="not B16's version-1 output of the reading plan_a_block_a_only"):
        run_sg(docs["tables"], docs["counts"], other["reading"])


# ----- the output and the command line -------------------------------------------------------------------------------


def test_the_output_carries_its_rules_provenance_and_primary(pipeline):
    s, docs, paths = pipeline("plan_a_block_a_only")
    out = docs["sg"]
    assert out["kind"] == sgc.KIND and out["version"] == 1 and out["reading"] == "plan_a_block_a_only"
    assert out["label_suffix"] == "block A only (3 seeds per method arm)"
    assert all(k["headline_cell"].endswith("[block A only (3 seeds per method arm)]")
               for k in out["coherent"]["contrasts"].values())
    prov = out["provenance"]
    assert prov["tables_sha256"] == sk.sha(paths["tables"].read_bytes())
    assert prov["counts_sha256"] == sk.sha(paths["counts"].read_bytes())
    assert prov["reading_sha256"] == sk.sha(paths["reading"].read_bytes())
    assert prov["b16_modules"] == docs["reading"]["provenance"]["modules"]
    here = TREE / "scripts" / "stage1_s1" / "reading_input"
    assert prov["modules"] == {p: sk.sha((here / p).read_bytes()) for p in ("coherent.py", "sg_coherent.py")}
    assert out["primary"] == {n: {"u_part_words": docs["reading"]["rows"][n]["u_part"]["words"],
                                  "headline": docs["reading"]["headline"][n]} for n in docs["reading"]["headline"]}
    assert out["rule"] == sgc.RULE and out["readings"] == sgc.READINGS and out["model"]["floor_pp2"] == 0.01


def test_the_pinned_rule_texts_are_the_frozen_texts():
    rev4 = TREE / "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md"
    prereg = TREE / "research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md"
    if not (rev4.is_file() and prereg.is_file()):
        pytest.skip("the pre-registrations are not in this tree")
    r4, pg = rev4.read_text(), prereg.read_text().replace("`", "").replace("**", "")
    assert "Coherent-only U is reported for every arm; every label is re-read on coherent answers (S-G)." in r4
    assert "Coherent-only U is reported for every arm; every label is re-read on coherent answers (S-G)." in sgc.RULE[0]
    for needle in ("The arm-level U in G2 is the frozen pooled U_coherent (coherent Unsafe over coherent answers).",
                   "A prompt with 0 coherent answers in either arm of a pair has no U_coh there",
                   "No limit on that count changes a verdict", "(a) unscored answers counted against the verdict"):
        assert needle in pg and any(needle in r for r in sgc.RULE)
    assert "S-G** (coherent-only U and both G3 corners)" in r4 and "labels it \"fixed after Gate B wave 1\"" in r4


def test_command_line_writes_once_and_prints_words_only(pipeline, tmp_path):
    s, docs, paths = pipeline("plan_a_block_a_only")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": os.pathsep.join([str(TREE), str(sk.TREE), os.environ.get("PYTHONPATH", "")])}
    cmd = [PY, "-B", "-m", "scripts.stage1_s1.reading_input.sg_coherent", "--tables", str(paths["tables"]),
           "--counts", str(paths["counts"]), "--reading", str(paths["reading"])]
    ok = subprocess.run(cmd + ["--out", str(tmp_path / "sg.json")], cwd=TREE, env=env, capture_output=True, text=True)
    assert ok.returncode == 0 and ok.stderr == "", ok.stderr
    data = (tmp_path / "sg.json").read_bytes()
    out = json.loads(data)
    assert data == canonical_json(out) and out == docs["sg"]
    lines = ok.stdout.splitlines()
    assert lines[0] == f"wrote {tmp_path / 'sg.json'} sha256 {sk.sha(data)}" and len(lines) == 2
    assert lines[1] == "S-G coherent headline: " + "; ".join(f"{k} {w}" for k, w in out["coherent"]["headline"].items())
    again = subprocess.run(cmd + ["--out", str(tmp_path / "sg.json")], cwd=TREE, env=env, capture_output=True, text=True)
    assert again.returncode == 2 and "sg.json exists" in again.stderr and (tmp_path / "sg.json").read_bytes() == data
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    worse = subprocess.run([PY, "-B", "-m", "scripts.stage1_s1.reading_input.sg_coherent", "--tables", str(bad),
                            "--counts", str(paths["counts"]), "--reading", str(paths["reading"]), "--out",
                            str(tmp_path / "x.json")], cwd=TREE, env=env, capture_output=True, text=True)
    assert worse.returncode == 2 and "not valid JSON" in worse.stderr and not (tmp_path / "x.json").exists()
    numbers = {f"{k['estimate']['est']:.{n}f}" for k in out["coherent"]["contrasts"].values() for n in (2, 3)}
    numbers |= {f"{v:.{n}f}" for a in out["coherent"]["arms"].values() for v in a["cells_pp"].values()
                if v is not None for n in (2, 3)}
    for text in (ok.stdout + ok.stderr, again.stdout + again.stderr, worse.stdout + worse.stderr):
        assert not VALUE.search(text) and not any(x in text for x in numbers) and sk.TEXT not in text


def test_an_unexpected_error_prints_its_type_only(pipeline, tmp_path, monkeypatch, capsys):
    s, docs, paths = pipeline("plan_a_block_a_only")

    def boom(*args, **kw):
        raise KeyError("a value 12.3456")
    monkeypatch.setattr(sgc, "sg", boom)
    rc = sgc.main(["--tables", str(paths["tables"]), "--counts", str(paths["counts"]), "--reading",
                   str(paths["reading"]), "--out", str(tmp_path / "x.json")])
    err = capsys.readouterr().err
    assert rc == 2 and "an unexpected KeyError" in err and "12.3456" not in err and not (tmp_path / "x.json").exists()


# ----- B16 is byte-identical to the stamp ----------------------------------------------------------------------------


def test_b16_is_byte_identical_to_the_stamped_tree():
    """Every file of scripts/stage1_s1/reading/ (its code, settings, tests, README and mutation spec) is the one at
    commit 55d5f8b, the tree the 31 Oct time stamp binds: this reader imports B16 and never edits it."""
    root = TREE / "scripts" / "stage1_s1" / "reading"
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    assert len(files) == B16_TREE_FILES
    assert hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() == B16_TREE_DIGEST


# ----- the coverage simulation runs (its full run is the lead's) ------------------------------------------------------


def test_the_coverage_simulation_runs_and_its_truths_hold():
    plain, coherent = sim.truths("concentrated", 0.15, ("S1", "S4"))
    assert coherent == pytest.approx(plain, abs=1e-12)          # failures unrelated to harm: G2's truth is plain's
    plain, coherent = sim.truths("answer-linked", 0.15, ("S1", "S4"))
    assert coherent["S1"] < plain["S1"] - 0.03 and coherent["S4"] == pytest.approx(plain["S4"], abs=1e-12)
    out = sim.simulate(["iii-prompt"], 3, 5, "plan_b")
    rec = out["iii-prompt"]["contrasts"]["P6"]
    assert out["iii-prompt"]["reps"] == 3 and rec["coherent"]["computable"] == 3 and rec["primary"]["computable"] == 3
    assert rec["coherent"]["truth_pp"] < rec["primary"]["truth_pp"]            # S1 loses its most harmful prompts
    again = sim.simulate(["iii-prompt"], 3, 5, "plan_b")
    assert again["iii-prompt"]["contrasts"] == out["iii-prompt"]["contrasts"]  # seeded
