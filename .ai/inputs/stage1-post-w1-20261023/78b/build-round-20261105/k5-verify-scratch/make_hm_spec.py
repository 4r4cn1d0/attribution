"""The K5 re-verifier's own hand mutants (K5v-*), one or more per item of round 5. Writes the spec and checks that each
find text occurs exactly once in its file. Usage: PY -B -I make_hm_spec.py KIT_DIR OUT.json"""
import json
import pathlib
import sys

kit, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
M = []


def mut(mid, item, file, describes, find, replace, expect):
    M.append({"id": mid, "item": item, "file": file, "describes": describes, "find": find, "replace": replace,
              "expect": expect})


JR = "setup/job_runner_stage1.py"
# ---- K4bcr-D1: c0's expected fingerprint from the packed source unit
mut("K5v-D1a-reads-q", "D1", JR, "c0_fingerprint reads the q checkpoint's adapter fingerprint, not e1's",
    '    e1 = points.get("e1") if isinstance(points.get("e1"), dict) else {}\n',
    '    e1 = points.get("q") if isinstance(points.get("q"), dict) else {}\n', "killed")
mut("K5v-D1b-fallback-on-refusal", "D1", JR, "a refusal of c0_fingerprint falls back to the plan's value",
    "        expect = c0_fingerprint(root, ins[C0_SOURCE_INPUT], job, index)   # K5: from the packed source unit\n",
    "        try:\n            expect = c0_fingerprint(root, ins[C0_SOURCE_INPUT], job, index)\n"
    "        except Unrunnable:\n            expect = job[\"expect_fingerprint\"]\n", "killed")
mut("K5v-D1c-link-accepted", "D1", JR, "c0_fingerprint accepts a symbolic link (the hash is still checked)",
    "    if not path.is_file() or path.is_symlink() or sha(path) != pin:\n",
    "    if not path.is_file() or sha(path) != pin:\n", "survive (equivalent in effect: the bytes are pinned)")
# ---- K4bcr-D2: HM6, HM7, HM13
mut("K5v-HM6-walk-follows-folder-links", "D2", JR, "hashed_outputs walks with followlinks=True (files under a linked folder hashed)",
    "            for f in sorted(base.rglob(\"*\")):\n                if f.is_file() and not f.is_symlink():\n"
    "                    out[str(f.relative_to(root))] = sha(f)\n",
    "            for d, _, names in os.walk(base, followlinks=True):\n"
    "                for f in sorted(pathlib.Path(d) / n for n in names):\n"
    "                    if f.is_file() and not f.is_symlink():\n"
    "                        out[str(f.relative_to(root))] = sha(f)\n", "killed")
mut("K5v-HM7-family-check-on-Y-only", "D2", "plan_tool.py", "the scorer release checks the receipt's family on engine Y only",
    "        if rec.get(\"family\") not in (None, family):\n            fail(f\"{name}: the packed stage1-{h['engine']} is",
    "        if rec.get(\"family\") not in (None, family) and h[\"engine\"] == \"Y\":\n"
    "            fail(f\"{name}: the packed stage1-{h['engine']} is", "killed")
mut("K5v-HM13-oext-kinds-exempt", "D2", JR, "the no-output crash skips the O-ext kinds (o_only)",
    "    if not record[\"outputs\"] and kind not in SC_UNIT_KINDS:\n",
    "    if not record[\"outputs\"] and kind not in SC_UNIT_KINDS and kind not in rules.OEXT_KINDS:\n", "killed")
# ---- K4bcr-D3: S1-S6
mut("K5v-R8-seed-pins-swapped", "D3", "stage1_rules.py", "the side-unit pins of seeds 1101 and 1102 are swapped",
    "table[SIDE_COMPLETE.format(seed=seed)] = A0_UNITS[seed][\"complete_sha256\"]",
    "table[SIDE_COMPLETE.format(seed=seed)] = A0_UNITS[{1101: 1102, 1102: 1101}.get(seed, seed)][\"complete_sha256\"]",
    "killed")
mut("K5v-R13-a1-pass-anchor-pin-dropped", "D3", "rules_78b.py", "a1_pass no longer needs ANCHOR_BANK (so no binding)",
    '    "a1_pass": ("RECIPE_S", "ANCHOR_BANK", "RETRAIN_UNIT"),\n',
    '    "a1_pass": ("RECIPE_S", "RETRAIN_UNIT"),\n', "killed")
mut("K5v-R17-backup-skips-a1-pass", "D3", "backup_records_stage1.py", "the backup does not check a1_pass's recorded outputs",
    "scorer_unit = plan[\"hosts\"][host].get(\"block\") == \"sc\" and job.get(\"kind\") not in rules.UNITLESS_KINDS",
    "scorer_unit = plan[\"hosts\"][host].get(\"block\") == \"sc\" and job.get(\"kind\") not in rules.UNITLESS_KINDS "
    "and job.get(\"kind\") != \"a1_pass\"", "killed")
