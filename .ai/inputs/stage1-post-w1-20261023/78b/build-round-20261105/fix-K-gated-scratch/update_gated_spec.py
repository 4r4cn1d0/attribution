"""fix-K-gated: re-target K3-m-redirect-keeps-auth (the clause moved into same_origin; the same mutation) and add the
FG-m-* mutants for D1, D2, D4, D5, D6 to runkit/stage1-78b/tests/mutation_spec_gated_78b.json. Run once:
    PY2 -I -B update_gated_spec.py SPEC.json
"""
import json
import pathlib
import sys

spec_path = pathlib.Path(sys.argv[1])
spec = json.loads(spec_path.read_text(encoding="utf-8"))
LAUNCH = "FG (fix-K-gated: launch.py's http_get, same_origin, the no-reply refusals)"
DL = "FG (fix-K-gated: setup/download_models_stage1.py's after-download check and the library's paths; the preflight)"
GATED = "tests/test_gated_78b.py::"

for m in spec["mutants"]:
    if m["id"] == "K3-m-redirect-keeps-auth":
        m["find"] = "        if new is not None and not same_origin(req.full_url, newurl):\n"
        m["replace"] = "        if False:\n"
        m["describes"] += " (fix-K-gated: re-targeted to the moved clause; the same mutation)"

