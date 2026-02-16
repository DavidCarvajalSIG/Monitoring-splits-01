from __future__ import annotations
from pathlib import Path
import yaml

def project_root() -> Path:
    # .../Monitoring-splits/src/config.py -> parents[1] = Monitoring-splits
    return Path(__file__).resolve().parents[1]

def load_apps_config(path: str = "config/apps.yml") -> dict:
    cfg_path = project_root() / path
    if not cfg_path.exists():
        raise FileNotFoundError(f"No existe {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def resolve_dataset(cfg: dict, app_key: str, dataset_key: str) -> dict:
    apps = cfg.get("apps", {})
    if app_key not in apps:
        raise KeyError(f"App '{app_key}' no existe en config.")
    datasets = apps[app_key].get("datasets", {})
    if dataset_key not in datasets:
        raise KeyError(f"Dataset '{dataset_key}' no existe para app '{app_key}'.")
    ds = datasets[dataset_key].copy()
    # Resolver file path a absoluto
    ds["file_abs"] = str(project_root() / ds["file"])
    return ds
