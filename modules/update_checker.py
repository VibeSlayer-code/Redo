import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from modules import storage


PYPI_URL = "https://pypi.org/pypi/redo-cli/json"
CACHE_SECONDS = 60 * 60 * 24
CURRENT_VERSION = "1.1.8"


def _result(code, status, message, data=None):
    result = {"code": code, "status": status, "message": message}
    if data is not None:
        result["data"] = data
    return result


def _version_tuple(version):
    parts = []
    for part in str(version).split("."):
        number = ""
        for char in part:
            if not char.isdigit():
                break
            number += char
        parts.append(int(number or 0))

    while len(parts) < 3:
        parts.append(0)

    return tuple(parts[:3])


def _is_newer(latest_version, current_version):
    return _version_tuple(latest_version) > _version_tuple(current_version)


def _fetch_latest_version():
    with urlopen(PYPI_URL, timeout=2.5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["info"]["version"]


def _cached_update_result(current_version):
    state_result = storage.load_state()
    if state_result["code"] != 0:
        return None

    cached = state_result["data"].get("update_check")
    if not isinstance(cached, dict):
        return None

    checked_at = cached.get("checked_at", 0)
    try:
        is_fresh = time.time() - float(checked_at) < CACHE_SECONDS
    except (TypeError, ValueError):
        return None

    if not is_fresh:
        return None

    latest_version = str(cached.get("latest_version", current_version))
    update_available = bool(cached.get("update_available", _is_newer(latest_version, current_version)))
    code = 2 if update_available else 0
    status = "warning" if update_available else "success"
    message = (
        f"Redo {latest_version} is available"
        if update_available
        else "Redo is up to date"
    )
    return _result(
        code,
        status,
        message,
        {
            "latest_version": latest_version,
            "current_version": current_version,
            "update_available": update_available,
            "source": "cache",
        },
    )


def _save_update_cache(latest_version, current_version):
    state_result = storage.load_state()
    state = state_result.get("data", {}) if state_result["code"] in {0, 2} else {}
    update_available = _is_newer(latest_version, current_version)
    state["update_check"] = {
        "checked_at": time.time(),
        "latest_version": latest_version,
        "update_available": update_available,
    }
    storage.save_state(state)


def check_for_update(current_version, force=False):
    if os.environ.get("REDO_DISABLE_UPDATE_CHECK") == "1":
        return _result(0, "success", "update check disabled", {"disabled": True})

    if not force:
        cached_result = _cached_update_result(current_version)
        if cached_result is not None:
            return cached_result

    try:
        latest_version = _fetch_latest_version()
    except (HTTPError, URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as error:
        return _result(
            2,
            "warning",
            f"could not check for updates: {error}",
            {"update_available": False, "error": str(error)},
        )

    update_available = _is_newer(latest_version, current_version)
    _save_update_cache(latest_version, current_version)

    if update_available:
        return _result(
            2,
            "warning",
            f"Redo {latest_version} is available",
            {
                "latest_version": latest_version,
                "current_version": current_version,
                "update_available": True,
                "source": "network",
            },
        )

    return _result(
        0,
        "success",
        "Redo is up to date",
        {
            "latest_version": latest_version,
            "current_version": current_version,
            "update_available": False,
            "source": "network",
        },
    )
