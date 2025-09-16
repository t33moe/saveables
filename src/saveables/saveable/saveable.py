from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Generator

from saveables.contracts.constants import attribute, none_type, saveable
from saveables.contracts.data_type import (python_type_literal_map,
                                           python_type_literal_map_reversed)
from saveables.python_utils import get_element_type  # type: ignore[attr-defined]
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.utils import is_simple_dictionary, is_simple_iterable

if TYPE_CHECKING:
    from saveables.contracts.data_type import tPythonTypeLiteral


@dataclass
class Saveable:
    """
    Base class for objects that are to be saved. Each object to be saved
    must inherit from this class
    """

    def iter_fields(self) -> Generator[DataField, None, None]:
        """
        iterate over attributes that are to be saved

        Raises:
            TypeError: if an object's attribute has a type that is not supported

        Yields:
            Generator[DataField, None, None]: DataField that holds attribute value
                                              along with meta data
        """
        for field in fields(self):
            name = field.name
            role = attribute
            value = getattr(self, name)
            python_type: tPythonTypeLiteral
            if isinstance(value, Saveable):
                python_type = saveable
            else:
                try:
                    python_type = python_type_literal_map[type(value)]
                except KeyError:
                    raise TypeError(
                        f"Unsupported field type: {type(value)} for field {name}"
                    )
            if is_simple_iterable(value):
                try:
                    element_type = python_type_literal_map[get_element_type(value)]
                except KeyError:
                    raise TypeError(
                        f"Unsupported element type: {get_element_type(value)} "
                        f"for field {name}"
                    )
            elif is_simple_dictionary(value):
                # put dummy placeholder as element type since
                # keys and values of a dictionary different element types
                # and the information is not relevant for dictionaries
                # since its keys/values are saved separately as lists
                element_type = none_type
            else:
                element_type = python_type
            meta = MetaData(
                python_type=python_type,
                role=role,
                name=name,
                element_type=element_type,  # type: ignore[arg-type]
            )
            yield DataField(meta=meta, value=value)


python_type_literal_map[Saveable] = saveable
python_type_literal_map_reversed[saveable] = Saveable
