"""Check one tokenizer folder against the engine's codec rules (brief multi-family-probe-engine-20261007, Item 1;
standalone, outside the engine's code identity; offline). Prints ids and counts only, never text of a data row.

    python scripts/family_codec_check.py --tokenizer DIR --end TOKEN --stop TOKEN [--stop ...] --pad TOKEN \\
        --header HEADER [--chat-template FILE] [--dolly DOLLY.jsonl]

--chat-template FILE: a JSON object with chat_template (and optionally bos_token, eos_token) that replaces the
folder's template (the Llama-3.1 template for both Llama probes, decision L1). --header is given with Python escapes
(for example '<|assistant|>\\n'). With --dolly: the line numbers of rows over the row or prompt limit, of rows whose
separate encoding differs from the joint one, and of responses that do not decode back to themselves.
"""
import argparse
import codecs
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.safety_selection.prepare_task import render_user_text  # noqa: E402
from experiments.safety_selection.textproc import (ControlTokenError, NoTargets, TemplateError, TooLong,  # noqa: E402
                                                   added_special_ids, build_codec, chat_template_reads_clock,
                                                   check_assistant_header, encode_train, separate_matches_joint)

ROUND_TRIP = ["Hello world.", "a  b", " leading space", "x .", "naïve café", "1+1=2", "tabs\tand\nnewlines",
              "emoji 🙂 text", "Don't stop", "quote \" and 'single'"]


def generation_suffix(tokenizer) -> str:
    turn = [{"role": "user", "content": "<<probe>>"}]
    with_header = tokenizer.apply_chat_template(turn, tokenize=False, add_generation_prompt=True)
    without = tokenizer.apply_chat_template(turn, tokenize=False, add_generation_prompt=False)
    return with_header[len(without):] if with_header.startswith(without) else None


def main(argv=None) -> int:
    from transformers import AutoTokenizer

    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--stop", action="append", required=True)
    ap.add_argument("--pad", required=True)
    ap.add_argument("--header", required=True)
    ap.add_argument("--chat-template")
    ap.add_argument("--dolly")
    ap.add_argument("--max-train", type=int, default=3072)
    ap.add_argument("--max-prompt", type=int, default=1536)
    a = ap.parse_args(argv)
    header = codecs.decode(a.header, "unicode_escape")
    tok = AutoTokenizer.from_pretrained(a.tokenizer, local_files_only=True, trust_remote_code=False)
    out = {"tokenizer": a.tokenizer, "own_template_reads_clock": chat_template_reads_clock(tok),
           "clean_up_tokenization_spaces_in_config": getattr(tok, "clean_up_tokenization_spaces", None)}
    if a.chat_template:
        spec = json.loads(Path(a.chat_template).read_text(encoding="utf-8"))
        tok.chat_template = spec["chat_template"]
        out["chat_template_replaced_from"] = a.chat_template
    try:
        codec = build_codec(tok, a.end, a.stop, a.pad)
    except TemplateError as exc:
        out["codec"] = f"refused: {exc}"
        print(json.dumps(out, indent=1, ensure_ascii=False))
        return 1
    out.update(eos_id=codec.eos_id, stop_ids=list(codec.stop_ids), pad_id=codec.pad_id,
               all_special_ids=len(tok.all_special_ids), added_special=len(added_special_ids(tok)),
               special_ids=len(codec.special_ids), unk_token_id=getattr(tok, "unk_token_id", None),
               generation_suffix=generation_suffix(tok))
    try:
        check_assistant_header(codec, header)
        out["header_check"] = "passed"
    except TemplateError as exc:
        out["header_check"] = f"refused: {exc}"
    joint = codec.conversation_ids("<<probe>>", "<<reply>>")
    chat = sorted({i for i in joint if i in codec.special_ids})
    out["chat_tokens"] = {tok.convert_ids_to_tokens(i): i for i in chat}
    out["template_tokens_one_turn"] = len(joint) - len(codec.encode("<<probe>>")) - len(codec.encode("<<reply>>"))
    out["prompt_tokens_empty_user"] = len(codec.prompt_ids(""))
    out["decode_round_trip_failures"] = sum(codec.decode(codec.encode(s)) != s for s in ROUND_TRIP)
    if a.dolly:
        over_row, over_prompt, control, separate, decode_fail, n = [], [], [], [], [], 0
        for line, text in enumerate(Path(a.dolly).read_text(encoding="utf-8").split("\n"), start=1):
            if not text.strip():
                continue
            n += 1
            row = json.loads(text)
            user = render_user_text(row["instruction"], row["context"])
            try:
                example = encode_train(codec, f"line{line}", user, row["response"], a.max_train)
                if example.n_prompt > a.max_prompt:
                    over_prompt.append(line)
                elif not separate_matches_joint(codec, user, row["response"]):
                    separate.append(line)
            except TooLong:
                over_row.append(line)
            except (ControlTokenError, NoTargets):
                control.append(line)
            if codec.decode(codec.encode(row["response"])) != row["response"]:
                decode_fail.append(line)
        out["dolly"] = {"rows": n, "over_row_limit": over_row, "over_prompt_limit": over_prompt,
                        "control_or_empty": control, "separate_not_joint": separate,
                        "response_decode_round_trip_failures": len(decode_fail),
                        "response_decode_round_trip_failure_lines": decode_fail[:50]}
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
