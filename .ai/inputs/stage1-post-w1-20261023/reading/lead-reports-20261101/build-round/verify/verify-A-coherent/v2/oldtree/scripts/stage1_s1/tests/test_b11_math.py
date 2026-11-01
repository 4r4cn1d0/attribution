"""B11 arithmetic on synthetic matrices (REF R.1.4 tests 1, 6 and 9; the operator, the cosine, rho, the ranking,
the tau counts and the rounding share). No model, no file."""

from __future__ import annotations

import math

import b11_fixtures  # noqa: F401  (puts the repository root on sys.path)
import pytest
import torch

from scripts.stage1_s1 import safe_lora as sl


def _gen(seed: int) -> torch.Generator:
    return torch.Generator().manual_seed(seed)


def _direct(b_new: torch.Tensor, b: torch.Tensor, a: torch.Tensor) -> tuple[float, float]:
    """The Frobenius cosine and norm ratio from the full products (out x in), float64."""
    new, old = (b_new.double() @ a.double()), (b.double() @ a.double())
    return float((new * old).sum() / (new.norm() * old.norm())), float(new.norm() / old.norm())


@pytest.mark.parametrize("out_dim, in_dim", [(24, 24), (40, 24), (24, 40)])
def test_the_factored_form_equals_the_formed_fast_form_c(out_dim, in_dim):
    g = _gen(10)
    v = torch.randn(out_dim, in_dim, generator=g)
    b = torch.randn(out_dim, 4, generator=g)
    projected, norm = sl.project_b(v, b)
    c64 = (v.double() @ v.double().T) / torch.linalg.vector_norm(v.double())
    assert norm == pytest.approx(float(torch.linalg.vector_norm(v.double())), rel=1e-15)
    assert torch.allclose(projected, c64 @ b.double(), rtol=1e-12, atol=1e-12)
    c32 = (v @ v.T) / torch.norm(v)                                           # the official code's float32 form
    assert torch.allclose(projected.float(), c32 @ b, rtol=1e-4, atol=1e-5)
    assert projected.dtype == torch.float64 and tuple(projected.shape) == (out_dim, 4)


def test_the_operator_rescales_a_scaled_identity_v_and_keeps_its_direction():
    """V = s I (n x n): C = (s / sqrt(n)) I, so B' = (s / sqrt(n)) B, cos = 1 and rho = s / sqrt(n) (REF R.1.2)."""
    n, s = 16, 0.5
    b = torch.randn(n, 4, generator=_gen(11))
    a = torch.randn(4, 9, generator=_gen(12))
    projected, norm = sl.project_b(s * torch.eye(n), b)
    assert norm == pytest.approx(s * math.sqrt(n))
    assert torch.allclose(projected, (s / math.sqrt(n)) * b.double(), rtol=1e-12)
    cosine, rho = sl.similarity(projected, b, a)
    assert cosine == pytest.approx(1.0, abs=1e-12) and rho == pytest.approx(s / math.sqrt(n), rel=1e-12)


@pytest.mark.parametrize("out_dim, in_dim", [(24, 24), (40, 24), (24, 40)])
def test_the_gram_form_equals_the_direct_frobenius_cosine_and_ratio(out_dim, in_dim):
    g = _gen(13)
    v = torch.randn(out_dim, in_dim, generator=g)
    for rank in (1, 3):                                       # low-rank V: the update turns and shrinks
        v_low = torch.randn(out_dim, rank, generator=g) @ torch.randn(rank, in_dim, generator=g)
        b, a = torch.randn(out_dim, 4, generator=g), torch.randn(4, in_dim, generator=g)
        for matrix in (v, v_low):
            projected, _ = sl.project_b(matrix, b)
            cosine, rho = sl.similarity(projected, b, a)
            direct_cos, direct_rho = _direct(projected, b, a)
            assert cosine == pytest.approx(direct_cos, rel=1e-12, abs=1e-14)
            assert rho == pytest.approx(direct_rho, rel=1e-12)
            assert -1.0 - 1e-12 <= cosine <= 1.0 + 1e-12 and rho > 0


def test_scaling_lora_b_by_a_constant_leaves_the_cosine_unchanged_and_scales_nothing_else():
    g = _gen(14)
    v, b, a = torch.randn(40, 24, generator=g), torch.randn(40, 4, generator=g), torch.randn(4, 24, generator=g)
    base_cos, base_rho = sl.similarity(sl.project_b(v, b)[0], b, a)
    for c in (4.0, 0.125, -2.0):                       # a power of two scales every float exactly: equal bits
        assert sl.similarity(sl.project_b(v, c * b)[0], c * b, a) == (base_cos, base_rho)
    cos_3, rho_3 = sl.similarity(sl.project_b(v, 3.0 * b)[0], 3.0 * b, a)   # 3 B rounds once in float32
    assert cos_3 == pytest.approx(base_cos, rel=1e-6) and rho_3 == pytest.approx(base_rho, rel=1e-6)
    assert sl.similarity(sl.project_b(v, b)[0], b, 4.0 * a) == (base_cos, base_rho)   # the scale of A cancels too


