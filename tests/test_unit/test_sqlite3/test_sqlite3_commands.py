from saveables.contracts.constants import (column_name_data, column_name_id,
                                           column_name_meta_data,
                                           column_name_object_id,
                                           column_name_reference,
                                           column_name_reference_id,
                                           meta_data_table_name)
from saveables.saveable.utils import list_meta_data_attributes
from saveables.sqlite3_format.sqlite3_commands import (
    get_first_row_of_table, insert_primitive_data, insert_saveable_data,
    select_meta_data, select_python_attributes_from_table, select_row_id,
    select_saveable_attributes_from_table, select_simple_iterable_elements)


def test_insert_primitive_data() -> None:
    cmd = insert_primitive_data("test_table")
    columns = [column_name_object_id, column_name_data, column_name_meta_data]
    assert cmd.command.strip() == (
        f"INSERT INTO test_table ({', '.join(columns)}) VALUES (?, ?, ?)"
    )
    assert cmd.columns == [
        column_name_object_id,
        column_name_data,
        column_name_meta_data,
    ]


def test_insert_saveable_data() -> None:
    cmd = insert_saveable_data("test_table")
    columns = [
        column_name_object_id,
        column_name_meta_data,
        column_name_reference,
        column_name_reference_id,
    ]
    assert cmd.command.strip() == (
        f"INSERT INTO test_table ({', '.join(columns)}) VALUES (?, ?, ?, ?)"
    )
    assert cmd.columns == [
        column_name_object_id,
        column_name_meta_data,
        column_name_reference,
        column_name_reference_id,
    ]


def test_select_row_id() -> None:
    cmd = select_row_id("test_table", ["column_a", "column_b"])
    assert cmd.command.strip() == (
        "SELECT id FROM test_table WHERE column_a = ? AND column_b = ?"
    )
    assert cmd.columns == [column_name_id]


def test_select_meta_data() -> None:
    cmd = select_meta_data()
    columns = [column_name_id] + list_meta_data_attributes()
    assert cmd.command.strip() == (
        f"SELECT {', '.join(columns)} FROM {meta_data_table_name} "
        f"WHERE {column_name_id} = ?"
    )
    assert cmd.columns == columns


def test_select_python_attributes_from_table() -> None:
    cmd = select_python_attributes_from_table("test_table")
    assert cmd.command.strip() == (
        f"SELECT {column_name_data}, {column_name_meta_data} FROM test_table "
        f"WHERE {column_name_object_id} = ? AND {column_name_reference} IS NULL AND "
        f"{column_name_reference_id} IS NULL"
    )
    assert cmd.columns == [column_name_data, column_name_meta_data]


def test_select_saveable_attributes_from_table() -> None:
    cmd = select_saveable_attributes_from_table("test_table")
    assert cmd.command.strip() == (
        f"SELECT {column_name_reference}, {column_name_reference_id} FROM test_table "
        f"WHERE {column_name_object_id} = ? AND {column_name_reference} IS NOT NULL "
        f"AND {column_name_reference_id} IS NOT NULL"
    )
    assert cmd.columns == [column_name_reference, column_name_reference_id]


def test_select_simple_iterable_elements() -> None:
    cmd = select_simple_iterable_elements("test_table")
    assert cmd.command.strip() == (
        f"SELECT {column_name_data} FROM test_table WHERE "
        f"{column_name_meta_data} = ? AND {column_name_object_id} = ?"
    )
    assert cmd.columns == ["data"]


def test_get_first_row_of_table() -> None:
    cmd = get_first_row_of_table("test_table", ["column_a", "column_b"])
    assert cmd.command.strip() == ("SELECT column_a, column_b FROM test_table LIMIT 1")
    assert cmd.columns == ["column_a", "column_b"]
