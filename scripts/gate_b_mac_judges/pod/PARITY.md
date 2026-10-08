# Mac-versus-pod parity of the HarmBench judge: design and pre-set rule

Written 8 October 2026, 20:07 UTC (clock checked), before any pod run. Revised 8 October 2026, 21:04 UTC (clock
checked), still before any pod run: the tokenizer fingerprint condition (rule 0) and the `--pod-run-record` argument,
after the review. Revised again 8 October 2026, 22:00 UTC (clock checked), still before any pod run, after the second
review: `parity.py` refuses a `--pod-cache` that is not the cache its run record names, and the zsh block starts with
`setopt interactivecomments` and holds no comment. The acceptance rule itself (rules 0 to 3) is unchanged. The rule below is fixed now and
is not changed after the pod numbers are seen. The lead records this file's SHA-256 in `research/FOCUS.md` before the
first launch.

## Why a parity check

The pod runs the same judge as the Mac: the same pinned snapshot (all ten files pinned by SHA-256), the same template
(SHA-256 `c1c47e30…`), the same tokenizer built from the same `tokenizer.model` (`dadfd56d…`) by the same code and the
same `transformers`/`tokenizers` versions, the same 512-token truncation, the same 2048-token input cap, fp16, batch
size 1, one greedy token, the same label rule (`pod_judge.py`; the syntax-tree tests in `tests/test_judge_pod.py`).
Only the device changes: `cuda` (A100, CUDA 12.8 kernels) instead of `mps`. Floating-point kernels differ between the
two devices (attention kernels, matrix-multiply summation order), so a few answers whose "Yes" and "No" logits are
nearly tied may get the other label. The parity check measures how many.

The text side (template, tokenizer, truncation) runs on the CPU and should agree exactly. Two checks cover it:

- **The tokenizer fingerprint.** On both devices `pod_judge.tokenizer_fingerprint` hashes the built tokenizer's vocab
  and merges (SHA-256 of canonical JSON). The pod writes its value into `run-record.json`; `parity.py` computes the
  Mac's from `harmbench_files.load_tokenizer` (the Mac's pinned snapshot; CPU only, no model). Both sides refuse
  when `sentencepiece` or `protobuf` is installed: the Mac venv has neither, and either could change how
  transformers builds the tokenizer.
- **Token counts.** The check reports token-count differences: any nonzero value means a setup difference (a file or
  package), not numerics.

## What is compared

- **Unit:** the Gate A seed-1101 e1 unit `olmo2-1b-1101/round1/1101-a0-e1-a1` (COMPLETE.json `8f0fa83a…`), 800 answers
  (600 sampled, 200 greedy). The Mac already judged them:
  `research/experiments/2026-10-08-harmbench-summary-olmo2-1b-gate-a.json` gives 186 "yes" of 600 sampled and 57 of
  200 greedy, with 0 unparsed.
- **Mac labels:** the old Mac cache `tmp/family-probe-olmo2-1b/harmbench-items.jsonl`, brought into the tool's cache format by
  the tool's own import (`import_cache.import_old`, as in `parity_gate_a.py`). The import pins each label to its
  unit's COMPLETE.json SHA-256 and checks each record against that unit's answer SHA-256. `parity.py` refuses unless
  the imported labels give 186/600 and 57/200 again. This was checked on 8 Oct with the real caches:
  `test_parity_gate_a_mac_side_on_the_real_caches` passed.
- **Pod labels:** one pod run of that unit (`judge_pod.py launch --unit …`, by itself or added to the first Gate B
  launch), and the cache that `judge_pod.py` fetched and hash-checked. The fetched `run-record.json` of that run gives
  the pod's tokenizer fingerprint and the SHA-256 of the cache that run wrote (`cache.sha256`). `parity.py` refuses
  (exit 2) unless `--pod-cache` has that SHA-256, so the labels compared are the ones that run produced.
