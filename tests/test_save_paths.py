from pathlib import Path
import sys

from game.save_system import default_save_path, load_game, save_game


def test_source_keeps_existing_save_location(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert default_save_path() == Path("saves/save.json")


def test_executable_save_survives_working_directory_change(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user-data"))
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    monkeypatch.chdir(first_dir)
    save_game({"gold": 123}, default_save_path())
    monkeypatch.chdir(second_dir)
    assert load_game(default_save_path()) == {"gold": 123}
    assert not (second_dir / "saves").exists()
