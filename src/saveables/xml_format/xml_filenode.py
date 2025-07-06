from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict
from typing import TYPE_CHECKING, Generator, Optional

from saveables.base.base_file_node import BaseFileNode
from saveables.contracts.constants import (
    dict_keys,
    dict_values,
    element_type,
    empty_type,
    name,
    none_literal,
    none_type,
    python_type,
    role,
    saveable,
)
from saveables.contracts.data_type import python_type_literal_map_reversed
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.utils import is_suppported_primitive

if TYPE_CHECKING:
    from saveables.contracts.data_type import tPrimitiveDataType


class XmlFileNode(BaseFileNode[ET.Element]):
    """
    XML specific implementations to save and load Saveable objects
    """

    def __init__(
        self, name: str, parent: Optional[BaseFileNode[ET.Element]], element: ET.Element
    ):
        super().__init__(name, parent)
        self._element = element
        self._processed_iterables_and_dictionary_names: list[str] = []

    def __iter__(self) -> Generator[tuple[ET.Element, type], None, None]:

        for elem in self._element:
            yield elem, python_type_literal_map_reversed[elem.attrib[python_type]]  # type: ignore[index] # noqa: E501

    def list_children(self) -> list[BaseFileNode[ET.Element]]:
        """
        list child nodes of current node

        Returns:
            list[BaseFileNode]: children of current node
        """

        children: list[BaseFileNode[ET.Element]] = []
        # iterate over all elements that have the current
        # node as parent and contain saveables as data
        # and create file nodes from these elements
        for elem in [el for el in self._element if el.attrib[python_type] == saveable]:
            name_ = elem.attrib[name]
            children.append(XmlFileNode(name_, self, elem))
        return children

    def create_child_node(self, meta: MetaData) -> BaseFileNode[ET.Element]:
        """
        create child node from given meta data

        Args:
            meta (MetaData): holds meta data neccessary
                             to create a node, like name
                             etc.

        Returns:
            BaseFileNode: newly created child node
        """

        # create xml tag meta attributes
        meta_dict = {key: str(val) for key, val in asdict(meta).items()}
        child = ET.SubElement(self._element, meta.name, attrib=meta_dict)

        # return filenode
        return XmlFileNode(meta.name, self, child)

    def write_primitive_data(self, data_field: DataField) -> None:
        """
        write scalar supported data to file node

        Args:
            data_field (DataField): object that holds scalar data and its meta data to
                                    be written into node
        """

        # check data type
        if not is_suppported_primitive(data_field.value):
            raise TypeError(
                f"field {data_field.meta.name} contains"
                f"an supported data type: {type(data_field.value)}"
            )

        # write data
        self._write_primitive_data(data_field.value, data_field.meta)  # type: ignore[arg-type] # noqa: E501

    def write_simple_iterable(self, data_field: DataField) -> None:
        """
        write python lists / tuples / set with uniformly typed
        elements into node

        Args:
            data_field (DataField): object that holds list / tuple / set and its meta
                                    data to be written into node
        """

        if len(data_field.value) == 0 and data_field.meta.element_type == empty_type:  # type: ignore[arg-type] # noqa: E501
            self._write_primitive_data(data="", meta=data_field.meta)
        elif len(data_field.value) != 0 and data_field.meta.element_type == empty_type:  # type: ignore[arg-type] # noqa: E501
            raise ValueError(
                f"attribute {data_field.meta.name} is declared emtpy but it is not"
            )

        # write each value in a separate xml tag
        for value in data_field.value:  # type: ignore[union-attr]
            self._write_primitive_data(value, data_field.meta)

    def write_none(self, data_field: DataField) -> None:
        """
        special method to write None into file node

        Args:
            data_field (DataField): object that holds None as a data along with its
                                    meta data
        """

        none_meta = MetaData(
            python_type=none_type,
            name=data_field.meta.name,
            role=data_field.meta.role,
            element_type=none_type,  # type: ignore[arg-type]
        )
        data = none_literal
        self._write_primitive_data(data, none_meta)

    def read_primitive_data(self, element: ET.Element) -> DataField:
        """
        read file data that represents primitive python data like int, str, float etc.

        Args:
            element (ET.Element): xml element whose text represents
                                  a primitive data type like int, str, float etc.

        Returns:
            DataField: datafield that holds the read value and its meta data
        """
        # extract meta data
        role_ = element.attrib[role]
        name_ = element.attrib[name]
        python_type_ = element.attrib[python_type]
        element_type_ = element.attrib[element_type]
        meta = MetaData(
            python_type=python_type_,  # type: ignore[arg-type]
            name=name_,
            element_type=element_type_,  # type: ignore[arg-type]
            role=role_,  # type: ignore[arg-type]
        )

        # extract value
        type_ = python_type_literal_map_reversed[element.attrib[python_type]]  # type: ignore[index] # noqa: E501
        value = type_(element.text)

        return DataField(value=value, meta=meta)

    def read_simple_iterable(self, element: ET.Element) -> DataField | None:
        """
        read list, set or tuples whose elements have all the same type

        Args:
            element (ET.Element): xml element element that represents an element
                                  of a list / tuple / set

        Returns:
            DataField | None: returns a datafield that holds list / tuple / set
                              and its meta data if the list / tuple / set has not
                              been already read
        """
        # extract meta data
        name_ = element.attrib[name]
        python_type_ = element.attrib[python_type]
        role_ = element.attrib[role]
        element_type_ = element.attrib[element_type]
        meta = MetaData(
            python_type=python_type_,  # type: ignore[arg-type]
            name=name_,
            role=role_,  # type: ignore[arg-type]
            element_type=element_type_,  # type: ignore[arg-type]
        )

        if meta.name in self._processed_iterables_and_dictionary_names:
            # we have alread read the data
            return None

        # create data field with empty list
        data_field = DataField(value=[], meta=meta)
        if meta.element_type != empty_type:
            # search all elements that belong to iterable and extract value
            elements = [el for el in self._element if el.tag == name_]
            for subelement in elements:
                # extract and cast value from subelement
                value = python_type_literal_map_reversed[meta.element_type](
                    subelement.text
                )
                # append value to data field
                data_field.value.append(value)  # type: ignore[union-attr]

        # restore original iterable type
        data_field.value = python_type_literal_map_reversed[meta.python_type](
            data_field.value
        )

        # mark that iterable has already been read
        self._processed_iterables_and_dictionary_names.append(meta.name)

        return data_field

    def read_simple_dictionary(self, element: ET.Element) -> DataField | None:
        """
        read dictionaries whose keys have all the same type
        and whose values have all the same type


        Args:
            element (ET.Element): xml element the belongs to the list of keys / values
                                  of a dictionary

        Returns:
            DataField | None: returns a datafield that holds a dictionary along
                              with its meta data, if keys and values have been read
        """
        # extract meta data
        name_ = element.attrib[name]
        python_type_ = element.attrib[python_type]
        role_ = element.attrib[role]
        element_type_ = none_type
        meta = MetaData(
            python_type=python_type_,  # type: ignore[arg-type]
            name=name_,
            role=role_,  # type: ignore[arg-type]
            element_type=element_type_,  # type: ignore[arg-type]
        )

        if meta.name in self._processed_iterables_and_dictionary_names:
            # dictonary has already been read
            return None

        # find subelements that hold keys of the dictionary
        key_elements = [
            el
            for el in self._element
            if el.attrib[name] == name_
            and el.attrib[role] == dict_keys
            and el.attrib[element_type] != empty_type
        ]

        # iter through elements and extract keys
        keys: list[str] | list[float] | list[bool] | list[int] = []
        for el in key_elements:
            # read value from element und cast into correct python type
            value = python_type_literal_map_reversed[el.attrib[element_type]](el.text)  # type: ignore[index] # noqa: E501
            keys.append(value)

        # find subelements that hold values of dictionary
        value_elements = [
            el
            for el in self._element
            if el.attrib[name] == name_
            and el.attrib[role] == dict_values
            and el.attrib[element_type] != empty_type
        ]

        # iter through elements and extract dictionary values
        values: list[str] | list[float] | list[bool] | list[int] = []
        for el in value_elements:
            # read value from element and cast into correct python type
            value = python_type_literal_map_reversed[el.attrib[element_type]](el.text)  # type: ignore[index] # noqa: E501
            values.append(value)

        # datafield with dict from found keys / values
        dict_ = {key: value for key, value in zip(keys, values)}
        data_field = DataField(value=dict_, meta=meta)

        # mark simple dictionary as processed
        self._processed_iterables_and_dictionary_names.append(meta.name)

        return data_field

    def _write_primitive_data(self, data: tPrimitiveDataType, meta: MetaData) -> None:
        """
        create xml tag and write data into it

        Args:
            data (tPrimitiveDataType): data that is used as element's text
            meta (MetaData): meta data that are written as tag attributes
        """
        attrib = {key: str(val) for key, val in asdict(meta).items()}
        el = ET.SubElement(self._element, meta.name, attrib=attrib)
        el.text = str(data)
