from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pytest

from saveables.contracts.constants import attribute, none_type, saveable
from saveables.contracts.data_type import python_type_literal_map
from saveables.hdf5_format.h5_filenode import H5FileNode
from saveables.saveable.meta_data import MetaData
from saveables.saveable.utils import get_element_type


@pytest.mark.parametrize("data", [[1, 2, 3], (1, 2, 3), {1, 2, 3}])
def test_create_dataset_simple_iterable(
    local_tmp: Path, data: list[Any] | tuple[Any] | set[Any]
) -> None:
    """
    test h5 data set creation with meta data

    Args:
        local_tmp (Path): temporary directory for test
        data (list  | tuple | set ): test data
    """
    tmpfile = local_tmp / "dataset.h5"

    with h5py.File(tmpfile, "w") as h5f:
        # create file node
        node = H5FileNode(name="test", parent=None, group=h5f)

        # create meta data
        python_type_ = python_type_literal_map[type(data)]
        element_type_ = python_type_literal_map[get_element_type(data)]
        meta = MetaData(
            python_type=python_type_,
            role=attribute,
            name="mydata",
            element_type=element_type_,
        )

        # preprocess data
        data_ = np.array(list(data))
        dtype = data_.dtype

        # call _create_dataset and check results
        node._create_dataset("mydata", data_, dtype=dtype, meta=meta)
        assert "mydata" in h5f
        dset = h5f["mydata"]
        assert type(data)(dset[:].tolist()) == data  # type: ignore[misc]
        for field in meta.__dataclass_fields__:
            assert dset.attrs[field] == str(getattr(meta, field))


def test_list_children_h5(local_tmp: Path) -> None:
    """
    test that children of a H5FileNode are listed correctly

    Args:
        local_tmp (Path): temporary test directory
    """

    # create temporary test h5 file
    tmpfile = local_tmp / "list_children.h5"

    with h5py.File(tmpfile, "w") as h5f:
        # create a structure with two direct child groups and one nested group
        h5f.create_group("group1")
        h5f.create_group("group2")
        h5f.create_group("group1/subgroup")

        # create file node and list children
        node = H5FileNode(name="test", parent=None, group=h5f)
        children = node.list_children()

        # only direct children should be returned
        child_names = sorted(child.name for child in children)
        assert child_names == ["group1", "group2"]


def test_create_child_node(local_tmp: Path) -> None:
    """
    test that child nodes are created correctly

    Args:
        local_tmp (Path): temporary test directory
    """

    # create temporary test h5 file
    tmpfile = local_tmp / "create_child_node.h5"

    with h5py.File(tmpfile, "w") as h5f:
        root_node = H5FileNode(name="root", parent=None, group=h5f)

        meta = MetaData(
            name="child1", python_type=saveable, role=attribute, element_type=none_type
        )

        child_node = root_node.create_child_node(meta)

        # test that there is a child group in the h5
        assert "child1" in h5f
        assert isinstance(h5f["child1"], h5py.Group)

        # return value must be a H5FileNode
        assert isinstance(child_node, H5FileNode)
        assert child_node.name == "child1"
        assert child_node.parent is root_node
