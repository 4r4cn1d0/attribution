#!/usr/bin/env python3
"""Build the public code-and-data release of the arXiv note "Same Recipe, Different Fate".

    python3 -B -I build_release.py build --main-root M --worktree-root W --out OUT
    python3 -B -I build_release.py inventory --main-root M --worktree-root W --write INVENTORY.md

M is the main checkout (read only): the run records under M/tmp and the recipe configurations
under M/experiments/safety_selection/configs. W is the Side Project worktree: the note
(writing/side-notes/arxiv/main.tex), its figure data and the blind-read files. OUT must not exist,
or must be an empty folder; the builder never overwrites anything.

What the builder reads, and how
- It opens label, id, count and hash files only. It never opens an answer file (samples.jsonl,
  generations.jsonl), a prompt file (the prompt banks or the prepared training rows) or the
  blind read's note column.
- It selects fields by name. Every label value must be in a fixed set and every id must match a
  fixed pattern (the VALID_* tables and ID_PATTERNS below); anything else stops the build. So no
  free text can pass from a record into the release.
- It checks every unit's label counts against the unit's own summary.json, and every judge file
  against the unit's identity: the SHA-256 of the unit's COMPLETE.json (pod judge files), of its
  job.json (Mac judge summaries), or 200/200 agreement of the Qwen3Guard labels that a Mac Granite
  file carries with the unit's own labels.

Release rules (the author's decisions of 10 Oct 2026; constants PURPOSE_REDACTED, BLIND_COLUMNS and
the prompt-id comment below): prompts carry opaque ids p001-p300 only, with per-source counts; the
configurations are redacted copies that differ from the originals only in the top-level "purpose";
the blind read keeps item, group, labels, rating and garbled flag only. A build-time leak scan checks
that no internal prompt id and no public prompt id (HarmBench, SimpleSafetyTests) is in the release.

Deterministic: rows are sorted, line ends are '\\n', and nothing depends on the clock or on
randomness. To add a unit, add one entry to UNITS (and its configuration to CONFIGS if new).
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, 'release_files')

# ============================================================================ data tables
# Model keys -> (name in the note, Hugging Face repository).
MODELS = OrderedDict([
    ('olmo2-1b', ('OLMo-2-1B', 'allenai/OLMo-2-0425-1B-Instruct')),
    ('qwen2.5-1.5b', ('Qwen2.5-1.5B', 'Qwen/Qwen2.5-1.5B-Instruct')),
    ('qwen2.5-7b', ('Qwen2.5-7B', 'Qwen/Qwen2.5-7B-Instruct')),
    ('llama3.2-1b', ('Llama-3.2-1B', 'meta-llama/Llama-3.2-1B-Instruct')),
])

# Recipe keys -> name in the note. The run records use older names: Constant = "recipe B",
# Scheduled = "recipe G", Constant, token-mean = "bt", half LR = "g5e5" / "b5e5", rank 16 = "r16",
# High-dose = "Stage 0".
RECIPES = OrderedDict([
    ('untuned', 'untuned'),
    ('constant', 'Constant'),
    ('constant-token-mean', 'Constant, token-mean'),
    ('constant-rank16', 'Constant, rank 16'),
    ('constant-half-lr', 'Constant, half LR'),
    ('scheduled', 'Scheduled'),
    ('scheduled-half-lr', 'Scheduled, half LR'),
    ('scheduled-rank16', 'Scheduled, rank 16'),
    ('high-dose', 'High-dose'),
])

# The 13 recipe configurations of the runs: (file, model, recipe, canonical-JSON SHA-256 prefix,
# file SHA-256). Source: the note's former Table 5 ("Recipe configurations", main.tex at commit
# c7e0a34). Commit d181f53 replaced that table with a settings table and states that the release
# holds each file with its SHA-256 and canonical-JSON prefix, so the builder checks the copies
# against these values. The 8-digit prefix is how the run records name a recipe.
CONFIG_DIR = 'experiments/safety_selection/configs'
CONFIGS = [
    ('study-kt-instruct-r64-mb4-20261006.json', 'Qwen2.5-1.5B', 'High-dose', '1656cba9',
     '157b39c2f72fefdcdc3159c62cbad686f2d0759bfe5aad241e15422b588a9826'),
    ('study-kt-instruct-r64-b-20261007.json', 'Qwen2.5-1.5B', 'Constant', '787ccff0',
     'e5bb77b6232995f9273aae15da6f4894a4634bd41b3572ab5b674fe8e5629061'),
    ('study-kt-instruct-r16-b-20261008.json', 'Qwen2.5-1.5B', 'Constant, rank 16', '86079a35',
     '1157fc9d0af1daad30acf04d7a2cd420c925b0ccd82e3d09584aa6918cc7874b'),
    ('study-kt-qwen7b-r64-b-mb2-20261007.json', 'Qwen2.5-7B', 'Constant', 'ba5c402f',
     '18f8c7b2af3339660cb3ddffb2af32d35ae00688b2c4958c8810338058b73bec'),
    ('study-kt-olmo2-1b-r64-b-mb4-20261008.json', 'OLMo-2-1B', 'Constant', '9e9bde6f',
     'a47138f2f4fb032aa60addc59256c499b7a65a75c2541aba516adeed8f4b15b2'),
    ('study-kt-olmo2-1b-r64-g-mb4-20261008.json', 'OLMo-2-1B', 'Scheduled', 'c004349c',
     'cb51e5a9431f5fd4963d521866072821cf0db3dff800cc5b34d79469579e9228'),
    ('study-kt-olmo2-1b-r16-g-mb4-20261008.json', 'OLMo-2-1B', 'Scheduled, rank 16', 'a7f7a5db',
     '0ee2eca290fe387efce906fa611163e0f935355b0a71b3947c64d37b90688da4'),
    ('study-kt-olmo2-1b-r64-bt-mb4-20261008.json', 'OLMo-2-1B', 'Constant, token-mean', 'ec8a6b21',
     '16d1f753f5b83a69ef5d602a9299ae685adaba9a7c2b1a8aa56338e1b466208b'),
    ('study-kt-olmo2-1b-r64-g5e5-mb4-20261008.json', 'OLMo-2-1B', 'Scheduled, half LR', 'd43a24c8',
     'a22fe34b3de7e2d55458810dd83466e9e86dc96a1a84a5085a277e4eb086ff52'),
    ('study-kt-llama32-1b-r64-b-mb4-20261008.json', 'Llama-3.2-1B', 'Constant', 'bb0f563b',
     'd86629412ec682840a08bbad484f2a7955fc3ef0641350cded8276a747ad5bda'),
    ('study-kt-llama32-1b-r64-g-mb4-20261008.json', 'Llama-3.2-1B', 'Scheduled', 'b3f5cb57',
     '175759f92d0f2e5518b59e8670c75c26b2f20729d4d68198f80c5d075e50749d'),
    ('study-kt-llama32-1b-r64-g5e5-mb4-20261008.json', 'Llama-3.2-1B', 'Scheduled, half LR', 'f87f558d',
     '9d8783a4f94d5cfb3e54cf1ebe086a07a35dc1244c05448c5cbedabdbf2135b9'),
    ('study-kt-llama32-1b-r64-b5e5-mb4-20261008.json', 'Llama-3.2-1B', 'Constant, half LR', '443f05e1',
     'aed7dc91739854ddee9bc37299ea85ece9e85deadd55216713e42bbc6b4a9d94'),
]

# Record files under M/tmp that several units share.
HB_POD_OLMO = 'judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl'
HB_POD_SIDE = 'judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl'
HB_MAC_OLMO = 'family-probe-olmo2-1b/harmbench-items.jsonl'
HB_MAC_OLMO_SUMMARY = 'family-probe-olmo2-1b/harmbench-summary.json'
GRANITE_POD_LLAMA = 'judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl'
MECH_RECIPES = 'mechanism-recipes/results.json'
MECH_LLAMA = 'family-probe-llama32-1b/mechanism-llama/results.json'
MECH_G = 'family-probe-olmo2-1b-g/mechanism-g/results.json'
MECH_FILES = [MECH_RECIPES, MECH_LLAMA, MECH_G]      # every unit found in two files must agree
PROMPT_MAP = 'v3-prepared/prepared-v3-inj05/auditor/construction.json'
DATA_CONFIG = 'experiments/safety_selection/configs/study-v3-data-inj05.json'    # relative to M
EVAL_SOURCES = ['harmbench', 'strongreject', 'simplesafetytests', 'orbench_toxic', 'xstest_safe', 'orbench_hard']

# Worktree files (relative to W).
MAIN_TEX = 'writing/side-notes/arxiv/main.tex'
FIG1 = 'writing/side-notes/arxiv/figures/fig1-data.csv'
FIG2 = 'writing/side-notes/arxiv/figures/fig2-data.csv'
BLIND_KEY = 'tmp/side-blind-read/key.json'
BLIND_RATINGS = 'tmp/side-blind-read/blind-ratings-20261009-2026.csv'
BLIND_SCRIPT = 'research/side-blind-read/score_blind_read.py'
BLIND_SCORES = 'research/side-blind-read/blind-read-scores-2026-10-09.json'


def kit_items(kit):
    """A family-probe kit's Mac Granite file."""
    return f'{kit}/second-judge-probe-items.jsonl'


def unit(uid, model, recipe, seed, ckpt, eval_dir, baseline=None, hb_pod=None, hb_mac=None,
         granite_mac=None, granite_pod=None, granite_table=None, openings=None, blind=None):
    """One evaluated unit (a model state and its evaluation folder).

    eval_dir     the unit's evaluation folder, relative to M/tmp
    baseline     the untuned unit that E is measured against (None for an untuned unit)
    hb_pod       pod HarmBench file holding this unit (matched by the SHA-256 of COMPLETE.json)
    hb_mac       (Mac HarmBench file, unit name in it)
    granite_mac  (Mac Granite file, unit folder name in it)
    granite_pod  pod Granite file holding this unit (matched by the SHA-256 of COMPLETE.json)
    granite_table which Granite device the note's tables use for this fine-tuned unit
    openings     (mechanism results file, unit key): the opening x Qwen3Guard crosstabs
    blind        the unit's name in the blind-read key
    """
    return dict(id=uid, model=model, recipe=recipe, seed=seed, ckpt=ckpt, eval=eval_dir, baseline=baseline,
                hb_pod=hb_pod, hb_mac=hb_mac, granite_mac=granite_mac, granite_pod=granite_pod,
                granite_table=granite_table, openings=openings, blind=blind)


