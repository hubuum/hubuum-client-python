from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from runpy import run_path

from hubuum_client import (
    OPENAPI_SERVER_REVISION,
    OPENAPI_SERVER_SHA256,
    OPENAPI_SERVER_VERSION,
)


def test_v008_contract_constants_match_validation_script() -> None:
    repository_root = Path(__file__).parents[2]
    values = run_path(str(repository_root / "scripts" / "check-openapi-contract.py"))

    assert values["TARGET_REVISION"] == OPENAPI_SERVER_REVISION
    assert values["TARGET_SHA256"] == OPENAPI_SERVER_SHA256
    assert values["TARGET_VERSION"] == OPENAPI_SERVER_VERSION


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
