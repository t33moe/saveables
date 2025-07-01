from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator, Generic, TypeVar

from saveables.contracts.constants import dict_keys, dict_values
from saveables.contracts.data_type import (
    EmptyIterable,
    python_type_literal_map,
    supported_primitive_data_types,
    tRole,
)
from saveables.python_utils import get_element_type
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.saveable import Saveable
from saveables.saveable.utils import is_simple_dictionary, is_simple_iterable

T = TypeVar("T")


class BaseFileNode(ABC, Generic[T]):
    """
    base class that provides format independet code to read / write
    data from / file
    """    

    def __init__(self, name: str, parent: BaseFileNode | None, *args, **kwargs):
        self.name = name
        self.parent = parent

    def read_python_attributes(self) -> list[DataField]:
        """
        read data from file that represents
        native python data type like str, int, list etc

        Returns:
            list: list of DataField objects holds data along with meta data
        """

        data_fields: list[DataField] = []
        data_field: DataField | None
        for data, python_type_ in self:
            if python_type_ in supported_primitive_data_types:
                data_field = self.read_primitive_data(data)
                data_fields.append(data_field)
            if python_type_ in (list, tuple, set):
                data_field = self.read_simple_iterable(data)
                if data_field is not None:
                    data_fields.append(data_field)
            if python_type_ == dict:
                data_field = self.read_simple_dictionary(data)
                if data_field is not None:
                    data_fields.append(data_field)
        return data_fields

    def write_data(self, data_field: DataField):
        """
        write data to node

        Args:
            data_field (DataField): object that holds data and
                                    meta data to be writen to node

        Raises:
            ValueError: raise ValueError if data type is not supported
                        and cannot be written to node
        """
        if data_field.value is None:
            self.write_none(data_field)
        elif type(data_field.value) in supported_primitive_data_types:
            self.write_primitive_data(data_field)
        elif isinstance(data_field.value, Saveable):
            self.write_saveable(data_field)
        elif is_simple_iterable(data_field.value):
            self.write_simple_iterable(data_field)
        elif is_simple_dictionary(data_field.value):
            self.write_simple_dictionary(data_field)
        else:
            raise ValueError(f"attribute {data_field.meta.name} cannot be saved")

    def write_saveable(self, data_field: DataField):
        """
        write saveable object along with its meta data to node

        Args:
            data_field (DataField): object that holds saveable
                                    and its meta data that is about
                                    to be written to node

        Raises:
            TypeError: if the data is not None and
                       does not inherit from Saveable
            ValueError: if data is None
        """
        # check if value is saveable
        if data_field.value is None:
            raise ValueError(
                f"value is not expected to be None for field {data_field.meta.name}"
            )
        if not isinstance(data_field.value, Saveable):
            raise TypeError(f"value of type {type(data_field.value)} is not supported")

        # create new sub node and save the fields
        sub_node = self.create_child_node(data_field.meta)
        for data_field in data_field.value.iter_fields():
            sub_node.write_data(data_field)

    def write_simple_dictionary(self, data_field: DataField):
        """
        write keys and values of a dictionary as lists into node

        Args:
            data_field (DataField): object that holds a dictionary
                                    and its meta data to be written into
                                    node

        Raises:
            TypeError: if data is not a dictionary that has
                       uniformly typed keys and values
        """

        # check if value type is correct
        if not is_simple_dictionary(data_field.value):
            msg = (
                f"value in {data_field.meta.name} is supposed to be a dictionary "
                f"with unformly typed keys and values"
            )
            raise TypeError(msg)

        # write dictionary keys as list
        self.write_dictionary_keys_or_values(data_field, dict_keys)

        # save dictionary values as a list
        self.write_dictionary_keys_or_values(data_field, dict_values)

    def write_dictionary_keys_or_values(self, data_field: DataField, role: tRole):
        """
        write keys or values of given dictionary as a list into node

        Args:
            data_field (DataField): object that holds the dictionary and its meta data
            role (tRole): role of the data. Can be either "dict_keys" or
                              "dict_values" which determines wether dictionary keys
                              or values shall be written to node

        Raises:
            ValueError: if an unexpected argument for role is used
            TypeError: if the type of dictionary keys / values
                       are not supported
        """
        if not isinstance(data_field.value, dict):
            raise TypeError(f"value in {data_field.meta.name} is supposed to be a list")

        # create data field for keys/values
        if role == dict_keys:
            value = list(data_field.value.keys())
        elif role == dict_values:
            value = list(data_field.value.values())
        else:
            raise ValueError(
                f"error while writing attribute {data_field.meta.name}. "
                f"Origin is expected to be {dict_keys} or {dict_values} but is {role}"
            )
        element_type = get_element_type(value)

        if (
            element_type not in supported_primitive_data_types
            and not element_type == EmptyIterable
        ):
            raise TypeError(
                f"element type in attribute {data_field.meta.name} ({role})"
                f" is {element_type} which is not supported"
            )
        element_type_literal = python_type_literal_map[element_type]
        meta = MetaData(
            data_field.meta.python_type,
            role,
            data_field.meta.name,
            element_type_literal,  # type: ignore[arg-type]
        )
        data_field_to_write = DataField(value=value, meta=meta)

        # write keys / values as list in file
        self.write_simple_iterable(data_field_to_write)

    def load(self, saveable: Saveable):
        """
        load data from node to given saveable

        Args:
            saveable (Saveable): object the node's data is written into

        Raises:
            AttributeError: if data in node is
                            supposed for a field that the saveable
                            object does not possess
        """

        # load standard python data
        for data_field in self.read_python_attributes():
            if not hasattr(saveable, data_field.meta.name):
                raise AttributeError(
                    f"object {saveable} does not have"
                    f"expected attribute {data_field.meta.name}"
                )
            setattr(saveable, data_field.meta.name, data_field.value)

        # load saveables
        for child_node in self.list_children():
            if not hasattr(saveable, child_node.name):
                raise AttributeError(
                    f"object {saveable} does not have the expected "
                    f"attribute {child_node.name}"
                )

            obj: Saveable = getattr(saveable, child_node.name)
            if isinstance(obj, Saveable):
                child_node.load(obj)

    @abstractmethod
    def __iter__(self) -> Generator[tuple[T, type]]:
        pass

    @abstractmethod
    def list_children(self) -> list[BaseFileNode]:
        """
        list child nodes of current node

        Returns:
            list[BaseFileNode]: children of current node
        """
        pass

    @abstractmethod
    def create_child_node(self, meta: MetaData) -> BaseFileNode:
        """
        create child node from given meta data

        Args:
            meta (MetaData): holds meta data neccessary
                             to create a node, like name
                             etc.

        Returns:
            BaseFileNode: newly created child node
        """
        pass

    @abstractmethod
    def write_primitive_data(self, data_field: DataField):
        """
        write scalar supported data to file node

        Args:
            data_field (DataField): object that holds scalar data and its meta data to
                                    be written into node
        """
        pass

    @abstractmethod
    def write_simple_iterable(self, data_field: DataField):
        """
        write python lists / tuples / set with uniformly typed
        elements into node

        Args:
            data_field (DataField): object that holds list / tuple / set and its meta
                                    data to be written into node
        """
        pass

    @abstractmethod
    def write_none(self, data_field: DataField):
        """
        special method to write None into file node

        Args:
            data_field (DataField): object that holds None as a data along with its
                                    meta data
        """
        pass

    @abstractmethod
    def read_primitive_data(self, filedata: T) -> DataField:
        """
        read file data that represents primitive python data like int, str, float etc.
        """
        pass

    @abstractmethod
    def read_simple_iterable(self, filedata: T) -> DataField | None:
        """
        read list, set or tuples whose elements have all the same type
        """
        pass

    @abstractmethod
    def read_simple_dictionary(self, filedata: T) -> DataField | None:
        """
        read dictionaries whose keys have all the same type
        and whose values have all the same type
        """
        pass