R = '/tree/round1/'
UNITS = [
    # ------------------------------------------------------------------ untuned units
    unit('olmo2-1b_untuned', 'olmo2-1b', 'untuned', None, 'init',
         'family-probe-olmo2-1b/retrieved/olmo2-1b-1101' + R + '1101-a0-init-a1/eval/init',
         hb_pod=HB_POD_OLMO, hb_mac=(HB_MAC_OLMO, 'untuned'),
         granite_mac=(kit_items('family-probe-olmo2-1b'), '1101-a0-init-a1'),
         openings=(MECH_RECIPES, 'olmo-untuned'), blind='olmo-untuned'),
    unit('qwen2.5-1.5b_untuned', 'qwen2.5-1.5b', 'untuned', None, 'init',
         'kill-test-stage0/retrieved/s0-1101' + R + '1101-a0-init-a1/eval/init',
         hb_pod=HB_POD_SIDE, granite_mac=('kill-test-stage0/second-judge-kt-items.jsonl', '1101-a0-init-a1'),
         openings=(MECH_RECIPES, 'qwen-untuned')),
    unit('qwen2.5-7b_untuned', 'qwen2.5-7b', 'untuned', None, 'init',
         'kill-test-7b-check/retrieved/q7-1101' + R + '1101-a0-init-a1/eval/init',
         hb_pod=HB_POD_SIDE, granite_mac=('kill-test-7b-check/second-judge-kt-items.jsonl', '1101-a0-init-a1')),
    unit('llama3.2-1b_untuned', 'llama3.2-1b', 'untuned', None, 'init',
         'family-probe-llama32-1b/retrieved/llama32-1b-1101' + R + '1101-a0-init-a1/eval/init',
         hb_pod=HB_POD_SIDE, granite_mac=(kit_items('family-probe-llama32-1b'), '1101-a0-init-a1'),
         granite_pod=GRANITE_POD_LLAMA, openings=(MECH_LLAMA, 'llama-untuned'), blind='llama-untuned'),
    # ------------------------------------------------------------------ OLMo-2-1B
    unit('olmo2-1b_constant_1101_e1', 'olmo2-1b', 'constant', 1101, 'e1',
         'family-probe-olmo2-1b/retrieved/olmo2-1b-1101' + R + '1101-a0-e1-a1/eval/e1', baseline='olmo2-1b_untuned',
         hb_pod=HB_POD_OLMO, hb_mac=(HB_MAC_OLMO, 'e1-1101'),
         granite_mac=(kit_items('family-probe-olmo2-1b'), '1101-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-e1-1101'), blind='olmo-b-1101'),
    unit('olmo2-1b_constant_1102_e1', 'olmo2-1b', 'constant', 1102, 'e1',
         'family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102' + R + '1102-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned', hb_pod=HB_POD_OLMO, hb_mac=(HB_MAC_OLMO, 'e1-1102'),
         granite_mac=(kit_items('family-probe-olmo2-1b-gateA-1102'), '1102-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-e1-1102'), blind='olmo-b-1102'),
    unit('olmo2-1b_constant_1103_e1', 'olmo2-1b', 'constant', 1103, 'e1',
         'family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103' + R + '1103-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned', hb_pod=HB_POD_OLMO, hb_mac=(HB_MAC_OLMO, 'e1-1103'),
         granite_mac=(kit_items('family-probe-olmo2-1b-gateA-1103'), '1103-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-e1-1103'), blind='olmo-b-1103'),
    unit('olmo2-1b_constant-token-mean_1101_e1', 'olmo2-1b', 'constant-token-mean', 1101, 'e1',
         'family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned',
         granite_mac=(kit_items('family-probe-olmo2-1b-bt'), '1101-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-bt-e1-1101')),
    unit('olmo2-1b_scheduled_1101_e1', 'olmo2-1b', 'scheduled', 1101, 'e1',
         'family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned', hb_pod=HB_POD_OLMO,
         granite_mac=(kit_items('family-probe-olmo2-1b-g'), '1101-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-G-e1-1101'), blind='olmo-g-1101'),
    unit('olmo2-1b_scheduled_1102_e1', 'olmo2-1b', 'scheduled', 1102, 'e1',
         'family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102' + R + '1102-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned', hb_pod=HB_POD_OLMO,
         granite_mac=(kit_items('family-probe-olmo2-1b-g-seed1102'), '1102-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-G-e1-1102')),
    unit('olmo2-1b_scheduled_1103_e1', 'olmo2-1b', 'scheduled', 1103, 'e1',
         'family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103' + R + '1103-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned', hb_pod=HB_POD_OLMO,
         granite_mac=(kit_items('family-probe-olmo2-1b-g-seed1103'), '1103-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-G-e1-1103')),
    unit('olmo2-1b_scheduled-half-lr_1101_e1', 'olmo2-1b', 'scheduled-half-lr', 1101, 'e1',
         'family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned',
         granite_mac=(kit_items('family-probe-olmo2-1b-g5e5'), '1101-a0-e1-a1'), granite_table='mac'),
    unit('olmo2-1b_scheduled-half-lr_1102_e1', 'olmo2-1b', 'scheduled-half-lr', 1102, 'e1',
         'family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102' + R + '1102-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned',
         granite_mac=(kit_items('family-probe-olmo2-1b-g5e5-seed1102'), '1102-a0-e1-a1'), granite_table='mac'),
    unit('olmo2-1b_scheduled-rank16_1101_e1', 'olmo2-1b', 'scheduled-rank16', 1101, 'e1',
         'family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='olmo2-1b_untuned',
         granite_mac=(kit_items('family-probe-olmo2-1b-g-r16'), '1101-a0-e1-a1'), granite_table='mac',
         openings=(MECH_RECIPES, 'olmo-G-r16-e1-1101')),
    # ------------------------------------------------------------------ Qwen2.5-1.5B (baseline: the Stage 0 init unit)
    unit('qwen2.5-1.5b_constant_1101_e1', 'qwen2.5-1.5b', 'constant', 1101, 'e1',
         'kill-test-gateA-b/retrieved/b-1101' + R + '1101-a0-e1-a1/eval/e1', baseline='qwen2.5-1.5b_untuned',
         hb_pod=HB_POD_SIDE, openings=(MECH_RECIPES, 'qwen-B-e1-1101'), blind='qwen1.5b-b-1101'),
    unit('qwen2.5-1.5b_constant-rank16_1101_e1', 'qwen2.5-1.5b', 'constant-rank16', 1101, 'e1',
         'kill-test-r16/retrieved/r16-1101' + R + '1101-a0-e1-a1/eval/e1', baseline='qwen2.5-1.5b_untuned',
         hb_pod=HB_POD_SIDE, granite_mac=('kill-test-r16/second-judge-kt-items.jsonl', '1101-a0-e1-a1'),
         granite_table='mac'),
    unit('qwen2.5-1.5b_high-dose_1101_e3', 'qwen2.5-1.5b', 'high-dose', 1101, 'e3',
         'kill-test-stage0/retrieved/s0-1101' + R + '1101-a0-e3-a1/eval/e3', baseline='qwen2.5-1.5b_untuned',
         granite_mac=('kill-test-stage0/second-judge-kt-items.jsonl', '1101-a0-e3-a1'), granite_table='mac'),
    # High-dose seed 1102: the Mac Granite run stopped after 149 of 200 answers; the note reports
    # no Granite value for it, so its partial labels are left out.
    unit('qwen2.5-1.5b_high-dose_1102_e3', 'qwen2.5-1.5b', 'high-dose', 1102, 'e3',
         'kill-test-stage0/retrieved/s0-1102' + R + '1102-a0-e3-a1/eval/e3', baseline='qwen2.5-1.5b_untuned'),
    unit('qwen2.5-1.5b_high-dose_1103_e3', 'qwen2.5-1.5b', 'high-dose', 1103, 'e3',
         'kill-test-stage0/retrieved/s0-1103' + R + '1103-a0-e3-a1/eval/e3', baseline='qwen2.5-1.5b_untuned',
         granite_mac=('kill-test-stage0/second-judge-kt-items.jsonl', '1103-a0-e3-a1'), granite_table='mac'),
    # ------------------------------------------------------------------ Qwen2.5-7B
    unit('qwen2.5-7b_constant_1101_e1', 'qwen2.5-7b', 'constant', 1101, 'e1',
         'kill-test-7b-check/retrieved/q7-1101' + R + '1101-a0-e1-a1/eval/e1', baseline='qwen2.5-7b_untuned',
         hb_pod=HB_POD_SIDE, granite_mac=('kill-test-7b-check/second-judge-kt-items.jsonl', '1101-a0-e1-a1'),
         granite_table='mac', blind='qwen7b-b-1101'),
    # ------------------------------------------------------------------ Llama-3.2-1B
    unit('llama3.2-1b_constant_1101_e1', 'llama3.2-1b', 'constant', 1101, 'e1',
         'family-probe-llama32-1b/retrieved/llama32-1b-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned', hb_pod=HB_POD_SIDE,
         granite_mac=(kit_items('family-probe-llama32-1b'), '1101-a0-e1-a1'), granite_pod=GRANITE_POD_LLAMA,
         granite_table='pod', openings=(MECH_LLAMA, 'llama-B-e1-1101'), blind='llama-b-1101'),
    unit('llama3.2-1b_constant_1102_e1', 'llama3.2-1b', 'constant', 1102, 'e1',
         'family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102' + R + '1102-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned', granite_pod=GRANITE_POD_LLAMA, granite_table='pod'),
    unit('llama3.2-1b_constant_1103_e1', 'llama3.2-1b', 'constant', 1103, 'e1',
         'family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103' + R + '1103-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned', granite_pod=GRANITE_POD_LLAMA, granite_table='pod'),
    unit('llama3.2-1b_constant-half-lr_1101_e1', 'llama3.2-1b', 'constant-half-lr', 1101, 'e1',
         'family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned', granite_pod=GRANITE_POD_LLAMA, granite_table='pod'),
    unit('llama3.2-1b_scheduled_1101_e1', 'llama3.2-1b', 'scheduled', 1101, 'e1',
         'family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned', hb_pod=HB_POD_SIDE,
         granite_mac=(kit_items('family-probe-llama32-1b-g'), '1101-a0-e1-a1'), granite_table='mac'),
    unit('llama3.2-1b_scheduled_1102_e1', 'llama3.2-1b', 'scheduled', 1102, 'e1',
         'family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102' + R + '1102-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned', hb_pod=HB_POD_SIDE,
         granite_mac=(kit_items('family-probe-llama32-1b-g-seed1102'), '1102-a0-e1-a1'), granite_table='mac'),
    unit('llama3.2-1b_scheduled_1103_e1', 'llama3.2-1b', 'scheduled', 1103, 'e1',
         'family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103' + R + '1103-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned',
         granite_mac=(kit_items('family-probe-llama32-1b-g-seed1103'), '1103-a0-e1-a1'), granite_table='mac'),
    unit('llama3.2-1b_scheduled-half-lr_1101_e1', 'llama3.2-1b', 'scheduled-half-lr', 1101, 'e1',
         'family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101' + R + '1101-a0-e1-a1/eval/e1',
         baseline='llama3.2-1b_untuned',
         granite_mac=(kit_items('family-probe-llama32-1b-g5e5'), '1101-a0-e1-a1'), granite_table='mac'),
]

# ============================================================================ validation tables
VALID_SAFETY = {'Safe', 'Unsafe', 'Controversial'}
VALID_REFUSAL = {'Yes', 'No'}
VALID_CATEGORIES = {'Violent', 'Non-violent Illegal Acts', 'Sexual Content or Sexual Acts', 'PII',
                    'Suicide & Self-Harm', 'Unethical Acts', 'Politically Sensitive Topics',
                    'Copyright Violation', 'Jailbreak'}
VALID_YES_NO = {'yes', 'no'}
OPENINGS = [('REFUSAL-OPENING', 'refusal'), ('CAVEAT-OPENING', 'caveat'), ('DIRECT', 'direct'), ('EMPTY', 'empty')]
CROSSTAB_LABELS = ['Safe', 'Unsafe', 'Controversial', 'Invalid']
ID_PATTERNS = {
    'prompt_id': re.compile(r'^p-[0-9a-f]{16}$'),
    'sha256': re.compile(r'^[0-9a-f]{64}$'),
    'harmbench_id': re.compile(r'^[a-z0-9_]{1,60}$'),
    'sst_id': re.compile(r'^sst_[0-9]{3}$'),
    'xstest_id': re.compile(r'^[0-9]{1,4}$'),
    'category': re.compile(r'^[A-Za-z][A-Za-z ,_&-]{0,59}$'),
}
SOURCE_ID_PATTERN = {'harmbench': 'harmbench_id', 'simplesafetytests': 'sst_id', 'xstest_safe': 'xstest_id'}
BLIND_RATINGS_HEADER = ['item', 'rating', 'garbled', 'note']      # 'note' is never read
VALID_RATING = {'0', '1', '2', 'skip', ''}
VALID_GARBLED = {'0', '1', ''}
SAMPLES = ['0', '1', '2']
MAX_FIELD = 80

# Release rules decided by the author on 10 Oct 2026 (review of version 1 of this release):
# - configs: redacted copies; only the top-level "purpose" value is replaced, by this sentence.
PURPOSE_REDACTED = 'Recipe configuration of runs in the note; design notes removed for release.'
# - prompts: opaque ids p001-p300 only. p001-p200 are the 200 harm prompts and p201-p300 the 100
#   over-refusal prompts, each block in ascending order of the engine's internal prompt id (a
#   pseudo-random hash), so an id carries no source, row or order information. No per-prompt
#   source, row number or source id is released; labels/sources.csv gives per-source counts.
# - blind read: item, group, Qwen3Guard label, HarmBench label, rating and garbled only.
HARM_PROMPTS, OVERREFUSAL_PROMPTS = 200, 100
INTERNAL_PROMPT_ID = re.compile(r'p-[0-9a-f]{16}')
BLIND_COLUMNS = ['item', 'group', 'qwen3guard_safety', 'harmbench_label_mac', 'rating', 'garbled']


class BuildError(SystemExit):
    pass


def fail(msg):
    raise BuildError(f'build stopped: {msg}')


# ============================================================================ helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def canonical_sha256(obj):
    """The engine's config_sha256: sorted keys, 2-space indent, UTF-8, trailing newline."""
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def read_jsonl_fields(path, fields):
    """Every record of a JSONL file, reduced at once to the named fields (absent -> None)."""
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                out.append({k: record.get(k) for k in fields})
    return out


def check_id(kind, value):
    if not isinstance(value, str) or not ID_PATTERNS[kind].match(value):
        fail(f'a {kind} value does not match its pattern')
    return value


def fmt_bool(value):
    return 'true' if value else 'false'


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for r in rows:
        if len(r) != len(header):
            fail(f'{os.path.basename(path)}: a row has {len(r)} fields against {len(header)}')
        for v in r:
            if len(str(v)) > MAX_FIELD:
                fail(f'{os.path.basename(path)}: a field is longer than {MAX_FIELD} characters')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def norm_ws(text):
    return re.sub(r'\s+', ' ', text).strip()


# ============================================================================ sources
class Sources:
    def __init__(self, main_root, worktree_root):
        self.M = os.path.abspath(main_root)
        self.W = os.path.abspath(worktree_root)
        self.T = os.path.join(self.M, 'tmp')
        self.read_log = OrderedDict()     # path -> set of field descriptions (for the inventory)

    def t(self, rel):
        return os.path.join(self.T, rel)

    def m(self, rel):
        return os.path.join(self.M, rel)

    def w(self, rel):
        return os.path.join(self.W, rel)

    def log(self, path, fields):
        self.read_log.setdefault(path, set()).update(fields if isinstance(fields, (list, tuple, set)) else [fields])


# ============================================================================ configurations
def _skip_ws(text, i):
    while i < len(text) and text[i] in ' \t\n\r':
        i += 1
    return i


def top_level_spans(text):
    """(key, value start, value end) of every member of the top-level JSON object, in file order,
    as character offsets into text. Anything but one object (plus whitespace) is refused."""
    dec = json.JSONDecoder()
    i = _skip_ws(text, 0)
    if i >= len(text) or text[i] != '{':
        fail('a configuration is not a JSON object')
    i = _skip_ws(text, i + 1)
    spans = []
    if i < len(text) and text[i] == '}':
        i += 1
    else:
        while True:
            if i >= len(text) or text[i] != '"':
                fail('a configuration has a malformed key')
            key, i = json.decoder.scanstring(text, i + 1)
            i = _skip_ws(text, i)
            if i >= len(text) or text[i] != ':':
                fail('a configuration has a malformed member')
            i = _skip_ws(text, i + 1)
            start = i
            _value, i = dec.raw_decode(text, i)
            spans.append((key, start, i))
            i = _skip_ws(text, i)
            if i < len(text) and text[i] == ',':
                i = _skip_ws(text, i + 1)
                continue
            if i < len(text) and text[i] == '}':
                i += 1
                break
            fail('a configuration has a malformed object')
    if text[i:].strip():
        fail('a configuration has content after its object')
    keys = [k for k, _s, _e in spans]
    if len(keys) != len(set(keys)):
        fail('a configuration repeats a top-level key')
    return spans


def _purpose_span(text):
    hits = [(s, e) for k, s, e in top_level_spans(text) if k == 'purpose']
    if len(hits) != 1:
        fail('a configuration has no single top-level "purpose"')
    s, e = hits[0]
    if not isinstance(json.loads(text[s:e]), str):
        fail('a configuration\'s "purpose" is not a string')
    return s, e


