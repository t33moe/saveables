import pytest
from resources.data import (  # type: ignore[import-not-found, import-untyped]
    HoldsDicts,
    HoldsLists,
    HoldsNestedData,
    HoldsPrimitives,
    HoldsSets,
    HoldsTuples,
    dicts,
    lists,
    nested0,
    primitives,
    sets,
    tuples,
)

from saveables.contracts.constants import read_mode, write_mode
from saveables.hdf5_format.h5_file import H5File


@pytest.mark.parametrize(
    "obj, cls_",
    [
        (lists, HoldsLists),
        (dicts, HoldsDicts),
        (tuples, HoldsTuples),
        (primitives, HoldsPrimitives),
        (sets, HoldsSets),
        (nested0, HoldsNestedData),
    ],
)
def test_write_load_hdf5(local_tmp, obj, cls_):
    """
    system test to write and read data to and from a given file

    Args:
        local_tmp (Path): temporary directory for test data
        obj (see cls_): data to be written / read
        cls_ (Type): class of data
    """

    # write file to hdf5
    filename = "test.h5"
    h5_path = local_tmp / filename
    with H5File(h5_path, mode=write_mode) as f:
        f.save(obj)

    # load data from file
    loaded = cls_()
    with H5File(h5_path, mode=read_mode) as f:
        f.load(loaded)

    # check if loaded data matches written data
    assert loaded == obj
