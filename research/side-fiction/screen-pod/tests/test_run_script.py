"""screen_run.sh with fake pythons, a fake nvcc and a fake apt-get (bash; no pip, no network, no GPU): the step
order, the CUDA build arguments, the environment each step sees (CUBLAS_WORKSPACE_CONFIG, offline flags, no token),
the known-answer stop, the nvcc fallback, the exit trap's record and DONE.json."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import stat
import subprocess

import pytest
from conftest import TOOL

FAKE_PY = r"""#!/bin/bash
who="$(basename "$(dirname "$(dirname "$0")")")"
step=""
case "$*" in *screen_job.py\ *) step="$(echo "$*" | sed -E 's/.*screen_job.py ([a-z-]+).*/\1/')";; esac
echo "$who | $* | cublas=${CUBLAS_WORKSPACE_CONFIG:-unset} cvd=${CUDA_VISIBLE_DEVICES:-unset} offline=${HF_HUB_OFFLINE:-unset} tf=${TRANSFORMERS_OFFLINE:-unset} pp=${PYTHONPATH:-unset} cmake=${CMAKE_ARGS:-unset} force=${FORCE_CMAKE:-unset} cudacxx=${CUDACXX:-unset} token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
if [ -n "$step" ] && [ "${FAIL_STEP:-}" = "$step" ]; then exit "${FAIL_CODE:-1}"; fi
case "$*" in *"import sys, torch"*) exit "${TORCH_RC:-0}";; esac
case "$*" in *"pip freeze"*) echo "fake==1";; esac
exit 0
"""

FAKE_SYS = r"""#!/bin/bash
if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then
  for dir; do :; done
  mkdir -p "$dir/bin" && cp "$FAKE_PY" "$dir/bin/python" && chmod +x "$dir/bin/python"
  echo "sys | $* | token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
  exit 0
fi
echo "sys | $* | token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
exit 0
"""

FAKE_APT = r"""#!/bin/bash
echo "apt | $* | token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$CALLS"
if [ "${APT_RC:-0}" != "0" ]; then exit "$APT_RC"; fi
if [ "$1" = "install" ] || [ "$2" = "install" ] || [ "$3" = "install" ]; then
  mkdir -p "$APT_NVCC_DIR" && printf '#!/bin/bash\necho release 12.8\n' > "$APT_NVCC_DIR/nvcc" && chmod +x "$APT_NVCC_DIR/nvcc"
