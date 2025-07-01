from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saveables.contracts.data_type import tFileMode, tPythonTypeLiteral, tRole

# reused constants
python_type = "python_type"
role = "role"
element_type = "element_type"
saveable: tPythonTypeLiteral = "saveable"
name = "name"
root = "root"
dict_values: tRole = "dict_values"
dict_keys: tRole = "dict_keys"
attribute: tRole = "attribute"
read_mode: tFileMode = "r"
write_mode: tFileMode = "w"
encoding = "utf-8"
none_literal = "__NONE__"
empty_type: tPythonTypeLiteral = "empty_iterable"
none_type: tPythonTypeLiteral = "none_type"
