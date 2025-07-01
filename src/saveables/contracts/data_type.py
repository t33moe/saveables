from typing import Literal


class EmptyIterable:
    pass


supported_primitive_data_types = (str, int, float, bool)
tPrimitiveDataType = str | int | None | float | bool
tIterableDataType = list | set | tuple | dict  # type: ignore[type-arg]
tPrimitivePythonLiteral = Literal["int", "str", "none_type", "float", "bool"]
tIterablePythonLiteral = Literal["list", "set", "tuple", "dict", "empty_iterable"]
tPythonTypeLiteral = (
    tPrimitivePythonLiteral | tIterablePythonLiteral | Literal["saveable"]
)
tRole = Literal["attribute", "dict_keys", "dict_values"]
tFileMode = Literal["r", "w"]
python_type_literal_map: dict[type, tPythonTypeLiteral] = {
    list: "list",
    set: "set",
    tuple: "tuple",
    int: "int",
    str: "str",
    float: "float",
    bool: "bool",
    dict: "dict",
    type(None): "none_type",
    EmptyIterable: "empty_iterable",
}
python_type_literal_map_reversed: dict[tPythonTypeLiteral, type] = {
    value: key for key, value in python_type_literal_map.items()
}
