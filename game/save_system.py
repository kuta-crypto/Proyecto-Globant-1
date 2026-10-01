import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_SAVE_PATH = Path("saves") / "save.json"


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
