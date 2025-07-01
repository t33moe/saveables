from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saveables.contracts.data_type import (
        tPrimitivePythonLiteral,
        tPythonTypeLiteral,
        tRole,
    )


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
