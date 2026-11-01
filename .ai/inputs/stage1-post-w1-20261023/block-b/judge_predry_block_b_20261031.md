# Block B judges: $0 pre-check on the 69 finished units (31 Oct 2026, 09:41–09:42 UTC, clock checked)

Purpose: close GB3 (no B10 unit had run on a real judge pod) before any paid launch, at no cost. No pod, no network.

- `judge_units_stage1.py units-of-block B --out <scratch>/units69.txt`: exit 0; `units 69`, by kind a0_arm 3, arm 21,
  ref_eval 28, ref_train 12, safe_lora 5 (b-20's 3 Safe LoRA units missing, as expected); file SHA-256 `4ff95d54…`.
  Written to scratch, not `$REC/judge_units_b.txt` (step 0 needs that absent).
- Dry bundles with scratch tags (not s1b-hb-1 / s1b-granite-1; `bundle` writes only its `--out` folder, R
  `judge_pod.py:1044-1047, 286-337`):
  - `s1b-dry-hb-0`: exit 0; one group `prepared-kt-dolly-olmo2`, manifest `9ed61826…`, 69 units; skipped 0;
    items greedy 13,800, sampled 41,400; todo 55,200; cap 5.0 h; cost_upper $9.25; estimate 65.2–120.4 min, $2.01–3.71.
  - `s1b-dry-gr-0` (Granite, gate on): exit 0; the same group, 69 units; greedy 13,800; cap 3.0 h; $5.55; estimate
    43.0–85.0 min; known_answers enabled, unit `olmo2-1b-1101/round1/1101-a0-e1-a1`, `8f0fa83a…`, reference `b5b2678e…`,
    items 200.
- GB3's $0 option, run: each bundle unpacked as `judge_pod.unpack_command` does (tarfile filter='data'), then
  `python -I bundle/tool/pod/pod_job.py verify --bundle bundle` on the Mac (venv Python 3.11.15; the pod has 3.12):
  - HarmBench: `bundle_verified`, files 428, group 1, units 69, greedy 13,800, sampled 41,400.
  - Granite: `bundle_verified`, files 451, group 1, units 69, greedy 13,800.
  The bundles shipped the stage-1 pod `bundle.py` (B10) plus `bundle_gateb.py`; the pod-side B10 check passed for every
  ref_eval and safe_lora unit present.
- Deleted right after (answer text): both bundle folders and both unpacked copies. Kept: the filtered printed records
  (no label counts), the unit list, stderr (empty of refusals).
- Not covered: b-20's 3 units (not run yet); the paid steps (snapshot download, judging, fetch). At launch, steps 0–3 run
  again with the real tags (GB10: the bundle SHA-256 changes with the tag and units).
