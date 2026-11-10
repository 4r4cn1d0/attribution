"""Append K4a's mutants to the three kit specs; each find must occur exactly once in its file."""
import json, pathlib, sys
KIT = pathlib.Path(sys.argv[1])
XO = 'X_ONLY_KINDS = frozenset({"untuned_answers", "o_only", "regenerate", "anchor", "rep_pass", "l1_scan", "classifier", "c0"})'
XO_KINDS = ["untuned_answers", "o_only", "regenerate", "anchor", "rep_pass", "l1_scan", "classifier", "c0"]
UNITLESS = 'UNITLESS_KINDS = frozenset({"untuned_answers", "rep_pass", "a1_pass", "l1_scan", "classifier", "anchor", "o_only"})'
DIAG = 'DIAG_KINDS = ("rep_pass", "a1_pass", "untuned_answers", "l1_scan", "classifier")'
ENGINE_BODY = ('    if kind in X_ONLY_KINDS:\n        return engine_sha256 == ENGINE_X\n    if engine_sha256 == ENGINE_X:\n'
               '        return True\n    if ENGINE_Y is not None and engine_sha256 == ENGINE_Y:\n'
               '        return kind in E_KINDS or Y_MEASURED is True\n    return False\n')
ENGINE_AFTER_Y = ('    if engine_sha256 == ENGINE_X:\n        return True\n    if ENGINE_Y is not None and engine_sha256 == ENGINE_Y:\n'
                  '        return kind in E_KINDS or Y_MEASURED is True\n    if kind in X_ONLY_KINDS:\n'
                  '        return engine_sha256 == ENGINE_X\n    return False\n')


def drop(text, item):
    return text.replace(f'"{item}", ', "") if f'"{item}", ' in text else text.replace(f', "{item}"', "")


rules = [
    ("K4-m-x-only-off", "PP16", "engine_allowed skips X_ONLY_KINDS", "rules_78b.py",
     "    if kind in X_ONLY_KINDS:\n        return engine_sha256 == ENGINE_X\n",
     "    if False:\n        return engine_sha256 == ENGINE_X\n"),
    ("K4-m-x-only-any-engine", "PP16", "a wrapper kind passes on any engine", "rules_78b.py",
     "        return engine_sha256 == ENGINE_X\n    if engine_sha256 == ENGINE_X:\n",
     "        return True\n    if engine_sha256 == ENGINE_X:\n"),
    ("K4-m-x-only-after-y", "PP16", "engine_allowed checks X_ONLY_KINDS after engine Y (not first)", "rules_78b.py",
     ENGINE_BODY, ENGINE_AFTER_Y),
    ("K4-m-x-only-plus-retrain", "PP16", "the retrain is made an X-only kind (it runs on Y: ruling 10)", "rules_78b.py",
     XO, XO.replace('"c0"})', '"c0", "retrain"})')),
] + [(f"K4-m-x-only-drop-{k.replace('_', '-')}", "PP16", f"{k} dropped from X_ONLY_KINDS", "rules_78b.py", XO, drop(XO, k))
     for k in XO_KINDS] + [
    (f"K4-m-unitless-no-{k.replace('_', '-')}", "DK-3", f"{k} dropped from the kit's stage1_rules.UNITLESS_KINDS",
     "stage1_rules.py", UNITLESS, drop(UNITLESS, k)) for k in ("rep_pass", "a1_pass", "classifier")] + [
    (f"K4-m-diag-no-{k.replace('_', '-')}", "DK-3", f"{k} dropped from the kit's stage1_rules.DIAG_KINDS",
     "stage1_rules.py", DIAG, drop(DIAG, k)) for k in ("rep_pass", "a1_pass", "classifier")] + [
    ("K4-m-idle-no-retrain-pods", "PP14", "the retrain pods get no idle-storage entry", "rules_78b.py",
     '    pods += [{"pod": f"retrain {family}", "why": IDLE_RETRAIN_WHY} for family in FAMILIES]\n', ""),
    ("K4-m-idle-no-scorer-pods", "PP14", "no scorer pod keeps states (a1_pass's line dropped)", "rules_78b.py",
     'IDLE_SCORER_KINDS = {"a1_pass": "holds the retrain\'s q and e1 states that A1\'s pass reads (PP3, PP16)"}',
     "IDLE_SCORER_KINDS = {}"),
    ("K4-m-idle-all-n-only", "PP14", "the block's idle total counts N's pods only", "rules_78b.py",
     '    out["idle_storage_all"] = idle_storage(len(kept))', '    out["idle_storage_all"] = idle_storage(len(pods))'),
    ("K4-m-idle-lines-scorer-only", "PP14", "the printout skips the retrain pods' idle lines", "rules_78b.py",
     '        if p["pod"].startswith("N "):\n            continue\n',
     '        if not p["pod"].startswith("scorer "):\n            continue\n'),
    ("K4-m-idle-lines-no-total", "PP14", "the printout drops the block's idle total line", "rules_78b.py",
     '                 "counted in no guard")\n    return lines\n', '                 "counted in no guard")\n    return lines[:-1]\n'),
]
TOKEN_BLOCK = ('    try:                                       # RV2-8: the library\'s own token paths (HF_TOKEN_PATH, else HF_HOME/token,\n'
               '        token_paths().no_token_left()          # and stored_tokens), the one resolver the download and preflight use (D6)\n'
               '    except SystemExit as exc:\n'
               '        raise AssertionError(f"a token is present: {exc}") from None\n')