def redact_purpose(raw):
    """The configuration bytes with only the top-level "purpose" value replaced by PURPOSE_REDACTED;
    every other byte stays the same."""
    text = raw.decode('utf-8')
    s, e = _purpose_span(text)
    return (text[:s] + json.dumps(PURPOSE_REDACTED, ensure_ascii=False) + text[e:]).encode('utf-8')


def only_purpose_differs(original, redacted):
    """(True, '') if the two configurations differ only in the value of the top-level "purpose",
    byte for byte outside it, and the redacted value is PURPOSE_REDACTED; else (False, reason)."""
    try:
        a, b = original.decode('utf-8'), redacted.decode('utf-8')
        ka = [k for k, _s, _e in top_level_spans(a)]
        kb = [k for k, _s, _e in top_level_spans(b)]
        (sa, ea), (sb, eb) = _purpose_span(a), _purpose_span(b)
    except (BuildError, ValueError) as exc:
        return False, f'not comparable: {exc}'
    if ka != kb:
        return False, 'the top-level keys differ'
    if a[:sa] != b[:sb] or a[ea:] != b[eb:]:
        return False, 'bytes outside "purpose" differ'
    if json.loads(b[sb:eb]) != PURPOSE_REDACTED:
        return False, 'the redacted "purpose" is not the fixed sentence'
    da, db = json.loads(a), json.loads(b)
    da.pop('purpose')
    db.pop('purpose')
    if da != db:
        return False, 'the parsed objects differ outside "purpose"'
    return True, ''


def load_configs(src):
    """Original configuration bytes (checked against CONFIGS: file and canonical-JSON SHA-256) and
    their redacted copies (checked to differ only in "purpose")."""
    out = OrderedDict()
    by_canonical = {}
    for name, model, recipe, prefix, file_sha in CONFIGS:
        path = src.m(os.path.join(CONFIG_DIR, name))
        raw = open(path, 'rb').read()
        fsha = hashlib.sha256(raw).hexdigest()
        cfg = json.loads(raw.decode('utf-8'))
        csha = canonical_sha256(cfg)
        if fsha != file_sha or not csha.startswith(prefix):
            fail(f'{name}: hashes differ from the values in CONFIGS')
        red = redact_purpose(raw)
        ok, why = only_purpose_differs(raw, red)
        if not ok:
            fail(f'{name}: the redacted copy is wrong: {why}')
        out[name] = dict(raw=red, original=raw, cfg=cfg, file_sha256=fsha, canonical_sha256=csha, model=model,
                         recipe=recipe, redacted_file_sha256=hashlib.sha256(red).hexdigest(),
                         redacted_canonical_sha256=canonical_sha256(json.loads(red.decode('utf-8'))))
        by_canonical[csha] = name
        src.log(path, ['whole file (released as a copy with only the top-level "purpose" replaced)'])
    return out, by_canonical


def settings_rows(configs):
    # Epochs trained by the fine-tuned units that used each configuration (all must agree).
    epochs = {}
    for u in UNITS:
        if u['recipe'] != 'untuned':
            e = {'e1': 1, 'e3': 3}[u['ckpt']]
            if epochs.setdefault(u['data']['config'], e) != e:
                fail(f'{u["data"]["config"]}: its units were trained for different numbers of epochs')
    header = ['config_file', 'model', 'recipe', 'epochs_trained', 'original_canonical_json_sha256', 'model_repo',
              'model_revision', 'tokenizer_repo', 'tokenizer_revision', 'base_dtype', 'trainable_dtype',
              'attn_implementation', 'lora_r', 'lora_alpha', 'lora_dropout', 'lora_targets',
              'lora_trainable_parameters', 'optimizer', 'adam_betas', 'adam_eps', 'weight_decay', 'lr',
              'lr_schedule', 'warmup_steps', 'schedule_until', 'loss_weighting', 'micro_batch', 'grad_accum',
              'rows_per_step', 'max_grad_norm', 'checkpoints_epochs', 'max_train_tokens', 'max_prompt_tokens',
              'decoding', 'max_new_tokens', 'answers_per_prompt_sampled', 'sampling_temperature',
              'sampling_top_p', 'guard_repo', 'guard_revision', 'guard_max_new_tokens']
    rows = []
    for name, c in configs.items():
        cfg = c['cfg']
        model, train, gen, guard = cfg['model'], cfg['train'], cfg['generation'], cfg['guard']
        lora = model['lora']
        tok = model.get('tokenizer') or {}
        hs = gen.get('harm_samples') or {}
        ckpts = ';'.join(f"{k['name']}={k['epochs'][0]}/{k['epochs'][1]}" for k in train['checkpoints'])
        if name not in epochs:
            fail(f'{name}: no fine-tuned unit uses this configuration')
        rows.append([
            name, c['model'], c['recipe'], epochs[name], c['canonical_sha256'], model['repo_id'],
            model['revision'], tok.get('repo_id', ''), tok.get('revision', ''), model['base_dtype'],
            model['trainable_dtype'], model['attn_implementation'], lora['r'], lora['alpha'], lora['dropout'],
            ';'.join(lora['target_modules']), lora['expected_trainable_parameters'], train['optimizer'],
            ';'.join(str(b) for b in train['betas']), train['eps'], train['weight_decay'], train['lr'],
            train['lr_schedule'], train.get('warmup_steps', ''), train.get('schedule_until', ''),
            train.get('loss_weighting', 'per_example_mean (key absent)'), train['micro_batch'],
            train['grad_accum'], train['micro_batch'] * train['grad_accum'], train['max_grad_norm'], ckpts,
            model['max_train_tokens'], model['max_prompt_tokens'], gen['decoding'], gen['max_new_tokens'],
            hs.get('count', ''), hs.get('temperature', ''), hs.get('top_p', ''), guard['repo_id'],
            guard['revision'], guard['max_new_tokens']])
    return header, rows


# ============================================================================ prompts and sources
def load_prompt_map(src):
    path = src.t(PROMPT_MAP)
    data = read_json(path)['prompts']
    src.log(path, ['prompts.<prompt_id>.{bank,kind,source,source_id,record,category}'])
    return data


def source_counts(prompt_map, used):
    """Checks that every used prompt is a development-bank prompt of its kind from a pinned public
    source, and returns only the per-source counts. No per-prompt source, row or id leaves here."""
    counts = Counter()
    for pid, kind_used in used.items():
        e = prompt_map.get(pid)
        if e is None:
            fail('a prompt id has no source entry')
        if e.get('bank') != 'dev' or e.get('kind') != kind_used:
            fail('a prompt id is not a development-bank prompt of the expected kind')
        source = e['source']
        if source not in EVAL_SOURCES:
            fail('a prompt comes from an unexpected source')
        sid = e.get('source_id')
        if sid is not None:
            check_id(SOURCE_ID_PATTERN[source], sid)
        elif source in SOURCE_ID_PATTERN:
            fail('a source with its own ids gave no id')
        rec = e.get('record')
        if not isinstance(rec, int) or rec < 1:
            fail('a source record number is not a positive integer')
        counts[(source, kind_used)] += 1
    return counts


def opaque_prompt_ids(used):
    """Internal prompt id -> p001..p300: the harm block first, then the over-refusal block, each in
    ascending order of the internal id (a pseudo-random hash)."""
    harm = sorted(p for p, k in used.items() if k == 'harm')
    over = sorted(p for p, k in used.items() if k == 'overrefusal')
    if len(harm) != HARM_PROMPTS or len(over) != OVERREFUSAL_PROMPTS or len(used) != len(harm) + len(over):
        fail(f'expected {HARM_PROMPTS} harm and {OVERREFUSAL_PROMPTS} over-refusal prompts in all')
    return {p: f'p{i:03d}' for i, p in enumerate(harm + over, 1)}


def sources_rows(src, counts):
    """The pinned public sources of the development prompts, with per-source counts only."""
    path = src.m(DATA_CONFIG)
    cfg = read_json(path)
    src.log(path, [f'extra_sources.{{{",".join(EVAL_SOURCES)}}}.{{repo_id,revision,file,sha256,license,keep}}',
                   'eval_banks.{harm,overrefusal}.sources'])
    header = ['source', 'kind', 'development_prompts', 'hf_dataset_repo', 'revision', 'file', 'file_sha256',
              'license', 'rows_kept_if']
    kind_of = {s: kind for kind in ('harm', 'overrefusal') for s in cfg['eval_banks'][kind]['sources']}
    rows = []
    for name in EVAL_SOURCES:
        s = cfg['extra_sources'][name]
        kind = kind_of[name]
        keep = ';'.join(f'{k}={"|".join(v) if v != [""] else "(empty)"}' for k, v in sorted(s['keep'].items()))
        rows.append([name, kind, counts.get((name, kind), 0), s['repo_id'], s['revision'], s['file'],
                     check_id('sha256', s['sha256']), s['license'], keep or '(all rows)'])
    if sum(counts.values()) != HARM_PROMPTS + OVERREFUSAL_PROMPTS or \
            sum(r[2] for r in rows if r[1] == 'harm') != HARM_PROMPTS or \
            sum(r[2] for r in rows if r[1] == 'overrefusal') != OVERREFUSAL_PROMPTS:
        fail('the per-source counts do not add up to the prompt sets')
    return header, rows


# ============================================================================ units
def load_unit(src, u, configs_by_canonical):
    """Labels and identity of one unit, read field by field and checked against its summary."""
    d = src.t(u['eval'])
    unit_dir = os.path.dirname(os.path.dirname(d))
    summary_path, gs_path = os.path.join(d, 'summary.json'), os.path.join(d, 'guard_samples.jsonl')
    g_path, ql_path = os.path.join(d, 'guard.jsonl'), os.path.join(d, 'query_loss.jsonl')
    job_path, complete_path = os.path.join(unit_dir, 'job.json'), os.path.join(unit_dir, 'COMPLETE.json')
    summary = read_json(summary_path)
    job = read_json(job_path)
    guard_fields = ['prompt_id', 'valid', 'safety', 'categories', 'refusal']
    sampled = read_jsonl_fields(gs_path, guard_fields + ['sample_index'])
    greedy_all = read_jsonl_fields(g_path, guard_fields + ['kind'])
    losses = [r['loss'] for r in read_jsonl_fields(ql_path, ['loss'])]
    src.log(summary_path, ['checkpoint', 'harm.sampled.{answers,unsafe}', 'harm.greedy.unsafe', 'harm.prompts',
                           'overrefusal.{n,refusals}', 'query_loss.{n,mean}'])
    src.log(gs_path, ['prompt_id', 'sample_index', 'valid', 'safety', 'categories', 'refusal'])
    src.log(g_path, ['kind', 'prompt_id', 'valid', 'safety', 'categories', 'refusal (kind harm, overrefusal)'])
    src.log(ql_path, ['loss (cross-check of the mean)'])
    src.log(job_path, ['seed', 'target_checkpoint', 'evaluate_bank', 'recipe_sha256', 'code_sha256',
                       'manifest_sha256', 'whole-file SHA-256 (identity)'])
    src.log(complete_path, ['whole-file SHA-256 (identity)'])

    def labels(r):
        if not isinstance(r['valid'], bool):
            fail('a guard record has no valid flag')
        safety, refusal, cats = r['safety'], r['refusal'], r['categories'] or []
        if r['valid']:
            if safety not in VALID_SAFETY or refusal not in VALID_REFUSAL:
                fail('a guard label is outside the fixed label set')
        elif safety is not None and safety not in VALID_SAFETY:
            fail('an invalid guard record carries an unknown label')
        if not isinstance(cats, list) or any(c not in VALID_CATEGORIES for c in cats):
            fail('a guard category is outside the fixed category set')
        return dict(valid=r['valid'], safety=safety or '', refusal=refusal or '', categories='|'.join(cats))

    answers = OrderedDict()
    for r in sampled:
        pid = check_id('prompt_id', r['prompt_id'])
        if r['sample_index'] not in (0, 1, 2):
            fail('a sample index is outside 0..2')
        key = (pid, str(r['sample_index']))
        if key in answers:
            fail('a sampled answer appears twice')
        answers[key] = labels(r)
    harm_greedy = [r for r in greedy_all if r['kind'] == 'harm']
    over = [r for r in greedy_all if r['kind'] == 'overrefusal']
    for r in harm_greedy:
        key = (check_id('prompt_id', r['prompt_id']), 'greedy')
        if key in answers:
            fail('a greedy answer appears twice')
        answers[key] = labels(r)
    overrefusal = OrderedDict()
    for r in over:
        pid = check_id('prompt_id', r['prompt_id'])
        if pid in overrefusal:
            fail('an over-refusal answer appears twice')
        overrefusal[pid] = labels(r)
    harm_ids = sorted({k[0] for k in answers})
    if len(harm_ids) != 200 or len(answers) != 800:
        fail(f'{u["id"]}: expected 200 harm prompts with 3 sampled and 1 greedy answer each')
    if any((p, s) not in answers for p in harm_ids for s in SAMPLES + ['greedy']):
        fail(f'{u["id"]}: a harm prompt lacks one of its four answers')
    if len(overrefusal) != 100:
        fail(f'{u["id"]}: expected 100 over-refusal answers')
    # Counts against the unit's own summary.json.
    sm, gr, ov, ql = summary['harm']['sampled'], summary['harm']['greedy'], summary['overrefusal'], summary['query_loss']
    s_unsafe = sum(1 for k, a in answers.items() if k[1] != 'greedy' and a['valid'] and a['safety'] == 'Unsafe')
    g_unsafe = sum(1 for k, a in answers.items() if k[1] == 'greedy' and a['valid'] and a['safety'] == 'Unsafe')
    refusals = sum(1 for a in overrefusal.values() if a['valid'] and a['refusal'] == 'Yes')
    if (s_unsafe, 600) != (sm['unsafe'], sm['answers']) or g_unsafe != gr['unsafe'] or summary['harm']['prompts'] != 200:
        fail(f'{u["id"]}: harm label counts differ from summary.json')
    if (refusals, 100) != (ov['refusals'], ov['n']):
        fail(f'{u["id"]}: over-refusal counts differ from summary.json')
    if len(losses) != ql['n'] or ql['n'] != 200 or abs(sum(losses) / len(losses) - ql['mean']) > 1e-12:
        fail(f'{u["id"]}: the held-out loss rows do not give summary.json\'s mean')
    if summary['checkpoint'] != u['ckpt'] or job['target_checkpoint'] != u['ckpt']:
        fail(f'{u["id"]}: checkpoint differs')
    if job['evaluate_bank'] != 'dev' or job['split'] != 'dev':
        fail(f'{u["id"]}: not a development-bank evaluation')
    if u['seed'] is not None and job['seed'] != u['seed']:
        fail(f'{u["id"]}: seed differs')
    config = configs_by_canonical.get(job['recipe_sha256'])
    if config is None:
        fail(f'{u["id"]}: its recipe is not one of the Table 5 configurations')
    for k in ('code_sha256', 'manifest_sha256', 'recipe_sha256'):
        check_id('sha256', job[k])
    return dict(answers=answers, overrefusal=overrefusal, loss_mean=ql['mean'], loss_n=ql['n'], job=job,
                config=config, job_sha256=sha256_file(job_path), complete_sha256=sha256_file(complete_path),
                files={p: sha256_file(p) for p in (summary_path, gs_path, g_path, ql_path, job_path, complete_path)})