fi
exit 0
"""


def _exe(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def run_script(tmp_path, nvcc=True, **env_over):
    root = tmp_path / "screen"
    (root / "bundle/tool").mkdir(parents=True)
    shutil.copy(TOOL / "screen_run.sh", root / "bundle/tool/screen_run.sh")
    fakes = tmp_path / "fakes"
    fake_py = _exe(fakes / "fake_python", FAKE_PY)
    sys_py = _exe(fakes / "sys_python", FAKE_SYS)
    _exe(fakes / "bin/apt-get", FAKE_APT)
    nvcc_path = tmp_path / "usrlocal/cuda/bin/nvcc"
    if nvcc:
        _exe(nvcc_path, "#!/bin/bash\necho release 12.8\n")
    calls = tmp_path / "calls.log"
    env = {"PATH": f"{fakes / 'bin'}:/usr/bin:/bin", "SCREEN_ROOT": str(root), "SYS_PYTHON": str(sys_py),
           "SCREEN_VENVS": str(tmp_path / "venvs"), "SCREEN_NVCC": str(nvcc_path), "FAKE_PY": str(fake_py),
           "CALLS": str(calls), "APT_NVCC_DIR": str(tmp_path / "usrlocal/cuda-12.8/bin"),
           "HF_TOKEN": "hf_" + "T" * 34, "HUGGING_FACE_HUB_TOKEN": "hf_" + "U" * 34, "HF_HOME": "/elsewhere",
           "CUBLAS_WORKSPACE_CONFIG": "", **env_over}
    done = subprocess.run(["bash", str(root / "bundle/tool/screen_run.sh")], env=env, capture_output=True, text=True,
                          timeout=120)
    lines = calls.read_text().splitlines() if calls.exists() else []
    done_json = json.loads((root / "DONE.json").read_text())
    return done, lines, done_json, root


def kind(line: str) -> str:
    who, args = line.split(" | ")[:2]
    if "screen_job.py " in args:
        return f"{who}:" + args.split("screen_job.py ")[1].split()[0]
    if "-m venv" in args:
        return "venv-" + pathlib.Path(args.split()[-1]).name
    if "pip install" in args:
        if "llama-requirements" in args:
            return "llama-build"
        if "torch==2.8.0" in args:
            return f"{who}:torch-install"
        return f"{who}:pip-" + ("granite" if "granite-requirements" in args else "guard")
    if "pip freeze" in args:
        return f"{who}:freeze"
    if "import sys, torch" in args:
        return f"{who}:torch-check"
    return who + ":" + args.split()[0]


def test_steps_order_build_args_and_environment(tmp_path):
    done, lines, done_json, root = run_script(tmp_path)
    assert done.returncode == 0, done.stderr
    assert [kind(x) for x in lines] == [
        "venv-g", "g:pip-granite", "llama-build", "g:freeze", "g:llama-info", "venv-q", "q:torch-check",
        "q:pip-guard", "q:freeze", "q:download", "g:ka", "g:granite", "q:qwen", "sys:record"]
    by = {kind(x): x for x in lines}
    assert "--system-site-packages" in by["venv-q"] and "--system-site-packages" not in by["venv-g"]
    build = by["llama-build"]
    assert "--no-binary=llama-cpp-python --require-hashes" in build and "--no-deps" in build
    assert "cmake=-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80 force=1" in build
    assert "cudacxx=" + str(tmp_path / "usrlocal/cuda/bin/nvcc") in build
    assert "--only-binary=:all:" in by["g:pip-granite"] and "--only-binary=:all:" in by["q:pip-guard"]
    assert "--nvcc-source image" in by["g:llama-info"] and "--cmake-args -DGGML_CUDA=on" in by["g:llama-info"]
    assert "offline=unset tf=unset pp=bundle/engine" in by["q:download"]
    for step in ("g:ka", "g:granite", "q:qwen"):
        assert "offline=1 tf=1" in by[step] and "cublas=:4096:8 cvd=0" in by[step]
    assert "pp=bundle/engine" in by["q:qwen"] and "pp=unset" in by["g:ka"]
    assert all(x.endswith("token=") for x in lines)                         # no token reaches any step
    assert "--exit 0 --step done" in by["sys:record"]
    assert done_json["exit"] == 0 and done_json["step"] == "done" and (root / "STARTED.json").is_file()
    assert (root / "STEP").read_text().strip() == "done"
    assert str(tmp_path / "venvs") in by["venv-g"]                            # venvs off the /workspace volume


@pytest.mark.parametrize("fail_step,code", [("ka", 4), ("ka", 2), ("granite", 5), ("qwen", 1), ("llama-info", 2),
                                            ("download", 1)])
def test_a_failed_step_ends_the_job_and_done_records_it(tmp_path, fail_step, code):
    done, lines, done_json, root = run_script(tmp_path, FAIL_STEP=fail_step, FAIL_CODE=str(code))
    kinds = [kind(x) for x in lines]
    assert done_json["exit"] == code and done.returncode == code
    expect_step = {"llama-info": "llama-build"}.get(fail_step, fail_step)
    assert done_json["step"] == expect_step
    assert kinds[-1] == "sys:record" and f"--exit {code} --step {expect_step}" in lines[-1]
    after = {"ka": ["g:granite", "q:qwen"], "granite": ["q:qwen"], "qwen": [], "llama-info": ["venv-q", "g:ka"],
             "download": ["g:ka"]}[fail_step]
    assert not set(after) & set(kinds)                                      # nothing runs after a failed step


def test_nvcc_fallback_from_apt_and_its_failure(tmp_path):
    done, lines, done_json, root = run_script(tmp_path / "a", nvcc=False)
    kinds = [kind(x) for x in lines]
    assert done_json == {**done_json, "exit": 0, "step": "done"}
    assert kinds.index("apt:update") < kinds.index("apt:install") < kinds.index("llama-build")
    install = next(x for x in lines if x.startswith("apt | install"))
    assert all(p in install for p in ("cuda-nvcc-12-8", "cuda-cudart-dev-12-8", "libcublas-dev-12-8",
                                      "cuda-driver-dev-12-8"))
    assert "--nvcc-source apt" in next(x for x in lines if "llama-info" in x)
    assert "cudacxx=" + str(tmp_path / "a/usrlocal/cuda-12.8/bin/nvcc") in next(x for x in lines if "llama-req" in x)
    done, lines, done_json, root = run_script(tmp_path / "b", nvcc=False, APT_RC="100")
    assert done_json["exit"] != 0 and done_json["step"] == "llama-build"
    assert "llama-build" not in [kind(x) for x in lines]


def test_torch_installed_from_the_cu128_index_when_the_image_lacks_it(tmp_path):
    done, lines, done_json, root = run_script(tmp_path, TORCH_RC="1")
    kinds = [kind(x) for x in lines]
    assert done_json["exit"] == 1 and done_json["step"] == "venv-guard"         # the re-check fails too (fake)
    assert kinds.count("q:torch-check") == 2 and "q:torch-install" in kinds
    assert "--index-url https://download.pytorch.org/whl/cu128" in next(x for x in lines if "torch==2.8.0" in x)


def test_script_holds_no_token_and_unsets_the_cache_variables():
    text = (TOOL / "screen_run.sh").read_text()
    assert "unset HF_TOKEN HUGGING_FACE_HUB_TOKEN HF_HOME HF_HUB_CACHE TRANSFORMERS_CACHE XDG_CACHE_HOME" in text
    assert "export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0" in text
    assert 'CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80"' in text
    from conftest import P
    assert P.LLAMA_CMAKE_ARGS in text and os.path.basename(P.POD_VENVS) in text
