from pathlib import Path

from saveables.contracts.constants import root, write_mode
from saveables.hdf5_format.h5_file import H5File
from saveables.hdf5_format.h5_filenode import H5FileNode


def test_h5file_open(local_tmp: Path) -> None:
    """
    test h5file creates root node upon opening

    Args:
        local_tmp (Path): temporary directory for test
    """
    # create h5file and open it
    tmpfile = local_tmp / "test.h5"
    file = H5File(path=tmpfile, mode=write_mode)
    file.open()

    # check that root node has been created correctly
    assert isinstance(file.root, H5FileNode)
    assert file.root.name == root
    assert file.root.parent is None
    assert file.root._group.name == f"/{root}"
