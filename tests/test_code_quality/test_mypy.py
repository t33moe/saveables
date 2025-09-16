import re
import subprocess
from pathlib import Path


def test_mypy() -> None:
    """run mypy in source folder and check output"""
    # run mypy
    cwd = str(Path(__file__).parent.parent.parent)
    result = subprocess.run(["mypy", "src"], capture_output=True, text=True, cwd=cwd)
    # check that process has terminated w/o error
    assert result.returncode == 0
    # check that no mypy issues have been found
    assert "no issues found" in result.stdout
    # check that the number of checked files has not been zero
    match = re.search(r"(\d+) source files", result.stdout)
    assert match is not None
    num_files = int(match.group(1))
    assert num_files > 0