- **Pairing:** label by label, by (COMPLETE.json SHA-256, mode, prompt id, sample index). For every pair, both caches must
  give the same answer SHA-256. If one does not, the comparison refuses.

## Reported, per mode

`n`, the items each cache holds, identical labels, agreement (identical / n), flips by direction (Mac label -> pod
label, for example `yes->no`, `no->unparsed`), "yes" and "unparsed" counts for each side, `delta_yes` = pod yes - Mac
yes, and token-count differences (`input_tokens`, `answer_tokens`, `truncated`). Once per report: the Mac and pod
tokenizer fingerprints and whether they are identical.

## The pre-set acceptance rule

0. The pod run record's tokenizer fingerprint equals the Mac's. A different or missing pod fingerprint fails parity,
   whatever the labels show.

A mode **passes** when all of these hold:

1. the pod judged every item of the mode;
2. at least 99% of the labels are identical (sampled: 594 or more of 600; greedy: 198 or more of 200);
3. |delta_yes| ≤ 2.

Parity **passes** only when rule 0 holds and both modes pass.

- **Pass:** pod-judged files may be used like Mac-judged files.
- **Fail:** pod numbers are reported only beside Mac numbers and never mixed in one contrast. For example, an arm's
  E_HB against the untuned baseline then uses labels from one device only: both from the pod, or both from the Mac.

What the rule allows at most, in yes share: 2/600 = 0.33 percentage points (sampled) and 2/200 = 1.0 percentage point
(greedy) per unit. For scale, the Gate A greedy E_HB values are tens of points. Agreement of 99% allows at most 6
sampled flips and 2 greedy flips. Flips that cancel do not move the yes count, but they do count against agreement.

**Not part of the rule, flagged for the lead:** a nonzero token-count difference means the pod's text path differs
from the Mac's. I recommend treating it as a setup defect to investigate before using any pod number, even when the
label rule passes. The lead decides.

## Commands (for the lead; not run by the builder)

The pod run is the README's launch (blocks 1 and 2 there) with `TAG='parity-1101'` and the `UNITS` below; its folder
is `tmp/judge-pod/parity-1101`. The comparison needs no model and no bank; `--work` must be a new folder outside the
repository's `tmp/`. As in the README, the zsh block starts with `setopt interactivecomments` and holds no comment (a
terminal pastes the whole block as one input, read before its first line runs).

```zsh
setopt interactivecomments
ROOT=/Users/spiderishi/Coding/attribution
K=$ROOT/scripts/gate_b_mac_judges
PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python
UNITS=(--unit $ROOT/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1)
P=$ROOT/tmp/judge-pod/parity-1101
PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$K/pod/parity.py" gate-a \
  --pod-cache "$P/fetched/out/harmbench-pod.jsonl" --pod-run-record "$P/fetched/out/run-record.json" \
  --work '<scratch>/judge-pod-parity-work' --report "$P/parity-report.json"
```

Exit codes: 0 PASS, 1 FAIL, 2 refused (also when `--pod-cache` is not the cache the run record names). The report
(canonical JSON) holds the rule, the two tokenizer fingerprints, the pod cache's SHA-256 and every row. The printed
lines hold counts and the fingerprints only.

`parity.py compare --mac-cache M --pod-cache P --pod-run-record R "${UNITS[@]}"` applies the same rule to any other
unit that has Mac labels in the tool's format, for example a Gate B unit judged on both devices.

## Limits

- One unit of one model family (OLMo-2-1B answers, 800 items) is the whole sample. A different answer distribution,
  such as Llama answers, could have a different rate of near-tie items. If a Llama unit with Mac HarmBench labels exists,
  adding it with `parity.py compare` would widen the check.
- The rule measures label agreement. It does not test CUDA numerics on any other input.
- The fingerprint covers the vocab and merges only. Other tokenizer settings (normalizer, pre-tokenizer, added tokens)
  are covered by the token-count differences.
- `harmbench_files.py`'s label rule maps NaN or Inf logits to `unparsed`. A pod-only `unparsed` therefore counts as a
  flip.
