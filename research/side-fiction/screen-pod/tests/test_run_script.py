"""screen_run.sh with fake pythons, a fake nvcc, apt-get, timeout and nproc (bash; no pip, no network, no GPU), running
the lead's REAL pod_run_granite.sh (copied from the pinned file into the fake bundle's gate_b): the step order (the
guard's setup, the lead's whole Granite job in /workspace/judge with its bundle/ linked to gate_b, then ka, granite,
qwen), the time limit of every setup step (the lead's job under one), the environment each step sees (the lead's CUDA
build arguments and job cap, offline flags, no token, no cache variable, CUBLAS_WORKSPACE_CONFIG), the lead's exit code
handed to the ka step, a step that runs out of time, the lead's nvcc fallback, the exit trap's record and DONE.json."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess

import pytest
from conftest import TOOL, P

LEAD_SCRIPT = P.MAC_GATE_B / "pod/pod_run_granite.sh"

FAKE_PY = r"""#!/bin/bash
who="$(basename "$(dirname "$(dirname "$0")")")"
step=""
case "$*" in *screen_job.py\ *) step="$(echo "$*" | sed -E 's/.*screen_job.py ([a-z-]+).*/\1/')";; esac
echo "$who | $* | cublas=${CUBLAS_WORKSPACE_CONFIG:-unset} cvd=${CUDA_VISIBLE_DEVICES:-unset} offline=${HF_HUB_OFFLINE:-unset} tf=${TRANSFORMERS_OFFLINE:-unset} pp=${PYTHONPATH:-unset} cmake=${CMAKE_ARGS:-unset} force=${FORCE_CMAKE:-unset} jobs=${CMAKE_BUILD_PARALLEL_LEVEL:-unset} cudacxx=${CUDACXX:-unset} hubcache=${HUGGINGFACE_HUB_CACHE:-unset}${HF_HUB_CACHE:-} token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
if [ -n "$step" ] && [ "${FAIL_STEP:-}" = "$step" ]; then exit "${FAIL_CODE:-1}"; fi
case "$*" in *"import sys, torch"*) exit "${TORCH_RC:-0}";; esac
case "$*" in *"pip freeze"*) echo "fake==1";; esac
case "$*" in *"granite-requirements.txt"*) exit "${LEAD_PIP_EXIT:-0}";; esac
case "$*" in *"llama_cpp_python-0.3.36.tar.gz"*) exit "${LEAD_BUILD_EXIT:-0}";; esac
case "$*" in *"pod_job.py run"*) exit "${LEAD_RUN_EXIT:-0}";; esac
exit 0
"""

FAKE_SYS = r"""#!/bin/bash
if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then
  for dir; do :; done
  mkdir -p "$dir/bin" && cp "$FAKE_PY" "$dir/bin/python" && chmod +x "$dir/bin/python"
  echo "sys | $* | token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
  exit 0
fi
echo "sys | $* | offline=${HF_HUB_OFFLINE:-unset} token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
case "$*" in *"granite_pod.py fetch-sdist"*) mkdir -p "$GRANITE_SRC"; touch "$GRANITE_SRC/llama_cpp_python-0.3.36.tar.gz"; exit 0;; esac
case "$*" in *"screen_job.py ka "*) exit "${KA_EXIT:-0}";; esac
exit 0
"""

FAKE_APT = r"""#!/bin/bash
echo "apt | $* | token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
if [ "${APT_RC:-0}" != "0" ]; then exit "$APT_RC"; fi
case "$*" in *install*) mkdir -p "$(dirname "$GRANITE_APT_NVCC")" && printf '#!/bin/bash\necho "Cuda compilation tools, release 12.8, V12.8.93"\n' > "$GRANITE_APT_NVCC" && chmod +x "$GRANITE_APT_NVCC";; esac
exit 0
"""

FAKE_TIMEOUT = r"""#!/bin/bash
kill=""
if [ "$1" = "-k" ]; then kill="$2"; shift 2; fi
limit="$1"; shift
echo "kill=$kill limit=$limit | $*" >> "$TIMEOUTS"
if [ -n "${TIMEOUT_HIT:-}" ]; then
  case "$*" in *"$TIMEOUT_HIT"*) exit 124;; esac