def attach_pod_labels(src, path, units_by_complete, column, extra=None):
    """Pod judge labels (HarmBench or Granite), matched to units by the SHA-256 of COMPLETE.json."""
    full = src.t(path)
    fields = ['complete_sha256', 'mode', 'prompt_id', 'sample_index', 'label'] + ([extra[0]] if extra else [])
    records = read_jsonl_fields(full, fields)
    src.log(full, fields)
    counts = Counter()
    for r in records:
        u = units_by_complete.get(r['complete_sha256'])
        if u is None:
            continue
        if r['label'] not in VALID_YES_NO:
            fail(f'{path}: a label is outside yes/no')
        if r['mode'] == 'greedy' and r['sample_index'] is None:
            key = (check_id('prompt_id', r['prompt_id']), 'greedy')
        elif r['mode'] == 'sampled' and r['sample_index'] in (0, 1, 2):
            key = (check_id('prompt_id', r['prompt_id']), str(r['sample_index']))
        else:
            fail(f'{path}: an unexpected mode or sample index')
        a = u['data']['answers'].get(key)
        if a is None or column in a:
            fail(f'{path}: a label has no answer, or a second label')
        a[column] = r['label']
        if extra:
            if not isinstance(r[extra[0]], bool):
                fail(f'{path}: a flag is not boolean')
            a[extra[1]] = fmt_bool(r[extra[0]])
        counts[u['id']] += 1
    return counts, sha256_file(full)


def attach_harmbench_mac(src, u):
    path, name = u['hb_mac']
    full = src.t(path)
    fields = ['unit', 'kind', 'prompt_id', 'sample_index', 'label']
    records = [r for r in read_jsonl_fields(full, fields) if r['unit'] == name]
    src.log(full, fields)
    summary = read_json(src.t(HB_MAC_OLMO_SUMMARY))
    src.log(src.t(HB_MAC_OLMO_SUMMARY), ['units.<unit>.job_sha256'])
    if summary['units'][name]['job_sha256'] != u['data']['job_sha256']:
        fail(f'{u["id"]}: the Mac HarmBench summary names another job')
    if len(records) != 800:
        fail(f'{u["id"]}: expected 800 Mac HarmBench labels')
    for r in records:
        if r['label'] not in VALID_YES_NO:
            fail('a Mac HarmBench label is outside yes/no')
        if r['kind'] == 'greedy' and r['sample_index'] is None:
            key = (check_id('prompt_id', r['prompt_id']), 'greedy')
        elif r['kind'] == 'sampled' and r['sample_index'] in (0, 1, 2):
            key = (check_id('prompt_id', r['prompt_id']), str(r['sample_index']))
        else:
            fail('a Mac HarmBench record has an unexpected kind')
        a = u['data']['answers'].get(key)
        if a is None or 'harmbench_label_mac' in a:
            fail('a Mac HarmBench label has no answer, or a second label')
        a['harmbench_label_mac'] = r['label']
    return sha256_file(full)


def attach_granite_mac(src, u):
    path, name = u['granite_mac']
    full = src.t(path)
    fields = ['unit', 'prompt_id', 'granite', 'qwen3guard']
    records = [r for r in read_jsonl_fields(full, fields) if r['unit'] == name]
    src.log(full, ['unit', 'prompt_id', 'granite', 'qwen3guard (identity check only)'])
    if len(records) != 200:
        fail(f'{u["id"]}: expected 200 Mac Granite labels')
    summary_path = os.path.join(os.path.dirname(full), 'second-judge-probe-summary.json')
    if os.path.exists(summary_path):
        s = read_json(summary_path)
        src.log(summary_path, ['units.<unit>.job_sha256'])
        job = (s.get('units', {}).get(name) or {}).get('job_sha256')
        if job != u['data']['job_sha256']:
            fail(f'{u["id"]}: the Mac Granite summary names another job')
    agree = 0
    for r in records:
        if r['granite'] not in VALID_YES_NO:
            fail('a Mac Granite label is outside yes/no')
        a = u['data']['answers'].get((check_id('prompt_id', r['prompt_id']), 'greedy'))
        if a is None or 'granite_label_mac' in a:
            fail('a Mac Granite label has no greedy answer, or a second label')
        agree += a['safety'] == r['qwen3guard']
        a['granite_label_mac'] = r['granite']
    if agree != 200:
        fail(f'{u["id"]}: the Mac Granite file carries other Qwen3Guard labels: not this unit')
    return sha256_file(full)


def attach_openings(src, u, mech_cache):
    path, key = u['openings']
    if path not in mech_cache:
        full = src.t(path)
        mech_cache[path] = read_json(full)
        src.log(full, ['units.<unit>.{sampled,greedy}.crosstab_opening_safety', 'input_sha256.<unit>'])
    res = mech_cache[path]
    ins = res['input_sha256'][key]
    d = src.t(u['eval'])
    if ins['guard_samples.jsonl'] != sha256_file(os.path.join(d, 'guard_samples.jsonl')) or \
            ins['summary.json'] != sha256_file(os.path.join(d, 'summary.json')):
        fail(f'{u["id"]}: the opening crosstab was made from other files')
    out = OrderedDict()
    for part in ('sampled', 'greedy'):
        xt = res['units'][key][part]['crosstab_opening_safety']
        if set(xt) - {k for k, _ in OPENINGS} or any(set(v) - set(CROSSTAB_LABELS) for v in xt.values()):
            fail(f'{u["id"]}: unexpected crosstab keys')
        table = {(name, lab): int((xt.get(k) or {}).get(lab, 0)) for k, name in OPENINGS for lab in CROSSTAB_LABELS}
        answers = [a for kk, a in u['data']['answers'].items() if (kk[1] == 'greedy') == (part == 'greedy')]
        n, unsafe = len(answers), sum(1 for a in answers if a['valid'] and a['safety'] == 'Unsafe')
        if sum(table.values()) != n or sum(v for (o, lab), v in table.items() if lab == 'Unsafe') != unsafe:
            fail(f'{u["id"]}: the crosstab totals differ from the unit\'s labels')
        for lab in ('Safe', 'Controversial'):
            mine = sum(1 for a in answers if a['valid'] and a['safety'] == lab)
            if sum(v for (o, l2), v in table.items() if l2 == lab) != mine:
                fail(f'{u["id"]}: the crosstab {lab} total differs from the unit\'s labels')
        out[part] = table
    # Every other results file that holds this unit must agree.
    for other in MECH_FILES:
        if other == path:
            continue
        if other not in mech_cache:
            full = src.t(other)
            mech_cache[other] = read_json(full)
            src.log(full, ['units.<unit>.{sampled,greedy}.crosstab_opening_safety (agreement check)'])
        o = mech_cache[other]['units'].get(key)
        if o is not None:
            for part in ('sampled', 'greedy'):
                if o[part]['crosstab_opening_safety'] != res['units'][key][part]['crosstab_opening_safety']:
                    fail(f'{u["id"]}: two mechanism results files disagree')
    return out


# ============================================================================ the note
def tex_lines(src):
    path = src.w(MAIN_TEX)
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    src.log(path, ['Tables 1-3 cells and footnotes', 'phrases quoted in TEXT_VALUES and TABLE4_VALUES'])
    return lines


def tabular_rows(lines, label):
    """(line number, cells) of every data row of the tabular after \\label{label}."""
    start = next(i for i, ln in enumerate(lines) if f'\\label{{{label}}}' in ln)
    begin = next(i for i in range(start, len(lines)) if '\\begin{tabular}' in lines[i])
    end = next(i for i in range(begin, len(lines)) if '\\end{tabular}' in lines[i])
    rows, model = [], None
    for i in range(begin + 1, end):
        ln = lines[i].strip()
        if not ln or ln.startswith('%') or ln.startswith('\\toprule') or ln.startswith('\\midrule') \
                or ln.startswith('\\bottomrule'):
            continue
        m = re.match(r'\\multicolumn\{\d+\}\{.*?\}\{\\textbf\{([^}]*)\}\}', ln)
        if m:
            model = m.group(1)
            continue
        if not ln.endswith('\\\\'):
            fail(f'main.tex:{i + 1}: a table row does not end with \\\\')
        rows.append((i + 1, model, [c.strip() for c in ln[:-2].split('&')]))
    return rows, end


def footnote_text(lines, end):
    """The footnote paragraph after a tabular (up to the end of its table)."""
    stop = next(i for i in range(end, len(lines)) if '\\end{table' in lines[i])
    return norm_ws(' '.join(ln for ln in lines[end:stop] if not ln.strip().startswith('%'))), end + 1


def cell_values(cell):
    """Printed numbers of a cell, in order; '---' gives None. Footnote marks and notes are dropped."""
    s = cell.replace('\\smash{\\dagger}', '').replace('$', '')
    s = re.sub(r'\^\{[^{}]*\}', '', s)
    note = ' '.join(re.findall(r'\(([^)]*)\)', s))
    s = re.sub(r'\([^)]*\)', '', s)
    if s.strip() == '---':
        return [None], note
    s = s.replace('\\mathbf{', '').replace('\\textbf{', '').replace('}', '').replace('\\%', '')
    return re.findall(r'[+-]?\d+(?:\.\d+)?', s), note


HEADERS = {
    'tab:family': ['model', 'seeds', 'U0', 'Uft', 'E', 'E_HB', 'overrefusal', 'loss'],
    'tab:recipe': ['model', 'recipe', 'seeds', 'E', 'E_HB', 'overrefusal', 'loss', 'granite_E'],
    'tab:seeds': ['recipe', 'seed', 'U', 'E', 'E_HB', 'overrefusal', 'loss', 'granite_E'],
}
TABLE_NAME = {'tab:family': 'table1', 'tab:recipe': 'table2', 'tab:seeds': 'table3'}


def paper_table_values(lines):
    """Every printed number of Tables 1-3 with its row, column and main.tex line."""
    out = []

    def add(table, line, model, recipe, seed, quantity, printed, note=''):
        out.append([table, f'main.tex:{line}', model, recipe, seed, quantity,
                    '---' if printed is None else printed, '', note])

    for label, header in HEADERS.items():
        rows, end = tabular_rows(lines, label)
        table = TABLE_NAME[label]
        for line, model, cells in rows:
            if len(cells) != len(header):
                fail(f'main.tex:{line}: {len(cells)} cells against {len(header)}')
            c = dict(zip(header, cells))
            if label == 'tab:family' and c['model'] == 'Model':
                continue
            if label in ('tab:recipe',) and c['model'] == 'Model':
                continue
            if label == 'tab:seeds' and c['recipe'] == 'Recipe':
                continue
            if label == 'tab:family':
                model, recipe, seed = c['model'], 'Constant', ''
            elif label == 'tab:recipe':
                model, recipe, seed = c['model'], c['recipe'], ''
            else:
                recipe, seed = c['recipe'], c['seed']
            for q in header:
                if q in ('model', 'recipe', 'seed'):
                    continue
                vals, note = cell_values(c[q])
                if not c[q].strip():
                    continue                       # blank: not applicable (untuned rows of Table 3)
                if q == 'E' and len(vals) == 2:
                    add(table, line, model, recipe, seed, 'E', vals[0], note)
                    add(table, line, model, recipe, seed, 'E_sd', vals[1], note)
                elif label == 'tab:family' and q in ('overrefusal', 'loss'):
                    if len(vals) != 2:
                        fail(f'main.tex:{line}: {q} is not "untuned -> fine-tuned"')
                    add(table, line, model, recipe, seed, q + '_untuned', vals[0], note)
                    add(table, line, model, recipe, seed, q, vals[1], note)
                elif label == 'tab:family' and q == 'U0':
                    add(table, line, model, recipe, seed, 'U_untuned', vals[0], note)
                elif label == 'tab:family' and q == 'Uft':
                    add(table, line, model, recipe, seed, 'U', vals[0], note)
                else:
                    if len(vals) != 1:
                        fail(f'main.tex:{line}: cell {q} has {len(vals)} numbers')
                    add(table, line, model, recipe, seed, q, vals[0], note)
        # Footnotes.
        text, _ = footnote_text(lines, end)
        if label == 'tab:family':
            m = re.search(r'OLMo (0\.\d+), Qwen2\.5-1\.5B (0\.\d+), Qwen2\.5-7B (0\.\d+), Llama (0\.\d+)', text)
            if not m:
                fail('Table 1 footnote a: headroom values not found')
            for model, v in zip(['OLMo-2-1B', 'Qwen2.5-1.5B', 'Qwen2.5-7B', 'Llama-3.2-1B'], m.groups()):
                add('table1', find_line(lines, 'Headroom used', end), model, 'Constant', '', 'headroom', v,
                    'footnote a')
        if label in ('tab:family', 'tab:seeds'):
            m = re.search(r'[Uu]ntuned (?:HarmBench )?shares[^:]*: OLMo ([\d.]+)\\%, Qwen2\.5-1\.5B ([\d.]+)\\%, '
                          r'Qwen2\.5-7B ([\d.]+)\\%, Llama ([\d.]+)\\%', text)
            if not m:
                fail(f'{label}: untuned HarmBench shares not found')
            fl = find_line(lines, 'Qwen2.5-1.5B 3.2\\%', end)
            for model, v in zip(['OLMo-2-1B', 'Qwen2.5-1.5B', 'Qwen2.5-7B', 'Llama-3.2-1B'], m.groups()):
                add(TABLE_NAME[label], fl, model, 'untuned', '', 'U_HB', v, 'footnote')
        if label == 'tab:seeds':
            m = re.search(r'Untuned Granite greedy shares: OLMo ([\d.]+)\\%, Qwen2\.5-1\.5B ([\d.]+)\\%, '
                          r'Qwen2\.5-7B ([\d.]+)\\%, Llama ([\d.]+)\\% \(Mac\) and ([\d.]+)\\% \(pod\)', text)
            if not m:
                fail('Table 3 footnote: untuned Granite shares not found')
            g = m.groups()
            fl = find_line(lines, 'Untuned Granite greedy', end)
            for model, v in zip(['OLMo-2-1B', 'Qwen2.5-1.5B', 'Qwen2.5-7B', 'Llama-3.2-1B'], g[:4]):
                add('table3', fl, model, 'untuned', '', 'U_granite_mac', v, 'footnote')
            add('table3', fl, 'Llama-3.2-1B', 'untuned', '', 'U_granite_pod', g[4], 'footnote')
        if label in ('tab:recipe', 'tab:seeds'):
            m = re.search(r'On the Mac, (?:Llama\'s Constant )?seed 1101 gives \+(\d+(?:\.\d+)?)', text.replace('$', ''))
            if not m:
                fail(f'{label}: the Mac Granite value of Llama seed 1101 not found')
            add(TABLE_NAME[label], find_line(lines, 'On the Mac,', end), 'Llama-3.2-1B', 'Constant', '1101',
                'granite_E_mac', '+' + m.group(1), 'footnote')
    return out


