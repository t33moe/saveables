import uuid
from typing import Any

from saveables.saveable.utils import get_element_type


def decode_list(lst: list[Any], encoding: str) -> list[Any]:
    """
    if lst is a list of bytes decode these bytes
    and return a list of strings with decoded data

    Args:
        lst (list): list
        encoding (str): encoding used to decode bytes

    Returns:
        list: if input was a list of decoded bytes
              it return a list of strings with decoded
              bytes information. If list elements are not bytes, the
              original list is returned
    """

    # return if list is empty
    if len(lst) == 0:
        return lst

    # get list element type and decode it if neccessary
    element_type = get_element_type(lst)
    if element_type == bytes:
        return [el.decode(encoding) for el in lst]
    else:
        return lst


def generate_uuid(n_chars: int) -> str:
    """
    generate a uuid with specified number of characters

    Args:
        n_chars (int): _number of characters the uuid is about to have

    Returns:
        str: uuid string
    """
    return str(uuid.uuid4().hex[:n_chars])