fi
exec "$@"
"""

FAKE_NPROC = """#!/bin/bash
echo "${NPROC:-8}"
"""


def _exe(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def run_script(tmp_path, nvcc=True, **env_over):
    root, judge = tmp_path / "screen", tmp_path / "judge"
    (root / "bundle/tool").mkdir(parents=True)
    (root / "bundle/gate_b/tool/pod").mkdir(parents=True)
    shutil.copy(TOOL / "screen_run.sh", root / "bundle/tool/screen_run.sh")
    shutil.copy(LEAD_SCRIPT, root / "bundle/gate_b/tool/pod/pod_run_granite.sh")    # the lead's, as pinned
    (root / "bundle/gate_b/tool/pod/granite-requirements.txt").write_text("fake==1\n")
    fakes = tmp_path / "fakes"
    fake_py = _exe(fakes / "fake_python", FAKE_PY)
    sys_py = _exe(fakes / "sys_python", FAKE_SYS)
    _exe(fakes / "bin/python3", FAKE_SYS)                       # the lead's script calls python3 from PATH
    _exe(fakes / "bin/apt-get", FAKE_APT)
    _exe(fakes / "bin/timeout", FAKE_TIMEOUT)
    _exe(fakes / "bin/nproc", FAKE_NPROC)
    nvcc_path = tmp_path / "usrlocal/cuda/bin/nvcc"
    if nvcc:
        _exe(nvcc_path, '#!/bin/bash\necho "Cuda compilation tools, release 12.8, V12.8.93"\n')
    calls, timeouts = tmp_path / "calls.log", tmp_path / "timeouts.log"
    env = {"PATH": f"{fakes / 'bin'}:/usr/bin:/bin", "SCREEN_ROOT": str(root), "SYS_PYTHON": str(sys_py),
           "SCREEN_VENVS": str(tmp_path / "venvs"), "SCREEN_JUDGE_ROOT": str(judge),
           "GRANITE_VENV": str(tmp_path / "granite-venv"), "GRANITE_SRC": str(tmp_path / "src"),
           "GRANITE_NVCC": str(nvcc_path), "GRANITE_APT_NVCC": str(tmp_path / "apt-cuda/nvcc"),
           "FAKE_PY": str(fake_py), "CALLS": str(calls), "TIMEOUTS": str(timeouts),
           "HF_TOKEN": "hf_" + "T" * 34, "HUGGING_FACE_HUB_TOKEN": "hf_" + "U" * 34, "HF_HOME": "/elsewhere",
           "HUGGINGFACE_HUB_CACHE": "/elsewhere/hub", "HF_HUB_CACHE": "/elsewhere/hub2", "CUBLAS_WORKSPACE_CONFIG": "",
           **env_over}
    done = subprocess.run(["bash", str(root / "bundle/tool/screen_run.sh")], env=env, capture_output=True, text=True,
                          timeout=120)
    lines = calls.read_text().splitlines() if calls.exists() else []
    limits = timeouts.read_text().splitlines() if timeouts.exists() else []
    done_json = json.loads((root / "DONE.json").read_text())
    return done, lines, done_json, root, limits


def kind(line: str) -> str:
    who, args = line.split(" | ")[:2]
    for needle, name in (("screen_job.py ", None), ("-m venv", "venv"), ("granite-requirements", "lead-pip"),
                         ("fetch-sdist", "fetch-sdist"), ("llama_cpp_python-0.3.36.tar.gz", "lead-build"),
                         ("llama-record", "llama-record"), ("pod_job.py download", "lead-download"),
                         ("pod_job.py run", "lead-run"), ("torch==2.8.0", "torch-install"),
                         ("guard-requirements", "pip-guard"), ("pip freeze", "freeze"),
                         ("import sys, torch", "torch-check")):
        if needle in args:
            if name is None:
                return f"{who}:" + args.split("screen_job.py ")[1].split()[0]
            if name == "venv":
                return "venv-" + pathlib.Path(args.split()[-1]).name
            return f"{who}:{name}"
    return who + ":" + args.split()[0]


def limit_kind(line: str) -> tuple:
    """(what the timeout wrapped, its limit, its kill grace) from one fake-timeout line."""
    head, cmd = line.split(" | ", 1)
    kill, limit = (field.split("=")[1] for field in head.split())
    for key, name in (("-m venv --system-site-packages", "venv-q"), ("guard-requirements", "pip-guard"),
                      ("pip freeze", "freeze"), ("import sys, torch", "torch-check"), ("torch==2.8.0", "torch-install"),
                      ("screen_job.py download", "download"), ("pod_run_granite.sh", "granite-job")):
        if key in cmd:
            return name, int(limit), kill
    return cmd.split()[0], int(limit), kill


SETUP_LIMITS = [("venv-q", 600, "60"), ("torch-check", 600, "60"), ("pip-guard", 1800, "60"), ("freeze", 600, "60"),
                ("download", 3600, "60"), ("granite-job", 5400, "60")]
ORDER = ["venv-q", "q:torch-check", "q:pip-guard", "q:freeze", "q:download", "venv-granite-venv",
         "granite-venv:lead-pip", "sys:fetch-sdist", "granite-venv:lead-build", "granite-venv:freeze",
         "granite-venv:llama-record", "granite-venv:lead-download", "granite-venv:lead-run", "sys:ka",
         "granite-venv:granite", "q:qwen", "sys:record"]


def test_steps_order_environment_and_the_leads_granite_job(tmp_path):
    done, lines, done_json, root, limits = run_script(tmp_path)
    assert done.returncode == 0, done.stderr
    assert [kind(x) for x in lines] == ORDER
    by = {kind(x): x for x in lines}
    assert "--system-site-packages" in by["venv-q"] and "--system-site-packages" not in by["venv-granite-venv"]
    build = by["granite-venv:lead-build"]                                # the lead's build line, its own arguments
    assert "cmake=-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80 force=1 jobs=8" in build and "--no-deps" in build
    assert "cudacxx=" + str(tmp_path / "usrlocal/cuda/bin/nvcc") in build
    assert "--only-binary=:all:" in by["granite-venv:lead-pip"] and "--only-binary=:all:" in by["q:pip-guard"]
    assert "offline=unset tf=unset pp=bundle/engine" in by["q:download"]
    assert "offline=unset tf=unset" in by["granite-venv:lead-download"]
    assert "offline=1 tf=1" in by["granite-venv:lead-run"] and "--bundle bundle" in by["granite-venv:lead-run"]
    assert "--granite-exit 0 " in by["sys:ka"] + " " and "--granite-root granite-job" in by["sys:ka"]
    assert "offline=1" in by["sys:ka"]
    for step in ("granite-venv:granite", "q:qwen"):
        assert "offline=1 tf=1" in by[step] and "cublas=:4096:8 cvd=0" in by[step]
    assert "pp=bundle/engine" in by["q:qwen"] and "pp=unset" in by["granite-venv:granite"]
    assert all(x.endswith("token=") for x in lines)                         # no token reaches any step
    assert all("hubcache=unset " in x for x in lines if not x.startswith(("sys", "apt")))   # nor a hub cache variable
    assert "--exit 0 --step done" in by["sys:record"]
    assert done_json["exit"] == 0 and done_json["step"] == "done" and (root / "STARTED.json").is_file()
    assert (root / "STEP").read_text().strip() == "done"
    judge = tmp_path / "judge"                                             # the lead's job: its own root and records
    lead_done = json.loads((judge / "DONE.json").read_text())
    assert (lead_done["exit"], lead_done["step"]) == (0, "done") and (judge / "STEP").read_text().strip() == "done"
    assert (judge / "bundle").is_symlink() and (judge / "bundle").resolve() == (root / "bundle/gate_b").resolve()
    assert (root / "granite-job").is_symlink() and (root / "granite-job").resolve() == judge.resolve()
    assert "release 12.8" in (judge / "out/llama-build.log").read_text() and (judge / "out/environment-pod.lock").is_file()
    assert str(tmp_path / "venvs") in by["venv-q"] and str(tmp_path / "granite-venv") in by["venv-granite-venv"]
    assert [limit_kind(x) for x in limits] == SETUP_LIMITS                  # every setup step under a time limit
    assert not [x for x in limits if any(f"screen_job.py {s} " in x for s in ("ka", "granite", "qwen", "record"))]
    copied = (root / "bundle/gate_b/tool/pod/pod_run_granite.sh").read_bytes()
    assert hashlib.sha256(copied).hexdigest() == P.LAUNCHER_PINS["pod/pod_run_granite.sh"]


@pytest.mark.parametrize("env,lead,granite_exit,ka_exit", [
    ({"LEAD_RUN_EXIT": "3"}, (3, "run"), 3, 4),                 # the lead's gate failed: the ka step's exit 4
    ({"LEAD_RUN_EXIT": "5"}, (5, "run"), 5, 5),                 # stopped during the gate
    ({"LEAD_PIP_EXIT": "3"}, (3, "pip"), 3, 1),                 # pip's own 3 (the real ka step: no verdict, exit 1)
    ({"LEAD_BUILD_EXIT": "1"}, (1, "llama"), 1, 1)])
def test_the_leads_exit_goes_to_the_ka_step_which_ends_the_job(tmp_path, env, lead, granite_exit, ka_exit):
    done, lines, done_json, root, limits = run_script(tmp_path, KA_EXIT=str(ka_exit), **env)
    kinds = [kind(x) for x in lines]
    lead_done = json.loads((tmp_path / "judge/DONE.json").read_text())
    assert (lead_done["exit"], lead_done["step"]) == lead
    ka_line = next(x for x in lines if kind(x) == "sys:ka")
    assert f"--granite-exit {granite_exit} " in ka_line
    assert (done_json["exit"], done_json["step"]) == (ka_exit, "ka") and done.returncode == ka_exit
    assert "granite-venv:granite" not in kinds and "q:qwen" not in kinds and kinds[-1] == "sys:record"


@pytest.mark.parametrize("hit,step,absent", [("guard-requirements", "venv-guard", ["q:download", "sys:ka"]),
                                             ("screen_job.py download", "download", ["venv-granite-venv", "sys:ka"])])
def test_a_setup_step_out_of_time_ends_the_job(tmp_path, hit, step, absent):
    done, lines, done_json, root, limits = run_script(tmp_path, TIMEOUT_HIT=hit)
    assert (done_json["exit"], done_json["step"]) == (124, step) and done.returncode == 124
    kinds = [kind(x) for x in lines]
    assert not set(absent) & set(kinds) and kinds[-1] == "sys:record" and "--exit 124" in lines[-1]


def test_the_leads_job_out_of_time_is_handed_to_the_ka_step(tmp_path):
    done, lines, done_json, root, limits = run_script(tmp_path, TIMEOUT_HIT="pod_run_granite.sh", KA_EXIT="1")
    kinds = [kind(x) for x in lines]
    assert kinds == ORDER[:5] + ["sys:ka", "sys:record"]                    # the lead's script never ran
    assert "--granite-exit 124 " in next(x for x in lines if kind(x) == "sys:ka")
    assert (done_json["exit"], done_json["step"]) == (1, "ka") and not (tmp_path / "judge/DONE.json").exists()


@pytest.mark.parametrize("fail_step,code", [("granite", 5), ("qwen", 1), ("download", 1)])
def test_a_failed_step_ends_the_job_and_done_records_it(tmp_path, fail_step, code):
    done, lines, done_json, root, limits = run_script(tmp_path, FAIL_STEP=fail_step, FAIL_CODE=str(code))
    kinds = [kind(x) for x in lines]
    assert done_json["exit"] == code and done.returncode == code and done_json["step"] == fail_step
    assert kinds[-1] == "sys:record" and f"--exit {code} --step {fail_step}" in lines[-1]
    after = {"granite": ["q:qwen"], "qwen": [], "download": ["venv-granite-venv", "sys:ka"]}[fail_step]
    assert not set(after) & set(kinds)                                      # nothing runs after a failed step


@pytest.mark.parametrize("nproc,jobs", [("64", "16"), ("16", "16"), ("12", "12"), ("x", "1")])
def test_the_leads_build_jobs_are_capped_at_16(tmp_path, nproc, jobs):
    done, lines, done_json, root, limits = run_script(tmp_path, NPROC=nproc)
    assert done_json["exit"] == 0
    assert f" jobs={jobs} " in next(x for x in lines if kind(x) == "granite-venv:lead-build")


def test_the_leads_nvcc_fallback_from_apt_and_its_failure(tmp_path):
    done, lines, done_json, root, limits = run_script(tmp_path / "a", nvcc=False)
    kinds = [kind(x) for x in lines]
    assert done_json == {**done_json, "exit": 0, "step": "done"}
    assert kinds.index("apt:update") < kinds.index("apt:install") < kinds.index("granite-venv:lead-build")
    install = next(x for x in lines if x.startswith("apt | install"))
    assert all(p in install for p in ("cuda-nvcc-12-8", "cuda-cudart-dev-12-8", "libcublas-dev-12-8",
                                      "cuda-driver-dev-12-8"))
    build = next(x for x in lines if kind(x) == "granite-venv:lead-build")
    assert "cudacxx=" + str(tmp_path / "a/apt-cuda/nvcc") in build
    done, lines, done_json, root, limits = run_script(tmp_path / "b", nvcc=False, APT_RC="100", KA_EXIT="1")
    lead_done = json.loads((tmp_path / "b/judge/DONE.json").read_text())
    assert (lead_done["exit"], lead_done["step"]) == (100, "nvcc") and "granite-venv:lead-build" not in [
        kind(x) for x in lines]
    assert "--granite-exit 100 " in next(x for x in lines if kind(x) == "sys:ka") and done_json["step"] == "ka"


def test_torch_installed_from_the_cu128_index_when_the_image_lacks_it(tmp_path):
    done, lines, done_json, root, limits = run_script(tmp_path, TORCH_RC="1")
    kinds = [kind(x) for x in lines]
    assert done_json["exit"] == 1 and done_json["step"] == "venv-guard"         # the re-check fails too (fake)
    assert kinds.count("q:torch-check") == 2 and "q:torch-install" in kinds
    assert "--index-url https://download.pytorch.org/whl/cu128" in next(x for x in lines if "torch==2.8.0" in x)
    assert ("torch-install", 2400, "60") in [limit_kind(x) for x in limits]


def test_a_real_directory_at_the_leads_bundle_path_refuses(tmp_path):
    (tmp_path / "judge/bundle").mkdir(parents=True)                         # never link inside an existing folder
    done, lines, done_json, root, limits = run_script(tmp_path, KA_EXIT="1")
    assert (done_json["exit"], done_json["step"]) == (1, "granite-job")
    assert "venv-granite-venv" not in [kind(x) for x in lines]


def test_script_holds_no_token_and_unsets_the_cache_variables():
    text = (TOOL / "screen_run.sh").read_text()
    assert ("unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_HOME HF_HUB_CACHE HUGGINGFACE_HUB_CACHE TRANSFORMERS_CACHE "
            "XDG_CACHE_HOME") in text
    assert "export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0" in text
    assert 'JR="${SCREEN_JUDGE_ROOT:-/workspace/judge}"' in text and P.JUDGE_ROOT == "/workspace/judge"
    assert 'VG="${GRANITE_VENV:-/root/granite-venv}"' in text and P.GRANITE_VENV == "/root/granite-venv"
    assert os.path.basename(P.POD_VENVS) in text and "T_GRANITE_JOB=5400" in text
    lead = LEAD_SCRIPT.read_text()                                            # the lead's defaults the screen relies on
    assert 'cd "${JUDGE_ROOT:-/workspace/judge}"' in lead and 'VG="${GRANITE_VENV:-/root/granite-venv}"' in lead