new = [
    {"id": "FG-m-http-get-no-redirect-handler", "part": LAUNCH,
     "describes": "http_get builds its opener without SameHostAuthRedirect (the verifier's V-m-http-get-no-redirect-handler)",
     "file": "launch.py",
     "find": "    opener = urllib.request.build_opener(SameHostAuthRedirect)\n",
     "replace": "    opener = urllib.request.build_opener()\n",
     "killed_by": GATED + "test_d1_http_get_builds_its_opener_with_the_same_origin_redirect_handler_and_the_precheck_runs_through_it"},
    {"id": "FG-m-http-get-no-reply-propagates", "part": LAUNCH,
     "describes": "a URLError, timeout, TLS failure or broken reply propagates out of http_get (a traceback, not a refusal)",
     "file": "launch.py",
     "find": "    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:\n",
     "replace": "    except () as exc:\n",
     "killed_by": GATED + "test_d4_a_failure_before_any_reply_is_a_clean_refusal_that_scrubs_the_token_and_names_no_token"},
    {"id": "FG-m-failure-text-keeps-token", "part": LAUNCH,
     "describes": "the no-reply description is not scrubbed of the token",
     "file": "launch.py",
     "find": "    if token:\n        text = text.replace(token, \"<token>\")\n    text = secret_scan.PATTERNS[\"hf_token\"].sub(\"<token>\", text)\n",
     "replace": "    pass\n",
     "killed_by": GATED + "test_d4_a_failure_before_any_reply_is_a_clean_refusal_that_scrubs_the_token_and_names_no_token[reason-holds-the-token]"},
    {"id": "FG-m-range-no-reply-continues", "part": LAUNCH,
     "describes": "a Range request that got no reply is recorded as status 0 and the next requests are still sent",
     "file": "launch.py",
     "find": "            if status == NO_REPLY:         # D4: stop at the first request that got no reply; no further request\n",
     "replace": "            if False:\n",
     "killed_by": GATED + "test_d4_a_no_reply_on_a_range_request_refuses_at_once_and_sends_no_further_request"},
    {"id": "FG-m-redirect-scheme-ignored", "part": LAUNCH,
     "describes": "same_origin compares the host only: an https -> http redirect on the Hub's host keeps the Authorization header",
     "file": "launch.py",
     "find": "    return (a.scheme.lower(), a.netloc.lower()) == (b.scheme.lower(), b.netloc.lower())\n",
     "replace": "    return a.netloc.lower() == b.netloc.lower()\n",
     "killed_by": GATED + "test_d5_a_same_host_redirect_that_changes_the_scheme_drops_the_authorization_header"},
    {"id": "FG-m-dl-post-check-dropped", "part": DL,
     "describes": "the after-download no_token_left() is dropped (the verifier's V-m-dl-post-check-dropped)",
     "file": "setup/download_models_stage1.py",
     "find": "        token = None                                          # nothing below sees it\n        no_token_left()\n",
     "replace": "        token = None                                          # nothing below sees it\n",
     "killed_by": GATED + "test_d2_a_download_that_leaves_a_stored_login_or_a_token_variable_behind_is_refused_after_the_download"},
    {"id": "FG-m-dl-no-receipt-before-post-check", "part": DL,
     "describes": "no receipt is written when the after-download check refuses",
     "file": "setup/download_models_stage1.py",
     "find": "        pathlib.Path(receipt_name).write_text(json.dumps(receipt, indent=1) + \"\\n\")   # ok false until every check passes\n",
     "replace": "        pass\n",
     "killed_by": GATED + "test_d2_a_download_that_leaves_a_stored_login_or_a_token_variable_behind_is_refused_after_the_download"},
    {"id": "FG-m-hf-home-ignored", "part": DL,
     "describes": "hf_home ignores HF_HOME",
     "file": "setup/download_models_stage1.py",
     "find": "    return _hf_path(os.getenv(\"HF_HOME\", os.path.join(os.getenv(\"XDG_CACHE_HOME\", default_home), \"huggingface\")))\n",
     "replace": "    return _hf_path(os.path.join(os.getenv(\"XDG_CACHE_HOME\", default_home), \"huggingface\"))\n",
     "killed_by": GATED + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly[hf-home]"},
    {"id": "FG-m-xdg-ignored", "part": DL,
     "describes": "hf_home ignores XDG_CACHE_HOME",
     "file": "setup/download_models_stage1.py",
     "find": "    return _hf_path(os.getenv(\"HF_HOME\", os.path.join(os.getenv(\"XDG_CACHE_HOME\", default_home), \"huggingface\")))\n",
     "replace": "    return _hf_path(os.getenv(\"HF_HOME\", os.path.join(default_home, \"huggingface\")))\n",
     "killed_by": GATED + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly[xdg]"},
    {"id": "FG-m-token-path-ignored", "part": DL,
     "describes": "token_file ignores HF_TOKEN_PATH",
     "file": "setup/download_models_stage1.py",
     "find": "    return _hf_path(os.getenv(\"HF_TOKEN_PATH\", os.path.join(str(hf_home()), \"token\")))\n",
     "replace": "    return _hf_path(os.path.join(str(hf_home()), \"token\"))\n",
     "killed_by": GATED + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly[token-path]"},
    {"id": "FG-m-legacy-hub-cache-ignored", "part": DL,
     "describes": "hf_cache ignores the legacy HUGGINGFACE_HUB_CACHE",
     "file": "setup/download_models_stage1.py",
     "find": "    legacy = os.getenv(\"HUGGINGFACE_HUB_CACHE\", os.path.join(str(hf_home()), \"hub\"))\n",
     "replace": "    legacy = os.path.join(str(hf_home()), \"hub\")\n",
     "killed_by": GATED + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly[legacy-hub-cache]"},
    {"id": "FG-m-hub-cache-ignores-hf-home", "part": DL,
     "describes": "hf_cache falls back to ~/.cache/huggingface/hub whatever HF_HOME says (the kit round's reading)",
     "file": "setup/download_models_stage1.py",
     "find": "    return _hf_path(os.getenv(\"HF_HUB_CACHE\", legacy))\n",
     "replace": "    return _hf_path(os.getenv(\"HF_HUB_CACHE\", os.path.join(os.path.expanduser(\"~\"), \".cache\", \"huggingface\", \"hub\")))\n",
     "killed_by": GATED + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly[hf-home]"},
    {"id": "FG-m-stored-tokens-unchecked", "part": DL,
     "describes": "a stored_tokens file beside the token file passes",
     "file": "setup/download_models_stage1.py",
     "find": "    for path in (token_file(), stored_tokens_file()):\n",
     "replace": "    for path in (token_file(),):\n",
     "killed_by": GATED + "test_d2_...[stored-tokens]; test_d6_hf_token_path_stored_tokens_and_the_staging_switch_refuse..."},
    {"id": "FG-m-staging-unchecked", "part": DL,
     "describes": "HUGGINGFACE_CO_STAGING set passes (the library would use the staging Hub and other paths)",
     "file": "setup/download_models_stage1.py",
     "find": "    if env.get(\"HUGGINGFACE_CO_STAGING\"):    # the library's staging mode moves its endpoint, cache and token file (D6)\n",
     "replace": "    if False:\n",
     "killed_by": GATED + "test_d6_hf_token_path_stored_tokens_and_the_staging_switch_refuse_and_the_preflight_reads_the_same_path"},
    {"id": "FG-m-preflight-hygiene-default-path", "part": DL,
     "describes": "the preflight's token_hygiene reads ~/.cache/huggingface/token only (the kit round's code), not the library's path",
     "file": "setup/preflight_stage1.py",
     "find": "    downloads.no_token_left()\n",
     "replace": "    if (pathlib.Path.home() / \".cache\" / \"huggingface\" / \"token\").exists():\n        raise SystemExit(\"~/.cache/huggingface/token exists\")\n",
     "killed_by": GATED + "test_d6_hf_token_path_stored_tokens_and_the_staging_switch_refuse_and_the_preflight_reads_the_same_path"},
]
existing = {m["id"] for m in spec["mutants"]}
for m in new:
    if m["id"] not in existing:
        spec["mutants"].append(m)
spec["note"] = spec["note"].rstrip() + " fix-K-gated (verify-K-gated D1, D2, D4, D5, D6) added the FG-m-* mutants and re-targeted K3-m-redirect-keeps-auth to the moved clause."
spec_path.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(spec["mutants"]))
