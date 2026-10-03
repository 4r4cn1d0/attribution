"""Offline checks for tools/export_anonymous_artifact.py: pinned-inventory copying, symlink and
destination refusals, identity/credential refusals and diagnostics that never print a match,
byte-identical code and a real export of this checkout (stage A, stage B and the calibration
slice) against a hand-written inventory.
Standard library only (runs under pytest or ``python tests/test_anonymous_artifact.py``); no
Git, network or subprocess. Fake credentials are assembled at run time so no credential-shaped
literal lives here; the extra identifier is made up."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("export_anonymous_artifact",
                                               ROOT / "tools" / "export_anonymous_artifact.py")
ex = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = ex
_spec.loader.exec_module(ex)

SAFETY, MINIMAL = "experiments/safety_selection", "experiments/minimal_safety"
POLICY = "experiments/safety_decision_policy"
PROTOCOL = "research/experiments/safety-selection-v2-protocol.md"
DECISION = "research/experiments/safety-selection-v2-decision-protocol.md"
TEMPLATE = "templates/anonymous-artifact/README.md"

# The reviewed export of this checkout, written out by hand and never discovered by globbing:
# 88 package files (59 of stage A and the calibration slice, 29 of stage B), the two protocols,
# the root README and the manifest. Exporting another file, or dropping one, is a deliberate
# review that changes SPEC in the tool and this list together.
INVENTORY = {f"{folder}/{name}" for folder, names in {
    SAFETY: ("README.md", "__init__.py", "__main__.py", "assets.py", "attribution.py", "common.py",
             "config.py", "engine.py", "jobs.py", "ledger.py", "loaders.py", "planning.py", "prepare.py",
             "runner.py", "scoring.py", "selector_view.py", "sources.py", "stream.py", "textproc.py",
             "verify.py"),
    f"{SAFETY}/configs": ("study-v2-data-expanded-arc.json", "study-v2-data.json",
                          "study-v2-primary-20261002.json", "study-v2-recipe-calibration-cap2048.json",
                          "study-v2-recipe-calibration-micro2.json", "study-v2-recipe-calibration-toxicbert.json",
                          "study-v2-recipe-calibration.json"),
    f"{SAFETY}/tests": ("conftest.py", "ss_fixtures.py", "test_ss_attribution.py", "test_ss_config_jobs.py",
                        "test_ss_engine.py", "test_ss_integration_contracts.py", "test_ss_prepare.py",
                        "test_ss_runner.py", "test_ss_selector_view.py", "test_ss_stream.py", "test_ss_text.py"),
    MINIMAL: ("README.md", "__init__.py", "__main__.py", "common.py", "data.py", "ledger.py", "model.py",
              "plan.py", "report.py", "requirements.lock", "run.py", "text.py"),
    f"{MINIMAL}/configs": ("calibration-cuda.json", "calibration.json"),
    f"{MINIMAL}/tests": ("conftest.py", "test_ms_data.py", "test_ms_model.py", "test_ms_plan.py",
                         "test_ms_report.py", "test_ms_run.py", "test_ms_text.py"),
    POLICY: ("README.md", "__init__.py", "__main__.py", "analysis.py", "backend.py", "common.py", "config.py",
             "controller.py", "costs.py", "development.py", "features.py", "outcomes.py", "policy.py", "ridge.py",
             "synthetic.py", "tfidf.py"),
    f"{POLICY}/configs": ("example-dev-fit-spec.json", "example-engineering.json"),
    f"{POLICY}/tests": ("conftest.py", "test_dp_analysis.py", "test_dp_config.py", "test_dp_controller.py",
                        "test_dp_costs.py", "test_dp_engine.py", "test_dp_features.py", "test_dp_outcomes.py",
                        "test_dp_policy.py", "test_dp_ridge.py", "test_dp_tfidf.py"),
}.items() for name in names} | {PROTOCOL, DECISION, "README.md", ex.MANIFEST}
EDITED = {f"{SAFETY}/README.md", f"{MINIMAL}/README.md", f"{POLICY}/README.md", PROTOCOL, DECISION}

# A miniature project: pinned files, one documented edit, and files never exported.
MINI_SPEC = {
    "dirs": {"pkg": ("README.md", "__init__.py", "core.py", "requirements.lock"), "pkg/configs": ("c.json",),
             "pkg/tests": ("test_core.py",)},
    "files": ("research/protocol.md",),
    "templates": {"README.md": "templates/README.md"},
    "edits": {"pkg/README.md": (("plan-link", "text", "[plan](../research/PLAN.md)",
                                 "[overview](../README.md)", "planning link replaced"),)},
}
ALLOWED = {
    "pkg/__init__.py": b'"""Fixture package."""\n',
    "pkg/core.py": b"value = 1\r\nraw = b'\xff\xfe'\n",  # CRLF and non-UTF-8 bytes must survive
    "pkg/README.md": b"# Pkg\n\nSee [plan](../research/PLAN.md) and [protocol](../research/protocol.md).\n",
    "pkg/requirements.lock": b"torch==2.8.0\n",
    "pkg/configs/c.json": b'{"model": "Qwen/Qwen2.5-0.5B-Instruct", "map": "/remote/runs"}\n',
    "pkg/tests/test_core.py": b"def test_core():\n    assert True\n",
    "research/protocol.md": b"# Protocol\n\nOverview: [README](../README.md).\n",
    "templates/README.md": b"# Review copy\n\n[Package](pkg/README.md); [manifest](ARTIFACT_MANIFEST.json).\n",
}
NEVER = {
    "pkg/__pycache__/core.cpython-311.pyc": b"\x00",
    "pkg/.DS_Store": b"\x00",
    "pkg/.hidden.py": b"x = 2\n",
    "pkg/extra.py": b"x = 3\n",                  # new files that a *.py or *.json pattern would
    "pkg/configs/internal-costs.json": b"{}\n",  # have copied; they are not pinned
    "pkg/notes.txt": b"private notes\n",
    "pkg/runs/summary.json": b"{}\n",
    "pkg/tests/rows.jsonl": b"{}\n",
    "research/PLAN.md": b"private plan\n",
    "research/review.md": b"reviewer correspondence\n",
    ".ai/HANDOFF.md": b"workflow\n",
    "AGENTS.md": b"workflow\n",
    "CLAUDE.md": b"workflow\n",
    "writing/draft.md": b"draft\n",
    ".git/config": b"[core]\n",
    ".env": b"KEY=value\n",
}
EXPORTED = {"README.md", ex.MANIFEST} | set(ALLOWED) - {"templates/README.md"}

# (rule, leaked text), assembled at run time.
LEAKS = (
    ("owner-identifier", lambda: ex.OWNER_HANDLES[0].title()),
    ("owner-identifier", lambda: "https://github.com/" + ex.OWNER_HANDLES[1] + "/repo"),
    ("home-directory-path", lambda: "/" + "Users/someone/project"),
    ("home-directory-path", lambda: "/" + "home/someone/.cache"),
    ("email-address", lambda: "someone" + "@" + "example.org"),
    ("credential-in-url", lambda: "https://user:" + "pa55word" + "@example.org/repo.git"),
    ("private-key-block", lambda: "-----BEGIN " + "OPENSSH PRIVATE KEY-----"),
    ("github-token", lambda: "gh" + "p_" + "aB3" * 12),
    ("github-token", lambda: "github" + "_pat_" + "x1Y2" * 6),
    ("huggingface-token", lambda: "hf" + "_" + "Qw3" * 12),
    ("sk-api-key", lambda: "sk" + "-proj-" + "Zz9" * 12),
    ("aws-access-key-id", lambda: "AK" + "IA" + "Z7" * 8),
    ("google-api-key", lambda: "AI" + "za" + "b" * 35),
    ("slack-token", lambda: "xo" + "xb-" + "1234567890-abcdef"),
    ("runpod-api-key", lambda: "rp" + "a_" + "K9" * 12),
)
# (file a leak is planted in, the export path its finding names); cycled over LEAKS.
TARGETS = (("pkg/core.py", "pkg/core.py"), ("pkg/configs/c.json", "pkg/configs/c.json"),
           ("pkg/README.md", "pkg/README.md"), ("templates/README.md", "README.md"),
           ("research/protocol.md", "research/protocol.md"),
           ("pkg/tests/test_core.py", "pkg/tests/test_core.py"))

# A made-up extra identifier for the redaction tests (the owner handles come from the tool), and
# how a path component "<handle>-<term>" prints once redacted.
TERM = "Fake Lab Name"
SHOWN = "<owner-identifier>-<identifier-1>"


def build(root: Path, files: dict[str, bytes]) -> Path:
    for rel, data in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
    return root


def pinned(spec: dict, folder: str, *names: str) -> dict:
    """``spec`` with ``names`` also pinned in ``folder``."""
    return {**spec, "dirs": {**spec["dirs"], folder: spec["dirs"][folder] + names}}


def tree(folder: Path) -> set[str]:
    """Relative paths of every file under ``folder``; any symlink fails."""
    found = set()
    for here, dirs, names in os.walk(folder):
        for name in dirs + names:
            if os.path.islink(os.path.join(here, name)):
                raise AssertionError(f"symlink in the export: {name}")
        found |= {Path(here, name).relative_to(folder).as_posix() for name in names}
    return found


def link(test: unittest.TestCase, target: Path, path: Path) -> None:
    try:
        os.symlink(target, path)
    except (OSError, NotImplementedError) as exc:
        test.skipTest(f"symlinks unavailable here: {exc}")


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = ex.main(argv)
        except SystemExit as exc:  # argument errors
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class MiniatureProjectTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.src = build(self.tmp / "src", {**ALLOWED, **NEVER})
        self.dest = self.tmp / "export"

    def tearDown(self):
        self._tmp.cleanup()

    def refused(self, src: Path | None = None, spec: dict = MINI_SPEC, **kwargs) -> list[str]:
        """Problems of a refused export, after checking that nothing was created."""
        with self.assertRaises(ex.ExportError) as caught:
            ex.export(src or self.src, self.dest, spec=spec, **kwargs)
        self.assertFalse(os.path.lexists(self.dest))
        return caught.exception.problems

    def assertHidden(self, text: str, *terms: str) -> None:
        for term in terms:
            self.assertNotIn(term.lower(), text.lower())

    def test_copies_only_allowlisted_files_byte_for_byte_and_lists_skips(self):
        summary = ex.export(self.src, self.dest, spec=MINI_SPEC)
        self.assertEqual(tree(self.dest), EXPORTED)
        for rel in ("pkg/__init__.py", "pkg/core.py", "pkg/requirements.lock", "pkg/configs/c.json",
                    "pkg/tests/test_core.py", "research/protocol.md"):
            self.assertEqual((self.dest / rel).read_bytes(), ALLOWED[rel], rel)
        self.assertEqual((self.dest / "README.md").read_bytes(), ALLOWED["templates/README.md"])
        self.assertEqual((self.dest / "pkg/README.md").read_bytes(),
                         b"# Pkg\n\nSee [overview](../README.md) and [protocol](../research/protocol.md).\n")
        self.assertEqual(summary["skipped"], ["pkg/.DS_Store", "pkg/.hidden.py", "pkg/__pycache__/", "pkg/extra.py",
                                              "pkg/notes.txt", "pkg/runs/", "pkg/configs/internal-costs.json",
                                              "pkg/tests/rows.jsonl"])
        self.assertEqual((summary["edited"], summary["written"]), (["pkg/README.md"], ["README.md", ex.MANIFEST]))

    def test_files_outside_the_allowlist_are_not_copied_even_when_they_hold_secrets(self):
        token = "gh" + "p_" + "aB3" * 12
        for rel in ("research/PLAN.md", ".env", "AGENTS.md", "pkg/notes.txt", "pkg/runs/summary.json",
                    "pkg/extra.py", "pkg/configs/internal-costs.json"):
            (self.src / rel).write_bytes(token.encode() + b"\n")
        ex.export(self.src, self.dest, spec=MINI_SPEC)
        self.assertEqual(tree(self.dest), EXPORTED)
        for rel in EXPORTED:
            self.assertNotIn(token.encode(), (self.dest / rel).read_bytes(), rel)

    def test_manifest_records_relative_paths_hashes_and_edits_deterministically(self):
        ex.export(self.src, self.dest, spec=MINI_SPEC)
        raw = (self.dest / ex.MANIFEST).read_bytes()
        listed = {entry["path"]: entry for entry in json.loads(raw)["files"]}
        self.assertEqual(set(listed), EXPORTED - {ex.MANIFEST})
        for rel, entry in listed.items():
            self.assertEqual(entry["sha256"], hashlib.sha256((self.dest / rel).read_bytes()).hexdigest(), rel)
        self.assertEqual({rel: entry["derivation"] for rel, entry in listed.items()}, {
            **{rel: "verbatim" for rel in EXPORTED - {ex.MANIFEST, "README.md", "pkg/README.md"}},
            "pkg/README.md": "edited", "README.md": "written for this package"})
        self.assertEqual(listed["pkg/README.md"]["edits"], [{"id": "plan-link", "change": "planning link replaced"}])
        for private in (self._tmp.name, str(self.tmp), hashlib.sha256(ALLOWED["pkg/README.md"]).hexdigest()):
            self.assertNotIn(private.encode(), raw)
        again = self.tmp / "export-again"
        ex.export(self.src, again, spec=MINI_SPEC)
        self.assertEqual((again / ex.MANIFEST).read_bytes(), raw)

    def test_identity_and_credentials_refuse_naming_file_line_and_rule_only(self):
        for number, (rule, make) in enumerate(LEAKS):
            leak = make()
            planted, shown = TARGETS[number % len(TARGETS)]
            with self.subTest(rule=rule, planted=planted):
                src = build(self.tmp / f"src-{number}", {**ALLOWED, **NEVER})
                (src / planted).write_bytes(b"# " + leak.encode() + b"\n" + ALLOWED[planted])
                problems = self.refused(src)
                self.assertIn(f"{shown}:1: {rule}", problems)
                self.assertNotIn(leak.lower(), "\n".join(problems).lower())

    def test_path_findings_are_redacted_and_skipped_names_too(self):
        handle = ex.OWNER_HANDLES[0]
        (self.src / "pkg" / f"{handle}-notes.txt").write_bytes(b"skipped, never read\n")
        summary = ex.export(self.src, self.dest, spec=MINI_SPEC)
        self.assertIn("pkg/<owner-identifier>-notes.txt", summary["skipped"])
        self.assertNotIn(handle, json.dumps(summary).lower())
        # A pinned file named with the handle: its path is a finding, and so is the manifest line
        # that lists it (line 46), because the manifest is scanned like every exported file.
        (self.src / "pkg" / f"{handle}.py").write_bytes(b"x = 1\n")
        self.dest = self.tmp / "export-2"
        problems = self.refused(spec=pinned(MINI_SPEC, "pkg", f"{handle}.py"))
        self.assertEqual(problems, [f"{ex.MANIFEST}:46: owner-identifier",
                                    "pkg/<owner-identifier>.py: owner-identifier (in the path)"])
        self.assertNotIn(handle, "\n".join(problems).lower())

    def test_extra_identifiers_refuse_in_any_case_and_stay_unprinted(self):
        (self.src / "pkg/configs/c.json").write_bytes(b'{"lab": "Example Lab of Things"}\n')
        self.assertEqual(self.refused(identifiers=["", "EXAMPLE LAB"]), ["pkg/configs/c.json:1: identifier-2"])

    def test_destination_source_write_and_summary_paths_never_echo_known_or_extra_terms(self):
        handle = ex.OWNER_HANDLES[1]
        named = self.tmp / f"{handle}-{TERM.lower()}"
        named.mkdir()
        for source, dest, expected in ((self.src, named, "destination exists"),
                                       (self.src, named / "missing" / "export", "destination parent is not"),
                                       (named / "missing", self.dest, "source is not a folder")):
            with self.subTest(expected=expected):
                with self.assertRaises(ex.ExportError) as caught:
                    ex.export(source, dest, spec=MINI_SPEC, identifiers=[TERM])
                (problem,) = caught.exception.problems
                self.assertTrue(problem.startswith(expected) and SHOWN in problem, problem)
                self.assertHidden(problem, handle, TERM)
        failure = OSError(f"device error at {named}")  # no strerror, so the message holds the path
        with mock.patch.object(ex, "open", create=True, side_effect=failure):
            with self.assertRaises(ex.PartialExportError) as caught:
                ex.export(self.src, named / "partial", spec=MINI_SPEC, identifiers=[TERM])
        message = str(caught.exception)
        self.assertIn(f"{SHOWN}{os.sep}partial is incomplete", message)
        self.assertHidden(message, handle, TERM)
        self.assertTrue((named / "partial").is_dir() and not (named / "partial" / ex.MANIFEST).exists())
        summary = ex.export(self.src, named / "review", spec=MINI_SPEC, identifiers=[TERM])
        self.assertTrue(summary["destination"].endswith(f"{SHOWN}{os.sep}review"), summary["destination"])
        self.assertHidden(json.dumps(summary), handle, TERM)

    def test_collect_problems_never_echo_known_or_extra_terms(self):
        handle = ex.OWNER_HANDLES[0]
        link(self, self.tmp / "missing", self.src / "pkg" / f"{handle}.py")
        problems = self.refused(spec=pinned(MINI_SPEC, "pkg", f"{TERM}.py"), identifiers=[TERM])
        self.assertEqual(problems, ["pkg/<owner-identifier>.py: symlink in an allowlisted folder (never followed)",
                                    "pkg/<identifier-1>.py: required file is missing"])

    def test_overlapping_matches_are_hidden_whole(self):
        # Replacing the home path first would leave " lab name" of the extra term visible.
        self.assertEqual(ex.redact(f"/home/{TERM.lower()}/x, {TERM.upper()}", ex.rules_for(["", TERM])),
                         "<home-directory-path>/x, <identifier-2>")

    def test_benign_lookalikes_are_not_findings(self):
        (self.src / "pkg/core.py").write_bytes(
            b"from huggingface_hub import hf_hub_download, snapshot_download\n"
            b"snapshot_download(repo_id='Qwen/Qwen2.5-1.5B-Instruct', token=False)\n"
            b"REVISION = 'ad96bd4dca687d8e1d9b6fd4b9eb8dcdddb0361d'\n"
            b"ROW = 'SECRET-UNSAFE text !!!'; MAP = '/remote/runs=<archive>'\n"
            b"DRIVER = '/proc/driver/nvidia/version'; URL = 'https://huggingface.co/datasets/x'\n"
            b"y = q @ g.T; name = 'task-" + b"x" * 40 + b"'\n"
            b"@decorator\n")
        ex.export(self.src, self.dest, spec=MINI_SPEC)
        self.assertTrue((self.dest / "pkg/core.py").read_bytes().startswith(b"from huggingface_hub"))

    def test_symlinks_refuse_and_are_never_followed(self):
        outside = build(self.tmp / "outside", {"secret.py": b"# outside the source tree\n"})
        for rel, target in (("pkg/leak.py", outside / "secret.py"),             # escapes the tree
                            ("pkg/configs/same.json", self.src / "pkg/configs/c.json"),  # stays inside
                            ("pkg/linked", outside),                            # a folder
                            ("pkg/dangling.py", self.tmp / "missing")):         # points nowhere
            with self.subTest(rel=rel):
                link(self, target, self.src / rel)
                self.assertIn(f"{rel}: symlink in an allowlisted folder (never followed)", self.refused())
                (self.src / rel).unlink()

    def test_symlinked_input_folder_or_template_refuses(self):
        moved = self.tmp / "moved-tests"
        (self.src / "pkg/tests").rename(moved)
        link(self, moved, self.src / "pkg/tests")
        self.assertIn("pkg/tests: symlink on an input path (never followed)", self.refused())
        (self.src / "pkg/tests").unlink()
        moved.rename(self.src / "pkg/tests")
        template, moved = self.src / "templates/README.md", self.tmp / "README.template"
        template.rename(moved)
        link(self, moved, template)
        self.assertIn("templates/README.md: symlink on an input path (never followed)", self.refused())

    def test_destination_must_be_new_with_a_parent_and_outside_the_inputs(self):
        occupied = build(self.tmp / "occupied", {"keep.txt": b"keep"})
        empty, a_file = self.tmp / "empty", self.tmp / "a-file"
        empty.mkdir()
        a_file.write_bytes(b"file")
        for dest, expected in ((occupied, "destination exists"), (empty, "destination exists"),
                               (a_file, "destination exists"),
                               (self.src / "pkg" / "export", "destination is inside the input folder pkg"),
                               (self.src / "pkg" / "tests" / "export", "destination is inside the input folder pkg"),
                               (self.src / "templates" / "export", "destination is inside the input folder templates"),
                               (self.tmp / "no-parent" / "export", "destination parent is not an existing folder")):
            with self.subTest(dest=dest.relative_to(self.tmp).as_posix()):
                existed = os.path.lexists(dest)
                with self.assertRaises(ex.ExportError) as caught:
                    ex.export(self.src, dest, spec=MINI_SPEC)
                self.assertTrue(caught.exception.problems[0].startswith(expected), caught.exception.problems)
                self.assertEqual(os.path.lexists(dest), existed)
        self.assertEqual(((occupied / "keep.txt").read_bytes(), tree(occupied)), (b"keep", {"keep.txt"}))
        self.assertEqual((list(empty.iterdir()), a_file.read_bytes()), ([], b"file"))
        ex.export(self.src, self.dest, spec=MINI_SPEC)  # a finished export is never reused
        before = {rel: (self.dest / rel).read_bytes() for rel in tree(self.dest)}
        with self.assertRaises(ex.ExportError):
            ex.export(self.src, self.dest, spec=MINI_SPEC)
        self.assertEqual({rel: (self.dest / rel).read_bytes() for rel in tree(self.dest)}, before)

    def test_destination_symlinks_are_refused(self):
        link(self, self.tmp / "missing", self.tmp / "dangling")
        with self.assertRaises(ex.ExportError):
            ex.export(self.src, self.tmp / "dangling", spec=MINI_SPEC)
        self.assertFalse(os.path.lexists(self.tmp / "missing"))
        link(self, self.src / "pkg", self.tmp / "alias")
        with self.assertRaises(ex.ExportError) as caught:
            ex.export(self.src, self.tmp / "alias" / "export", spec=MINI_SPEC)
        self.assertEqual(caught.exception.problems, ["destination is inside the input folder pkg"])
        self.assertFalse(os.path.lexists(self.src / "pkg" / "export"))

    def test_stale_edits_and_dangling_links_refuse(self):
        readme = self.src / "pkg/README.md"
        for content, hits in ((b"# Pkg\n\nThe planning link is gone.\n", 0),
                              (ALLOWED["pkg/README.md"] + b"Again: [plan](../research/PLAN.md)\n", 2)):
            with self.subTest(hits=hits):
                readme.write_bytes(content)
                self.assertEqual(self.refused(), [f"pkg/README.md: edit 'plan-link': anchor found {hits} "
                                                  "times, expected exactly once"])
        readme.write_bytes(ALLOWED["pkg/README.md"])
        (self.src / "research/protocol.md").write_bytes(
            b"# Protocol\n\n[Review](review.md), [web](https://example.org/page), [here](#protocol),\n"
            b"`[code](not-a-link.md)` and\n\n```\n[fenced](also-not-a-link.md)\n```\n")
        self.assertEqual(self.refused(), ["research/protocol.md: dangling link -> review.md"])

    def test_line_and_section_edits(self):
        text = ("# T\n\nStatus: old\n\n## Drop\n\n```sh\n# shell comment, not a heading\n```\n\n"
                "### Sub\n\ny\n\n## Next\n\nz\n")
        edited, problems = ex.apply_edits(text, [("status", "line", "Status:", "Status: new", ""),
                                                 ("drop", "section", "## Drop", "", "")])
        self.assertEqual((edited, problems), ("# T\n\nStatus: new\n\n## Next\n\nz\n", []))
        self.assertEqual(ex.apply_edits("# T\n\nkeep\n\n## Last\n\ngone\n", [("last", "section", "## Last", "", "")]),
                         ("# T\n\nkeep\n", []))
        self.assertEqual(ex.apply_edits(text, [("bad", "section", "Status:", "", "")])[1],
                         ["edit 'bad': anchor is not a Markdown heading"])

    def test_cli_exit_codes_and_messages(self):
        token = "hf" + "_" + "Qw3" * 12
        (self.src / "pkg/core.py").write_bytes(f"TOKEN = '{token}'\n".encode())
        argv = ["--source", str(self.src), "--dest", str(self.dest)]
        with mock.patch.object(ex, "SPEC", MINI_SPEC):
            code, out, err = run_cli(argv)
            self.assertEqual(code, 2)
            self.assertIn("pkg/core.py:1: huggingface-token", err)
            self.assertNotIn(token, out + err)
            self.assertFalse(os.path.lexists(self.dest))
            (self.src / "pkg/core.py").write_bytes(ALLOWED["pkg/core.py"])
            code, out, err = run_cli(argv)
            self.assertEqual((code, err, json.loads(out)["files"]), (0, "", len(EXPORTED)))
            code, out, err = run_cli(argv)
            self.assertEqual(code, 2)
            self.assertIn("destination exists", err)

    def test_cli_never_echoes_known_or_extra_terms(self):
        handle = ex.OWNER_HANDLES[1]
        named = self.tmp / f"{handle}-{TERM.lower()}"
        named.mkdir()
        argv = ["--source", str(self.src), "--identifier", TERM, "--dest"]
        with mock.patch.object(ex, "SPEC", MINI_SPEC):
            refused = run_cli(argv + [str(named)])
            mistyped = run_cli(["--dest", str(self.dest), "--identifer", TERM])
            with mock.patch.object(ex, "export", side_effect=RuntimeError(f"loop at {named}")):
                unexpected = run_cli(argv + [str(self.dest)])
            done = run_cli(argv + [str(named / "review")])
        self.assertEqual([result[0] for result in (refused, mistyped, unexpected, done)], [2, 2, 1, 0])
        self.assertIn("destination exists and is never reused or overwritten: ", refused[2])
        self.assertIn("2 unrecognized argument(s), not printed", mistyped[2])
        self.assertIn("export failed unexpectedly (RuntimeError: loop at ", unexpected[2])
        for err in (refused[2], unexpected[2]):
            self.assertIn(SHOWN, err)
        self.assertTrue(json.loads(done[1])["destination"].endswith(f"{SHOWN}{os.sep}review"))
        self.assertFalse(os.path.lexists(self.dest))
        self.assertHidden("".join(out + err for _, out, err in (refused, mistyped, unexpected, done)), handle, TERM)


class ShippedInventoryTests(unittest.TestCase):
    """The shipped SPEC on a copy of exactly this checkout's export inputs."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        inputs = (INVENTORY - {"README.md", ex.MANIFEST}) | {TEMPLATE}
        self.src = build(self.tmp / "src", {rel: (ROOT / rel).read_bytes() for rel in inputs})
        self.dest = self.tmp / "export"

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_private_files_in_allowlisted_folders_are_skipped_and_never_exported(self):
        secret = "q7" + "Zx" * 20  # no listed shape: no rule would refuse it
        new = {f"{SAFETY}/configs/internal-costs.json": b'{"billing_key": "' + secret.encode() + b'"}\n',
               f"{MINIMAL}/costs.py": b"KEY = '" + secret.encode() + b"'\n"}
        build(self.src, new)
        summary = ex.export(self.src, self.dest)
        self.assertEqual((tree(self.dest), sorted(summary["skipped"])), (INVENTORY, sorted(new)))
        for rel in INVENTORY:
            self.assertNotIn(secret.encode(), (self.dest / rel).read_bytes(), rel)

    def test_missing_pinned_files_refuse(self):
        for package in (MINIMAL, SAFETY):
            (self.src / package / "ledger.py").unlink()
        (self.src / POLICY / "costs.py").unlink()
        (self.src / DECISION).unlink()
        with self.assertRaises(ex.ExportError) as caught:
            ex.export(self.src, self.dest)
        self.assertEqual(caught.exception.problems, [
            f"{MINIMAL}/ledger.py: required file is missing", f"{POLICY}/costs.py: required file is missing",
            f"{SAFETY}/ledger.py: required file is missing", f"{DECISION}: No such file or directory",
            f"{DECISION}: edited document is not exported"])
        self.assertFalse(os.path.lexists(self.dest))

    def test_the_recovery_tooling_is_never_read_or_exported(self):
        """``experiments/durability`` is not part of the package: no allowlisted folder, so its
        files are neither exported nor even listed as skipped, whatever they hold."""
        secret = "q7" + "Zx" * 20
        build(self.src, {"experiments/durability/admission.py": b"KEY = '" + secret.encode() + b"'\n",
                         "experiments/durability/README.md": b"# Recovery tooling\n"})
        summary = ex.export(self.src, self.dest)
        self.assertEqual((tree(self.dest), summary["skipped"]), (INVENTORY, []))
        self.assertFalse(any("durability" in folder for folder in ex.SPEC["dirs"]) or
                         any("durability" in rel for rel in (*ex.SPEC["files"], *ex.SPEC["templates"].values())))
        for rel in INVENTORY:
            self.assertNotIn(secret.encode(), (self.dest / rel).read_bytes(), rel)


