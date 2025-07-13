from typing import Any

import pytest
from saveables.contracts.data_type import (
    EmptyIterable,
    supported_primitive_data_types,
    tIterableDataType,
)
from saveables.saveable.utils import (
    get_element_type,
    is_simple_dictionary,
    is_simple_iterable,
    is_supported_primitive,
    is_typed_uniformly,
)


@pytest.mark.parametrize(
    "input_, result",
    [
        ([1, 2], True),
        ([1, 2.0], False),
        ([], True),
        ((1, 2), True),
        ((1, 2.0), False),
        (tuple(), True),
        ({1, 2}, True),
        ({1, 2.0}, False),
        (set(), True),
    ],
)
def test_is_typed_uniformly(input_: tIterableDataType, result: bool) -> None:
    assert is_typed_uniformly(input_) == result


@pytest.mark.parametrize(
    "input_, result",
    [
        ([1, 2, 3], int),
        ((1, 2, 3), int),
        ({1, 2, 3}, int),
        (["1", "2"], str),
        (("1", "2"), str),
        ({"1", "2"}, str),
        ([], EmptyIterable),
        (tuple(), EmptyIterable),
        (set(), EmptyIterable),
    ],
)
def test_get_element_type(input_: tIterableDataType, result: bool) -> None:
    assert get_element_type(input_) is result


@pytest.mark.parametrize(
    "input_, result",
    [
        ([1, 2, 3], True),
        ([1, "2"], False),
        ((1, 2, 3), True),
        ((1, "2"), False),
        ({1, 2}, True),
        ({1, "2"}, False),
    ],
)
def test_is_simple_iterable(input_: tIterableDataType, result: bool) -> None:
    assert is_simple_iterable(input_) == result


@pytest.mark.parametrize(
    "input_, result", [({1: "a", 2: "b"}, True), (({1: 1, 2: "b"}, False))]
)
def test_is_simple_dictionary(input_: dict[Any, Any], result: bool) -> None:
    assert is_simple_dictionary(input_) == result


def test_is_suppported_primitive() -> None:
    # create an input that can be cast into all supported data types
    input_raw = 1

    # test method for all supported data types
    for type_ in supported_primitive_data_types:
        # cast raw input to desired input
        input_ = type_(input_raw)

        # check result
        assert is_supported_primitive(input_)
