"""Read-only check of the objects that a push of the Side Project branch sends (administrative; step 4 b).

Lists every object reachable from the branch and not from any origin/* ref, then checks each blob:
  - size: GitHub refuses a file over 100 MB and warns over 50 MB;
  - the kit's secret patterns (runkit/gate-b-olmo/secret_scan.py), the value of each token variable in the
    environment and in ~/.config/attribution/secrets.env (values compared, never shown);
  - path names that must never go to GitHub: model weights, selector*.jsonl, hidden/, held-out, banks/, anchors*.json,
    secrets*.env, SSH keys, pod address files.
Prints pattern names and paths only, never matched text. Writes nothing except the JSON given by --out.
"""
import importlib.util, json, os, pathlib, re, subprocess, sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
BRANCH = "claude/wonderful-greider-d1aa5b"
spec = importlib.util.spec_from_file_location("kit_secret_scan", ROOT / "runkit/gate-b-olmo/secret_scan.py")
secret_scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(secret_scan)
TOKEN_VARS = ("RUNPOD_OPERATOR_API_KEY", "RUNPOD_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
              "CLAUDE_CODE_MESSAGING_TOKEN")
BAD_NAME = re.compile(r"(\.safetensors|\.bin|\.pt|\.pth|\.gguf|\.ckpt)$|(^|/)selector[^/]*\.jsonl$|(^|/)hidden(/|$)|"
                      r"held[-_]?out|(^|/)banks(/|$)|(^|/)anchors[^/]*\.json$|secrets[^/]*\.env$|(^|/)(id_(rsa|ed25519)|key)$|"
                      r"(^|/)known_hosts|(^|/)pod[^/]*\.json$", re.I)


def token_values() -> dict:
    vals = {n: os.environ[n].strip() for n in TOKEN_VARS if len(os.environ.get(n, "").strip()) >= 16}
    env_file = pathlib.Path.home() / ".config/attribution/secrets.env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if m:
                v = m.group(2).strip().strip("'\"")
                if len(v) >= 16:
                    vals[f"secrets.env:{m.group(1)}"] = v
    return vals


def git(*args, inp=None):
    return subprocess.run(["git", "-C", str(ROOT), *args], input=inp, capture_output=True, check=True).stdout


def main() -> int:
    out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    objs = git("rev-list", "--objects", BRANCH, "--not", "--remotes=origin").decode().splitlines()
    paths = {}
    for line in objs:
        sha, _, name = line.partition(" ")
        if name:
            paths.setdefault(sha, set()).add(name)
    commits = int(git("rev-list", "--count", BRANCH, "--not", "--remotes=origin").decode().strip())
    check = git("cat-file", "--batch-check", inp=("\n".join(l.split(" ")[0] for l in objs) + "\n").encode()).decode()
    blobs = [(s, int(z)) for s, t, z in (l.split() for l in check.splitlines()) if t == "blob"]
    values = token_values()
    hits, big, warn, names = [], [], [], []
    for sha, size in blobs:
        label = sorted(paths.get(sha, {"(no path)"}))
        if size > 100 * 1024 * 1024:
            big.append((label, size))
        elif size > 50 * 1024 * 1024:
            warn.append((label, size))
        for p in label:
            if BAD_NAME.search(p):
                names.append(p)
        data = git("cat-file", "blob", sha).decode("utf-8", "ignore")
        hits += [(label, n) for n in secret_scan.scan_text(data)]
        hits += [(label, f"value of {n}") for n, v in sorted(values.items()) if v in data]
    record = {"branch": BRANCH, "commits_not_on_origin_refs": commits, "objects": len(objs), "blobs": len(blobs),
              "blob_bytes": sum(z for _, z in blobs), "over_100MB": big, "over_50MB": warn,
              "forbidden_names": sorted(set(names)), "secret_hits": hits,
              "patterns": sorted(secret_scan.PATTERNS), "token_values_checked": sorted(values),
              "ok": not (big or names or hits)}
    text = json.dumps(record, indent=1, default=list)
    print(text)
    if out:
        out.write_text(text + "\n")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