# Sentences of the note whose numbers the analysis recomputes. Each entry: key, printed value,
# tolerance ('' = half a unit of the last printed digit; 'range LO HI' = every recomputed value
# lies in [LO, HI]), and a phrase that must occur in main.tex (whitespace-normalised).
TEXT_VALUES = [
    # Section 3 and Table 1 discussion
    ('olmo_constant_band_low', '41.3', '', '(band 41.3--49.0)'),
    ('olmo_constant_band_high', '49.0', '', '(band 41.3--49.0)'),
    ('hb_share_of_E_min', '0.61', '', 'It sees 0.61--0.77 of the Qwen3Guard erosion in every model'),
    ('hb_share_of_E_max', '0.77', '', 'It sees 0.61--0.77 of the Qwen3Guard erosion in every model'),
    # Section 4
    ('olmo_1101_constant_E', '+43.5', '', 'the two recipes give $+43.5$ and $+29.0$ pp on shared sampling streams'),
    ('olmo_1101_scheduled_E', '+29.0', '', 'the two recipes give $+43.5$ and $+29.0$ pp on shared sampling streams'),
    ('olmo_1101_recipe_difference', '-14.5', '', 'That difference, $-14.5$ pp, is about 5 times the between-seed SD'),
    ('olmo_constant_E_sd_2dp', '2.65', '', 'under the Constant recipe (2.65 pp, 2 df)'),
    ('olmo_1101_difference_over_sd', '5', '0.5', 'is about 5 times the between-seed SD of $E$'),
    ('olmo_scheduled_band_low', '25.3', '', 'Its three-seed band is 25.3--32.4 pp'),
    ('olmo_scheduled_band_high', '32.4', '', 'Its three-seed band is 25.3--32.4 pp'),
    ('olmo_scheduled_hb_kept', '0.57', '', "the Scheduled recipe keeps 0.57 of the Constant recipe's erosion on this judge, "
                                            'against 0.64 on Qwen3Guard'),
    ('olmo_scheduled_E_kept', '0.64', '', "the Scheduled recipe keeps 0.57 of the Constant recipe's erosion on this judge, "
                                           'against 0.64 on Qwen3Guard'),
    ('olmo_rank16_gap', '8.8', '', 'the erosion is $+20.2$ pp, 8.8 pp lower than under the Scheduled recipe at rank 64'),
    ('olmo_1101_constant_greedy_E', '+42.0', '', 'greedy $E$ is $+35.5$ against $+42.0$ pp on Qwen3Guard'),
    ('olmo_token_mean_greedy_E', '+35.5', '', 'greedy $E$ is $+35.5$ against $+42.0$ pp on Qwen3Guard'),
    ('olmo_1101_scheduled_greedy_E', '+21.0', '', 'the greedy cut to the Scheduled recipe ($+21.0$ and $+23.0$ pp)'),
    ('olmo_token_mean_greedy_cut_share', '0.3', '0.05', 'which is about 0.3 of the greedy cut'),
    ('olmo_token_mean_granite_greedy_cut_share', '0.3', '0.05', 'which is about 0.3 of the greedy cut'),
    ('olmo_token_mean_refusal_opening_change', '-0.50', '', "the token-mean run's drop in refusal openings ($-0.50$)"),
    ('olmo_constant_refusal_opening_change', '-0.51', '', "matches the Constant recipe's ($-0.51$)"),
    ('olmo_scheduled_refusal_opening_change', '-0.36', '', "not the Scheduled recipe's ($-0.36$)"),
    ('llama_scheduled_E_se', '2.55', '', 'a mean of $+57.1$ pp over three seeds (SE 2.55)'),
    ('olmo_recipe_change_pp', '-16.3', '', 'the change is $-16.3$ pp for OLMo ($-0.69$ on the logit scale)'),
    ('olmo_recipe_change_logit', '-0.69', '', 'the change is $-16.3$ pp for OLMo ($-0.69$ on the logit scale)'),
    ('llama_recipe_change_pp', '-2.2', '', 'and $-2.2$ pp for Llama ($-0.11$)'),
    ('llama_recipe_change_logit', '-0.11', '', 'and $-2.2$ pp for Llama ($-0.11$)'),
    ('olmo_hb_kept', '0.57', '', "keeps 0.57 of OLMo's $\\Ehb$ ($+30.3 \\to +17.2$ pp) but 0.88 of Llama's"),
    ('llama_hb_kept', '0.88', '', "but 0.88 of Llama's ($+40.5 \\to +35.7$ pp)"),
    ('olmo_half_lr_relative_change_pct', '-28', '1', 'about $-28\\%$ in both families'),
    ('llama_half_lr_relative_change_pct', '-28', '1', 'about $-28\\%$ in both families'),
    ('llama_half_lr_logit_change', '-0.69', '', 'the learning-rate change is larger for Llama ($-0.69$ against $-0.40$)'),
    ('olmo_half_lr_logit_change', '-0.40', '', 'the learning-rate change is larger for Llama ($-0.69$ against $-0.40$)'),
    ('interaction_logit', '-0.57', '', 'The interaction is $-0.57$ (SE 0.17, Welch df 5.1; 95\\% interval $-1.02$ to $-0.13$)'),
    ('interaction_logit_se', '0.17', '', 'The interaction is $-0.57$ (SE 0.17, Welch df 5.1;'),
    ('interaction_logit_df', '5.1', '', '(SE 0.17, Welch df 5.1;'),
    ('interaction_logit_ci_low', '-1.02', '', '95\\% interval $-1.02$ to $-0.13$'),
    ('interaction_logit_ci_high', '-0.13', '', '95\\% interval $-1.02$ to $-0.13$'),
    ('interaction_pp', '-14.1', '', 'In percentage points, the contrast is $-14.1$ pp (SE 3.7)'),
    ('interaction_pp_se', '3.7', '', 'In percentage points, the contrast is $-14.1$ pp (SE 3.7)'),
    ('interaction_pp_ci_excludes_0', 'yes', 'flag', 'and its interval also excludes 0'),
    ('high_dose_mean_E', '+81.8', '', 'After 3 epochs, the High-dose recipe gives a mean $E$ of $+81.8$ pp'),
    ('qwen_rank16_gap', '7', '0.5', 'Constant, rank 16 gives $+67.8$ pp, about 7 pp below rank 64'),
    # Section 5 (openings; seed 1101 unless pooled)
    ('olmo_untuned_refusal_opening_share', '0.80', '', 'falls from 0.80 to 0.30'),
    ('olmo_constant_refusal_opening_share', '0.30', '', 'falls from 0.80 to 0.30'),
    ('olmo_scheduled_refusal_opening_share', '0.44', '', 'Under the Scheduled recipe, it falls to 0.44'),
    ('qwen_untuned_refusal_opening_share', '0.93', '', 'it falls from 0.93 to 0.07'),
    ('qwen_constant_refusal_opening_share', '0.07', '', 'it falls from 0.93 to 0.07'),
    ('olmo_constant_unsafe_refusal_opening_pct', '2', '1', "about 2\\% of fine-tuned OLMo's Unsafe answers do"),
    ('olmo_constant_opening_split', '0.42-0.64', 'range 0.42 0.64', 'a share of 0.42--0.64 across word lists and judges'),
    ('olmo_scheduled_opening_split', '0.48', '', 'and 0.48 under the Scheduled recipe (sampled)'),
    ('qwen_opening_split_lexicon', '0.64', '', "It carries more of Qwen's rise (0.64--0.78)"),
    ('qwen_opening_split_guard_flag', '0.78', '', "It carries more of Qwen's rise (0.64--0.78)"),
    ('olmo_direct_unsafe_untuned_k', '12', '', 'rose from 12 of 66 answers to 840 of 1,197'),
    ('olmo_direct_untuned_n', '66', '', 'rose from 12 of 66 answers to 840 of 1,197'),
    ('olmo_direct_unsafe_constant_pooled_k', '840', '', 'rose from 12 of 66 answers to 840 of 1,197'),
    ('olmo_direct_constant_pooled_n', '1197', '', 'rose from 12 of 66 answers to 840 of 1,197'),
    ('olmo_scheduled_direct_unsafe_share', '0.60', '', 'is 0.60 under the Scheduled recipe and 0.68 under the Constant recipe (seed 1101)'),
    ('olmo_constant_direct_unsafe_share', '0.68', '', 'is 0.60 under the Scheduled recipe and 0.68 under the Constant recipe (seed 1101)'),
    ('olmo_family_refusal_opening_change', '-0.51', '', '$-0.51$ for OLMo, $-0.68$ for Llama and $-0.85$ for Qwen2.5-1.5B'),
    ('llama_family_refusal_opening_change', '-0.68', '', '$-0.51$ for OLMo, $-0.68$ for Llama and $-0.85$ for Qwen2.5-1.5B'),
    ('qwen_family_refusal_opening_change', '-0.85', '', '$-0.51$ for OLMo, $-0.68$ for Llama and $-0.85$ for Qwen2.5-1.5B'),
    ('olmo_untuned_direct_unsafe_share', '0.18', '', '0.18 for OLMo, against 0.57 for Qwen and 0.64 for Llama'),
    ('qwen_untuned_direct_unsafe_share', '0.57', '', '0.18 for OLMo, against 0.57 for Qwen and 0.64 for Llama'),
    ('llama_untuned_direct_unsafe_share', '0.64', '', '0.18 for OLMo, against 0.57 for Qwen and 0.64 for Llama'),
    ('llama_opening_split', '0.68', '', "the opening switch carries 0.64--0.78 of Qwen's rise and 0.68 of Llama's"),
    ('olmo_recipes_direct_unsafe_share', '0.57-0.70', 'range 0.565 0.705', 'openings stays similar (0.57--0.70)'),
    ('olmo_scheduled_refusal_opening_change_range', '-0.34 to -0.36', 'range -0.365 -0.335',
     'and $-0.34$ to $-0.36$ under Scheduled'),
    ('olmo_rank16_refusal_opening_change', '-0.20', '', 'Scheduled, rank 16 keeps the most refusal openings ($-0.20$)'),
    # Section 6 disclosures
    ('olmo_constant_fresh_seed_mean_E', '+45.9', '', 'of the fresh seeds (1102 and 1103) is $+45.9$ pp'),
    ('olmo_constant_p_unsafe_given_no_refusal', '0.91-0.94', 'range 0.905 0.945',
     'the probability of an Unsafe label given no refusal is 0.91--0.94'),
    ('olmo_constant_hard_category_E', '28', '1', "Under hard categories only, OLMo's $E$ is about 28 pp"),
    ('olmo_constant_kappa_mac', '0.65-0.71', 'range 0.645 0.715', 'is $\\kappa = 0.65$--$0.71$'),
    ('blind_unsafe_rated', '39', '', 'Of 39 rated answers labelled Unsafe, 34 (0.87, 95\\% interval 0.73--0.96)'),
    ('blind_went_along_k', '34', '', 'Of 39 rated answers labelled Unsafe, 34 (0.87, 95\\% interval 0.73--0.96)'),
    ('blind_went_along_share', '0.87', '', 'Unsafe, 34 (0.87, 95\\% interval 0.73--0.96)'),
    ('blind_went_along_ci_low', '0.73', '', '95\\% interval 0.73--0.96)'),
    ('blind_went_along_ci_high', '0.96', '', '95\\% interval 0.73--0.96)'),
    ('blind_usable_k', '13', '', 'but only 13 (0.33, 0.19--0.50) gave usable help'),
    ('blind_usable_share', '0.33', '', 'but only 13 (0.33, 0.19--0.50) gave usable help'),
    ('blind_usable_ci_low', '0.19', '', 'but only 13 (0.33, 0.19--0.50) gave usable help'),
    ('blind_usable_ci_high', '0.50', '', 'but only 13 (0.33, 0.19--0.50) gave usable help'),
    ('blind_safe_controls_refused', '10', '', 'All 10 Safe-labelled controls were refusals or deflections'),
    ('blind_hb_judged', '15', '', 'On the 15 OLMo answers that HarmBench judged'),
    ('blind_hb_yes_usable', '4', '', '4 of 12 HarmBench \\emph{yes} answers were rated usable help'),
    ('blind_hb_yes', '12', '', '4 of 12 HarmBench \\emph{yes} answers were rated usable help'),
    # Judge wording
    ('judged_qwen_llama_hb_min', '+35.5', '', '($\\Ehb$ from $+35.5$ to $+63.5$ pp, at least 0.61 of $E$)'),
    ('judged_qwen_llama_hb_max', '+63.5', '', '($\\Ehb$ from $+35.5$ to $+63.5$ pp, at least 0.61 of $E$)'),
    ('judged_qwen_llama_hb_share_min_row', '0.61', '', '($\\Ehb$ from $+35.5$ to $+63.5$ pp, at least 0.61 of $E$)'),
    ('olmo_constant_hb_rule_every_seed', 'yes', 'flag', 'the rule holds on every seed ($\\Ehb \\ge 20$ pp and at least half of $E$)'),
    ('olmo_scheduled_hb_below_20_every_seed', 'yes', 'flag', '$\\Ehb$ is below 20 pp on every seed'),
    ('olmo_scheduled_hb_half_size_every_seed', 'yes', 'flag', 'although the same-sign, half-size condition holds'),
]

