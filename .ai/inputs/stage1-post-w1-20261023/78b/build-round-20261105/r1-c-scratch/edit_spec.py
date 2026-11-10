import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
old_start = s.index(' ("C-ec-write-wb"'); old_end = s.index(' ("C-ec-guard-record"')
new = r''' ("C-ec-write-direct", "the record is opened at --out itself, not at a temporary name", E,
  """        with open(partial, "xb") as handle:""", """        with open(out, "xb") as handle:"""),
 ("C-ec-partial-kept", "the temporary file is not removed (a partial or stray file survives)", E,
  """                os.unlink(partial)""", """                pass"""),
 ("C-ec-systemexit", "a SystemExit escapes main with its message", E,
  """    except (Exception, SystemExit) as exc:     # every refusal""", """    except Exception as exc:     # every refusal"""),
 ("V-bank-guard-add", "bank mode: bank prompts never enter the text guard", E,
  "    for _, prompt in loaded.rows:\n        guard.add(prompt)\n", "    for _, prompt in loaded.rows:\n        pass\n"),
 ("V-anchor-guard-add", "anchor mode: anchor texts never enter the text guard", E,
  "        guard.add(p[\"prompt\"], p[\"unsafe_response\"])\n", "        pass\n"),
 ("V-guard-no-responses", "lists mode: responses never enter the text guard", E,
  "        guard.add(item.get(\"prompt\"), item.get(\"response\"))\n", "        guard.add(item.get(\"prompt\"))\n"),
 ("V-train-catch-all", "encode_train: any exception counted as a refusal", E,
  "            encode_train(codec, row_id, prompt, response, max_tokens)\n        except ValueError as exc:",
  "            encode_train(codec, row_id, prompt, response, max_tokens)\n        except Exception as exc:"),
'''
s = s[:old_start] + new + s[old_end:]
i = s.index(' ("C-tl-twice"')
add_t = r''' ("C-tl-partial-kept", "the temporary file is not removed (a partial or stray file survives)", T,
  """                os.unlink(partial)""", """                pass"""),
 ("C-tl-write-direct", "the record is opened at --out itself, not at a temporary name", T,
  """        with open(partial, "xb") as handle:""", """        with open(out, "xb") as handle:"""),
 ("C-tl-systemexit", "a SystemExit escapes main with its message", T,
  """    except (Exception, SystemExit) as exc:     # no traceback""", """    except Exception as exc:     # no traceback"""),
'''
s = s[:i] + add_t + s[i:]
p.write_text(s)
