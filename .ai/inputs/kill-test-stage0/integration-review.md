# Integration review: kill-test-stage0-engine-20261006

6 October 2026 (IST). Reviewed and integrated by General Implementation 2, the lead. Built by the Specialized Implementation chat from the brief [kill-test-stage0-engine-20261006](../../briefs/kill-test-stage0-engine-20261006.md), in a workspace prepared by hand at `fefb142` (manifest `0c54d947…`).

## Scope and identity

- **Changes:** 7 files changed and 19 added in `experiments/safety_selection/**` and `scripts/`, plus the new run kit `runkit/kill-test-stage0/` (16 files). All are inside the brief's owned paths.
  - Every file was copied byte for byte from the workspace.
  - The repository's copies of the changed files were unchanged since the workspace copy.
- **Engine code identity:** `c52c0ebc83793fc552f84908e83542d5e46543459fcafb7be2fc9c7ff42ac597` (was `0d55658c…`).
- **Recipes** (config SHA-256 / training identity). The preflight tries them in this order:

  | Recipe | Config SHA-256 | Training identity |
  |---|---|---|
  | `study-kt-instruct-r64-mb4-20261006` (SDPA, 4 × 2) | `1656cba9…` | `71bd0a2a…` |
  | `study-kt-instruct-r64-mb2-20261006` (SDPA, 2 × 4) | `47f1b13a…` | `3124bf7b…` |
  | `study-kt-instruct-r64-mb2-eager-20261006` (eager, 2 × 4) | `92563768…` | `982c51fb…` |

- **Data config:** `study-kt-data-dolly` `1dffddc8…`, in its first-preparation form (asserted counts null, design seed 20261006).

## Checks run here

| Check | Result |
|---|---|
| Engine suites (`safety_selection`, `minimal_safety`), in the workspace and again in the repository | 311 passed, 3 CUDA-only skips, exit 0 |
| Stage B | 172 passed, exit 0 |
| Durability | 260 passed, exit 0 |
| Code identity in the repository | `c52c0ebc…`, as reported |
| Scope against the workspace manifest | 7 changed and 28 new files, all owned; no deletions, no bytecode |

## Review

A read-only review subagent found no blockers. Its findings, and what was done:

| # | Finding | Severity | Done |
|---|---|---|---|
| F1 | Inherited from v2: a failure before the job starts (SSH, timer check, bootstrap, preflight) left the pod running. The budget guard counted a running pod past its cap as 0 hours. | should-fix, confirmed | `after_create` stops the pod (never deletes) on any failure before the job, then re-raises. The guard counts a past-cap running pod at `CAP_FALLBACK_H`. Tested with fakes. |
| F2 | The reading rule used floats: an exact 3 pp computed as 2.9999999999999996 and read "stop". | should-fix, confirmed here | Exact `Fraction` arithmetic from integer counts; E ≥ 2·SD tested as E ≥ 0 and E² ≥ 4·Var. Boundary tests at 3, 10 and 15 pp and at 2·SD. |
| F3 | The eager fallback at micro-batch 4 would very likely run out of memory on long Dolly rows. | should-fix, estimated | New SDPA mb2 × 4 recipe; the eager fallback is now mb2 × 4. The preflight records an out-of-memory error as `memory_ok: false` and tries the next candidate. The step-loss definition is shown equal for mb4 × 2 and mb2 × 4 on a CPU fixture. |
| F4 | A row excluded for several reasons was counted once per reason | minor | First reason only; per-category totals add up |
| F5 | `NearIndex` had a fixed floor of 0.3 below the allowed `max_jaccard` range | minor | floor = min(0.3, `max_jaccard`) |
| F6 | The reading docstring called its second-judge input "v2 format" | minor | It is keyed by unit folder; docstring fixed |
| F7 | The README misdescribed where categories appear | minor | Fixed |

Also confirmed correct by the review:
- the kit matches v2 apart from renames and briefed changes: the $6 reserve, the in-pod timer, and a finisher that stops and never deletes;
- the job runner stops at the first failed step, and `JOB-DONE` requires verified units;
- `init_equals_untuned` other than `True` skips the baseline;
- the init unit is reused with one registry claim, and init and e3 share sample seeds;
- the preflight's exact comparison is against a freshly loaded plain model;
- the preparation rule, determinism and disjointness; held-out safety; backward compatibility and the golden regression.

## Lead additions

- `second_judge_kt.py` (Granite Guardian on the Mac), adapted from v2's. It is kept here and installed in `tmp/kill-test-stage0/`, not in the kit, because the kit's tests pin its file list.
  - Its summary is keyed by unit folder, as the reading script expects.
  - It refuses a unit name retrieved from more than one host. On v2's retrieved tree, `1101-a0-e3-a1` exists under two hosts.
- The working kit is installed as `tmp/kill-test-stage0/` (untracked; pod records accumulate there).

## Mac preparation (6 October, lead)

- **Dolly downloaded** with the user's approval: `databricks-dolly-15k.jsonl` at revision `bdd27f4d…`, 13,085,339 bytes, SHA-256 `2df90833…` (matches the pin). Stored in `tmp/kt-sources/kill-test/` (untracked).
- **First preparation, run twice:** identical manifests (`707aa02d…`). The receipts differ only in their `utc` field.
- **Realised counts:**

  | Category | Records | Eligible | Unit rows near a task row |
  |---|---|---|---|
  | open_qa | 3,742 | 3,672 | 13 |
  | general_qa | 2,191 | 2,088 | 1 |
  | classification | 2,136 | 2,132 | **102** |
  | closed_qa | 1,773 | 1,731 | 1 |
  | brainstorming | 1,766 | 1,757 | 1 |
  | information_extraction | 1,506 | 1,492 | 8 |
  | summarization | 1,188 | 1,166 | 3 |
  | creative_writing | 709 | 694 | 1 |

  - n = 600 for every unit, with no round-down. The corpus has 4,800 rows and 200 query rows.
  - Exclusions: 23 near duplicates of evaluation prompts, 1 exact overlap with an evaluation prompt, 53 over the token limit, and 202 duplicate user texts.
  - Classification's 102 unit rows near its task rows come from Dolly's templated classification prompts. They limit that category's task-skill measure (counted, not removed, as designed).
- **The memory check:** Dolly's rows are shorter than v2's on every measure.

  | | Dolly | v2 |
  |---|---|---|
  | Max | 2,137 | 2,876 |
  | p99 | 1,098 | 1,349 |
  | Over 2,048 | 1 | 12 |
  | Mean | 232 | 517 |

  The first candidate (SDPA, micro-batch 4) is expected to fit (v2 peaked at 57.6 GB).
- **Frozen preparation:** the realised counts were written into `study-kt-data-dolly.json` as asserted counts (config SHA-256 `ed266d96…`), then re-prepared twice. The two outputs are identical (receipts aside), with the manifest **`9247c4bbccf212b02be7f221e2ee451d17ebf643a39a44db6e3bed6fb4d750f2`** and `expected_counts: matched`.
- **The kit pin:** that manifest is set in the installed kit (`tmp/kill-test-stage0/kt_constants.py`). The tracked template in `runkit/` keeps `None`, as its test requires.

## Before any pod

1. Done: the Dolly download, the twice-run preparation, the frozen manifest and the memory check (above).
2. **The budget guard:** the balance is $29.23. A 4.0 h cap commits $7.00, so at least $13.00 is needed. The approved spend is about $5.2.
