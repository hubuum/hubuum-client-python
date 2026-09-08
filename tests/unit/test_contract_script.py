from __future__ import annotations

import subprocess
import sys
import urllib.request
from pathlib import Path
from runpy import run_path

import pytest

from hubuum_client import (
    OPENAPI_SERVER_REVISION,
    OPENAPI_SERVER_SHA256,
    OPENAPI_SERVER_VERSION,
)


def test_v0012_contract_constants_match_validation_script() -> None:
    repository_root = Path(__file__).parents[2]
    values = run_path(str(repository_root / "scripts" / "check-openapi-contract.py"))

    assert values["TARGET_REVISION"] == OPENAPI_SERVER_REVISION
    assert values["TARGET_SHA256"] == OPENAPI_SERVER_SHA256
    assert values["TARGET_VERSION"] == OPENAPI_SERVER_VERSION


def test_default_contract_check_uses_vendored_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = Path(__file__).parents[2]
    values = run_path(str(repository_root / "scripts" / "check-openapi-contract.py"))

    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"unexpected network request: {args!r}, {kwargs!r}")

    monkeypatch.setattr(urllib.request, "urlopen", reject_network)

    assert values["LOCAL_OPENAPI"] == repository_root / "docs" / "openapi.json"
    assert values["main"]([]) == 0


def test_contract_script_upstream_check_and_update_are_explicit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).parents[2]
    values = run_path(str(repository_root / "scripts" / "check-openapi-contract.py"))
    main = values["main"]
    main_globals = main.__globals__
    destination = tmp_path / "docs" / "openapi.json"
    destination.parent.mkdir()
    payload = b'{"openapi":"3.1.0"}\n'
    validated_sources: list[str] = []

    def validate(source: str) -> bytes:
        validated_sources.append(source)
        return payload

    monkeypatch.setitem(main_globals, "LOCAL_OPENAPI", destination)
    monkeypatch.setitem(main_globals, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setitem(main_globals, "validate", validate)

    assert main(["--check-upstream"]) == 0
    assert not destination.exists()
    assert main(["--update"]) == 0
    assert destination.read_bytes() == payload
    assert validated_sources == [values["TARGET_URL"], values["TARGET_URL"]]


def test_contract_script_rejects_non_https_remote_source() -> None:
    repository_root = Path(__file__).parents[2]
    result = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "check-openapi-contract.py"),
            "http://example.test/openapi.json",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "existing local file or an absolute HTTPS URL" in result.stderr
