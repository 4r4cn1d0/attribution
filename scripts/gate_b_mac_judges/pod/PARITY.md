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

## Granite parity (pre-set rule)

Added 9 October 2026, 12:57 UTC (clock checked), before any Granite pod run, for the Granite judge on the pod
(`judge_pod.py --judge granite`; the user, 9 Oct: "just use the gpus for granite as well"). Everything above this
section is the HarmBench rule, unchanged: it is byte for byte the first 7,880 bytes of this file, the file whose
SHA-256 `76e1457f…` the lead recorded. The rule below is fixed now and is not changed after the pod numbers are seen.
**The lead records this file's new SHA-256 in `research/FOCUS.md` before the first Granite pod launch.**

Revised 9 October 2026, 15:29 UTC (clock checked), still before any Granite pod run (the lead's choices after the
second review): the pod's input hashes are paired with the Mac's **per item**, and the run record must also name the
GGUF SHA-256 the pod measured and a llama.cpp build with GPU offload. The thresholds (rule 0, 196 of 200, ≤ 3) are
unchanged. The parity launch runs without the launcher's known-answer gate (README, "The known-answer gate"): its four
units already hold the gate's 200 answers, and this rule is the stricter test of them.

### Why a Granite parity check

The pod runs the Mac's Granite judge. `pod/granite_pod.py` calls `granite_files.granite_judge` itself (the same
prompt construction `granite_input`, trimming, token check `granite_precheck`, call with 32 new tokens, temperature 0
and top_k 1, and label parse `parse_score`), with loaders that are the Mac's loaders with the pod's paths. It uses the
pinned Q4_K_M GGUF (commit `8c87479a…`, SHA-256 `b4fa861b…`, checked before the load), the Mac's tokenizer folder (ten
files pinned by SHA-256 and shipped in the bundle), the Mac judge venv's package versions (transformers 5.18.0,
tokenizers 0.23.2, Jinja2 3.1.6) and llama-cpp-python 0.3.36 built from the sdist the Mac built its wheel from
(SHA-256 `832db069…`). Only the llama.cpp backend changes: CUDA on an A100 (compute capability 8.0) instead of Metal.
The GPU kernels differ (matrix-multiply order, quantized dot products), so an output whose score is nearly tied may
come out with the other label. The check measures how often that happens.

### What is compared

- **Units:** the four OLMo-2-1B Gate A units of `parity_gate_a.UNIT_DIRS`: the untuned unit `1101-a0-init-a1` and the
  e1 units `1101-a0-e1-a1` (both under `tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/`),
  `1102-a0-e1-a1` (`tmp/family-probe-olmo2-1b-gateA-1102/…`) and `1103-a0-e1-a1` (`tmp/family-probe-olmo2-1b-gateA-1103/…`).
  The items are their 800 greedy harm answers, 200 per unit.
- **Mac labels:** each probe kit's `second-judge-probe-items.jsonl`, brought into the tool's cache format by the tool's
  own import (`import_cache.import_old` over `parity_gate_a.GRANITE_KITS`, as `parity_gate_a.py` does; each label is
  pinned to its unit's COMPLETE.json SHA-256 and bound to the unit by its guard rows). `parity.py` refuses unless the
  import gives 5, 93, 86 and 94 "yes" of 200 (untuned, e1 1101, 1102, 1103) and no unparsed label, as the kits'
  `second-judge-probe-summary.json` record.
- **Pod labels:** one Granite pod run of the four units (`judge_pod.py launch --judge granite
  --no-known-answer-gate`), and the cache, the inputs file and the run record that `judge_pod.py` fetched and
  hash-checked. `parity.py` refuses (exit 2) unless `--pod-cache` and `--pod-inputs` have the SHA-256 that the run
  record names for them, and the record names cuda, `common.GRANITE`, the pinned GGUF (as its revision, and as the
  SHA-256 the pod measured before the load, `files.gguf_sha256`) and a llama.cpp build with GPU offload
  (`llama.gpu_offload`).
- **The text path.** The Mac side is computed by `parity.py granite` under the judge venv: the Mac tokenizer folder is
  checked against the pins, the venv's packages against the pod's pins, the tokenizer is loaded by
  `granite_files.load_granite_tokenizer`, its fingerprint is `pod_judge.tokenizer_fingerprint` (the SHA-256 of the
  vocab and merges as canonical JSON, the same function as on the pod), and every item's templated input comes from
  `granite_files.granite_input` and is kept as its SHA-256 only. The pod side is the run record's fingerprint (the pod
  also refuses, before it judges anything, a fingerprint other than the Mac's pinned `5354502d…`) and the inputs file:
  one row per judged item, keyed by the item's ids, with the SHA-256 of the text that the pod's llama.cpp received.
- **Pairing:** labels by (COMPLETE.json SHA-256, greedy, prompt id); both caches must name the unit's answer SHA-256,
  or the comparison refuses. Input hashes by the same item: each Mac item is paired with the pod's row of that item
  (COMPLETE.json SHA-256, prompt id, sample index), never with another unit's row of the same prompt and answer (the
  800 Gate A items hold 647 distinct prompt-and-answer pairs; 255 items share theirs with an item of another unit). The row must name the unit's
  answer SHA-256, or the comparison refuses; a row whose prompt SHA-256 differs counts as different. The run record's
  inputs count is 800 for the 800 items.

