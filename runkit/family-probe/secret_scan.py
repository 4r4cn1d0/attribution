"""Token and key patterns (those of tmp/kill-test-7b-check/backup_records_q7.py) and a scanner that reports the
pattern names and paths only, never the matched text (administrative)."""
import pathlib
import re

PATTERNS = {"runpod_key": re.compile(r"rpa_[A-Za-z0-9]{10,}"), "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
            "github_pat": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "hf_token": re.compile(r"hf_[A-Za-z0-9]{30,}"),
            "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "ssh_public_key": re.compile(r"ssh-(ed25519|rsa) AAAA")}
MODEL_TEXT = ("generations.jsonl", "samples.jsonl", "guard.jsonl", "guard_samples.jsonl")


def scrubbed(environ, names) -> dict:
    """A copy of ``environ`` without the named token variables and without any variable whose value holds an HF token
    (review fix 5: a renamed variable is still dropped)."""
    return {k: v for k, v in environ.items() if k not in names and not PATTERNS["hf_token"].search(v or "")}


def scrub_process(environ, names) -> None:
    """Remove the token variables from this process's own environment after use (the disputed review item); a child
    started later no longer inherits them. The environment block fixed at the process's start is not erased."""
    for key in [k for k, v in environ.items() if k in names or PATTERNS["hf_token"].search(v or "")]:
        environ.pop(key, None)


def scan_text(text: str) -> list[str]:
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


def scan_paths(paths) -> list[tuple[str, str]]:
    """(path, pattern name) for every hit in the given files."""
    hits = []
    for path in paths:
        text = pathlib.Path(path).read_bytes().decode("utf-8", "ignore")
        hits += [(str(path), name) for name in scan_text(text)]
    return hits


def scan_tree(root) -> dict:
    """Hits in a retrieved tree: those in the model's evaluation text (counted, never a verdict: the model never
    receives a token) and those anywhere else (a secret: the host is not verified)."""
    root = pathlib.Path(root)
    model, other = [], []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = str(path.relative_to(root))
        for name in scan_text(path.read_bytes().decode("utf-8", "ignore")):
            # model text: an evaluation file under any eval* folder (eval/, the preflight's eval-sample/); review fix 17
            in_eval = path.name in MODEL_TEXT and any(part.startswith("eval") for part in path.relative_to(root).parts[:-1])
            (model if in_eval else other).append((rel, name))
    return {"model_text_pattern_hits": model, "secret_hits": other}
