from typing import Any

from src.contracts.data_type import EmptyIterable, supported_primitive_data_types


def is_typed_uniformly(data: list | set | tuple) -> bool:
    """
    checks if each element in data is of the same type as
    the first one

    Args:
        data (list | set | tuple): data that is to be checked

    Returns:
        bool: True if each element in data is of the same type as
              the first one or len(data) = 0
    """
    if len(data) == 0:
        return True
    else:
        obj_ = list(data)  # make sure data is indexable
        return all([isinstance(el, type(obj_[0])) for el in obj_])


def get_element_type(data: list | set | tuple) -> type:
    """
    return type of elements in list / set / tuple

    Args:
        data (list | set | tuple): uniformly typed list / set / tuple. Uniformly
                                   typed means that each element in list / set / tuple
                                   must have the same type

    Raises:
        ValueError: elements in list / tuple / are not of the same type

    Returns:
        type: type of elments in list/tuple/set
    """
    if len(data) == 0:
        return EmptyIterable
    if not is_typed_uniformly(data):
        raise ValueError(
            "can only return element type if all elements have the same type"
        )
    else:
        return type(list(data)[0])


def is_simple_iterable(data: Any) -> bool:
    """
    check if data is list / set / tuple

    Args:
        data (Any): object to be checked

    Returns:
        bool: True if data is list / set / tuple

    """
    ret = isinstance(data, list) or isinstance(data, tuple) or isinstance(data, set)
    if not ret:
        return False
    else:
        ret = ret and is_typed_uniformly(data)
        return ret


def is_simple_dictionary(data: Any) -> bool:
    """
    check if data is a dictionary with uniformly typed keys and values.

    Args:
        data (Any): data to be checked

    Returns:
        bool: True, if data is a dictionary, and each key has the same data type
              and each value has the same data type. The data type of keys and values
              are allowed to differ
    """
    # check object type
    if not isinstance(data, dict):
        return False

    if len(data) == 0:
        # no keys / values to check for their type
        return True

    # check keys
    keys = list(data.keys())
    keys_okay = is_typed_uniformly(keys) and is_suppported_primitive(keys[0])

    # check values
    values = list(data.values())
    values_okay = is_typed_uniformly(values) and is_suppported_primitive(values[0])

    return keys_okay and values_okay


def is_suppported_primitive(data: Any) -> bool:
    """
    check if data is supported primitive data type

    Args:
        data (Any): object to be checked

    Returns:
        bool: True if data's type is any of the supported primitive data types
    """
    return any([isinstance(data, type_) for type_ in supported_primitive_data_types])