mut("K5v-R6-none-none-equal", "D3", JR, "acceptance: a field missing on both sides is equal",
    "\"equal\": rules.hex64(src) is not None and src == got}",
    "\"equal\": (src is None and got is None) or (rules.hex64(src) is not None and src == got)}", "killed")
mut("K5v-R7-missing-defaults-to-side", "D3", JR, "acceptance: a field the regenerated unit omits takes the side's value",
    "source, got = listed[key], (regen_points.get(point) or {}).get(key)",
    "source, got = listed[key], (regen_points.get(point) or {}).get(key, listed[key])", "killed")
mut("K5v-R21-no-e1-checkpoint-accepted", "D3", JR,
    "acceptance: the e1 adapter check runs only when the side lists an e1 checkpoint",
    "if rules.hex64((side_points.get(\"e1\") or {}).get(\"adapter_fingerprint\")) is None:",
    "if \"e1\" in side_points and rules.hex64((side_points.get(\"e1\") or {}).get(\"adapter_fingerprint\")) is None:",
    "unknown")
mut("K5v-R9-any-LS-reason", "D3", "plan_tool.py", "record-done accepts any LS-* reason for acceptance false",
    "(acc is False and r.get(\"reason\") != \"LS-04\") or \\",
    "(acc is False and not str(r.get(\"reason\")).startswith(\"LS-\")) or \\", "killed")
# ---- R1: the process-wide wrapper and socket kinds
mut("K5v-G1-wrapper-skips-explicit-proto", "R1", "tests/conftest.py",
    "the wrapper lets a socket with a nonzero proto (e.g. IPPROTO_UDP given explicitly) through to C",
    "    def call(self, *args, **kwargs):\n        if name in (\"connect\", \"connect_ex\"):\n",
    "    def call(self, *args, **kwargs):\n        if getattr(self, \"proto\", 0):\n"
    "            return real(self, *args, **kwargs)\n        if name in (\"connect\", \"connect_ex\"):\n", "unknown")
mut("K5v-G1-wrapper-skips-v6-dgram", "R1", "tests/conftest.py", "the wrapper lets IPv6 datagram sockets through to C",
    "    def call(self, *args, **kwargs):\n        if name in (\"connect\", \"connect_ex\"):\n",
    "    def call(self, *args, **kwargs):\n"
    "        if self.family == socket.AF_INET6 and getattr(self, \"type\", None) == socket.SOCK_DGRAM:\n"
    "            return real(self, *args, **kwargs)\n        if name in (\"connect\", \"connect_ex\"):\n", "killed")
# ---- R2: the hook in other thread kinds
mut("K5v-G2-hook-default-named-threads-free", "R2", "tests/conftest.py",
    "the hook ignores threads with a default name (Thread-N: any library thread started without a name)",
    "    if event not in _AUDITED:\n        return\n    kind = _AUDITED[event]\n",
    "    if event not in _AUDITED or __import__(\"threading\").current_thread().name.startswith(\"Thread-\"):\n"
    "        return\n    kind = _AUDITED[event]\n", "unknown")
mut("K5v-G2-hook-dummy-threads-free", "R2", "tests/conftest.py",
    "the hook ignores threads not started by threading (_thread.start_new_thread: a _DummyThread)",
    "    if event not in _AUDITED:\n        return\n    kind = _AUDITED[event]\n",
    "    if event not in _AUDITED or isinstance(__import__(\"threading\").current_thread(), "
    "__import__(\"threading\")._DummyThread):\n        return\n    kind = _AUDITED[event]\n", "unknown")
# ---- R3: http_get's TLS and its redirect path
mut("K5v-G3-redirect-keeps-token", "R3", "launch.py",
    "SameHostAuthRedirect's http_error_30x calls the PARENT's redirect_request (the header is kept on a real redirect)",
    "    def redirect_request(self, req, fp, code, msg, headers, newurl):\n"
    "        new = super().redirect_request(req, fp, code, msg, headers, newurl)\n",
    "    def http_error_302(self, req, fp, code, msg, headers):\n"
    "        newurl = urllib.parse.urljoin(req.full_url, headers.get(\"location\") or headers.get(\"uri\") or \"\")\n"
    "        new = urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)\n"
    "        return None if new is None else self.parent.open(new, timeout=req.timeout)\n\n"
    "    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302\n\n"
    "    def redirect_request(self, req, fp, code, msg, headers, newurl):\n"
    "        new = super().redirect_request(req, fp, code, msg, headers, newurl)\n", "unknown")
