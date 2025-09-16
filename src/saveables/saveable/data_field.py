from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saveables.contracts.data_type import (tIterableDataType,
                                               tPrimitiveDataType)
    from saveables.saveable.meta_data import MetaData
    from saveables.saveable.saveable import Saveable


@dataclass
class DataField:
    """
    holds value to be saved along with its meta data
    """

    meta: MetaData
    value: Saveable | tPrimitiveDataType | tIterableDataType