def test_bfloat16_minus_float32_in_float32_is_exact():
    g = _gen(15)
    aligned = (0.02 * torch.randn(64, 48, generator=g)).to(torch.bfloat16)
    base = aligned.to(torch.float32) + 1e-3 * torch.randn(64, 48, generator=g)
    v = sl.alignment_matrix(aligned, base)
    assert v.dtype == torch.float32
    assert torch.equal(aligned.to(torch.float32).to(torch.bfloat16), aligned)        # the cast is exact
    exact = (aligned.to(torch.float64) - base.to(torch.float64)).to(torch.float32)   # one rounding of the exact value
    assert torch.equal(v, exact)
    assert not torch.equal(v, (aligned - base.to(torch.bfloat16)).to(torch.float32))  # not a bfloat16 subtraction


def test_alignment_matrix_refuses_a_shape_mismatch():
    with pytest.raises(sl.Refusal, match="differ in shape"):
        sl.alignment_matrix(torch.zeros(4, 5), torch.zeros(5, 4))


def test_project_b_refuses_a_zero_or_non_finite_v_and_a_misfit_b():
    b = torch.ones(4, 2)
    with pytest.raises(sl.Refusal, match="V is zero"):
        sl.project_b(torch.zeros(4, 3), b)
    with pytest.raises(sl.Refusal, match="V is zero"):
        sl.project_b(torch.full((4, 3), float("inf")), b)
    with pytest.raises(sl.Refusal, match="output size"):
        sl.project_b(torch.ones(5, 3), b)
    nan_b = b.clone()
    nan_b[0, 0] = float("nan")
    with pytest.raises(sl.Refusal, match="not finite"):
        sl.project_b(torch.ones(4, 3), nan_b)


def test_similarity_refuses_an_undefined_cosine():
    a = torch.ones(2, 3)
    with pytest.raises(sl.Refusal, match="undefined"):
        sl.similarity(torch.ones(4, 2), torch.zeros(4, 2), a)              # B A = 0
    with pytest.raises(sl.Refusal, match="undefined"):
        sl.similarity(torch.zeros(4, 2), torch.ones(4, 2), a)              # B' A = 0
    with pytest.raises(sl.Refusal, match="fit together"):
        sl.similarity(torch.ones(4, 2), torch.ones(4, 2), torch.ones(3, 3))


def test_the_ranking_is_ascending_with_ties_by_name():
    assert sl.ranking({"m.b": 0.1, "m.a": 0.1, "m.c": 0.05, "m.d": 0.7}) == ["m.c", "m.a", "m.b", "m.d"]
    assert sl.ranking({"model.layers.2.x": 0.2, "model.layers.10.x": 0.2}) == ["model.layers.10.x", "model.layers.2.x"]


def test_the_ranking_uses_the_exact_float64_cosine_never_a_rounded_one():
    """Rounded to 5 decimals (the official code) these two would tie and the name would put m.a first."""
    cosines = {"m.a": 0.30000002, "m.b": 0.30000001}
    assert sl.ranking(cosines) == ["m.b", "m.a"]
    assert sl.ranking({"m.a": math.nextafter(0.3, 1.0), "m.b": 0.3}) == ["m.b", "m.a"]


def test_tau_counts_follow_the_paper_and_the_official_code_rules():
    cosines = [0.35, 0.349999, 0.3500004, 0.6, 0.1]
    counts = sl.tau_counts(cosines, (0.35, 0.5))
    assert counts["0.35"] == {"paper_strict_below": 2, "official_code_rounded_at_or_below": 4}
    assert counts["0.5"] == {"paper_strict_below": 4, "official_code_rounded_at_or_below": 4}
    assert sl.tau_counts([0.5000049, 0.500006], (0.5,))["0.5"] == {"paper_strict_below": 0,
                                                                     "official_code_rounded_at_or_below": 1}


def test_the_bf16_rounding_share_is_the_rounding_norm_over_the_v_norm():
    exact = torch.tensor([[1.0, 0.5], [0.25, -2.0]])                     # exactly representable in bfloat16
    assert sl.bf16_rounding_share(exact, 1.0) == 0.0
    w = torch.tensor([[1.0 + 2.0 ** -12, 3.0]])                           # rounds to 1.0 in bfloat16
    assert sl.bf16_rounding_share(w, 2.0 ** -11) == pytest.approx(0.5, rel=1e-12)
    assert sl.bf16_rounding_share(w.to(torch.bfloat16), 1.0) == 0.0       # a bfloat16 base has no rounding
    half_kept = torch.tensor([[1.0 + 2.0 ** -9]])                         # float16 keeps it; bfloat16 rounds it
    assert sl.bf16_rounding_share(half_kept, 2.0 ** -8) == pytest.approx(0.5, rel=1e-12)


def test_pin_matches_is_a_prefix_rule():
    assert sl.pin_matches("a1847dff" + "0" * 32, "a1847dff")
    assert not sl.pin_matches("00a1847dff" + "0" * 30, "a1847dff")
    assert sl.pin_matches("ab" * 20, "ab" * 20) and not sl.pin_matches("ab" * 20, "ab" * 19 + "ac")