class RealExportTests(unittest.TestCase):
    """Exports this checkout with the shipped SPEC. A failure means a pinned file is missing or a
    new one appeared, a source document changed under an edit, a link dangles, or an identity or
    credential pattern appeared."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dest = Path(cls._tmp.name).resolve() / "artifact"
        cls.summary = ex.export(ROOT, cls.dest)
        cls.files = tree(cls.dest)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_exports_exactly_the_reviewed_inventory(self):
        self.assertEqual(self.files, INVENTORY)
        self.assertEqual((self.summary["edited"], self.summary["written"]), (sorted(EDITED), ["README.md", ex.MANIFEST]))

    def test_no_unreviewed_file_sits_in_an_allowlisted_folder(self):
        """Only caches and hidden entries may be skipped. Anything else is new: review it, then pin
        it in SPEC and INVENTORY or move it out of the package."""
        names = {rel: rel.rstrip("/").rsplit("/", 1)[-1] for rel in self.summary["skipped"]}
        self.assertEqual([rel for rel, name in names.items() if name != "__pycache__" and not name.startswith(".")], [])

    def test_unedited_files_are_byte_identical(self):
        verbatim = INVENTORY - EDITED - {"README.md", ex.MANIFEST}
        self.assertEqual(self.summary["verbatim"], len(verbatim))
        for rel in sorted(verbatim):
            self.assertEqual((self.dest / rel).read_bytes(), (ROOT / rel).read_bytes(), rel)

    def test_local_markdown_links_resolve_inside_the_export(self):
        markdown = sorted(rel for rel in self.files if rel.endswith(".md"))
        self.assertEqual(markdown, ["README.md", "experiments/minimal_safety/README.md",
                                    "experiments/safety_decision_policy/README.md",
                                    "experiments/safety_selection/README.md", DECISION, PROTOCOL])
        for rel in markdown:
            text = (self.dest / rel).read_text(encoding="utf-8")
            checked = 0
            for target in re.findall(r"\]\(\s*<?([^)\s>]+)", text):  # independent of the tool's parser
                if re.match(r"[A-Za-z][\w+.-]*:", target) or target.startswith("#"):
                    continue
                resolved = ((self.dest / rel).parent / target.split("#")[0]).resolve()
                self.assertTrue(resolved.exists() and resolved.is_relative_to(self.dest), f"{rel} -> {target}")
                checked += 1
            self.assertGreater(checked, 0, rel)
            for internal in ("research/FOCUS.md", "EDGE_CHECKS", "minimal-safety-pilot.md",
                             "calibration-results", ".ai/"):
                self.assertNotIn(internal, text, rel)

    def test_cited_protocol_and_new_links_point_into_the_export(self):
        self.assertIn(PROTOCOL, (self.dest / "experiments/safety_selection/__init__.py").read_text())
        protocol = (self.dest / PROTOCOL).read_text(encoding="utf-8")
        self.assertIn("[README](../../README.md)", protocol)
        self.assertIn("DATE-LM Appendix D.2/Table 9", protocol)  # source citations kept
        for rel in ("experiments/safety_selection/README.md", "experiments/minimal_safety/README.md"):
            self.assertIn("the [overview](../../README.md)", (self.dest / rel).read_text(encoding="utf-8"))
        # stage B: the stage-A protocol and the stage-B README cite the decision protocol, which
        # links back to the stage-A protocol and the root README
        self.assertIn("[stage-B protocol](safety-selection-v2-decision-protocol.md)", protocol)
        self.assertIn(f"](../../{DECISION})", (self.dest / f"{POLICY}/README.md").read_text(encoding="utf-8"))
        decision = (self.dest / DECISION).read_text(encoding="utf-8")
        self.assertIn("[stage-A protocol](safety-selection-v2-protocol.md)", decision)
        self.assertIn("[README](../../README.md)", decision)
        root = (self.dest / "README.md").read_text(encoding="utf-8")
        for linked in (f"{POLICY}/README.md", DECISION, "experiments/safety_decision_policy/tests", "simulate"):
            self.assertIn(linked, root)
        self.assertNotIn("is not part of this package", root + protocol)

    def test_manifest_hashes_and_documented_edits(self):
        raw = (self.dest / ex.MANIFEST).read_text(encoding="utf-8")
        listed = {entry["path"]: entry for entry in json.loads(raw)["files"]}
        self.assertEqual(set(listed), self.files - {ex.MANIFEST})
        for rel, entry in listed.items():
            self.assertEqual(entry["sha256"], hashlib.sha256((self.dest / rel).read_bytes()).hexdigest(), rel)
        derivation = {rel: entry["derivation"] for rel, entry in listed.items()}
        edited = {rel for rel, value in derivation.items() if value == "edited"}
        self.assertEqual(edited, set(ex.EDITS))
        self.assertEqual({rel for rel, value in derivation.items() if value == "written for this package"},
                         {"README.md"})
        for rel in edited:
            self.assertEqual([edit["id"] for edit in listed[rel]["edits"]], [edit[0] for edit in ex.EDITS[rel]])
            self.assertNotIn(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), raw)
        self.assertNotIn(str(ROOT), raw)

    def test_dated_run_statements_are_removed_and_nothing_else_changes(self):
        for rel in (f"{SAFETY}/README.md", PROTOCOL):  # their edits keep the line count
            source = (ROOT / rel).read_text(encoding="utf-8").split("\n")
            exported = (self.dest / rel).read_text(encoding="utf-8").split("\n")
            anchored = [index for index, line in enumerate(source) if any(edit[2] in line for edit in ex.EDITS[rel])]
            self.assertEqual(len(exported), len(source), rel)
            self.assertEqual([index for index, (old, new) in enumerate(zip(source, exported)) if old != new],
                             anchored, rel)
        stage_a = (self.dest / f"{SAFETY}/README.md").read_text(encoding="utf-8")
        protocol = (self.dest / PROTOCOL).read_text(encoding="utf-8")
        for removed in ("Its author has run nothing", "not yet run by its author", "110 passed", "lead's run"):
            self.assertNotIn(removed, stage_a + protocol)
        self.assertIn("\nTests use\nENGINEERING FIXTURES (", stage_a)
        self.assertIn("\n## Acceptance checks implemented as tests (CPU fixtures)\n", protocol)
        self.assertIn("\n**From the first implementation:**\n", protocol)

    def test_stage_b_documents_lose_run_statements_review_rounds_and_unexported_links(self):
        """The stage-B README and decision protocol: every changed source line holds an edit
        anchor (nothing else changes), the removed passages are gone and the definitions stay."""
        import difflib

        for rel in (f"{POLICY}/README.md", DECISION):
            source = (ROOT / rel).read_text(encoding="utf-8").split("\n")
            exported = (self.dest / rel).read_text(encoding="utf-8").split("\n")
            fragments = [part for edit in ex.EDITS[rel] for part in edit[2].split("\n") if part.strip()]
            matcher = difflib.SequenceMatcher(a=source, b=exported, autojunk=False)
            changed = [index for tag, i1, i2, _, _ in matcher.get_opcodes() if tag != "equal"
                       for index in range(i1, i2)]
            self.assertTrue(changed, rel)
            for index in changed:
                self.assertTrue(any(fragment in source[index] for fragment in fragments), f"{rel}:{index + 1}")
            self.assertLessEqual(len(changed), sum(edit[2].count("\n") + 1 for edit in ex.EDITS[rel]), rel)
        readme = (self.dest / f"{POLICY}/README.md").read_text(encoding="utf-8")
        decision = (self.dest / DECISION).read_text(encoding="utf-8")
        for removed in ("have run no data", "fifth revision", "lead's runs", "run by the author", "ICML",
                        "the proposal", "non-author", "review", "fourth-candidate", "follow-up brief",
                        "decision notes", "second snapshot", "archived snapshot", "F1:", "F2:", "amendment.md",
                        "precision-targets.md", "EDGE_CHECKS", ".ai/", "not in the repository"):
            self.assertNotIn(removed, readme + decision, removed)
        # what the documents define is still there
        for kept in ("## Outcome definition (pinned)", "## Costs (cost-scope amendment of 2 October 2026)",
                     "\nEvery test uses ENGINEERING FIXTURES: the synthetic world and\n",
                     "not the study's planned D_info estimand and not a\nnew allocator. Protocol, decisions and limits:",
                     "observed (its record is not part of this package; the definition is stated below);",
                     "\nNo feasibility-adjusted H2, D_info\n"):
            self.assertIn(kept, readme, kept)
        for kept in ("\nStatus, 3 October 2026: draft describing the implemented policy package",
                     "\n## Engineering tests (engineering fixtures)\n",
                     "- **Session ownership** (`costs.session_allocation`):",
                     "- **Completeness** is computed per scope",
                     "- **Authoritative accounting** (cost contract v3). Physical cost evidence",
                     "- **Interpretation** (inference-interpretation amendment; estimators",
                     "or general capability.\n- Average utility and refusal results do not show that every selected "
                     "edit is feasible in expectation.\n",
                     "## Open decisions for the lead (unresolved; not invented here)",
                     "Cost contract v3 keeps plan v4, with estimators, family and allocation unchanged: the cost",
                     "T = C+ - r·C-"):
            self.assertIn(kept, decision, kept)

    def test_the_recovery_tooling_is_not_in_the_export(self):
        self.assertFalse([rel for rel in self.files if "durability" in rel])

    def test_export_rescans_clean_and_keeps_public_identifiers(self):
        output = {rel: (self.dest / rel).read_bytes() for rel in self.files}
        self.assertEqual((ex.scan(output), ex.check_links(output)), ([], []))
        data = (self.dest / "experiments/safety_selection/configs/study-v2-data.json").read_text(encoding="utf-8")
        for public in ("DataAttributionEval/Toxicity-Bias-Filtering", "lmsys/toxic-chat", "allenai/ai2_arc",
                       "Qwen/Qwen2.5-1.5B-Instruct"):
            self.assertIn(public, data)
        self.assertIn("--map /remote/runs=<archive>",
                      (self.dest / "experiments/safety_selection/README.md").read_text(encoding="utf-8"))
        minimal = (self.dest / "experiments/minimal_safety/README.md").read_text(encoding="utf-8")
        for removed in ("Verified first CUDA run", "ICML", "dated run note"):
            self.assertNotIn(removed, minimal)
        self.assertIn("## Outputs (`<RUN>/`)", minimal)
        self.assertTrue(minimal.endswith("\n") and not minimal.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
