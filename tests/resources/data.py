from dataclasses import dataclass, field, make_dataclass
from typing import Any, Optional

from saveables.contracts.constants import attribute, saveable
from saveables.contracts.data_type import (
    python_type_literal_map,
    python_type_literal_map_reversed,
)
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.saveable import Saveable


# create test data for lists
@dataclass
class HoldsLists(Saveable):  # type: ignore[misc]
    lst_str: list[str] = field(default_factory=list)
    lst_int: list[int] = field(default_factory=list)
    lst_empty: list[int] = field(default_factory=list)


lists = HoldsLists(["1", "2"], [1, 2])


# create test data for sets
@dataclass
class HoldsSets(Saveable):  # type: ignore[misc]
    set_str: set[str] = field(default_factory=set)
    set_int: set[int] = field(default_factory=set)
    set_empty: set[int] = field(default_factory=set)


sets = HoldsSets({"1", "2"}, {1, 2})


# create test data for tuples
@dataclass
class HoldsTuples(Saveable):  # type: ignore[misc]
    tpl_str: tuple[str, ...] = field(default_factory=tuple)
    tpl_int: tuple[int, ...] = field(default_factory=tuple)
    tpl_empty: tuple[int, ...] = field(default_factory=tuple)


tuples = HoldsTuples(tpl_str=("1", "2"), tpl_int=(1, 2))


# create test data for dictionaries
@dataclass
class HoldsDicts(Saveable):  # type: ignore[misc]
    dct_str_str: dict[str, str] = field(default_factory=dict)
    dct_str_int: dict[str, int] = field(default_factory=dict)
    dct_empty: dict[str, int] = field(default_factory=dict)


dicts = HoldsDicts({"foo": "bar", "fizz": "buzz"}, {"one": 1, "two": 2})


# create test data for primitive data
@dataclass
class HoldsPrimitives(Saveable):  # type: ignore[misc]
    str_: Optional[str] = "foo"
    int_: Optional[int] = 0
    none_: Optional[int] = None
    float_: Optional[float] = 1.0
    bool_: Optional[bool] = True


primitives = HoldsPrimitives()


# create test data for nested data
@dataclass
class NestedLevel2(Saveable):  # type: ignore[misc]
    str_: str = "2"
    int_: int = 1
    lst_: list[str] = field(default_factory=list)


@dataclass
class NestedLevel1(Saveable):  # type: ignore[misc]
    str_: str = "1"
    int_: int = 1
    lst_: list[str] = field(default_factory=list)
    nested: NestedLevel2 = field(default_factory=NestedLevel2)


@dataclass
class HoldsNestedData(Saveable):  # type: ignore[misc]
    str_: str = "0"
    int_: int = 0
    lst_: list[str] = field(default_factory=list)
    nested: NestedLevel1 = field(default_factory=NestedLevel1)


nested2 = NestedLevel2(lst_=["2", "2"])
nested1 = NestedLevel1(lst_=["1", "1"], nested=nested2)
nested0 = HoldsNestedData(lst_=["0", "0"], nested=nested1)


# create test data fields
@dataclass
class MyMixedSaveable(Saveable):  # type: ignore[misc]
    str_: str = "0"
    lst_: list[str] = field(default_factory=list)
    saveable_: HoldsPrimitives = field(default_factory=HoldsPrimitives)


mixed = MyMixedSaveable(saveable_=primitives)

meta_saveable = MetaData(
    name="my_saveable",
    python_type=python_type_literal_map[Saveable],
    role=attribute,
    element_type=python_type_literal_map[type(None)],
)
data_field_saveable = DataField(value=mixed, meta=meta_saveable)

meta_str = MetaData(
    name="my_string",
    python_type=python_type_literal_map[str],
    role=attribute,
    element_type=python_type_literal_map[str],
)
data_field_str = DataField(value="string", meta=meta_str)

meta_int = MetaData(
    name="my_int",
    python_type=python_type_literal_map[int],
    role=attribute,
    element_type=python_type_literal_map[int],
)
data_field_int = DataField(value=0, meta=meta_int)

meta_integer_list = MetaData(
    name="my_list",
    python_type=python_type_literal_map[list],
    role=attribute,
    element_type=python_type_literal_map[int],
)
data_field_list = DataField(value=[1, 2], meta=meta_integer_list)

meta_integer_tuple = MetaData(
    name="my_tuple",
    python_type=python_type_literal_map[tuple],
    role=attribute,
    element_type=python_type_literal_map[int],
)
data_field_tuple = DataField(value=(1, 2), meta=meta_integer_tuple)

meta_integer_set = MetaData(
    name="my_set",
    python_type=python_type_literal_map[set],
    role=attribute,
    element_type=python_type_literal_map[int],
)
data_field_set = DataField(value=(1, 2), meta=meta_integer_set)

meta_dict = MetaData(
    name="my_dict",
    python_type=python_type_literal_map[dict],
    role=attribute,
    element_type=python_type_literal_map[type(None)],
)
data_field_dict = DataField(value={1: "2", 3: "4"}, meta=meta_dict)


def create_saveable_from_datafields(name: str, data_fields: tuple[DataField]) -> type:
    """create saveable that matches given list of data_fields"""
    fields = []
    for data_field in data_fields:
        # extract type and create default values from them
        python_type_ = data_field.meta.python_type
        if (
            python_type_ == python_type_literal_map[str]
            or python_type_ == python_type_literal_map[int]
        ):

            # append field information
            default = None
            fields.append((data_field.meta.name, Any, default))
        elif python_type_ == saveable:
            factory = MyMixedSaveable
            fields.append((data_field.meta.name, Any, field(default_factory=factory)))  # type: ignore[arg-type] # noqa: E501
        else:
            factory = python_type_literal_map_reversed[python_type_]
            fields.append((data_field.meta.name, Any, field(default_factory=factory)))  # type: ignore[arg-type] # noqa: E501

    # create data class from given fields
    return make_dataclass(name, fields, bases=(Saveable,))
