from src.base.base_file_node import BaseFileNode
from src.saveable.data_field import DataField
from src.saveable.meta_data import MetaData


class MockedFileData:

    def __init__(self, data_field: DataField):
        self.data_field = data_field


class MockedBaseNode(BaseFileNode[MockedFileData]):

    def __init__(self, name, parent, *args, **kwargs):
        super().__init__(name, parent, *args, **kwargs)
        self._calls: dict[str, int] = dict()
        self._children: list[BaseFileNode[MockedFileData]] = []

    def __iter__(self):
        yield from []

    def list_children(self) -> list[BaseFileNode]:
        return self._children

    def create_child_node(self, meta: MetaData) -> BaseFileNode:
        child = MockedBaseNode(name=f"child_of_{self.name}", parent=self)
        self._children.append(child)
        return child

    def write_primitive_data(self, data_field: DataField):
        if "write_primitive_data" not in self._calls:
            self._calls["write_primitive_data"] = 1
        else:
            self._calls["write_primitive_data"] += 1

    def write_simple_iterable(self, data_field: DataField):
        if "write_simple_iterable" not in self._calls:
            self._calls["write_simple_iterable"] = 1
        else:
            self._calls["write_simple_iterable"] += 1

    def write_none(self, data_field: DataField):
        if "write_none" not in self._calls:
            self._calls["write_none"] = 1
        else:
            self._calls["write_none"] += 1

    def read_primitive_data(self, filedata) -> DataField:  # type: ignore[return]
        """read file data that holds primitive python data like int, str, float etc."""
        if "read_primitive_data" not in self._calls.keys():
            self._calls["read_primitive_data"] = 1
        else:
            self._calls["read_primitive_data"] += 1

    def read_simple_iterable(self, filedata) -> DataField | None:  # type: ignore[return] # noqa: E501
        """read list, set or tuples whose elements have all the same type"""
        if "read_simple_iterable" not in self._calls.keys():
            self._calls["read_simple_iterable"] = 1
        else:
            self._calls["read_simple_iterable"] += 1

    def read_simple_dictionary(self, filedata) -> DataField | None:  # type: ignore[return] # noqa: E501
        """
        read dictionaries whose keys have all
        the same type and whose values have all the same type
        """
        if "read_simple_dictionary" not in self._calls.keys():
            self._calls["read_simple_dictionary"] = 1
        else:
            self._calls["read_simple_dictionary"] += 1