### Reported, per unit

`n`, the items each side holds, identical labels, agreement, flips by direction (Mac label -> pod label, for example
`no->yes` or `no->unparsed`), "yes" and "unparsed" counts of each side, `delta_yes` = pod yes - Mac yes, the input
hashes (identical, different, missing), and the token-count and trim differences between the pod's cache and the
Mac's recomputed `granite_input`. Once per report: both tokenizer fingerprints and the inputs total.

### The pre-set acceptance rule

0. The two tokenizer fingerprints are identical, and every item's input SHA-256 is identical on both sides (800 of
   800, each item against its own pod row; an item without its own row counts as different). Otherwise parity fails,
   whatever the labels show.

A unit **passes** when all of these hold:

1. the pod judged every item of the unit (200 of 200);
2. at least 98% of the labels are identical: 196 or more of 200;
3. |pod yes - Mac yes| ≤ 3.

An unparsed label on one side counts as a flip: it is not identical to the other side's yes or no. Parity **passes**
only when rule 0 holds and all four units pass.

- **Pass:** pod-judged Granite files may be used like Mac-judged ones.
- **Fail:** pod Granite numbers are never mixed with Mac Granite numbers in one contrast. For example, an arm's Granite
  harm rate against the untuned baseline then uses labels from one device only: both from the pod, or both from the
  Mac.

What the rule allows at most, per unit: 4 flips and a yes-share difference of 3/200 = 1.5 percentage points. For
scale, the Gate A Mac Granite harm rates are 2.5% (untuned) and 43% to 47% (e1). Flips that cancel do not move the
yes count, but they count against agreement.

**Not part of the rule, flagged for the lead:** with identical input hashes, a nonzero token-count or trim difference
means the cache's counts were made differently; I recommend treating it as a setup defect to investigate before using
any pod number. The lead decides.

### Commands (for the lead; not run by the builder)

The pod run is the README's Granite parity launch (its blocks G0 and G2; G0 sets `GATE=(--no-known-answer-gate)`),
with a new tag. The comparison needs no model
and no GPU, but it reads the dev bank's harm prompts and the units' answers (in memory, hashed only), and it must run
under the judge venv (`tmp/judge-venv`, transformers 5.18.0: the minimal venv's 4.56.2 is refused). `--work` must be a
new folder outside the repository's `tmp/`. As in the README, the zsh block starts with `setopt interactivecomments`
and holds no comment.

```zsh
setopt interactivecomments
ROOT=/Users/spiderishi/Coding/attribution
K=$ROOT/scripts/gate_b_mac_judges
JV=$ROOT/tmp/judge-venv/bin/python
TAG='<the-granite-parity-tag>'
P=$ROOT/tmp/judge-pod/$TAG
cd /private/tmp && PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "$JV" -B "$K/pod/parity.py" granite \
  --pod-cache "$P/fetched/out/granite-pod.jsonl" --pod-run-record "$P/fetched/out/run-record.json" \
  --pod-inputs "$P/fetched/out/granite-inputs.jsonl" --work '<scratch>/granite-parity-work' \
  --report "$P/granite-parity-report.json"
```

Exit codes: 0 PASS, 1 FAIL, 2 refused (also when `--pod-cache` or `--pod-inputs` is not the file the run record names,
when the record is not a cuda Granite run of the pinned GGUF with GPU offload, when the Mac import does not give 5, 93,
86 and 94, or when a cache record or an inputs row names another answer).
The report (canonical JSON) holds the rule, both fingerprints, the input-hash counts, the pod files' SHA-256 and every
row. The printed lines hold counts, hashes and the fingerprints only.

### Limits

- Four units of one model family (OLMo-2-1B answers, 800 items) are the whole sample. Llama answers could have another
  rate of near ties.
- The rule measures label agreement on these inputs. It does not test CUDA numerics on any other input.
- llama-cpp-python reuses the key-value cache of the longest token prefix shared with the previous call, on both
  devices. So an item's numerics can depend on the item judged before it. The pod judges in the tool's order (the
  given units in turn, each in file order), which need not be the order the old probe used. The tolerance covers this.
- The Mac labels are the old probe's (`second_judge_probe.py`, SHA-256 `c51e466c…`), whose judge settings
  `granite_files.py` ported unchanged; they were made on the Mac judge venv as it was then.
- `granite_files.parse_score` maps any output without a final yes or no score to `unparsed`; a pod-only `unparsed`
  counts as a flip.
