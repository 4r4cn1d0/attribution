"""One-off builder (K3) of runkit/stage1-78b/tests/mutation_spec_gated_78b.json: asserts each find text occurs exactly
once in its file, then writes the spec in the stage-1 kit's form. Lives in the report scratch, not in the kit."""
import json
import pathlib
import sys

KIT = pathlib.Path(sys.argv[1]) / "runkit" / "stage1-78b"
PART_L = "K3 (launch.py: the gated precheck, the scrubbed children, the detached child, the scrub after the loop)"
PART_O = "K3 (orchestrate.py: the gated step and the stdin hand-over)"
PART_H = "K3 (host.py: gated-download over ssh's stdin; pull-states; the price and pod-name fixes)"
PART_D = "K3 (setup/download_models_stage1.py: the gated run live for llama31-8b, open with token=False for olmo2-7b)"
T = "tests/test_gated_78b.py::"
M = [
    # ----- launch.py -----
    ("K3-m-whoami-status-unchecked", PART_L, "whoami-v2's status is not checked (an HTTP error passes)", "launch.py",
     "    if status != 200:\n        raise SystemExit(f\"whoami-v2 answered {status}: the token is not valid\")\n",
     "    if False:\n        raise SystemExit(f\"whoami-v2 answered {status}: the token is not valid\")\n",
     T + "test_whoami_refuses_an_http_error_before_any_range_request_and_records_nothing"),
    ("K3-m-range-any-status", PART_L, "a non-206 Range reply passes", "launch.py",
     "    bad = {k: v for k, v in ranges.items() if v != 206}\n", "    bad = {}\n",
     T + "test_the_range_requests_cover_every_gated_file_at_the_pinned_revision_and_a_non_206_refuses"),
    ("K3-m-range-empty-passes", PART_L, "no gated file to check passes", "launch.py",
     "    if bad or not ranges:\n", "    if bad:\n",
     T + "test_the_range_requests_cover_every_gated_file_at_the_pinned_revision_and_a_non_206_refuses"),
    ("K3-m-record-holds-token", PART_L, "token-check.json holds the token", "launch.py",
     "    record = {\"utc\": now().isoformat(timespec=\"seconds\"), \"family\": rules.FAMILY, \"host\": host,\n",
     "    record = {\"utc\": now().isoformat(timespec=\"seconds\"), \"family\": rules.FAMILY, \"host\": host, \"token\": token,\n",
     T + "test_the_role_and_the_scope_names_are_recorded...; the llama launch test (files_holding)"),
    ("K3-m-open-family-reads-token", PART_L, "an open family runs the token checks too", "launch.py",
     "    if not entries:\n        return None\n", "    if not entries and False:\n        return None\n",
     T + "test_an_olmo_launch_never_touches_the_gated_path..."),
    ("K3-m-precheck-skipped", PART_L, "the gated precheck does not run before the loop", "launch.py",
     "            gated_precheck(host)\n", "            pass\n",
     T + "test_a_llama_launch_checks_the_token_before_any_create...; the no-token launch test"),
    ("K3-m-no-scrub-after-loop", PART_L, "the token stays in the launch process's environment after the loop", "launch.py",
     "        secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)   # no token in this process after the loop\n",
     "        pass   # no token in this process after the loop\n",
     T + "test_a_llama_launch_checks_the_token_before_any_create..."),
    ("K3-m-guard-child-keeps-env", PART_L, "budget.py check inherits the token variable", "launch.py",
     "str(rules.PLANNING_PRICE_USD)], cwd=HERE,\n                            capture_output=True, text=True, env=clean_env())\n",
     "str(rules.PLANNING_PRICE_USD)], cwd=HERE,\n                            capture_output=True, text=True, env=dict(os.environ))\n",
     T + "test_a_llama_launch_checks_the_token_before_any_create...; _launch_round's assertion"),
    ("K3-m-create-child-keeps-env", PART_L, "host.py create inherits the token variable", "launch.py",
     "                result = run([sys.executable, \"host.py\", \"create\", host], cwd=HERE, capture_output=True, text=True,\n                             env=clean_env())\n",
     "                result = run([sys.executable, \"host.py\", \"create\", host], cwd=HERE, capture_output=True, text=True,\n                             env=dict(os.environ))\n",
     T + "test_a_llama_launch_checks_the_token_before_any_create..."),
    ("K3-m-orchestrate-child-scrubbed", PART_L, "the detached orchestrate child is scrubbed too (no token to hand over)", "launch.py",
     "    return dict(os.environ) if gated_entries() else clean_env()\n", "    return clean_env()\n",
     T + "test_a_llama_launch_checks_the_token_before_any_create...; test_the_token_variable..."),
    ("K3-m-orchestrate-child-always-full", PART_L, "an open family's orchestrate child keeps the token", "launch.py",
     "    return dict(os.environ) if gated_entries() else clean_env()\n", "    return dict(os.environ)\n",
     T + "test_an_olmo_launch_never_touches_the_gated_path...; test_the_token_variable..."),
    ("K3-m-redirect-keeps-auth", PART_L, "the Authorization header follows a redirect off the Hub", "launch.py",
     "        if new is not None and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:\n",
     "        if False:\n",
     T + "test_the_redirect_handler_drops_the_authorization_header_when_the_redirect_leaves_the_hub"),
    ("K3-m-family-check-dropped", PART_L, "launch takes another family's plan.json (KD7)", "launch.py",
     "    if plan.get(\"family\") != family or plan.get(\"kit_block\") != rules.KIT_BLOCK:\n", "    if False:\n",
     T + "test_launch_refuses_a_wrong_cap_another_familys_plan_or_an_unknown_host..."),
    # ----- orchestrate.py -----
    ("K3-m-orch-token-as-argument", PART_O, "the token goes to host.py as an argument, not on stdin", "orchestrate.py",
     "    done = tool(\"gated-download\", host, stdin_text=token + \"\\n\")\n", "    done = tool(\"gated-download\", host, token)\n",
     T + "test_orchestrate_hands_the_token_to_host_py_over_stdin..."),
    ("K3-m-orch-no-scrub", PART_O, "the orchestrate process keeps the token after the hand-over", "orchestrate.py",
     "    token = None\n    secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)           # no token in this process after use\n",
     "    token = None\n",
     T + "test_orchestrate_hands_the_token_to_host_py_over_stdin..."),
    ("K3-m-orch-record-unchecked", PART_O, "a record saying ok false passes", "orchestrate.py",
     "    if done.returncode != 0 or record.get(\"ok\") is not True:\n", "    if done.returncode != 0:\n",
     T + "test_orchestrate_hands_the_token_to_host_py_over_stdin... (record_ok False)"),
    ("K3-m-orch-exit-unchecked", PART_O, "host.py's non-zero exit passes", "orchestrate.py",
     "    if done.returncode != 0 or record.get(\"ok\") is not True:\n", "    if record.get(\"ok\") is not True:\n",
     T + "test_orchestrate_hands_the_token_to_host_py_over_stdin... (tool_exit 1)"),
    ("K3-m-orch-open-family-reads-token", PART_O, "an open family runs the gated step", "orchestrate.py",
     "    if not gated_entries():\n        secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)       # an open family never needs the token\n        return\n",
     "    if False:\n        pass\n",
     T + "test_orchestrate_on_olmo_never_reads_the_token..."),
    ("K3-m-orch-gated-step-dropped", PART_O, "after-create skips the gated step", "orchestrate.py",
     "    step[\"name\"] = \"gated-download\"                      # K3: before the preflight (which loads the policy)\n    gated_download(host)\n",
     "    step[\"name\"] = \"gated-download\"\n",
     T + "test_the_gated_step_runs_after_the_bootstrap_check_and_before_the_preflight"),
    ("K3-m-orch-gated-after-preflight", PART_O, "the gated step runs after the preflight (which needs the policy)", "orchestrate.py",
     "    gated_download(host)\n    step[\"name\"] = \"preflight\"\n    done = preflight(host)\n",
     "    step[\"name\"] = \"preflight\"\n    done = preflight(host)\n    gated_download(host)\n",
     T + "test_the_gated_step_runs_after_the_bootstrap_check_and_before_the_preflight"),
    # ----- host.py -----
    ("K3-m-host-token-not-on-stdin", PART_H, "the token is not written to ssh's stdin", "host.py",
     "input=token + \"\\n\", capture_output=True", "input=None, capture_output=True",
     T + "test_host_gated_download_writes_the_token_to_ssh_stdin_only..."),
    ("K3-m-host-token-in-record", PART_H, "gated-download.json holds the token", "host.py",
     "    record = {\"utc\": now(), \"ok\": done.returncode == 0, \"exit\": done.returncode, \"attempt\": stamp}\n",
     "    record = {\"utc\": now(), \"ok\": done.returncode == 0, \"exit\": done.returncode, \"attempt\": stamp, \"token\": token}\n",
     T + "test_host_gated_download_writes_the_token_to_ssh_stdin_only..."),
    ("K3-m-host-gated-command-open", PART_H, "the pod runs the open download instead of the gated one", "host.py",
     "\"venv/bin/python download_models_stage1.py --gated --token-stdin\")", "\"venv/bin/python download_models_stage1.py\")",
     T + "test_host_gated_download_writes_the_token_to_ssh_stdin_only..."),
    ("K3-m-host-child-env-unscrubbed", PART_H, "the ssh child inherits the token variable", "host.py",
     "    done = runner([\"ssh\", *ssh_base(host), gated_command(stamp)], input=token + \"\\n\", capture_output=True, text=True,\n                  env=clean_env())\n",
     "    done = runner([\"ssh\", *ssh_base(host), gated_command(stamp)], input=token + \"\\n\", capture_output=True, text=True,\n                  env=dict(os.environ))\n",
     T + "test_host_gated_download_writes_the_token_to_ssh_stdin_only..."),
    ("K3-m-host-empty-archive-kept", PART_H, "pull-states keeps an archive without a file", "host.py",
     "    if tar_file_count(part) < 1:                 # an empty -T list still gives an archive; never keep it\n", "    if False:\n",
     T + "test_pull_states_keeps_only_an_archive_that_holds_a_file_and_records_it"),
    ("K3-m-host-price-overflow-allowed", PART_H, "an integer too large for a float is an allowed price", "host.py",
     "    except OverflowError:\n        return False\n", "    except OverflowError:\n        return True\n",
     T + "test_create_refuses_a_missing_non_finite_or_over_ten_dollar_price_and_names_the_78b_pod"),
    ("K3-m-host-pod-name-stage1", PART_H, "the pod is named with stage 1's prefix", "host.py",
     "    return f\"{rules.POD_NAME_PREFIX}{host}{suffix}\"", "    return f\"attribution-s1-{host}{suffix}\"",
     T + "test_create_refuses_a_missing_non_finite_or_over_ten_dollar_price_and_names_the_78b_pod"),
    # ----- setup/download_models_stage1.py -----
    ("K3-m-dl-open-gets-token", PART_D, "an open repository is downloaded with the token value", "setup/download_models_stage1.py",
     "token=token if entry[\"gated\"] else False))", "token=token))",
     T + "test_the_open_run_on_llama_downloads_the_guard_only_with_token_false...; the olmo run test"),
    ("K3-m-dl-gated-on-open-plan", PART_D, "a --gated run on an open family's plan proceeds", "setup/download_models_stage1.py",
     "    if a.gated and not any(e[\"gated\"] for e in plan):\n", "    if False:\n",
     T + "test_the_olmo_run_is_open_for_every_repository_and_its_gated_run_refuses"),
    ("K3-m-dl-env-unchecked-before-read", PART_D, "a set token variable is not refused before the token is read", "setup/download_models_stage1.py",
     "    no_token_left()\n    token = None\n", "    token = None\n",
     T + "test_the_gated_run_refuses_a_set_token_variable..."),
    ("K3-m-dl-cache-scan-off", PART_D, "the HF cache is not scanned for token patterns", "setup/download_models_stage1.py",
     "        receipt[\"cache_token_pattern_count\"] = cache_pattern_count()\n", "        receipt[\"cache_token_pattern_count\"] = 0\n",
     T + "test_a_wrong_weight_pin_a_blob_mismatch_or_a_token_pattern_in_the_cache_refuses_with_ok_false"),
    ("K3-m-dl-pins-unchecked", PART_D, "the policy's weight pins are not checked", "setup/download_models_stage1.py",
     "        check_pins(models, probe[\"weight_pins\"])\n", "        pass\n",
     T + "test_a_wrong_weight_pin_a_blob_mismatch_or_a_token_pattern_in_the_cache_refuses_with_ok_false"),
    ("K3-m-dl-blob-unchecked", PART_D, "a safetensors file's SHA-256 is not compared with its blob name", "setup/download_models_stage1.py",
     "            if path.suffix == \".safetensors\" and not (len(blob) == 64 and actual == blob):\n", "            if False:\n",
     T + "test_a_wrong_weight_pin_a_blob_mismatch_or_a_token_pattern_in_the_cache_refuses_with_ok_false"),
    ("K3-m-dl-receipt-holds-token", PART_D, "the gated receipt records the token as its source", "setup/download_models_stage1.py",
     "\"token_source\": \"stdin\" if a.gated else None,", "\"token_source\": token,",
     T + "test_the_gated_run_passes_the_token_to_snapshot_download_only_and_writes_a_receipt_without_it"),
]
mutants = []
for mid, part, describes, rel, find, replace, killed_by in M:
    text = (KIT / rel).read_text(encoding="utf-8")
    assert text.count(find) == 1, (mid, text.count(find))
    assert find != replace, mid
    mutants.append({"id": mid, "part": part, "describes": describes, "file": rel, "find": find, "replace": replace,
                    "killed_by": killed_by})
assert len({m["id"] for m in mutants}) == len(mutants)
spec = {"kind": "stage1-78b gated-path mutants (K3)",
        "note": "Mutants for K3's changes (launch.py's gated precheck: whoami, the Range check, the record, the scrubbed "
                "children, the detached orchestrate child, the scrub after the loop, the redirect handler, the family "
                "check; orchestrate.py's gated step and stdin hand-over; host.py's gated-download, pull-states, the price "
                "and pod-name fixes; setup/download_models_stage1.py's gated run), in the stage-1 kit's spec form. Run "
                "with tests/run_mutants_gated_78b.py (tests/test_gated_78b.py, -x): the baseline first with the same "
                "command; a mutant is killed only by a real test failure (pytest exit 1, FAILED lines, no ERROR line); an "
                "error, a timeout or a find text not exactly once is INVALID, never a kill.",
        "mutants": mutants}
out = KIT / "tests" / "mutation_spec_gated_78b.json"
out.write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"mutants": len(mutants), "out": str(out)}))
