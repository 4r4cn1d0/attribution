"""Verifier probe (R3 Track P): blinding, refusals and writes of padded_tokens_78b.main on synthetic fixtures.

Every text (P_F prompts and responses, added prompts and responses, rewritten responses, the edit's name, ids planted in
messages) holds the sentinel. Each case runs main in-process with a fake codec and a fixture loader and checks: the exit
code; no sentinel in stdout, stderr or any file in the output folder; no partial file left; on a refusal, no --out.
Prints one line per case (ids, codes and booleans only) and writes S/probe_blind.json.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

WSC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(WSC))
sys.path.insert(0, str(OUT.parent))

import probe_compute as pc                                                    # noqa: E402  (fixture helpers only)
from experiments.safety_selection import edits as E                          # noqa: E402
from scripts.scale78b import encode_count_78b as ec                           # noqa: E402
from scripts.scale78b import padded_tokens_78b as pt                          # noqa: E402

SENT = pc.SENT
LONGTEXT = f"{SENT} " + " ".join(["z"] * 5000)        # too long for max_train_tokens


class TextError(Exception):
    pass


def leaks(*texts):
    return any(SENT in t or " a a a" in t or " b b b" in t or " z z z" in t or " c c c" in t for t in texts)


def call(tmp, prep, argv_extra, *, out_name, codec=None, loader=None, context=None, check=False):
    outdir = tmp / "out"
    outdir.mkdir(exist_ok=True)
    out = outdir / out_name
    from experiments.safety_selection.config import tokenizer_of
    recipe = ec.load_recipe(pc.FAM, None)[0]
    repo_id, rev = tokenizer_of(recipe)
    tk = {"repo_id": repo_id, "revision": rev, "end_of_turn_token": recipe["model"]["end_of_turn_token"]}
    ctx = context or (lambda f, p: ec.Context(codec or pc.Codec(), tk, ec.MANIFESTS[pc.FAM]))
    argv = ["--family", pc.FAM, "--prepared", str(tmp / "prep")] + (["--check-a0"] if check else []) + argv_extra + \
        ["--out", str(out)]
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
        try:
            code = pt.main(argv, context=ctx, loader=loader or (lambda p, s: prep))
        except SystemExit as exc:          # argparse
            code = f"SystemExit({exc.code})"
    files = sorted(p for p in outdir.iterdir())
    contents = [p.read_text(errors="replace") for p in files if p.is_file()]
    partial = [p.name for p in files if p.name.endswith(".partial")]
    return {"code": code, "err": e.getvalue(), "out": o.getvalue(), "wrote": out.exists(), "partial": partial,
            "leak": leaks(o.getvalue(), e.getvalue(), *contents), "out_path": out}


def write_edit(tmp, name, doc=None, raw=None):
    p = tmp / "edits" / name
    p.parent.mkdir(exist_ok=True)
    data = raw if raw is not None else E.edit_bytes(doc)
    p.write_bytes(data)
    return p, E.sha256_bytes(data)


def main():
    rows = []
    with tempfile.TemporaryDirectory(dir=OUT.parent) as td:
        tmp = Path(td)
        prep = pc.fixture(300)
        ids = sorted(prep.train_rows)
        good, gsha = write_edit(tmp, "good.json", pc.edit_doc(
            remove=ids[:3], rewrite=[(ids[10], f"{SENT} " + " ".join(["c"] * 30))],
            add=[("add-000", f"{SENT} q x y", f"{SENT} s t u")]))
        other, osha = write_edit(tmp, "other.json", pc.edit_doc(remove=ids[5:9]))

        def case(name, want, argv, **kw):
            r = call(tmp, prep, argv, out_name=f"{name}.json", **kw)
            ok = r["code"] == want and not r["leak"] and not r["partial"] and \
                (r["wrote"] if want in (0, 1) else not r["wrote"])
            rows.append({"case": name, "code": r["code"], "want": want, "wrote": r["wrote"], "leak": r["leak"],
                         "partial": r["partial"], "ok": ok, "err_head": r["err"][:160].replace(str(tmp), "<tmp>")})
            return r

        case("record_ok", 0, ["--edit", f"{good}:{gsha}", "--edit", f"{other}:{osha}"])
        case("check_differs", 1, [], check=True)
        # pins
        case("pin_of_another_edit", 2, ["--edit", f"{good}:{osha}"])
        case("pin_upper_hex", 2, ["--edit", f"{good}:{gsha.upper()}"])
        case("pin_short", 2, ["--edit", f"{good}:{gsha[:63]}"])
        changed, csha = write_edit(tmp, "changed.json", raw=good.read_bytes())
        changed.write_bytes(changed.read_bytes().replace(b"s t u", b"s t v"))
        case("bytes_changed_after_pin", 2, ["--edit", f"{changed}:{csha}"])
        case("edit_is_a_folder", 2, ["--edit", f"{tmp / 'edits'}:{gsha}"])
        case("edit_missing", 2, ["--edit", f"{tmp / 'edits' / 'none.json'}:{gsha}"])
        # engine edit checks with sentinel-bearing content
        p, s = write_edit(tmp, "notjson.json", raw=f'{{"name": "{SENT} broken'.encode())
        case("edit_not_json_with_text", 2, ["--edit", f"{p}:{s}"])
        d = pc.edit_doc(add=[("add-000", f"{SENT} q", f"{SENT} r")]); d["extra"] = f"{SENT} extra text"
        p, s = write_edit(tmp, "extrakey.json", d)
        case("edit_extra_key_with_text", 2, ["--edit", f"{p}:{s}"])
        d = pc.edit_doc(rewrite=[(f"{SENT} unknown id text", f"{SENT} replacement")])
        p, s = write_edit(tmp, "unknownid.json", d)
        r = case("edit_unknown_row_id_text", 2, ["--edit", f"{p}:{s}"])
        d = pc.edit_doc(add=[(f"bad-{SENT}", f"{SENT} q w e", f"{SENT} r t y")])
        p, s = write_edit(tmp, "badaddid.json", d)
        case("edit_bad_add_id_text", 2, ["--edit", f"{p}:{s}"])
        d = pc.edit_doc(rewrite=[(ids[4], LONGTEXT)])
        p, s = write_edit(tmp, "toolong.json", d)
        case("rewrite_too_long", 2, ["--edit", f"{p}:{s}"])
        d = pc.edit_doc(add=[("add-000", LONGTEXT, f"{SENT} r t y")])
        p, s = write_edit(tmp, "addtoolong.json", d)
        case("add_too_long", 2, ["--edit", f"{p}:{s}"])

        class LeakyCodec(pc.Codec):
            def encode(self, text):
                if "s t u" in text:
                    raise TextError(f"cannot encode {text}")
                return super().encode(text)
        case("codec_error_with_text", 2, ["--edit", f"{good}:{gsha}"], codec=LeakyCodec())

        def leaky_loader(p, s):
            raise TextError(f"{SENT} loader saw this text")
        case("loader_error_with_text", 2, ["--edit", f"{good}:{gsha}"], loader=leaky_loader)
        case("loader_error_check_mode", 2, [], loader=leaky_loader, check=True)

        def leaky_context(f, p):
            raise SystemExit(f"{SENT} a SystemExit with text")
        case("context_systemexit_with_text", 2, ["--edit", f"{good}:{gsha}"], context=leaky_context)
        bad_audit = pc.fixture(300)
        bad_audit.train_rows[ids[7]]["token_sha256"] = "0" * 64
        r = call(tmp, bad_audit, [], out_name="audit_check.json", check=True)
        rows.append({"case": "audit_mismatch_check_mode", "code": r["code"], "want": 2, "wrote": r["wrote"],
                     "leak": r["leak"], "partial": r["partial"],
                     "ok": r["code"] == 2 and not r["leak"] and not r["wrote"] and not r["partial"],
                     "err_head": r["err"][:160]})
        # writes
        r = case("out_exists_first", 0, ["--edit", f"{other}:{osha}"])
        before = r["out_path"].read_bytes()
        r2 = call(tmp, prep, ["--edit", f"{other}:{osha}"], out_name="out_exists_first.json")
        rows.append({"case": "out_exists_again", "code": r2["code"], "want": 2, "leak": r2["leak"],
                     "partial": r2["partial"], "ok": r2["code"] == 2 and r2["out_path"].read_bytes() == before
                     and not r2["partial"] and not r2["leak"], "err_head": r2["err"][:120]})
        # a stale partial of this pid: refused, the stale file is not ours and stays
        stale = tmp / "out" / f".stale.json.{os.getpid()}.partial"
        stale.write_bytes(b"x")
        r = call(tmp, prep, ["--edit", f"{other}:{osha}"], out_name="stale.json")
        rows.append({"case": "stale_partial_of_this_pid", "code": r["code"], "want": 2, "wrote": r["wrote"],
                     "ok": r["code"] == 2 and not r["wrote"] and stale.read_bytes() == b"x" and not r["leak"],
                     "err_head": r["err"][:120]})
        stale.unlink()
        # an fsync failure: refused, no --out, no partial
        real = os.fsync
        os.fsync = lambda fd: (_ for _ in ()).throw(OSError("disk full"))
        try:
            case("fsync_fails", 2, ["--edit", f"{other}:{osha}"])
        finally:
            os.fsync = real
        # a racing writer creates --out between the check and the link: refused, its bytes kept, no partial
        real_link = os.link

        def racing(src, dst):
            Path(dst).write_bytes(b"racer")
            return real_link(src, dst)
        os.link = racing
        try:
            r = call(tmp, prep, ["--edit", f"{other}:{osha}"], out_name="race.json")
        finally:
            os.link = real_link
        rows.append({"case": "race_on_link", "code": r["code"], "want": 2,
                     "ok": r["code"] == 2 and r["out_path"].read_bytes() == b"racer" and not r["partial"],
                     "err_head": r["err"][:120]})
        # --out as a dangling symlink, in a missing folder, inside the prepared folder (by a symlinked parent)
        (tmp / "out" / "dangling.json").symlink_to(tmp / "nowhere.json")
        r = call(tmp, prep, ["--edit", f"{other}:{osha}"], out_name="dangling.json")
        rows.append({"case": "out_dangling_symlink", "code": r["code"], "want": 2,
                     "ok": r["code"] == 2 and not (tmp / "nowhere.json").exists(), "err_head": r["err"][:120]})
        (tmp / "prep").mkdir(exist_ok=True)
        (tmp / "out" / "via").symlink_to(tmp / "prep")
        r = call(tmp, prep, ["--edit", f"{other}:{osha}"], out_name="via/inside.json")
        rows.append({"case": "out_inside_prepared_via_symlink", "code": r["code"], "want": 2,
                     "ok": r["code"] == 2 and not (tmp / "prep" / "inside.json").exists(), "err_head": r["err"][:120]})
        # argparse refusals (outside main's try): exit code and text
        r = call(tmp, prep, ["--family", "xx"], out_name="argparse.json")
        rows.append({"case": "argparse_bad_family", "code": r["code"], "want": "SystemExit(2)",
                     "ok": r["code"] == "SystemExit(2)" and not r["wrote"] and not r["leak"],
                     "err_head": r["err"][-120:]})
    ok = all(x["ok"] for x in rows)
    OUT.write_text(json.dumps({"all_ok": ok, "cases": rows}, indent=1, sort_keys=True))
    for x in rows:
        print(x["case"], x["code"], "ok" if x["ok"] else "NOT OK", "|", x.get("err_head", "")[:110].replace("\n", " "))
    print("ALL OK" if ok else "SOME NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
