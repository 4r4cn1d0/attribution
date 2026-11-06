"""reverify-K-core: run a working copy's pack_setup.main(argv) with git_state stubbed to ws-k's HEAD.

The scratch copy of ws-k has no .git (so no git command can touch the shared worktree from it), and pack_setup's
dry run and real pack both call git_state() (status of experiments/ and scripts/, then rev-parse HEAD). Everything
else runs as the real command would: the engine identity through the venv interpreter, the config hashes, the
prepared set, the sealed set's MANIFEST and R_d1-R_d3 by pin, the bundle and setup tars, the receipt.

    PY -B run_pack.py WORKING_COPY X [--dry-run] [--family F]
"""
import pathlib
import sys

wc = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(wc))
import pack_setup  # noqa: E402

WS_K_HEAD = "f5e3b4c27e117ba5f84917c9dd91a9b9e6f5a14a"   # ws-k's HEAD (git rev-parse, read-only, 6 Nov 2026)
pack_setup.git_state = lambda: WS_K_HEAD              # the only stub: the scratch copy has no .git
pack_setup.main(sys.argv[2:])
