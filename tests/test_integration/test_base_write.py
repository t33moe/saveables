import pytest
from resources.data import (  # type: ignore[import-not-found, import-untyped]
    data_field_dict,
    data_field_int,
    data_field_list,
    data_field_saveable,
    data_field_set,
    data_field_tuple,
)
from resources.mocks import MockedBaseNode  # type: ignore[import-not-found, import-untyped] # noqa: E501

from saveables.contracts.constants import dict_keys, dict_values
from saveables.contracts.data_type import python_type_literal_map
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData


def test_write_simple_dictionary():
    """
    integration test for writing dictionaries
    """

    # create expected meta data
    meta_keys = MetaData(
        python_type=python_type_literal_map[dict],
        name="my_dict",
        role=dict_keys,
        element_type=python_type_literal_map[int],
    )
    meta_values = MetaData(
        python_type=python_type_literal_map[dict],
        name="my_dict",
        role=dict_values,
        element_type=python_type_literal_map[str],
    )

    # create Test class that tests arguments of write_simple_iterable
    class TestSimpleDictionaryNode(MockedBaseNode):

        def write_simple_iterable(self, data_field):
            super().write_simple_iterable(data_field)
            if self._calls["write_simple_iterable"] == 1:
                assert data_field.value == list(data_field_dict.value.keys())
                assert data_field.meta == meta_keys
            elif self._calls["write_simple_iterable"] == 2:
                assert data_field.value == list(data_field_dict.value.values())
                assert data_field.meta == meta_values
            else:
                assert False, (
                    f"method write_simple_iterable has been called"
                    f" {self._calls['write_simple_iterable']} times and not 2 times"
                )

    # perform test
    node = TestSimpleDictionaryNode(name="test", parent=None)
    node.write_simple_dictionary(data_field_dict)


@pytest.mark.parametrize(
    "data_field, call_key, n_calls",
    [
        (data_field_int, "write_primitive_data", 1),
        (data_field_list, "write_simple_iterable", 1),
        (data_field_set, "write_simple_iterable", 1),
        (data_field_tuple, "write_simple_iterable", 1),
        (data_field_dict, "write_simple_iterable", 2),
    ],
)
def test_write_data_native_python_types(
    data_field: DataField, call_key: str, n_calls: int
):
    """
    integration test for writing native python types to a file

    Args:
        data_field (DataField): mocked data to be written
        call_key (str): name of method expected to be called
        n_calls (int): expected number of method calls
    """
    # initialize node
    node = MockedBaseNode(name="test", parent=None)

    # call write_data
    node.write_data(data_field)

    # check that write_data has called correct abstract method
    assert list(node._calls.keys()) == [call_key]
    assert node._calls[call_key] == n_calls


def test_write_data_saveable():
    """
    integration test for writing saveable to a file
    """
    # initialize root
    root = MockedBaseNode(name="root", parent=None)

    # write saveable datafield
    root.write_data(data_field_saveable)

    # check that the method write_data has created a subnode for each saveable
    assert len(root.list_children()) == 1
    child = root.list_children()[0]
    assert len(child.list_children()) == 1
    grandchild = child.list_children()[0]

    # check that within each subnode the correct write methods have been called
    assert child._calls == {"write_primitive_data": 1, "write_simple_iterable": 1}
    assert grandchild._calls == {"write_primitive_data": 4, "write_none": 1}
