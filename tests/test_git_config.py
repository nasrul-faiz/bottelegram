import importlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_configure_git_python_sets_git_path(monkeypatch, tmp_path):
    git_bin = tmp_path / "git"
    git_bin.write_text("#!/bin/sh\nexit 0\n")
    git_bin.chmod(0o755)

    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.delenv("GIT_PYTHON_GIT_EXECUTABLE", raising=False)
    monkeypatch.delenv("GIT_PYTHON_REFRESH", raising=False)

    import config
    importlib.reload(config)

    assert os.environ.get("GIT_PYTHON_GIT_EXECUTABLE") == str(git_bin)
    assert os.environ.get("GIT_PYTHON_REFRESH") == "quiet"
