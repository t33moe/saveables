from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from saveables.contracts.constants import attribute
from saveables.contracts.data_type import python_type_literal_map

if TYPE_CHECKING:
    from saveables.contracts.data_type import (tPrimitivePythonLiteral,
                                               tPythonTypeLiteral, tRole)


@dataclass
class MetaData:
    """
    Holds meta data information for the data to be saved
    """

    python_type: tPythonTypeLiteral  # determines original python type of the data
    role: tRole  # determines data role. Data can either be the value of an object field
    # or a list dictionary keys/values # noqa: E116, E114
    name: str  # name of attribute
    element_type: tPrimitivePythonLiteral  # type of elements if data is list/tuple/set

    def __post_init__(self) -> None:
        if (
            self.python_type == python_type_literal_map[dict]
            and self.element_type != python_type_literal_map[type(None)]
            and self.role == attribute
        ):
            raise ValueError(
                f"if python type is {self.python_type}, element_type must be "
                f"{python_type_literal_map[type(None)]}"
            )
