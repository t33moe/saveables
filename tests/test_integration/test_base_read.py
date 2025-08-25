from __future__ import annotations

from dataclasses import replace
from typing import Generator

import pytest
from resources.data import (create_saveable_from_datafields, data_field_int,
                            data_field_list, data_field_saveable,
                            data_field_set, data_field_tuple)
from resources.mocks import MockedBaseNode, MockedFileData

from saveables.contracts.constants import empty_type, saveable
from saveables.contracts.data_type import (python_type_literal_map,
                                           python_type_literal_map_reversed)
from saveables.saveable.data_field import DataField
from saveables.saveable.saveable import Saveable


@pytest.mark.parametrize(
    "data_fields, calls",
    [
        ([data_field_int], {"read_primitive_data": 1}),
        ([data_field_list], {"read_simple_iterable": 1}),
        ([data_field_tuple], {"read_simple_iterable": 1}),
        ([data_field_set], {"read_simple_iterable": 1}),
        ([data_field_saveable], {}),
    ],
)
def test_load(data_fields: list[DataField], calls: dict[str, int]) -> None:
    """
    integration test for reading data from a file
    Args:
        data_fields (list[DataField]): mocked data to be read from file
        calls (dict[str, int]): dictionary that holds method names and
                                expected number of their calls

    """

    # create saveable class from given data fields
    saveable_cls = create_saveable_from_datafields("root_class", data_fields)
    loaded: Saveable = saveable_cls()

    # make dummy changes to data_fields such that they differ from default values
    class DummyChanger:
        """makes dummy changes to given saveable object"""

        def __init__(self, obj: Saveable):
            self.obj = replace(
                obj
            )  # make copy of object, since changing the original effects other tests

        def change_values(self) -> None:
            """make dummy change to given saveable"""
            for data_field in self.obj.iter_fields():
                # change value according to their type
                if isinstance(data_field.value, str):
                    new_value = self._changed_str(data_field)
                elif isinstance(data_field.value, int) or isinstance(
                    data_field.value, float
                ):
                    new_value = self._changed_int_or_float(data_field)  # type: ignore[assignment] # noqa: E501
                elif (
                    isinstance(data_field.value, tuple)
                    or isinstance(data_field.value, set)
                    or isinstance(data_field.value, list)
                ):
                    new_value = self._changed_iterable(data_field)  # type: ignore[assignment] # noqa: E501
                elif isinstance(data_field.value, Saveable):
                    changer = DummyChanger(data_field.value)
                    changer.change_values()
                    new_value = changer.obj
                elif data_field.value is None:
                    new_value = None
                else:
                    msg = (
                        f"unexpected case for value {data_field.value} "
                        f"of {data_field.meta.name}"
                    )
                    raise ValueError(msg)

                # set attribute value
                setattr(self.obj, data_field.meta.name, new_value)

        def _changed_bool(self, data_field: DataField) -> bool:
            return not data_field.value

        def _changed_int_or_float(self, data_field: DataField) -> int:
            return data_field.value + 1  # type: ignore[no-any-return]

        def _changed_str(self, data_field: DataField) -> str:
            return f"{data_field.value}_dummy_change"

        def _changed_iterable(self, data_field: DataField) -> list | tuple | set:  # type: ignore[type-arg] # noqa: E501
            element_type_ = data_field.meta.element_type

            if element_type_ == python_type_literal_map[str]:
                # add new string element to iterable
                new_value = list(data_field.value)
                new_value.append("dummy_change")
            elif element_type_ == python_type_literal_map[int]:
                # add new integer to iterable
                new_value = list(data_field.value)
                new_value.append(1)
            elif element_type_ == empty_type:
                new_value = [1]
            else:
                raise ValueError("element type is supposed to integer or string")

            # restore original iterable type
            python_type_ = python_type_literal_map_reversed[data_field.meta.python_type]
            return python_type_(new_value)  # type:ignore[no-any-return]

    for data_field in data_fields:
        if isinstance(data_field.value, Saveable):
            changer = DummyChanger(data_field.value)
            changer.change_values()
            data_field.value = changer.obj

    # ensure that each datafield from loaded differs from original datafield
    for default_datafield, data_field in zip(loaded.iter_fields(), data_fields):
        assert default_datafield.value != data_field.value

    # create node class that implements simple reading routines
    class TestNode(MockedBaseNode):  # type: ignore[misc]

        def __init__(
            self, name: str, parent: TestNode | None, data_fields: list[DataField]
        ):
            super().__init__(name, parent)
            self._data_fields = data_fields

        def __iter__(self) -> Generator[tuple[MockedFileData, type], None, None]:
            for data_field in self._data_fields:
                type_ = python_type_literal_map_reversed[data_field.meta.python_type]
                yield MockedFileData(data_field=data_field), type_

        def list_children(self) -> list[TestNode]:

            children: list[TestNode] = []
            file_data: MockedFileData
            for file_data, _ in self:
                if file_data.data_field.meta.python_type == saveable:
                    data_fields_ = list(file_data.data_field.value.iter_fields())
                    node = TestNode(
                        file_data.data_field.meta.name,
                        parent=self,
                        data_fields=data_fields_,
                    )
                    children.append(node)
            return children

        def read_primitive_data(self, filedata: MockedFileData) -> DataField:
            super().read_primitive_data(filedata)
            return filedata.data_field

        def read_simple_iterable(self, filedata: MockedFileData) -> DataField | None:
            super().read_simple_iterable(filedata)
            return filedata.data_field

        def read_simple_dictionary(self, filedata: MockedFileData) -> DataField | None:
            super().read_simple_dictionary(filedata)
            return filedata.data_field

    # call load method
    node = TestNode(name="root", parent=None, data_fields=data_fields)
    node.load(loaded)

    # check that method has loaded data correctly
    for loaded_data_field, data_field in zip(loaded.iter_fields(), data_fields):
        assert loaded_data_field.value == data_field.value

    # check that expected methods have been called
    assert node._calls == calls