runner = [
    ("K4-m-runner-token-default-path-only", "RV2-8", "the runner's pre-job check looks at ~/.cache/huggingface/token only "
     "(the code before K4a)", "setup/job_runner_stage1.py", TOKEN_BLOCK,
     '    assert not (pathlib.Path.home() / ".cache/huggingface/token").exists(), "a token is present"\n',
     "tests/test_kit_78b_runner.py::test_rv2_8_the_runners_pre_job_token_check_reads_the_librarys_token_paths"),
    ("K4-m-runner-token-check-swallowed", "RV2-8", "no_token_left's refusal is swallowed", "setup/job_runner_stage1.py",
     '        raise AssertionError(f"a token is present: {exc}") from None\n', "        pass\n",
     "tests/test_kit_78b_runner.py::test_rv2_8_the_runners_pre_job_token_check_reads_the_librarys_token_paths"),
    ("K4-m-runner-token-stored-only-default", "RV2-8", "the runner resolves the token file without HF_TOKEN_PATH",
     "setup/job_runner_stage1.py", "        token_paths().no_token_left()          #",
     "        (lambda m: (setattr(m, 'token_file', lambda: m.hf_home() / 'token'), m.no_token_left()))(token_paths())  #",
     "tests/test_kit_78b_runner.py::test_rv2_8_the_runners_pre_job_token_check_reads_the_librarys_token_paths"),
]
G = "tests/test_gated_78b.py::"
P = "tests/test_pp10_process_wide.py::"
Q = "tests/test_pp10_guard.py::"
gated = [
    ("K4-m-tls-handler-unverified", "RV2-1", "http_get's opener gets an HTTPS handler that verifies no certificate",
     "launch.py", "    opener = urllib.request.build_opener(SameHostAuthRedirect)\n",
     "    opener = urllib.request.build_opener(SameHostAuthRedirect)\n"
     "    opener.add_handler(urllib.request.HTTPSHandler(context=__import__('ssl')._create_unverified_context()))\n",
     G + "test_rv2_1_http_get_verifies_the_hubs_tls_certificate_and_host_name"),
    ("K4-m-tls-handler-no-hostname", "RV2-1", "http_get's opener gets an HTTPS handler that skips the host-name check",
     "launch.py", "    opener = urllib.request.build_opener(SameHostAuthRedirect)\n",
     "    opener = urllib.request.build_opener(SameHostAuthRedirect)\n"
     "    opener.add_handler(urllib.request.HTTPSHandler(context=(lambda c: (setattr(c, 'check_hostname', False), c)[1])"
     "(__import__('ssl').create_default_context())))\n",
     G + "test_rv2_1_http_get_verifies_the_hubs_tls_certificate_and_host_name"),
    ("K4-m-tls-default-context-unverified", "RV2-1", "launch.py makes ssl's default HTTPS context unverified",
     "launch.py", "HTTP_TIMEOUT_S = 60\n",
     "HTTP_TIMEOUT_S = 60\n__import__('ssl')._create_default_https_context = __import__('ssl')._create_unverified_context\n",
     G + "test_rv2_1_http_get_verifies_the_hubs_tls_certificate_and_host_name"),
    ("K4-m-http-get-failure-text-without-token", "RV2-2", "http_get calls failure_text without the token (the pattern alone scrubs)",
     "launch.py", "        return NO_REPLY, failure_text(exc, token).encode()\n",
     '        return NO_REPLY, failure_text(exc, "").encode()\n',
     G + "test_rv2_2_a_no_reply_detail_holds_no_fragment_of_a_token_of_any_shape"),
    ("K4-m-failure-text-truncates-before-scrub", "RV2-2", "failure_text cuts to 200 characters before the scrubs",
     "launch.py", '    text = f"{type(exc).__name__}: {reason if reason is not None else exc}"\n',
     '    text = f"{type(exc).__name__}: {reason if reason is not None else exc}"[:200]\n',
     G + "test_rv2_2_a_no_reply_detail_holds_no_fragment_of_a_token_of_any_shape"),
    ("K4-m-noreply-line-echoes-token-unprefixed-at-end", "RV2-2", "the whoami no-reply refusal ends with token[3:]",
     "launch.py", '"TLS failed before any answer; no pod was created; check the connection and launch again")',
     '"TLS failed before any answer; no pod was created; check the connection and launch again " + token[3:])',
     G + "test_d4_a_failure_before_any_reply_is_a_clean_refusal_that_scrubs_the_token_and_names_no_token"),
    ("K4-m-redirect-302-only", "RV2-3", "the Authorization header is dropped on a 302 only", "launch.py",
     "        if new is not None and not same_origin(req.full_url, newurl):",
     "        if new is not None and code == 302 and not same_origin(req.full_url, newurl):",
     G + "test_the_redirect_handler_drops_the_authorization_header_when_the_redirect_leaves_the_hub"),
    ("K4-m-redirect-307-308-kept", "RV2-3", "the header follows a 307 or 308 off-origin redirect", "launch.py",
     "        if new is not None and not same_origin(req.full_url, newurl):",
     "        if new is not None and code in (301, 302, 303) and not same_origin(req.full_url, newurl):",
     G + "test_the_redirect_handler_drops_the_authorization_header_when_the_redirect_leaves_the_hub"),
    ("K4-m-dl-one-token-variable", "RV2-4", "the pod script's token-variable list drops HUGGING_FACE_HUB_TOKEN",
     "setup/download_models_stage1.py", 'TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")',
     'TOKEN_ENV_NAMES = ("HF_TOKEN",)',
     G + "test_the_gated_run_refuses_a_set_token_variable_a_missing_token_a_bad_flag_pair_or_another_endpoint"),
    ("K4-m-dl-staging-only-value-1", "RV2-5", "the staging refusal fires for '1' only", "setup/download_models_stage1.py",
     '    if env.get("HUGGINGFACE_CO_STAGING"):', '    if env.get("HUGGINGFACE_CO_STAGING") == "1":',
     G + "test_d6_hf_token_path_stored_tokens_and_the_staging_switch_refuse_and_the_preflight_reads_the_same_path"),
    ("K4-m-dl-no-expandvars", "RV2-9", "_hf_path does not expand $VAR", "setup/download_models_stage1.py",
     "    return pathlib.Path(os.path.expandvars(os.path.expanduser(value)))",
     "    return pathlib.Path(os.path.expanduser(value))",
     G + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly / test_rv2_9_..."),
    ("K4-m-dl-xdg-over-hf-home", "RV2-9", "XDG_CACHE_HOME is read before HF_HOME", "setup/download_models_stage1.py",
     '    return _hf_path(os.getenv("HF_HOME", os.path.join(os.getenv("XDG_CACHE_HOME", default_home), "huggingface")))',
     '    return _hf_path(os.path.join(os.getenv("XDG_CACHE_HOME"), "huggingface") if os.getenv("XDG_CACHE_HOME") '
     'else os.getenv("HF_HOME", os.path.join(default_home, "huggingface")))',
     G + "test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly / test_rv2_9_..."),
]
C = "tests/conftest.py"
guard = [
    ("K4-m-guard-hook-not-installed", "DK-1", "the audit hook is never installed", "    sys.addaudithook(_audit)\n", "    pass\n"),
    ("K4-m-guard-hook-any-subprocess", "DK-1", "the hook lets every subprocess.Popen through",
     "            if program_allowed(args[0]):", "            if True:"),
    ("K4-m-guard-hook-by-base-name", "DK-2", "the hook allows a program by base name, not by exact path",
     "    return prog in ALLOWED and os.path.basename(prog) not in NEVER\n",
     "    return os.path.basename(prog) in {os.path.basename(p) for p in ALLOWED} and os.path.basename(prog) not in NEVER\n"),
    ("K4-m-guard-hook-no-os-system", "DK-1", "os.system is not audited", '"os.system": "process", ', ""),
    ("K4-m-guard-hook-no-os-exec", "DK-1", "os.exec* is not audited", '"os.exec": "process", ', ""),
    ("K4-m-guard-hook-no-posix-spawn", "DK-1", "os.posix_spawn is not audited", '"os.posix_spawn": "process",', ""),
    ("K4-m-guard-hook-no-os-spawn", "DK-1", "os.spawn* is not audited", '"os.spawn": "process", ', ""),
    ("K4-m-guard-hook-no-fork", "DK-1", "os.fork is not audited", '"os.fork": "process", ', ""),
    ("K4-m-guard-hook-no-forkpty", "DK-1", "os.forkpty is not audited", '"os.forkpty": "process",', ""),
    ("K4-m-guard-hook-socket-any-address", "DK-1", "the hook lets a socket call to any address through",
     "        if detail is not None:\n            _refuse_hook(event, detail)\n",
     "        if False:\n            _refuse_hook(event, detail)\n"),
    ("K4-m-guard-hook-no-connect", "DK-1", "socket.connect is not audited", '"socket.connect": "socket", ', ""),
    ("K4-m-guard-hook-no-sendto", "DK-1", "socket.sendto is not audited", '"socket.sendto": "socket", ', ""),
    ("K4-m-guard-hook-no-sendmsg", "DK-1", "socket.sendmsg is not audited", '"socket.sendmsg": "socket",', ""),
    ("K4-m-guard-loopback-substring", "DK-1", "any host name holding 'localhost' counts as loopback",
     '    if host.lower() == "localhost":', '    if "localhost" in host.lower():'),
    ("K4-m-guard-loopback-any-ip", "DK-1", "any IP address counts as loopback",
     '        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback\n',
     '        return ipaddress.ip_address(host.split("%", 1)[0]) is not None\n'),
    ("K4-m-guard-hook-no-getaddrinfo", "DK-1", "getaddrinfo is not audited", '"socket.getaddrinfo": "lookup", ', ""),
    ("K4-m-guard-hook-no-gethostbyname", "DK-1", "gethostbyname(_ex) is not audited", '"socket.gethostbyname": "lookup", ', ""),
    ("K4-m-guard-hook-no-gethostbyaddr", "DK-1", "gethostbyaddr is not audited", '"socket.gethostbyaddr": "lookup",', ""),
    ("K4-m-guard-hook-no-getnameinfo", "DK-1", "getnameinfo is not audited", '"socket.getnameinfo": "lookup", ', ""),
    ("K4-m-guard-hook-no-urllib", "DK-1", "urllib opens are not audited", '"urllib.Request": "urllib", ', ""),
    ("K4-m-guard-hook-no-http-client", "DK-1", "http.client's connect is not audited", ', "http.client.connect": "http"}', "}"),
    ("K4-m-guard-no-fork-exec-refusal", "DK-1", "multiprocessing's fork_exec is not replaced",
     "    _posixsubprocess.fork_exec = _fork_exec_refused\n", "    pass\n"),
    ("K4-m-guard-no-socket-wrappers", "DK-1", "socket.socket's methods are not wrapped process-wide",
     "        setattr(socket.socket, name, _checked_socket_method(name, getattr(_socket.socket, name)))\n", "        pass\n"),
    ("K4-m-guard-socket-wrapper-any-address", "DK-1", "the process-wide socket wrapper lets any address through",
     '        if detail is not None:\n            _refuse_hook(f"socket {name} (before any name resolution)", detail)\n',
     '        if False:\n            _refuse_hook(f"socket {name} (before any name resolution)", detail)\n'),
    ("K4-m-guard-flag-not-cleared", "DK-1", "the flag (ALLOWED) outlives the test that set it",
     "        allowed.clear()                                # the flag never outlives the test that set it\n", "        pass\n"),
    ("K4-m-guard-fixture-executable-unchecked", "RV2-7", "the fixture ignores Popen's executable=",
     "        programs = [prog] + ([os.fsdecode(executable)] if executable is not None else [])\n", "        programs = [prog]\n"),
    ("K4-m-guard-fixture-by-base-name", "DK-2", "the fixture allows a program by base name, not by exact path",
     "        if all(p in allowed and os.path.basename(p) not in NEVER for p in programs):",
     "        if all(os.path.basename(p) in {os.path.basename(x) for x in allowed} and os.path.basename(p) not in NEVER "
     "for p in programs):"),
    ("K4-m-guard-fixture-any-under-local", "RV2-7", "under local_processes the fixture allows any program not in NEVER",
     "        if all(p in allowed and os.path.basename(p) not in NEVER for p in programs):",
     "        if all((bool(allowed) or p in allowed) and os.path.basename(p) not in NEVER for p in programs):"),
    ("K4-m-guard-fixture-no-getnameinfo", "RV2-7", "the fixture does not replace getnameinfo",
     '    monkeypatch.setattr(socket, "getnameinfo", nameinfo)\n', "    pass\n"),
    ("K4-m-guard-fixture-sendto-inet-only", "RV2-7", "the fixture's datagram refusal covers AF_INET only",
     "            if self.family in (socket.AF_INET, socket.AF_INET6):\n                _refuse(f\"socket {_name}\"",
     "            if self.family in (socket.AF_INET,):\n                _refuse(f\"socket {_name}\""),
    ("K4-m-guard-fixture-no-connect", "RV2-6", "the fixture does not replace socket.connect",
     '    monkeypatch.setattr(socket.socket, "connect", lambda self, address: _refuse("socket connect", repr(address)[:80]))\n', ""),
    ("K4-m-guard-fixture-no-gethostbyname", "RV2-6", "the fixture does not replace gethostbyname",
     '    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):\n',
     '    for name in ("getaddrinfo", "gethostbyname_ex", "gethostbyaddr"):\n'),
    ("K4-m-guard-fixture-no-opener", "RV2-6", "the fixture does not replace OpenerDirector.open",
     '    monkeypatch.setattr(urllib.request.OpenerDirector, "open",\n', '    (lambda *a: None)(urllib.request.OpenerDirector, "open",\n'),
    ("K4-m-guard-fixture-no-create-connection", "RV2-6", "the fixture does not replace socket.create_connection",
     '    monkeypatch.setattr(socket, "create_connection", lambda address',
     '    (lambda *a: None)(socket, "create_connection", lambda address'),
]


def check(entry):
    text = (KIT / entry["file"]).read_text()
    n = text.count(entry["find"])
    assert n == 1, (entry["id"], n)
    assert entry["replace"] != entry["find"]


out = {}
for spec_name, items, form in (("mutation_spec_rules_78b.json", rules, "rules"),
                               ("mutation_spec_runner_78b.json", runner, "runner"),
                               ("mutation_spec_gated_78b.json", gated, "gated"),
                               ("mutation_spec_gated_78b.json", guard, "guard")):
    path = KIT / "tests" / spec_name
    spec = json.loads(path.read_text())
    ids = {m["id"] for m in spec["mutants"]}
    for item in items:
        if form == "rules":
            mid, part, desc, file, find, repl = item
            entry = {"id": mid, "part": f"K4a ({part})", "describes": desc, "file": file, "find": find, "replace": repl}
        elif form == "guard":
            mid, part, desc, find, repl = item
            entry = {"id": mid, "part": f"K4a ({part}; conftest.py)", "describes": desc, "file": C, "find": find,
                     "replace": repl, "killed_by": "tests/test_pp10_process_wide.py or tests/test_pp10_guard.py"}
        else:
            mid, part, desc, file, find, repl, killed = item
            entry = {"id": mid, "part": f"K4a ({part})", "describes": desc, "file": file, "find": find, "replace": repl,
                     "killed_by": killed}
        assert mid not in ids, mid
        check(entry)
        spec["mutants"].append(entry)
        ids.add(mid)
    if form in ("rules", "runner", "guard"):
        spec["note"] = spec["note"].rstrip() + (
            " K4a (6 Nov) added the K4-m-* mutants: " + {
                "rules": "PP16's X_ONLY_KINDS (engine_allowed checks it first), DK-3's kind sets in the kit's "
                         "stage1_rules.py, PP14's idle-storage pods and lines.",
                "runner": "RV2-8, the runner's pre-job token check through download_models_stage1.no_token_left().",
                "guard": "RV2-1 (TLS verification), RV2-2 (no token fragment), RV2-3 (every redirect code), RV2-4, "
                         "RV2-5, RV2-9 (the D6 paths by hand), and conftest.py's process-wide layer and fixture (DK-1, "
                         "DK-2, RV2-6, RV2-7). The runner now also runs tests/test_pp10_guard.py and "
                         "tests/test_pp10_process_wide.py and refuses a Python without huggingface_hub; run the whole "
                         "spec under sandbox-exec with outbound IP denied (RV2-6)."}[form])
    path.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
    out[spec_name] = len(spec["mutants"])
print(out)