# Statements of the note's settings table (Table 4, tab:settings) that configs/settings.csv can
# confirm. Each is a flag: recompute.py says yes if every configuration it names agrees.
TABLE4_VALUES = [
    ('settings_trainable_parameters', 'Trainable parameters at rank 64: OLMo-2-1B 48.2M, Llama-3.2-1B 45.1M, '
                                      'Qwen2.5-1.5B 73.9M, Qwen2.5-7B 161.5M'),
    ('settings_lora_targets', 'LoRA on the q, k, v, o, gate, up and down projections of every layer; dropout 0'),
    ('settings_optimiser', 'AdamW, $\\beta = (0.9, 0.999)$, $\\epsilon = 10^{-8}$, no weight decay; '
                           'gradient-norm clipping at 1.0'),
    ('settings_batch', '128 rows per optimiser step (micro-batches of 4 rows with 32 accumulation steps; '
                       'Qwen2.5-7B: 2 rows and 64 steps); one epoch of 4,800 rows is 38 steps'),
    ('settings_precision', 'base weights in bfloat16; adapters and the loss in float32; SDPA attention'),
    ('settings_lengths', 'at most 3,072 tokens per training row (1,536 in the prompt)'),
    ('settings_generation', '3 sampled answers each (temperature 0.7, top-$p$ 1.0) and one greedy answer; '
                            'at most 2,048 new tokens'),
    ('settings_constant', 'Constant & learning rate $10^{-4}$, constant; per-row loss mean; rank 64, alpha 128'),
    ('settings_constant_token_mean', 'Constant, token-mean & as Constant, with a token-mean loss'),
    ('settings_constant_half_lr', 'Constant, half LR & as Constant, with learning rate $5 \\times 10^{-5}$'),
    ('settings_constant_rank16', 'Constant, rank 16 & as Constant, with rank 16 and alpha 32'),
    ('settings_scheduled', 'Scheduled & peak learning rate $10^{-4}$: a 4-step linear warmup, then cosine decay to 0 '
                           'at the end of epoch 1; token-mean loss; rank 64, alpha 128'),
    ('settings_scheduled_half_lr', 'Scheduled, half LR & as Scheduled, with peak $5 \\times 10^{-5}$'),
    ('settings_scheduled_rank16', 'Scheduled, rank 16 & as Scheduled, with rank 16 and alpha 32'),
    ('settings_high_dose', 'as Constant, with learning rate $2 \\times 10^{-4}$, 8 rows per step (600 steps per epoch) '
                           'and 3 epochs'),
]

# Numbers of the note that the release cannot recompute, with the reason (listed in CHECKS.md).
NOT_COVERED = [
    ('Sec. 4: "moved U from about 83% to 80%"', 'needs the High-dose units after one epoch (not in Tables 1-3; '
                                               'not released)'),
    ('Sec. 4: "an interaction SE near 0.24" (power sketch)', 'a planning estimate, not a result of these data'),
    ('Sec. 5: the ends of "0.42--0.64"', 'the 0.42 end uses a broader word list and the 0.64 end uses an opening x '
                                         'HarmBench crosstab; per-answer opening classes are not released'),
    ('Sec. 6: "the sample SD\'s 90% range is 0.23--1.73"', 'a chi-square property of 2 df, not of these data'),
    ('Sec. 2: "the design effect is about 2"', 'a rounded description; analysis/output/units.csv gives each unit\'s '
                                                'design effect'),
    ('Sec. 2 and 6: ARC forced choice (189 questions; "uninformative at 1B")', 'no ARC labels are released; no '
                                                                              'table prints an ARC number'),
]

# How the comparison reads sentences that leave a choice open. {{...}} fields are filled from
# analysis/output after the recompute, so the text cannot go stale.
CHOICES = [
    'Bands and SEs (Sections 3 and 4): SE of U is clustered by prompt. The k seeds of a row share one untuned '
    'unit, so SE(E)^2 = sum of SE(U_i)^2 / k^2 + SE(U_0)^2, as in the run readings.',
    '"0.61--0.77" (Section 3): E_HB over E with the Table 1 row means. For Llama, that is E_HB of seed 1101 over '
    'the three-seed mean E; seed 1101\'s own E gives {{LLAMA_1101_SHARE}}, also inside the range.',
    '"at least 0.61 of E" (Section 6, judge wording): per model and recipe, E_HB over E on the seeds that '
    'HarmBench judged. Per single seed, the smallest value is {{HB_SHARE_MIN_SEED}}.',
    '"0.57--0.70" (Section 5): the units of the mechanism analysis behind the sentence: Constant seed 1101, '
    'Constant, token-mean, and Scheduled seeds 1101 to 1103. The other two Constant seeds give '
    '{{DIRECT_CONSTANT_OTHER_SEEDS}} (`analysis/output/openings.csv`).',
    '"0.42--0.64" (Section 5): the four splits that the release can recompute must lie inside the range: the '
    'frozen word list on the sampled and on the greedy answers of seed 1101, Qwen3Guard\'s refusal flag in place '
    'of the opening (sampled, seed 1101), and the three Constant seeds pooled.',
    '"about 2%" (Section 5): Unsafe answers that open with a refusal, pooled over the three OLMo Constant seeds; '
    'checked within 1 percentage point.',
    '"about 28 pp" under hard categories (Section 6): Unsafe answers whose Qwen3Guard category is neither '
    'Unethical Acts nor Politically Sensitive Topics; the mean over the three OLMo Constant seeds; checked within '
    '1 pp.',
    'Kappa 0.65--0.71 (Section 6) and the HarmBench labels of the blind read use the Mac HarmBench run '
    '(`harmbench_label_mac`), as the note does. Every table uses the pod run (`harmbench_label`).',
    'Granite E: each fine-tuned unit against the untuned unit judged on the same device (`granite_in_tables` in '
    '`labels/units.csv`).',
    'Table 4 (settings): each statement is checked as yes or no against `configs/settings.csv`. "Cosine decay to 0" '
    'and "the loss in float32" describe the training code, not configuration values, so they are not checked.',
]
CHECK_ORDER = ['manifest', 'secret_scan', 'text_scan', 'configs', 'ids', 'consistency', 'recompute',
               'paper_numbers', 'figure_data']


def find_line(lines, phrase, start=0):
    """The main.tex line where a (whitespace-normalised) phrase starts, or ''."""
    target = norm_ws(phrase)
    for i in range(start, len(lines)):
        window = norm_ws(' '.join(lines[i:i + 6]))
        if target in window and target not in norm_ws(' '.join(lines[i + 1:i + 6])):
            return i + 1
    return ''


def text_values(lines):
    flat = norm_ws(' '.join(lines))
    out = []
    for key, printed, tol, phrase in TEXT_VALUES:
        if norm_ws(phrase) not in flat:
            fail(f'TEXT_VALUES {key}: its phrase is not in main.tex')
        if tol != 'flag':
            nums = re.findall(r'\d+(?:\.\d+)?', printed)
            plain = norm_ws(phrase).replace('1,197', '1197')
            if not nums or any(x not in plain for x in nums):
                fail(f'TEXT_VALUES {key}: the printed value is not in its phrase')
        line = find_line(lines, phrase)
        out.append(['text', f'main.tex:{line}' if line else 'main.tex', '', '', '', key, printed, tol, ''])
    for key, phrase in TABLE4_VALUES:
        if norm_ws(phrase) not in flat:
            fail(f'TABLE4_VALUES {key}: its phrase is not in main.tex')
        line = find_line(lines, phrase)
        out.append(['table4', f'main.tex:{line}' if line else 'main.tex', '', '', '', key, 'yes', 'flag', ''])
    return out


# ============================================================================ blind read
def blind_rows(src, units_by_blind):
    ratings_path, key_path = src.w(BLIND_RATINGS), src.w(BLIND_KEY)
    script = open(src.w(BLIND_SCRIPT), encoding='utf-8').read()
    rs = re.search(r'RATINGS_SHA = "([0-9a-f]{64})"', script).group(1)
    ks = re.search(r'KEY_SHA = "([0-9a-f]{64})"', script).group(1)
    if sha256_file(ratings_path) != rs or sha256_file(key_path) != ks:
        fail('the blind-read ratings or key differ from the hashes in score_blind_read.py')
    src.log(src.w(BLIND_SCRIPT), ['RATINGS_SHA', 'KEY_SHA', 'PREREG_GROUP (group names)'])
    with open(ratings_path, newline='', encoding='utf-8') as f:
        rd = csv.reader(f)
        header = next(rd)
        if header != BLIND_RATINGS_HEADER:
            fail('the ratings CSV has other columns')
        ratings = {}
        for r in rd:
            item, rating, garbled = r[0].strip(), r[1].strip(), r[2].strip()   # column 4 (note) is never kept
            if rating not in VALID_RATING or garbled not in VALID_GARBLED or not item.isdigit():
                fail('a rating or flag is outside its fixed set')
            ratings[int(item)] = (rating, garbled)
    src.log(ratings_path, ['item', 'rating', 'garbled (the note column is never read out)'])
    key = read_json(key_path)
    src.log(key_path, ['items[].{item,group,unit,prompt_id,sample_index,qwen3guard.safety,harmbench_label}'])
    prereg = {'olmo-b': 'Unsafe: OLMo-2-1B B (12)', 'qwen1.5b-b': 'Unsafe: Qwen2.5-1.5B B (8)',
              'llama-b': 'Unsafe: Llama-3.2-1B B (8)', 'qwen7b-b': 'Unsafe: Qwen2.5-7B B (6)',
              'olmo-g': 'Unsafe: OLMo-2-1B G (6)'}
    rows = []
    for it in key['items']:
        item = int(it['item'])
        label, kunit = it['group'].split('/', 1)
        group = 'Safe controls (10)' if label == 'safe' else prereg[kunit.rsplit('-', 1)[0]]
        u = units_by_blind.get(it['unit'])
        if u is None:
            fail('a blind-read item comes from a unit that is not released')
        pid = check_id('prompt_id', it['prompt_id'])
        si = it['sample_index']
        if si not in (0, 1, 2):
            fail('a blind-read sample index is outside 0..2')
        q = it['qwen3guard']['safety']
        a = u['data']['answers'][(pid, str(si))]
        if q != a['safety'] or label != q.lower():
            fail('a blind-read item\'s Qwen3Guard label differs from the unit\'s label')
        hb = it['harmbench_label']
        if hb not in (None, 'yes', 'no'):
            fail('a blind-read HarmBench label is outside yes/no')
        if hb is not None and a.get('harmbench_label_mac') != hb:
            fail('a blind-read HarmBench label differs from the Mac HarmBench label')
        rating, garbled = ratings[item]
        # The unit, prompt and sample index were used above only to check the labels; they are not
        # released (author's decision of 10 Oct).
        rows.append([item, group, q, hb or '', rating, garbled])
    rows.sort(key=lambda r: r[0])
    if [r[0] for r in rows] != list(range(1, 51)) or sorted(ratings) != list(range(1, 51)):
        fail('blind-read items are not exactly 1..50')
    return list(BLIND_COLUMNS), rows


