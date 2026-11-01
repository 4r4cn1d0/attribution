"""ENGINEERING FIXTURE transforms for the B10 hook tests (interface stage1-adapter-transform-v1). Each maps the
adapter's tensors (name -> float32 CPU tensor) and the context to (tensors, record). They stand for no method."""

INTERFACE = "stage1-adapter-transform-v1"


def identity(tensors, context):
    """K = 0 in Safe LoRA's terms: the source adapter, byte for byte."""
    return dict(tensors), {"op": "identity", "seed": context["source"]["seed"],
                           "source": context["source"]["adapter_fingerprint"], "lora_scale": context["lora"]["scale"]}


def half_b(tensors, context):
    """lora_B halved, lora_A kept (what scale 0.5 does)."""
    return {k: (v * 0.5 if ".lora_B." in k else v) for k, v in tensors.items()}, {"op": "half_b"}


def zero_b(tensors, context):
    import torch

    return {k: (torch.zeros_like(v) if ".lora_B." in k else v) for k, v in tensors.items()}, {"op": "zero_b"}


def change_a(tensors, context):
    return {k: (v * 2.0 if ".lora_A." in k else v) for k, v in tensors.items()}, {"op": "change_a"}


def nan_b(tensors, context):
    out = dict(tensors)
    name = sorted(k for k in out if ".lora_B." in k)[0]
    out[name] = out[name].clone()
    out[name].view(-1)[0] = float("nan")
    return out, {"op": "nan_b"}


def float64(tensors, context):
    return {k: v.double() for k, v in tensors.items()}, {"op": "float64"}


def bad_shape(tensors, context):
    out = dict(tensors)
    name = sorted(out)[0]
    out[name] = out[name][:1].clone()
    return out, {"op": "bad_shape"}


def missing_key(tensors, context):
    out = dict(tensors)
    out.pop(sorted(out)[0])
    return out, {"op": "missing_key"}


def long_record(tensors, context):
    return dict(tensors), {"op": "x" * 201}


def no_record(tensors, context):
    return dict(tensors)


def inplace_half_b(tensors, context):
    """lora_B halved IN PLACE: the input tensors themselves change, so B10 must hand the callable copies."""
    for name, tensor in tensors.items():
        if ".lora_B." in name:
            tensor.mul_(0.5)
    return tensors, {"op": "inplace_half_b"}
