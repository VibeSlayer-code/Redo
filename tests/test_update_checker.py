import time

from modules import storage, update_checker


def test_check_for_update_detects_newer_version(tmp_path, monkeypatch):
    monkeypatch.delenv("REDO_DISABLE_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    monkeypatch.setattr(update_checker, "_fetch_latest_version", lambda: "1.1.6")

    result = update_checker.check_for_update("1.1.5", force=True)

    assert result["code"] == 2
    assert result["status"] == "warning"
    assert result["data"]["update_available"] is True
    assert result["data"]["latest_version"] == "1.1.6"


def test_check_for_update_uses_fresh_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("REDO_DISABLE_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    storage.save_state(
        {
            "update_check": {
                "checked_at": time.time(),
                "latest_version": "1.1.6",
                "update_available": True,
            }
        }
    )
    monkeypatch.setattr(
        update_checker,
        "_fetch_latest_version",
        lambda: (_ for _ in ()).throw(AssertionError("network should not be called")),
    )

    result = update_checker.check_for_update("1.1.5")

    assert result["code"] == 2
    assert result["data"]["source"] == "cache"


def test_disabled_update_check_returns_quiet_success(monkeypatch):
    monkeypatch.setenv("REDO_DISABLE_UPDATE_CHECK", "1")

    result = update_checker.check_for_update("1.1.5", force=True)

    assert result["code"] == 0
    assert result["data"]["disabled"] is True
