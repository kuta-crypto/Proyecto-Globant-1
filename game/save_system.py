import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

def default_save_path() -> Path:
    if getattr(sys, "frozen", False):
        # One-file bundles extract resources to a temporary directory.
        # Keep player data in a stable, writable location outside the bundle.
        local_data = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return local_data / "TimbaRNG" / "saves" / "save.json"
    return Path("saves") / "save.json"


DEFAULT_SAVE_PATH = default_save_path()


def ensure_save_dir(path: str | Path) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def save_game(player_state: Any, path: str | Path = DEFAULT_SAVE_PATH) -> Dict[str, Any]:
    file_path = ensure_save_dir(path)
    payload = player_state.to_dict() if hasattr(player_state, "to_dict") else player_state
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return payload


def load_game(path: str | Path = DEFAULT_SAVE_PATH) -> Dict[str, Any]:
    file_path = ensure_save_dir(path)
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        return {}
    return {}
