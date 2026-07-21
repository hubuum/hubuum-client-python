from __future__ import annotations

import subprocess
import sys
from pathlib import Path


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
