from __future__ import annotations

from dataclasses import fields
from typing import Any, Generator

import h5py
import numpy as np
from h5py import Dataset, Group

from saveables.base.base_file_node import BaseFileNode
from saveables.contracts.constants import (
    attribute,
    dict_keys,
    dict_values,
    element_type,
    encoding,
    name,
    none_literal,
    none_type,
    python_type,
    role,
)
from saveables.contracts.data_type import (
    EmptyIterable,
    python_type_literal_map,
    python_type_literal_map_reversed,
)
from saveables.python_utils import decode_list
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.saveable import Saveable
from saveables.saveable.utils import is_simple_iterable, is_suppported_primitive


class H5FileNode(BaseFileNode[Dataset | Group]):
    def __init__(self, name: str, parent: H5FileNode | None, group: Group):
        super().__init__(name, parent)
        self._group = group
        self._dict_keys_cache: dict[
            str, list[float] | list[str] | list[int] | list[bool]
        ] = dict()
        self._dict_values_cache: dict[
            str, list[float] | list[str] | list[int] | list[bool]
        ] = dict()

    def __iter__(self) -> Generator[tuple[Dataset | Group, type], None, None]:

        # iter through group an extract dataset
        for name_ in self._group:
            item = self._group[name_]
            if isinstance(item, Dataset):
                python_type_ = python_type_literal_map_reversed[item.attrs[python_type]]
                yield item, python_type_
            else:
                yield item, Saveable

    def read_python_attributes(self) -> list[DataField]:
        """
        read data from file that represents
        native python data type like str, int, list etc

        Returns:
            list: list of DataField objects holds data along with meta data
        """
        # call super call method with cleared caches
        self._dict_keys_cache = dict()
        self._dict_values_cache = dict()
        return super().read_python_attributes()

    def create_child_node(self, meta: MetaData) -> BaseFileNode[Dataset | Group]:
        """
        create child node from given meta data

        Args:
            meta (MetaData): holds meta data neccessary
                             to create a node, like name
                             etc.

        Returns:
            BaseFileNode: newly created child node
        """

        child_group = self._group.create_group(meta.name)
        return H5FileNode(meta.name, self, child_group)

    def write_primitive_data(self, data_field: DataField) -> None:
        """
        write scalar supported data to file node

        Args:
            data_field (DataField): object that holds scalar data and its meta data to
                                    be written into node
        """

        # check if data type is correct
        if not is_suppported_primitive(data_field.value):
            raise TypeError(f"data type {type(data_field.value)} is not supported")

        # write data
        dtype = None
        if isinstance(data_field.value, str):
            dtype = h5py.string_dtype(encoding=encoding)
        self._create_dataset(
            name=data_field.meta.name,
            data=data_field.value,
            dtype=dtype,
            meta=data_field.meta,
        )

    def write_simple_iterable(self, data_field: DataField) -> None:
        """
        write python lists / tuples / set with uniformly typed
        elements into node

        Args:
            data_field (DataField): object that holds a list / tuple / set and its meta
                                    data to be written into node

        Raises:
            TypeError: if data_field does not represent a list / tuple / set with
                       uniformly typed elements
            ValueError: if meta data indicates that the list / tuple / set is empty
                        but it is not
        """
        # check if value type is correct
        if not is_simple_iterable(data_field.value):
            raise TypeError("value must be of type list, set or tuple ")

        # save data as a numpy array
        len_ = len(data_field.value)  # type: ignore[arg-type]
        data_ = list(data_field.value)  # type: ignore[arg-type]
        if (
            len_ == 0
            and data_field.meta.element_type == python_type_literal_map[EmptyIterable]
        ):
            # we are dealing with an empty list / set / tuple. Set default data type
            # to integer
            data = np.array(data_, dtype=np.int_)
        elif (
            len_
            and data_field.meta.element_type == python_type_literal_map[EmptyIterable]
        ):
            raise ValueError(
                f"data for {data_field.meta.name} is declared as empty, but it is not"
            )
        else:
            # determine data type from value.
            # If it is a string, give encoding information
            dtype = None
            if data_field.meta.element_type == python_type_literal_map[str]:
                dtype = h5py.string_dtype(encoding=encoding)
            data = np.array(data_, dtype=dtype)
        self._create_dataset(
            data_field.meta.name, data=data, dtype=data.dtype, meta=data_field.meta
        )

    def write_none(self, data_field: DataField) -> None:
        """
        special method to write None into file node

        Args:
            data_field (DataField): object that holds None as a data along with its
                                    meta data

        Raises:
            TypeError: if data to be written is not None
        """
        if data_field.value is not None:
            raise TypeError(
                f"datafield {data_field.meta.name} is"
                f"expected to be None but is {data_field.value}"
            )

        # write none string into file
        none_meta = MetaData(
            python_type=none_type,
            name=data_field.meta.name,
            role=data_field.meta.role,
            element_type=none_type,  # type:ignore[arg-type]
        )
        dtype = h5py.string_dtype(encoding=encoding)
        data = none_literal
        self._create_dataset(none_meta.name, data, dtype, none_meta)

    def read_primitive_data(self, filedata: Dataset | Group) -> DataField:
        """
        read file data that represents primitive python data like int, str, float etc.

        Args:
            filedata (Dataset | Group): h5 file element that holds data from file

        Raises:
            TypeError: if filedata is a h5 group. Primitive data is supposed to be
                       in a data set

        Returns:
            DataField: object that holds read data and its meta data
        """

        if isinstance(filedata, Group):
            raise TypeError("primitive data is expected to be hold by a dataset")

        # extract meta data
        python_type_ = python_type_literal_map_reversed[filedata.attrs[python_type]]
        role_ = filedata.attrs[role]
        name_ = filedata.attrs[name]
        element_type_ = filedata.attrs[element_type]
        meta = MetaData(
            python_type=filedata.attrs[python_type],
            role=role_,
            name=name_,
            element_type=element_type_,
        )

        # extract data
        if python_type_ == str:
            # string is saved as bytes, we need to decode
            value = filedata[()].decode(encoding)
        else:
            value = filedata[()].tolist()

        return DataField(meta, value)

    def read_simple_iterable(self, filedata: Dataset | Group) -> DataField | None:
        """
        read list, set or tuple whose elements have all the same type

        Args:
            filedata (Dataset | Group): h5 file element that holds data from file

        Raises:
            TypeError: if file element is a h5 group. list, set or tuple whose elements
                       have all the same type are supposed to be saved as a dataset

        Returns:
            DataField | None: _description_
        """
        if isinstance(filedata, Group):
            raise TypeError("primitive data is expected to be hold by a dataset")

        # extract meta data
        meta = self._create_meta_data(filedata)

        # read data as a list
        value = filedata[:].tolist()

        # strings are saved as bytes, so we need to encode them
        value = decode_list(value, encoding)

        # restore original python type
        python_type_ = python_type_literal_map_reversed[filedata.attrs[python_type]]
        value = python_type_(value)

        return DataField(value=value, meta=meta)

    def read_simple_dictionary(self, filedata: Dataset | Group) -> DataField | None:
        """
        read dictionaries whose keys have all the same type
        and whose values have all the same type

        Raises:
            TypeError: if filedata is a hdf5 group

        Returns:
            DataField | None: if keys and values have been read, a datafield
                              is returned
        """

        if isinstance(filedata, Group):
            raise TypeError("primitive data is expected to be hold by a dataset")

        # read data
        data = filedata[:].tolist()

        # decode if neccessary
        data = decode_list(data, encoding)

        # put data into cache
        role_ = filedata.attrs[role]
        name_ = filedata.attrs[name]
        if role_ == dict_keys:
            self._dict_keys_cache[name_] = data
        if role_ == dict_values:
            self._dict_values_cache[name_] = data

        # if keys and values are read, create datafield
        if name_ in self._dict_keys_cache and name_ in self._dict_values_cache:
            python_type_ = filedata.attrs[python_type]
            meta = MetaData(
                python_type=python_type_,
                role=attribute,
                name=name_,
                element_type=none_type,  # type: ignore[arg-type]
            )
            value = {
                key: val
                for key, val in zip(
                    self._dict_keys_cache[name_], self._dict_values_cache[name_]
                )
            }
            return DataField(value=value, meta=meta)
        else:
            # cannot restore dictionary yet, since either keys or values are missing
            return None

    def list_children(self) -> list[BaseFileNode[Dataset | Group]]:
        """
        list child nodes of current node

        Returns:
            list[BaseFileNode]: list child file nodes
        """

        # create empty child list that is going to be filled
        children: list[BaseFileNode[Dataset | Group]] = []

        # create child node for each h5 group that is a direct child
        # of the node's h5 group
        for h5_element_name in self._group:
            h5_element = self._group[h5_element_name]
            if isinstance(h5_element, Group):
                children.append(H5FileNode(h5_element_name, self, h5_element))

        return children

    def _create_dataset(self, name: str, data: Any, dtype: Any, meta: MetaData) -> None:
        """
        create h5 dataset

        Args:
            name (str): name of dataset
            data (Any): data of dataset
            dtype (Any): type of data
            meta (MetaData): meta data of data that are written as dataset attributes
                             to file

        Raises:
            ValueError: raises  ValueError if a dataset with intended name already
                        exists in current node
        """

        # add suffix _keys / _values if data represent dictionary keys/values
        if meta.role == dict_keys:
            name_ = f"__{name}__" + "_keys"
        elif meta.role == dict_values:
            name_ = f"__{name}__" + "_values"
        else:
            name_ = name

        # check if there already is a dataset with given name in group
        if name_ in self._group and isinstance(self._group[name], Dataset):
            raise ValueError(
                f"An error occured while writing {meta.name}: Dataset {name_} "
                f"already exists in {self._group.name}"
            )

        # create dataset
        dset = self._group.create_dataset(name=name_, data=data, dtype=dtype)

        # update attributes with meta data
        for field in fields(meta):
            dset.attrs[field.name] = str(getattr(meta, field.name))

    def _create_meta_data(self, filedata: Dataset) -> MetaData:
        """
        create meta data object from dataset attributes

        Args:
            filedata (Dataset): dataset with attributes

        Returns:
            MetaData: meta data object that holds dataset attribute data
        """
        role_ = filedata.attrs[role]
        name_ = filedata.attrs[name]
        element_type_ = filedata.attrs[element_type]
        return MetaData(
            python_type=filedata.attrs[python_type],
            role=role_,
            name=name_,
            element_type=element_type_,
        )
