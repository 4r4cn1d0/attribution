"""Test oracle for B11: a port of the math of the official Safe LoRA code, ``model.py`` of github.com/IBM/SafeLoRA
(commit dc756cf5, as the SL note read it on 16 Oct 2026). Test code only; never imported by the transform.

Licence notice. The official repository is licensed under the Apache License, Version 2.0
(http://www.apache.org/licenses/LICENSE-2.0); SL section 1 records the licence field and the file headers. This file
is a modified, reduced re-implementation of that file's math (no file text is copied): class SafeLoRA, its
get_aligned_matrix and its projected_weighted, with the "number" (top-K) and "threshold" selections. Changes: plain
functions instead of a class; models passed in instead of loaded from paths; no printing; the first pass of the
"number" mode uses the threshold -1 (the code's value since its 10 Sep 2025 commit; SL section 5 item 10); the
distance diagnostic is dropped. The builder wrote it from the SL note's description of the code and from memory of
its structure; it was NOT diffed against the repository file here (no network). The lead should diff it before
relying on it as the official code.

Behaviour kept on purpose (SL section 3 rows 5, 9, 10, 11), because these are what the oracle compares:
- V pairs the base and aligned parameters BY POSITION (zip of named_parameters), keeping names that contain a
  target-module string; the adapter's lora_B tensors are paired with that list by position too;
- C = V V^T / ||V||_F is formed as an out x out matrix (torch.mm) in the models' dtype (float32 here);
- lora_A and lora_B are told apart by their first dimension (lora_A has r rows);
- the cosine is the cosine of the flattened products C B A and B A, rounded to 5 decimals with numpy.round;
- a matrix is projected when its rounded cosine is <= the threshold; in "number" mode the threshold is the K-th
  smallest rounded cosine of a first pass, so ties can project more than K.
"""

from __future__ import annotations

import copy

import numpy
import torch


def get_aligned_matrix(base_model: torch.nn.Module, aligned_model: torch.nn.Module,
                       target_modules: list[str]) -> list[torch.Tensor]:
    """One C = V V^T / ||V||_F per targeted parameter, in the models' parameter order (position pairing)."""
    out = []
    for (_, b_param), (a_name, a_param) in zip(base_model.named_parameters(), aligned_model.named_parameters()):
        if any(module in a_name for module in target_modules):
            assert b_param.shape == a_param.shape, "the base and aligned weights must have one shape"
            vec = a_param - b_param
            vec = torch.mm(vec, vec.t()) / torch.norm(vec)
            out.append(vec.detach().cpu())
    return out


def projected_weighted(peft_model: torch.nn.Module, model_ori: torch.nn.Module, project_matrix: list[torch.Tensor],
                       r: int, thrs_cos: float) -> tuple[torch.nn.Module, list[float], list[str]]:
    """The official second pass: project each lora_B whose rounded cosine is <= thrs_cos (from the untouched
    copy model_ori). Returns the model, every rounded cosine in order, and the names of the projected lora_B."""
    idx, cos_total, projected = 0, [], []
    a_copy = None
    with torch.no_grad():
        for (name, param), (_, param_ori) in zip(peft_model.named_parameters(), model_ori.named_parameters()):
            if "lora" not in name:
                continue
            if param.shape[0] == r:
                a_copy = copy.deepcopy(param_ori)
            if param.shape[0] != r:
                p = project_matrix[idx].to(param.device)
                w = torch.mm(p, param_ori.data)
                f_w = torch.mm(w, a_copy)
                ori = torch.mm(param_ori, a_copy)
                w_new = torch.mm(p, param_ori.data)
                cos = numpy.round(torch.nn.functional.cosine_similarity(f_w.reshape(1, -1), ori.reshape(1, -1)).item(), 5)
                cos_total.append(cos)
                if cos <= thrs_cos:
                    param.data = w_new
                    projected.append(name)
                else:
                    param.data = param_ori
                idx += 1
    return peft_model, cos_total, projected


def official_safe_lora(peft_model: torch.nn.Module, base_model: torch.nn.Module, aligned_model: torch.nn.Module, *,
                       r: int, target_modules: list[str], select_layers_type: str, num_proj_layers: int = 10,
                       threshold: float = 0.5) -> tuple[torch.nn.Module, list[float], list[str]]:
    """The official flow on a PEFT model: build the C list, then select by "number" (top-K) or "threshold"."""
    model_ori = copy.deepcopy(peft_model)
    project_matrix = get_aligned_matrix(base_model, aligned_model, target_modules)
    if select_layers_type == "threshold":
        return projected_weighted(peft_model, model_ori, project_matrix, r, threshold)
    if select_layers_type == "number":
        _, cos, _ = projected_weighted(peft_model, model_ori, project_matrix, r, -1)
        thrs = numpy.sort(cos)[:num_proj_layers][-1]
        return projected_weighted(peft_model, model_ori, project_matrix, r, thrs)
    raise ValueError("select_layers_type is threshold or number")
