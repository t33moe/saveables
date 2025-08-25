import sqlite3
from pathlib import Path

import pytest

from saveables.contracts.constants import (attribute, column_name_data,
                                           column_name_meta_data,
                                           column_name_object_id, element_type,
                                           meta_data_table_name, name,
                                           python_type, read_mode, role, root,
                                           write_mode)
from saveables.contracts.data_type import python_type_literal_map
from saveables.sqlite3_format.sqlite3_commands import (
    create_meta_data_table, create_saveables_object_table, insert_meta_data,
    insert_primitive_data, table_exists)
from saveables.sqlite3_format.sqlite3_file import Sqlite3File


def test_open_to_write(local_tmp: Path) -> None:
    """
    test that root table and meta data table are created when a Sqlite3File is
    opened for writing

    Args:
        local_tmp (Path): path for test data base
    """

    # create temporary path for the sqlite3 file
    db_path = local_tmp / "test_db.sqlite3"

    # instantiate Sqlite3File
    sqlite_file = Sqlite3File(str(db_path), mode=write_mode)

    # open database for writing
    sqlite_file._open_to_write()

    # check database file exists
    db_path.exists()

    # create cursor
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # assert meta_data table exists in the database
    cmd = table_exists()
    cursor.execute(cmd.command, (meta_data_table_name,))
    assert cursor.fetchall() is not None

    # assert root table exists in the data
    cmd = table_exists()
    cursor.execute(cmd.command, (root,))
    assert cursor.fetchall() is not None

    conn.close()


def test_open_to_read(local_tmp: Path) -> None:
    """
    test that Sqlite3File opens correctly in read mode.
    It will be checked that the root node initializes correctly

    Args:
        tmp_path (Path): path for test data base
    """
    # create temporary SQLite DB file
    db_path = local_tmp / "test_db_test_open_to_read.sqlite3"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # create meta_data
    cursor.execute(create_meta_data_table().command)

    # insert metadata entry
    cmd = insert_meta_data()
    data: dict[str, str | int] = {
        role: attribute,
        python_type: python_type_literal_map[int],
        element_type: python_type_literal_map[int],
        name: "my_integer",
    }
    cursor.execute(cmd.command, tuple([data[col] for col in cmd.columns]))
    meta_id = cursor.lastrowid
    assert meta_id is not None

    # create root table
    cursor.execute(create_saveables_object_table(root).command)

    # insert dummy data into root table
    cmd = insert_primitive_data(root)
    expected_object_id = "root-123"
    data = {
        column_name_object_id: expected_object_id,
        column_name_data: "42",
        column_name_meta_data: meta_id,
    }
    cursor.execute(cmd.command, tuple([data[col] for col in cmd.columns]))
    conn.commit()
    conn.close()

    # instantiate Sqlite3File with path to existing DB
    sqlite_file = Sqlite3File(db_path, mode=read_mode)

    # open the database for reading
    sqlite_file._open_to_read()

    # check that root node initialized correctly
    assert sqlite_file.root is not None
    assert sqlite_file.root.name == root
    assert sqlite_file.root._object_id == expected_object_id

    # cleanup
    conn.close()


def test_open_to_read_fails(local_tmp: Path) -> None:
    """
    test that Sqlite3File raises an ValueError when a db is opened
    in read mode but root table does not exist

    Args:
        local_tmp (Path): path for test data base
    """

    # create empty SQLite DB file
    db_path = local_tmp / "test_db_test_open_to_read_fails.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.commit()
    assert db_path.exists()

    # instantiate Sqlite3File with path to existing DB
    sqlite_file = Sqlite3File(db_path, mode=read_mode)

    # open the database for reading
    with pytest.raises(ValueError):
        sqlite_file._open_to_read()
