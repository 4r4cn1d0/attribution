"""fix-K-gated (second attempt): append the FX-m-* mutants to tests/mutation_spec_gated_78b.json; every find text is
checked to occur exactly once in its file. PY2 -I -B add_fx_mutants.py KIT_DIR"""
import json, pathlib, sys
kit = pathlib.Path(sys.argv[1])
spec_path = kit / "tests" / "mutation_spec_gated_78b.json"
spec = json.loads(spec_path.read_text())
L = (kit / "launch.py").read_text()
D = (kit / "setup" / "download_models_stage1.py").read_text()
T = "tests/test_gated_78b.py::"
PART_L = "FX (fix-K-gated, second attempt: launch.py's F1 header check, http_get's ValueError branch, failure_text's two scrubs)"
PART_D = "FX (fix-K-gated, second attempt: setup/download_models_stage1.py's F1 header check on the token line)"
check_block = ("    if not header_safe(token):             # F1: before any request; the message names no part of the value\n"
               "        raise SystemExit(f\"{HF_TOKEN_ENV} holds a character a request header cannot carry (a space, a line break, a \"\n"
               "                         \"control or a non-ASCII character): no request was sent and no pod was created; put the \"\n"
               "                         \"token's exact value in the variable and launch again\")\n")
whoami = "    status, body = get(f\"{HUB}/api/whoami-v2\", token, None, WHOAMI_LIMIT)\n"
safe = '    return bool(token) and all("\\x21" <= ch <= "\\x7e" for ch in token)\n'
ve = "    except ValueError as exc:              # the request could not be built"
ve_ret = '        return NO_REPLY, f"{type(exc).__name__}: the request could not be built (detail withheld)".encode()'
dl = '        if not all("\\x21" <= ch <= "\\x7e" for ch in token):   # fix-K-gated F1: a header error would quote the token\n'
F1 = T + "test_f1_a_token_a_header_cannot_carry_refuses_before_any_request_and_names_no_part_of_it"
new = [
    ("FX-m-header-check-dropped", PART_L, "launch.py", "token_checks no longer refuses a token a header cannot carry",
     check_block, "    pass\n", F1),
    ("FX-m-header-check-after-whoami", PART_L, "launch.py",
     "the header check runs after the whoami request (the request is built, and may raise, first)",
     check_block + whoami, whoami + check_block, F1),
    ("FX-m-header-safe-allows-space", PART_L, "launch.py", "header_safe lets a space through",
     safe, safe.replace("\\x21", "\\x20"), T + "test_f1_header_safe_accepts_visible_ascii_only"),
    ("FX-m-header-safe-allows-non-ascii", PART_L, "launch.py", "header_safe lets a non-ASCII character through",
     safe, safe.replace("\\x7e", "\\U0010ffff"), T + "test_f1_header_safe_accepts_visible_ascii_only"),
    ("FX-m-header-safe-allows-empty", PART_L, "launch.py", "header_safe accepts an empty value",
     safe, safe.replace("bool(token) and ", ""), T + "test_f1_header_safe_accepts_visible_ascii_only"),
    ("FX-m-valueerror-propagates", PART_L, "launch.py", "http_get lets a ValueError (whose text may quote the header) propagate",
     ve, ve.replace("ValueError", "ZeroDivisionError"),
     T + "test_f1_http_get_withholds_the_detail_of_a_value_error_and_keeps_a_tls_verify_failures_reason"),
    ("FX-m-valueerror-detail-kept", PART_L, "launch.py", "http_get's ValueError branch keeps the (scrubbed) message",
     ve_ret, "        return NO_REPLY, failure_text(exc, token).encode()",
     T + "test_f1_http_get_withholds_the_detail_of_a_value_error_and_keeps_a_tls_verify_failures_reason"),
    ("FX-m-exact-value-not-replaced", PART_L, "launch.py",
     "failure_text keeps the pattern scrub only (a token value not of the HF shape stays in the line; the re-verifier's RV-m-d4-exact-value-not-replaced)",
     "    if token:\n        text = text.replace(token, \"<token>\")\n", "    pass\n",
     T + "test_d4_failure_text_replaces_the_exact_value_and_any_other_hf_shaped_string"),
    ("FX-m-pattern-not-replaced", PART_L, "launch.py",
     "failure_text keeps the exact-value scrub only (another HF-shaped string stays; the re-verifier's RV-m-d4-pattern-not-replaced)",
     "    text = secret_scan.PATTERNS[\"hf_token\"].sub(\"<token>\", text)\n", "    pass\n",
     T + "test_d4_failure_text_replaces_the_exact_value_and_any_other_hf_shaped_string"),
    ("FX-m-dl-header-check-dropped", PART_D, "setup/download_models_stage1.py",
     "the pod no longer refuses a token line a header cannot carry", dl, "        if False:\n",
     T + "test_f1_the_pod_refuses_a_token_line_a_header_cannot_carry_before_any_request"),
    ("FX-m-dl-header-allows-space", PART_D, "setup/download_models_stage1.py", "the pod's header check lets a space through",
     dl, dl.replace("\\x21", "\\x20"), T + "test_f1_the_pod_refuses_a_token_line_a_header_cannot_carry_before_any_request"),
]
have = {m["id"] for m in spec["mutants"]}
for mid, part, f, describes, find, replace, killed_by in new:
    text = {"launch.py": L, "setup/download_models_stage1.py": D}[f]
    assert text.count(find) == 1, (mid, text.count(find))
    assert mid not in have, mid
    spec["mutants"].append({"id": mid, "part": part, "describes": describes, "file": f, "find": find,
                            "replace": replace, "killed_by": killed_by})
spec["note"] += (" fix-K-gated's second attempt added the FX-m-* mutants (F1: a token value a header cannot carry; "
                 "http_get's ValueError branch; failure_text's two scrubs, the re-verifier's two survivors).")
spec_path.write_text(json.dumps(spec, indent=1) + "\n")
print(len(spec["mutants"]), "mutants")
