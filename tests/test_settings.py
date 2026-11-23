"""Unit tests for persistent UI settings (app/settings.py)."""

import json

import pytest

from app import settings


@pytest.fixture(autouse=True)
def _fresh_settings():
    settings.reset_to_defaults()
    yield
    settings.reset_to_defaults()


@pytest.mark.unit
class TestSettings:
    def test_missing_file_gives_defaults(self, tmp_path):
        loaded = settings.load(str(tmp_path / "nope.json"))
        assert loaded == settings.DEFAULTS

    def test_save_load_round_trip(self, tmp_path):
        path = str(tmp_path / "settings.json")
        settings.set("view.logo", False)
        settings.set("ppi.history", 120)
        assert settings.save(path)
        settings.reset_to_defaults()
        loaded = settings.load(path)
        assert loaded["view.logo"] is False
        assert loaded["ppi.history"] == 120

    def test_unknown_and_mistyped_values_fall_back(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"view.ppi": "yes", "ppi.history": True,
                                    "fft.y_min": -90, "bogus.key": 1}))
        loaded = settings.load(str(path))
        assert loaded["view.ppi"] is True            # string rejected
        assert loaded["ppi.history"] == settings.DEFAULTS["ppi.history"]  # bool is not an int here
        assert loaded["fft.y_min"] == -90.0 and isinstance(loaded["fft.y_min"], float)
        assert "bogus.key" not in loaded

    def test_corrupt_file_gives_defaults(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text("{not json")
        assert settings.load(str(path)) == settings.DEFAULTS

    def test_snapshot_restore(self):
        snap = settings.snapshot()
        settings.set("ppi.rings", False)
        settings.restore(snap)
        assert settings.get("ppi.rings") is True

    def test_set_unknown_key_raises(self):
        with pytest.raises(KeyError):
            settings.set("nope", 1)