mut("K5v-G3-https-request-moves-host", "R3", "launch.py",
    "SameHostAuthRedirect's https_request sends the request to another host (the scheme stays https)",
    "    def redirect_request(self, req, fp, code, msg, headers, newurl):\n"
    "        new = super().redirect_request(req, fp, code, msg, headers, newurl)\n",
    "    def https_request(self, req):\n        req.host = \"huggingface.co.example.net\"\n        return req\n\n"
    "    def redirect_request(self, req, fp, code, msg, headers, newurl):\n"
    "        new = super().redirect_request(req, fp, code, msg, headers, newurl)\n", "killed")
# ---- R4: the pack's scan
mut("K5v-R4-scan-reads-head-only", "R4", "secret_scan.py", "scan_paths reads only each file's first 2 KiB",
    "        text = pathlib.Path(path).read_bytes().decode(\"utf-8\", \"ignore\")\n",
    "        text = pathlib.Path(path).read_bytes()[:2048].decode(\"utf-8\", \"ignore\")\n", "unknown")
mut("K5v-R4-bundle-scan-after-first-write", "R4", "pack_setup.py",
    "the bundle's scan runs after the packed folder and probe.json are written",
    "    refuse_secrets(files, {**payload, \"probe.json\": probe_json, rules.KIT_FAMILY_FILE: family_json}, DATA_PREFIXES)\n"
    "    out.mkdir(parents=True, exist_ok=False)\n    (out / \"probe.json\").write_bytes(probe_json)\n",
    "    out.mkdir(parents=True, exist_ok=False)\n    (out / \"probe.json\").write_bytes(probe_json)\n"
    "    refuse_secrets(files, {**payload, \"probe.json\": probe_json, rules.KIT_FAMILY_FILE: family_json}, DATA_PREFIXES)\n",
    "killed")
mut("K5v-R4-refusal-quotes-the-match", "R4", "pack_setup.py", "the bundle refusal quotes the first matched text",
    "        raise SystemExit(f\"a secret pattern is in a packed file: {[(pathlib.Path(n).name, p) for n, p in hits][:10]}\")\n",
    "        quoted = [secret_scan.PATTERNS[p].search(pathlib.Path(n).read_bytes().decode('utf-8', 'ignore')).group(0)\n"
    "                  for n, p in hits if pathlib.Path(n).is_absolute() and pathlib.Path(n).is_file()][:1]\n"
    "        raise SystemExit(f\"a secret pattern is in a packed file: {[(pathlib.Path(n).name, p) for n, p in hits][:10]} {quoted}\")\n",
    "killed")
# ---- R5: the steps' environment
mut("K5v-R5-drops-one-token-name", "R5", JR, "the runner's job env drops HF_TOKEN only (HUGGING_FACE_HUB_TOKEN kept)",
    "    env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}\n",
    "    env = {k: v for k, v in os.environ.items() if k != \"HF_TOKEN\"}\n", "killed")
mut("K5v-R5-run-job-verify-whole-env", "R5", JR, "run_job's engine verify gets the whole os.environ",
    "    check = subprocess.run([*ENGINE, \"verify\", \"--run\", unit, \"--prepared\", PREPARED], env=env, cwd=root,\n"
    "                           capture_output=True, text=True)\n    record.update(unit=unit,",
    "    check = subprocess.run([*ENGINE, \"verify\", \"--run\", unit, \"--prepared\", PREPARED], env=dict(os.environ), cwd=root,\n"
    "                           capture_output=True, text=True)\n    record.update(unit=unit,", "killed")
mut("K5v-R5-oext-step-online", "R5", JR, "run_sc_job's O-ext step gets HF_HUB_OFFLINE=0",
    "        done = subprocess.run([\"python3\", \"process_receipt.py\", \"--out\", name, \"--\", *argv], env=env, cwd=root)\n"
    "        steps.append({\"name\": name, \"seconds\": round(time.monotonic() - start, 3), \"exit\": done.returncode})\n"
    "        exits[name] = done.returncode\n        s4_few",
    "        done = subprocess.run([\"python3\", \"process_receipt.py\", \"--out\", name, \"--\", *argv],\n"
    "                              env={**env, \"HF_HUB_OFFLINE\": \"0\"} if name.endswith(\"-oext\") else env, cwd=root)\n"
    "        steps.append({\"name\": name, \"seconds\": round(time.monotonic() - start, 3), \"exit\": done.returncode})\n"
    "        exits[name] = done.returncode\n        s4_few", "killed")

bad = []
for m in M:
    text = (kit / m["file"]).read_text(encoding="utf-8")
    if text.count(m["find"]) != 1:
        bad.append((m["id"], text.count(m["find"])))
out.write_text(json.dumps({"kind": "K5 re-verifier hand mutants", "mutants": M}, indent=1) + "\n")
print({"mutants": len(M), "bad_find_texts": bad})
