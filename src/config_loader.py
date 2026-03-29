"""YAML configuration loading for the surrogate simulation project."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .utils import wavelength_grid_from_config


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file as a dictionary."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}, got {type(data).__name__}.")
    return data


def deep_merge_dicts(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge dictionaries without mutating the inputs."""
    merged = deepcopy(base)
    for key, value in update.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_config_bundle(config_dir: str | Path) -> dict[str, Any]:
    """Load the project configuration bundle from a config directory."""
    config_root = Path(config_dir)
    base_cfg = load_yaml(config_root / "base.yaml")
    telescope_cfg = load_yaml(config_root / "telescope_1m.yaml")
    detector_cfg = load_yaml(config_root / "detector.yaml")
    scenario_cfg = load_yaml(config_root / "scenarios.yaml")

    bundle = {
        "base": base_cfg,
        "telescope": telescope_cfg,
        "detector": detector_cfg,
        "scenarios": scenario_cfg.get("scenarios", []),
        "config_dir": str(config_root.resolve()),
    }
    if not bundle["scenarios"]:
        raise ValueError("config/scenarios.yaml must define a non-empty 'scenarios' list.")

    bundle["lam_nm"] = wavelength_grid_from_config(base_cfg["wavelength_nm"])
    bundle["merged_defaults"] = deep_merge_dicts(
        deep_merge_dicts(base_cfg, {"telescope": telescope_cfg}),
        {"detector": detector_cfg},
    )
    return bundle
