import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def local_tmp(request) -> Path:  # type: ignore[no-untyped-def]
    """create temporary directory folder for data during test"""
    # get directory of test
    test_dir = request.node.path.parent

    # new directory for test data
    tmp_name = request.node.name.replace("[", "__").replace("]", "__")
    tmp_dir: Path = test_dir / "tmp" / tmp_name

    # delete directory that has been created from older run
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    # create directory
    os.makedirs(tmp_dir)

    return tmp_dir
