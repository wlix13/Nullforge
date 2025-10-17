"""Utility functions for merging and ensuring models."""

from collections.abc import Mapping
from typing import Any

from .dns import DnsMold
from .docker import DockerMold
from .features import ALLOWED_FEATURES_LAYERS, FeaturesMold
from .inet import InetMold
from .profiles import ProfilesMold
from .system import SystemMold
from .tor import TorMold
from .user import UserMold
from .warp import WarpMold
from .xray import XrayCoreMold


def _deep_merge_dicts(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    """
    Recursively merge dict b into dict a without mutating a.
    None/empty containers in b will overwrite a.
    """

    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


def _to_features_fragment(value: object) -> dict[str, Any]:
    """
    Accept a full FeaturesMold, any sub-mold (UserMold, WarpMold, ...), a mapping,
    or None; return a dict fragment suitable for deep-merge into FeaturesMold.
    """

    match value:
        case None:
            return {}
        case FeaturesMold():
            return value.model_dump()
        case UserMold():
            return {"users": value.model_dump()}
        case ProfilesMold():
            return {"profiles": value.model_dump()}
        case DnsMold():
            return {"dns": value.model_dump()}
        case WarpMold():
            return {"warp": value.model_dump()}
        case DockerMold():
            return {"docker": value.model_dump()}
        case InetMold():
            return {"inet": value.model_dump()}
        case TorMold():
            return {"tor": value.model_dump()}
        case XrayCoreMold():
            return {"xray": value.model_dump()}
        case Mapping():
            prepared = {k: (v.model_dump() if isinstance(v, *ALLOWED_FEATURES_LAYERS) else v) for k, v in value.items()}
            return FeaturesMold.model_validate(prepared).model_dump()
        case _:
            raise TypeError(f"Unsupported features layer type: {type(value)!r}")


def merge_features(base: FeaturesMold, *layers: object | None) -> FeaturesMold:
    """Start from base FeaturesMold, deep-merge each layer (full mold, sub-mold, dict, or None)."""

    acc = base.model_dump()
    for layer in layers:
        if layer is None:
            continue
        acc = _deep_merge_dicts(acc, _to_features_fragment(layer))
    return FeaturesMold.model_validate(acc)


def ensure_features(value: Any | None) -> FeaturesMold:
    """
    Coerce whatever is in inventory (None/dict/Features) into a Features instance,
    falling back to model defaults when absent.
    """

    match value:
        case None:
            return FeaturesMold()
        case FeaturesMold():
            return value
        case Mapping():
            return FeaturesMold.model_validate(value)
        case _:
            raise TypeError("host.data.features must be FeaturesMold or dict or None")


def _to_system_dict(value: SystemMold | Mapping[str, Any]) -> dict[str, Any]:
    match value:
        case SystemMold():
            return value.model_dump()
        case Mapping():
            return SystemMold.model_validate(value).model_dump()


def merge_system(base: SystemMold, *layers: SystemMold | Mapping[str, Any] | None) -> SystemMold:
    """
    - start from base SystemMold
    - apply each layer (dict or SystemMold), deep-merging into the accumulated dict
    """

    acc = base.model_dump()
    for layer in layers:
        if layer is None:
            continue
        acc = _deep_merge_dicts(acc, _to_system_dict(layer))
    return SystemMold.model_validate(acc)


def ensure_system(value: Any | None) -> SystemMold:
    """
    Coerce whatever is in inventory (None/dict/SystemMold) into a SystemMold instance,
    falling back to model defaults when absent.
    """

    match value:
        case None:
            return SystemMold()
        case SystemMold():
            return value
        case Mapping():
            return SystemMold.model_validate(value)
        case _:
            raise TypeError("host.data.system must be SystemMold or dict or None")