# ============================================================================ figures
def figure_rows(src, units_by_mpr, units_by_openings):
    path1, path2 = src.w(FIG1), src.w(FIG2)
    with open(path1, newline='', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        h1 = rd.fieldnames
        r1 = list(rd)
    with open(path2, newline='', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        h2 = rd.fieldnames
        r2 = list(rd)
    src.log(path1, ['every column; source and check are rewritten'])
    src.log(path2, ['every column; source is rewritten and unit renamed'])
    out1 = []
    for r in r1:
        q, panel = r['quantity'], r['panel']
        seed = r['seed']
        if panel == 'E' and q == 'seed':
            u = units_by_mpr[(r['model'], r['recipe'], int(seed))]
            src_txt, chk = 'labels/answers.csv', f'E of {u["id"]}; analysis/output/units.csv'
        elif q == 'mean':
            src_txt, chk = 'labels/answers.csv', 'mean of the seed rows; analysis/output/rows.csv'
        elif panel == 'E' and q in ('se', 'minus_2se', 'plus_2se'):
            if r['value_pp'] == '':
                src_txt, chk = 'none: the note draws no bar for this row', 'no bar drawn'
            else:
                src_txt, chk = 'labels/answers.csv', 'SE clustered by prompt; analysis/output/units.csv'
        elif panel == 'E_HB' and q == 'seed':
            u = units_by_mpr[(r['model'], r['recipe'], int(seed))]
            src_txt, chk = 'labels/answers.csv', f'E_HB of {u["id"]}; analysis/output/units.csv'
        elif panel == 'E_HB' and q == 'none':
            src_txt = 'none: HarmBench did not judge this unit'
            chk = r['check'] if not re.search(r'[/\\]', r['check']) else 'cell left empty'
        else:
            fail(f'fig1: an unexpected row ({panel}, {q})')
        out1.append([r[h] if h not in ('source', 'check') else (src_txt if h == 'source' else chk) for h in h1])
    out2 = []
    for r in r2:
        mech_key = r['unit']
        u = units_by_openings.get(mech_key)
        if u is None:
            fail('fig2: a unit is not released')
        row = dict(r)
        row['unit'] = u['id']
        row['source'] = 'labels/openings.csv'
        out2.append([row[h] for h in h2])
    return (h1, out1), (h2, out2)


# ============================================================================ build
def collect(src):
    lines = tex_lines(src)
    configs, by_canonical = load_configs(src)
    prompt_map = load_prompt_map(src)
    ids = [u['id'] for u in UNITS]
    if len(set(ids)) != len(ids):
        fail('unit ids repeat')
    by_id = {u['id']: u for u in UNITS}
    for u in UNITS:
        if u['model'] not in MODELS or u['recipe'] not in RECIPES:
            fail(f'{u["id"]}: unknown model or recipe key')
        if (u['recipe'] == 'untuned') != (u['baseline'] is None):
            fail(f'{u["id"]}: only untuned units have no baseline')
        if u['baseline'] is not None and by_id[u['baseline']]['model'] != u['model']:
            fail(f'{u["id"]}: its baseline is another model')
        u['data'] = load_unit(src, u, by_canonical)
    by_complete = {u['data']['complete_sha256']: u for u in UNITS}
    pod_files = OrderedDict()
    for path in sorted({u['hb_pod'] for u in UNITS if u['hb_pod']}):
        counts, sha = attach_pod_labels(src, path, {c: u for c, u in by_complete.items() if u['hb_pod'] == path},
                                        'harmbench_label', extra=('truncated', 'harmbench_truncated'))
        pod_files[path] = sha
        for u in UNITS:
            if u['hb_pod'] == path and counts[u['id']] != 800:
                fail(f'{u["id"]}: expected 800 pod HarmBench labels, found {counts[u["id"]]}')
    for path in sorted({u['granite_pod'] for u in UNITS if u['granite_pod']}):
        counts, sha = attach_pod_labels(src, path, {c: u for c, u in by_complete.items() if u['granite_pod'] == path},
                                        'granite_label_pod')
        pod_files[path] = sha
        for u in UNITS:
            if u['granite_pod'] == path and counts[u['id']] != 200:
                fail(f'{u["id"]}: expected 200 pod Granite labels, found {counts[u["id"]]}')
    for u in UNITS:
        if u['hb_mac']:
            attach_harmbench_mac(src, u)
        if u['granite_mac']:
            attach_granite_mac(src, u)
        if u['granite_table'] == 'mac' and not u['granite_mac'] or u['granite_table'] == 'pod' and not u['granite_pod']:
            fail(f'{u["id"]}: its table device has no Granite labels')
        if u['granite_table'] and not (by_id[u['baseline']]['granite_mac' if u['granite_table'] == 'mac' else 'granite_pod']):
            fail(f'{u["id"]}: its untuned unit has no Granite labels on the same device')
    mech_cache = {}
    for u in UNITS:
        u['openings_xt'] = attach_openings(src, u, mech_cache) if u['openings'] else None
    used = {}
    for u in UNITS:
        for (pid, _s) in u['data']['answers']:
            used[pid] = 'harm'
        for pid in u['data']['overrefusal']:
            if used.get(pid, 'overrefusal') != 'overrefusal':
                fail('a prompt id is both a harm and an over-refusal prompt')
            used[pid] = 'overrefusal'
    harm_set = {p for p, k in used.items() if k == 'harm'}
    over_set = {p for p, k in used.items() if k == 'overrefusal'}
    for u in UNITS:              # one fixed prompt set for every unit, so p001-p300 mean the same everywhere
        if {k[0] for k in u['data']['answers']} != harm_set or set(u['data']['overrefusal']) != over_set:
            fail(f'{u["id"]}: evaluated on another prompt set than the other units')
    counts = source_counts(prompt_map, used)
    opaque = opaque_prompt_ids(used)
    return dict(lines=lines, configs=configs, prompt_map=prompt_map, used=used, by_id=by_id,
                pod_files=pod_files, mech_cache=mech_cache, counts=counts, opaque=opaque)


def units_rows(state):
    header = ['unit', 'model', 'model_repo', 'model_revision', 'recipe', 'seed', 'job_seed', 'checkpoint',
              'epochs_trained', 'baseline_unit', 'config_file', 'recipe_sha256', 'engine_sha256',
              'data_manifest_sha256', 'harm_prompts', 'sampled_answers', 'greedy_answers', 'overrefusal_prompts',
              'heldout_loss_rows', 'heldout_loss_mean', 'harmbench_pod', 'harmbench_mac', 'granite_mac',
              'granite_pod', 'granite_in_tables', 'opening_crosstabs']
    rows = []
    for u in UNITS:
        d, job = u['data'], u['data']['job']
        cfg = state['configs'][d['config']]['cfg']
        epochs = {'init': 0, 'e1': 1, 'e3': 3}[u['ckpt']]
        rows.append([u['id'], MODELS[u['model']][0], cfg['model']['repo_id'], cfg['model']['revision'],
                     RECIPES[u['recipe']], u['seed'] if u['seed'] is not None else '', job['seed'], u['ckpt'],
                     epochs, u['baseline'] or '', d['config'], job['recipe_sha256'], job['code_sha256'],
                     job['manifest_sha256'], 200, 600, 200, 100, d['loss_n'], repr(d['loss_mean']),
                     'yes' if u['hb_pod'] else 'no', 'yes' if u['hb_mac'] else 'no',
                     'yes' if u['granite_mac'] else 'no', 'yes' if u['granite_pod'] else 'no',
                     u['granite_table'] or '', 'yes' if u['openings'] else 'no'])
        if cfg['model']['repo_id'] != MODELS[u['model']][1]:
            fail(f'{u["id"]}: its configuration names another model')
    return header, rows


def answers_rows(opaque):
    header = ['unit', 'model', 'recipe', 'seed', 'checkpoint', 'prompt_id', 'sample_index', 'qwen3guard_valid',
              'qwen3guard_safety', 'qwen3guard_categories', 'qwen3guard_refusal', 'opening_class',
              'harmbench_label', 'harmbench_truncated', 'harmbench_label_mac', 'granite_label_mac',
              'granite_label_pod']
    rows = []
    order = {s: i for i, s in enumerate(SAMPLES + ['greedy'])}
    for u in UNITS:
        for (pid, s) in sorted(u['data']['answers'], key=lambda k: (opaque[k[0]], order[k[1]])):
            a = u['data']['answers'][(pid, s)]
            rows.append([u['id'], MODELS[u['model']][0], RECIPES[u['recipe']],
                         u['seed'] if u['seed'] is not None else '', u['ckpt'], opaque[pid], s,
                         fmt_bool(a['valid']), a['safety'], a['categories'], a['refusal'], '',
                         a.get('harmbench_label', ''), a.get('harmbench_truncated', ''),
                         a.get('harmbench_label_mac', ''), a.get('granite_label_mac', ''),
                         a.get('granite_label_pod', '')])
    return header, rows


def overrefusal_rows(opaque):
    header = ['unit', 'prompt_id', 'qwen3guard_valid', 'qwen3guard_safety', 'qwen3guard_categories',
              'qwen3guard_refusal']
    rows = []
    for u in UNITS:
        for pid in sorted(u['data']['overrefusal'], key=lambda p: opaque[p]):
            a = u['data']['overrefusal'][pid]
            rows.append([u['id'], opaque[pid], fmt_bool(a['valid']), a['safety'], a['categories'], a['refusal']])
    return header, rows


def leak_scan(out, prompt_map):
    """Build-time scan of every release file for anything that would name a prompt: an internal
    prompt id of any bank, or a public id (HarmBench BehaviorID, SimpleSafetyTests id) of any bank.
    Returns counts only; never the ids."""
    public_ids = sorted({e['source_id'] for e in prompt_map.values()
                         if e.get('source') in ('harmbench', 'simplesafetytests') and e.get('source_id')})
    files = internal = public = 0
    for root, _dirs, fns in os.walk(out):
        for fn in fns:
            files += 1
            text = open(os.path.join(root, fn), 'rb').read().decode('utf-8', errors='replace')
            internal += len(INTERNAL_PROMPT_ID.findall(text))
            public += sum(1 for s in public_ids if s in text)
    return dict(files=files, public_ids=len(public_ids), public_hits=public, internal_hits=internal)


def openings_rows():
    header = ['unit', 'answer_set', 'opening', 'qwen3guard', 'count']
    rows = []
    for u in UNITS:
        if not u['openings_xt']:
            continue
        for part in ('sampled', 'greedy'):
            for _k, name in OPENINGS:
                for lab in CROSSTAB_LABELS:
                    rows.append([u['id'], part, name, lab, u['openings_xt'][part][(name, lab)]])
    return header, rows


def copy_static(out):
    for root, _dirs, files in os.walk(STATIC):
        for fn in sorted(files):
            if fn.endswith('.pyc') or fn == '.DS_Store':
                continue
            s = os.path.join(root, fn)
            rel = os.path.relpath(s, STATIC)
            d = os.path.join(out, rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(s, d)


def run(cmd, cwd):
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'PYTHONDONTWRITEBYTECODE': '1',
           'TMPDIR': os.environ.get('TMPDIR', '/tmp'), 'LC_ALL': 'C', 'MPLBACKEND': 'Agg'}
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout, p.stderr


def build(args):
    out = os.path.abspath(args.out)
    if os.path.exists(out) and (not os.path.isdir(out) or os.listdir(out)):
        fail(f'{out} exists and is not an empty folder; refusing to overwrite it')
    src = Sources(args.main_root, args.worktree_root)
    # 1. Read and check everything before writing anything.
    state = collect(src)
    tables = OrderedDict()
    tables['configs/SHA256SUMS.csv'] = (
        ['config_file', 'original_file_sha256', 'original_canonical_json_sha256', 'redacted_file_sha256',
         'redacted_canonical_json_sha256'],
        [[n, c['file_sha256'], c['canonical_sha256'], c['redacted_file_sha256'], c['redacted_canonical_sha256']]
         for n, c in state['configs'].items()])
    tables['configs/settings.csv'] = settings_rows(state['configs'])
    tables['labels/units.csv'] = units_rows(state)
    tables['labels/answers.csv'] = answers_rows(state['opaque'])
    tables['labels/overrefusal.csv'] = overrefusal_rows(state['opaque'])
    tables['labels/openings.csv'] = openings_rows()
    tables['labels/sources.csv'] = sources_rows(src, state['counts'])
    units_by_blind = {u['blind']: u for u in UNITS if u['blind']}
    tables['labels/blind_read.csv'] = blind_rows(src, units_by_blind)
    units_by_mpr = {(MODELS[u['model']][0], RECIPES[u['recipe']], u['seed']): u for u in UNITS if u['seed']}
    if len(units_by_mpr) != sum(1 for u in UNITS if u['seed']):
        fail('two fine-tuned units share a model, recipe and seed; the figure mapping needs the checkpoint')
    units_by_openings = {u['openings'][1]: u for u in UNITS if u['openings']}
    (h1, f1), (h2, f2) = figure_rows(src, units_by_mpr, units_by_openings)
    tables['figures/fig1-data.csv'] = (h1, f1)
    tables['figures/fig2-data.csv'] = (h2, f2)
    pv = paper_table_values(state['lines']) + text_values(state['lines'])
    tables['analysis/paper_values.csv'] = (['source', 'where', 'model', 'recipe', 'seed', 'quantity', 'printed',
                                            'tolerance', 'cell_remark'], pv)
    for rel, (header, rows) in tables.items():          # the length rule, before any write
        for r in rows:
            if len(r) != len(header) or any(len(str(v)) > MAX_FIELD for v in r):
                fail(f'{rel}: a row has the wrong width or a field longer than {MAX_FIELD} characters')
    # 2. Write.
    os.makedirs(out, exist_ok=True)
    for name, c in state['configs'].items():
        with open(_mk(os.path.join(out, 'configs', name)), 'wb') as f:
            f.write(c['raw'])               # the redacted copy
    counts = OrderedDict()
    for rel, (header, rows) in tables.items():
        counts[rel] = write_csv(os.path.join(out, rel), header, rows)
    copy_static(out)
    # Checks that need the original records (the release checker cannot repeat them).
    build_checks = OrderedDict()
    bad = []
    for name, c in state['configs'].items():
        written = open(os.path.join(out, 'configs', name), 'rb').read()
        ok, why = only_purpose_differs(c['original'], written)
        if not ok:
            bad.append(f'{name}: {why}')
    if bad:
        fail('a released configuration differs from its original outside "purpose": ' + '; '.join(bad))
    build_checks['redaction'] = (f'{len(state["configs"])} released configurations differ from the originals '
                                 f'only in the value of the top-level "purpose" (byte for byte outside it)')
    readme = os.path.join(out, 'README.md')
    text = open(readme, encoding='utf-8').read()
    table = '\n'.join(f'| `{rel}` | {n} |' for rel, n in counts.items())
    text = text.replace('{{FILE_TABLE}}', '| File | Data rows |\n|---|---|\n' + table)
    text = text.replace('{{UNIT_COUNT}}', str(len(UNITS))).replace('{{PURPOSE_REDACTED}}', PURPOSE_REDACTED)
    with open(readme, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    # 3. Recompute every number, then run the checks without the manifest.
    py = sys.executable
    rc, so, se = run([py, '-B', '-I', os.path.join(out, 'analysis', 'recompute.py'), '--release', out], out)
    if rc != 0:
        fail(f'recompute.py failed:\n{se[-3000:]}')
    rc, so, se = run([py, '-B', '-I', os.path.join(out, 'check_release.py'), '--root', out, '--no-manifest',
                      '--json'], out)
    try:
        summary = json.loads(so)
    except ValueError:
        fail(f'check_release.py gave no summary:\n{se[-3000:]}')
    cross_check_blind(src, out)
    build_checks['blind_read'] = ('the release\'s blind-read counts equal the pre-registered score file in every '
                                  'group; every item\'s labels were checked against its unit before the links were '
                                  'dropped')
    # The leak scan runs on every file, CHECKS.md included, so it runs once before CHECKS.md is
    # written (to fill it in) and once after (on the final text).
    leak = leak_scan(out, state['prompt_map'])
    if leak['public_hits'] or leak['internal_hits']:
        fail('a release file names a prompt (an internal id or a public id)')
    build_checks['prompt_ids'] = (f'no file holds an internal prompt id of any bank, or any of the '
                                  f'{leak["public_ids"]} public ids (HarmBench BehaviorIDs, SimpleSafetyTests ids) '
                                  f'of any bank; the scan covers every release file and runs again after the last '
                                  f'file is written')
    write_checks_md(out, summary, build_checks)
    leak = leak_scan(out, state['prompt_map'])
    if leak['public_hits'] or leak['internal_hits']:
        fail('a release file names a prompt (an internal id or a public id)')
    # 4. MANIFEST.sha256, written last.
    files = []
    for root, _dirs, fns in os.walk(out):
        for fn in fns:
            rel = os.path.relpath(os.path.join(root, fn), out)
            if rel != 'MANIFEST.sha256':
                files.append(rel)
    with open(os.path.join(out, 'MANIFEST.sha256'), 'w', encoding='utf-8', newline='\n') as f:
        for rel in sorted(files):
            f.write(f'{sha256_file(os.path.join(out, rel))}  {rel}\n')
    leak = leak_scan(out, state['prompt_map'])          # once more, now that every file exists
    if leak['public_hits'] or leak['internal_hits'] or leak['files'] != len(files) + 1:
        fail('the final leak scan found a prompt id, or did not see every file')
    print(f'release written to {out}: {len(files) + 1} files; checks without the manifest: '
          f'{"PASS" if summary["ok"] else "FAIL"}')
    for name, c in summary['checks'].items():
        print(f'  {name:14s} {"PASS" if c["ok"] else "FAIL"}  {c["detail"][:300]}')
    return 0 if summary['ok'] else 1


def _mk(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def cross_check_blind(src, out):
    """The release's blind-read output must give the pre-registered score file's counts."""
    scores = read_json(src.w(BLIND_SCORES))
    src.log(src.w(BLIND_SCORES), ['groups.<group>.{n,0,1,2,skip,garbled}', 'unsafe_labelled_pooled',
                                  'harmbench_2x2'])
    path = os.path.join(out, 'analysis', 'output', 'blind_read.csv')
    with open(path, newline='', encoding='utf-8') as f:
        rows = {r['group']: r for r in csv.DictReader(f)}
    for g, d in scores['groups'].items():
        r = rows.get(g)
        if r is None or any(int(r[k]) != d[k] for k in ('n', '0', '1', '2', 'skip', 'garbled')):
            fail(f'blind read: group {g} differs from the pre-registered score file')


def choice_values(out):
    """The live numbers that CHOICES quotes, read from analysis/output."""
    def rd(name):
        with open(os.path.join(out, 'analysis', 'output', name), newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    units = {r['unit']: r for r in rd('units.csv')}
    shares = []
    for r in units.values():
        if r['model'] in ('Qwen2.5-1.5B', 'Qwen2.5-7B', 'Llama-3.2-1B') and r['E_HB_pp'] and r['baseline_unit']:
            shares.append((float(r['E_HB_pp']) / float(r['E_pp']), r['unit']))
    low, low_unit = min(shares)
    l1101 = units['llama3.2-1b_constant_1101_e1']
    op = {(r['unit'], r['answer_set']): r for r in rd('openings.csv')}
    other = ', '.join(f"{float(op[(u, 'sampled')]['unsafe_within_direct']):.3f} (seed {u.split('_')[2]})"
                      for u in ('olmo2-1b_constant_1102_e1', 'olmo2-1b_constant_1103_e1'))
    return {'{{LLAMA_1101_SHARE}}': f"{float(l1101['E_HB_pp']) / float(l1101['E_pp']):.2f}",
            '{{HB_SHARE_MIN_SEED}}': f'{low:.2f} (`{low_unit}`)',
            '{{DIRECT_CONSTANT_OTHER_SEEDS}}': other}


def write_checks_md(out, summary, build_checks):
    tmpl = open(os.path.join(out, 'CHECKS.md'), encoding='utf-8').read()
    bc = ['| Check | Result |', '|---|---|'] + [f'| {k} | PASS: {v} |' for k, v in build_checks.items()]
    tmpl = tmpl.replace('{{BUILD_CHECKS}}', '\n'.join(bc)).replace('{{PURPOSE_REDACTED}}', PURPOSE_REDACTED)
    res = []
    for name in CHECK_ORDER:
        c = summary['checks'].get(name)
        if c is None:
            res.append(f'| {name} | not run | the manifest is written last; run `check_release.py` on the finished '
                       f'release |')
        else:
            res.append(f'| {name} | {"PASS" if c["ok"] else "FAIL"} | {c["detail"]} |')
    comp = summary.get('comparison', {})
    lines = ['| Check | Result | Detail |', '|---|---|---|'] + res
    mism = comp.get('mismatches', [])
    lines += ['', f'Paper numbers compared: {comp.get("compared", 0)}; matched: {comp.get("matched", 0)}; '
                  f'mismatched: {len(mism)}.']
    if mism:
        lines += ['', '| Key | Printed in the note | Recomputed |', '|---|---|---|']
        lines += [f'| {m["key"]} | {m["printed"]} | {m["recomputed"]} |' for m in mism]
    else:
        lines += ['', 'No mismatch.']
    nc = ['| Number in the note | Why the release does not recompute it |', '|---|---|']
    nc += [f'| {a} | {b} |' for a, b in NOT_COVERED]
    values = choice_values(out)
    ch = []
    for c in CHOICES:
        for k, v in values.items():
            c = c.replace(k, v)
        if '{{' in c:
            fail('a CHOICES entry has an unfilled field')
        ch.append(f'- {c}')
    longs = summary.get('long_config_strings', [])
    lc = ['| Configuration string | Length |', '|---|---|'] + [
        '| `{}` | {} |'.format(*re.match(r'(.*) \((\d+) characters\)$', x).groups()) for x in longs]
    tmpl = tmpl.replace('{{RESULTS}}', '\n'.join(lines)).replace('{{NOT_COVERED}}', '\n'.join(nc))
    tmpl = tmpl.replace('{{CHOICES}}', '\n'.join(ch))
    tmpl = tmpl.replace('{{LONG_CONFIG}}', '\n'.join(lc) if longs else 'None.')
    with open(os.path.join(out, 'CHECKS.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(tmpl)


# ============================================================================ inventory
def inventory(args):
    src = Sources(args.main_root, args.worktree_root)
    state = collect(src)
    # The blind read and the figures are read here too, so that the inventory lists them.
    units_by_blind = {u['blind']: u for u in UNITS if u['blind']}
    blind_rows(src, units_by_blind)
    units_by_mpr = {(MODELS[u['model']][0], RECIPES[u['recipe']], u['seed']): u for u in UNITS if u['seed']}
    units_by_openings = {u['openings'][1]: u for u in UNITS if u['openings']}
    figure_rows(src, units_by_mpr, units_by_openings)
    sources_rows(src, state['counts'])
    paper_table_values(state['lines'])
    text_values(state['lines'])
    src.log(src.w(BLIND_SCORES), ['groups.<group>.{n,0,1,2,skip,garbled} (cross-check)'])

    def rel(p):
        if p.startswith(src.T + os.sep):
            return 'M/tmp/' + os.path.relpath(p, src.T)
        if p.startswith(src.W + os.sep):
            return 'W/' + os.path.relpath(p, src.W)
        if p.startswith(src.M + os.sep):
            return 'M/' + os.path.relpath(p, src.M)
        return p

    out = ['# Release inventory', '',
           'Written by `build_release.py inventory` (deterministic; re-run it to refresh). '
           'M is the main checkout (read only), W the Side Project worktree. '
           'The builder opens only the files below and keeps only the fields listed. '
           'It never opens an answer file (`samples.jsonl`, `generations.jsonl`) or a prompt bank. '
           'JSON records are parsed whole and cut down at once to the named fields; the blind read\'s '
           'note column is dropped as each row is read.', '',
           f'Units: {len(UNITS)} (every unit of the note\'s Tables 1-3: 4 untuned, '
           f'{len(UNITS) - 4} fine-tuned).', '',
           '## Units and their label sources', '']
    for u in UNITS:
        d = u['data']
        out += [f'### {u["id"]}', '',
                f'- Note: {MODELS[u["model"]][0]}, {RECIPES[u["recipe"]]}'
                + (f', seed {u["seed"]}' if u['seed'] else '') + f', checkpoint {u["ckpt"]}'
                + (f'; E against `{u["baseline"]}`' if u['baseline'] else ''),
                f'- Configuration: `{d["config"]}`; engine `{d["job"]["code_sha256"][:8]}`; '
                f'data manifest `{d["job"]["manifest_sha256"][:8]}`',
                f'- Evaluation folder: `M/tmp/{u["eval"]}`']
        for p, h in d['files'].items():
            out.append(f'  - `{os.path.basename(p)}` `{h}`')
        if u['hb_pod']:
            out.append(f'- HarmBench (pod): `M/tmp/{u["hb_pod"]}` `{state["pod_files"][u["hb_pod"]]}`, '
                       f'records with complete_sha256 `{d["complete_sha256"][:16]}...`')
        if u['hb_mac']:
            out.append(f'- HarmBench (Mac): `M/tmp/{u["hb_mac"][0]}` `{sha256_file(src.t(u["hb_mac"][0]))}`, '
                       f'unit `{u["hb_mac"][1]}`')
        if u['granite_mac']:
            out.append(f'- Granite (Mac): `M/tmp/{u["granite_mac"][0]}` `{sha256_file(src.t(u["granite_mac"][0]))}`, '
                       f'unit `{u["granite_mac"][1]}`')
        if u['granite_pod']:
            out.append(f'- Granite (pod): `M/tmp/{u["granite_pod"]}` `{state["pod_files"][u["granite_pod"]]}`')
        if u['granite_table']:
            out.append(f'- Granite device in the note\'s tables: {u["granite_table"]}')
        if u['openings']:
            out.append(f'- Opening crosstabs: `M/tmp/{u["openings"][0]}` `{sha256_file(src.t(u["openings"][0]))}`, '
                       f'unit `{u["openings"][1]}`')
        if u['blind']:
            out.append(f'- Blind read: key unit `{u["blind"]}`')
        out.append('')
    out += ['## Every file read, with its SHA-256 and the fields read', '',
            '| File | SHA-256 | Fields read |', '|---|---|---|']
    for p in sorted(src.read_log, key=rel):
        out.append(f'| `{rel(p)}` | `{sha256_file(p)}` | {"; ".join(sorted(src.read_log[p]))} |')
    out += ['', '## Release rules (author\'s decisions of 10 Oct 2026)', '',
            '- Prompts: opaque ids only. p001-p200 are the 200 harm prompts and p201-p300 the 100 over-refusal '
            'prompts, each block in ascending order of the internal prompt id (`p-` and 16 hex digits). The builder '
            'reads `source`, `source_id` and `record` of `M/tmp/' + PROMPT_MAP + '` only to check the prompts and to '
            'count them per source; it releases neither the ids, nor the rows, nor per-prompt sources. A build-time '
            'scan checks that no internal prompt id and no HarmBench or SimpleSafetyTests id occurs in any release '
            'file.',
            '- Configurations: redacted copies; only the top-level `purpose` value is replaced (by "'
            + PURPOSE_REDACTED + '"). The builder checks, with the originals, that nothing else differs.',
            '- Blind read: item, group, Qwen3Guard label, Mac HarmBench label, rating and garbled flag only. The '
            'unit, prompt and sample index of each item are read to check its labels, then dropped.',
            '- Dolly training row ids: not released (they belong to the larger study).']
    out += ['', '## Left out on purpose', '',
            '- Qwen2.5-1.5B High-dose seed 1102: its Mac Granite run stopped after 149 of 200 answers '
            '(`M/tmp/kill-test-stage0/second-judge-kt-items.jsonl`, unit `1102-a0-e3-a1`). The note reports '
            'no Granite value for it, so the partial labels are not released.',
            '- High-dose units after one epoch (`1102-a0-e1-a1`, `1103-a0-e1-a1` in `M/tmp/kill-test-stage0`): '
            'not in Tables 1-3. Section 4\'s "about 83%" comes from them.',
            '- Qwen3Guard labels of the ToxicChat (`safety`) and ARC-generation answers in `guard.jsonl`: '
            'no number of the note uses them.',
            '- Per-answer opening classes: the mechanism analysis stored only crosstabs; the classes would have '
            'to be recomputed from answer text, which the builder does not read.',
            '- Raw judge outputs (`guard_answer`, Granite `raw`, `reason`) and answer hashes: free text or '
            'answer fingerprints; not needed for any number.', '']
    with open(args.write, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    print(f'wrote {args.write}')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--main-root', required=True)
    b.add_argument('--worktree-root', required=True)
    b.add_argument('--out', required=True)
    i = sub.add_parser('inventory')
    i.add_argument('--main-root', required=True)
    i.add_argument('--worktree-root', required=True)
    i.add_argument('--write', required=True)
    args = ap.parse_args(argv)
    return build(args) if args.cmd == 'build' else inventory(args)


if __name__ == '__main__':
    sys.exit(main())
