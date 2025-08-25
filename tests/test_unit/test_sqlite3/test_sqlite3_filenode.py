import sqlite3

import pytest
from resources.data import (data_field_int, data_field_list, data_field_set,
                            data_field_str, data_field_tuple, datafield_bool,
                            datafield_float)

from saveables.contracts.constants import (attribute, column_name_data,
                                           column_name_meta_data,
                                           column_name_object_id,
                                           column_name_reference,
                                           column_name_reference_id,
                                           element_type, meta_data_table_name,
                                           name, python_type, role, saveable)
from saveables.contracts.data_type import python_type_literal_map
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.utils import (list_meta_data_attribute_values,
                                      list_meta_data_attributes)
from saveables.sqlite3_format.sqlite3_commands import (
    SqlCommand, create_meta_data_table, create_saveables_object_table,
    insert_meta_data, insert_primitive_data, select_meta_data,
    select_python_attributes_from_table, select_row_id,
    select_saveable_attributes_from_table, select_simple_iterable_elements,
    table_exists)
from saveables.sqlite3_format.sqlite3_filenode import Sqlite3FileNode
from saveables.sqlite3_format.sqlite3filedata import SqlLite3FileData


@pytest.mark.parametrize(
    "data_field", [data_field_int, datafield_float, data_field_str, datafield_bool]
)
def test_write_primitive_data(data_field: DataField) -> None:
    """
    test that write primitve data writes python scalar variables correctly into
    database

    Args:
        data_field (DataField): test data field that holds scalar python data type
    """
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    table_name = "test"

    # create meta_data table
    cursor.execute(create_meta_data_table().command)
    connection.commit()

    # create target table
    cmd = create_saveables_object_table(table_name)
    cursor.execute(cmd.command)
    connection.commit()

    # set up node
    object_id = "test-id"
    node = Sqlite3FileNode(name="test", parent=None, object_id=object_id, cursor=cursor)

    # write datafield
    node.write_primitive_data(data_field)
    connection.commit()

    # check data in database
    cmd = select_python_attributes_from_table(table_name)
    cursor.execute(cmd.command, (object_id,))
    rows = cursor.fetchall()
    assert len(rows) == 1
    data, meta_id = rows[0]
    assert data == str(data_field.value)

    # check meta_data entry
    cmd = select_meta_data()
    cursor.execute(cmd.command, (meta_id,))
    meta_row = cursor.fetchone()
    assert list(meta_row[1:]) == list_meta_data_attribute_values(data_field.meta)
    assert meta_row[0] == 1

    connection.close()


@pytest.mark.parametrize(
    "data_field", [data_field_list, data_field_set, data_field_tuple]
)
def test_write_simple_iterable(data_field: DataField) -> None:
    """
    test that iterables are written correctly

    Args:
        data_field (DataField): datafield object that holds a simple iterable value
    """

    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    table_name = "test"
    object_id = "parent-id"

    # create required tables
    cmd = create_meta_data_table()
    cursor.execute(cmd.command)
    cmd = create_saveables_object_table(table_name)
    cursor.execute(cmd.command)
    connection.commit()

    # set up file node and data field
    node = Sqlite3FileNode(
        name=table_name, parent=None, object_id=object_id, cursor=cursor
    )

    # write iterable
    node.write_simple_iterable(data_field)
    connection.commit()

    # get meta data id
    cmd = select_row_id(meta_data_table_name, list_meta_data_attributes())
    cursor.execute(cmd.command, tuple(list_meta_data_attribute_values(data_field.meta)))
    rows = cursor.fetchall()
    assert len(rows) == 1
    meta_data_id = rows[0][0]

    # check meta data
    cmd = select_meta_data()
    cursor.execute(cmd.command, (meta_data_id,))
    rows = cursor.fetchall()
    assert len(rows) == 1
    row = list(rows[0])
    assert row[1:] == list_meta_data_attribute_values(data_field.meta)

    # assert inserted elements
    cmd = select_simple_iterable_elements(table_name)
    cursor.execute(cmd.command, (meta_data_id, object_id))
    rows = cursor.fetchall()
    assert len(rows) == len(data_field.value)
    indices: dict[str, int] = {
        column_name: index for index, column_name in enumerate(cmd.columns)
    }
    assert column_name_data in indices
    for index_row, row in enumerate(rows):
        assert row[indices[column_name_data]] == str(data_field.value[index_row])

    connection.close()


def test_create_child_node() -> None:
    """
    test that child node is created correctly
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(create_meta_data_table().command)

    # Create parent node
    parent_id = "parent-id"
    parent_node = Sqlite3FileNode(
        name="parent", parent=None, object_id=parent_id, cursor=cursor
    )

    # Define MetaData for child node
    meta = MetaData(
        name="child",
        python_type=saveable,
        role=attribute,
        element_type=python_type_literal_map[type(None)],
    )

    # create child node
    child_node = parent_node.create_child_node(meta)

    # save database changes
    conn.commit()

    # check child node attributes
    assert isinstance(child_node, Sqlite3FileNode)
    assert child_node.name == meta.name
    assert child_node._object_id != parent_node._object_id

    # check parent table has correct entries for child
    cmd = select_saveable_attributes_from_table(parent_node.name)
    cursor.execute(cmd.command, (parent_id,))
    rows = cursor.fetchall()
    row = rows[0]
    assert rows is not None and len(rows) == 1
    indices = {column_name: index for index, column_name in enumerate(cmd.columns)}
    index_reference = indices[column_name_reference]
    index_reference_id = indices[column_name_reference_id]
    assert row[index_reference] == meta.name
    assert row[index_reference_id] == child_node._object_id

    # get meta data id
    cmd = select_row_id(meta_data_table_name, list_meta_data_attributes())
    cursor.execute(cmd.command, tuple(list_meta_data_attribute_values(meta)))
    rows = cursor.fetchall()
    assert len(rows) == 1
    meta_data_id = rows[0][0]

    # check meta data is correct
    cmd = select_meta_data()
    cursor.execute(cmd.command, (meta_data_id,))
    rows = cursor.fetchall()
    assert len(rows) == 1
    row = list(rows[0])
    assert row[1:] == list_meta_data_attribute_values(meta)

    # check that child table exists
    cmd = table_exists()
    cursor.execute(cmd.command, (meta.name,))
    assert cursor.fetchone() is not None


def test_insert_data() -> None:
    """
    test method _insert_data by inserting the row ("value-A", 123)
    into a table that has column col1 and
    """

    # setup in-memory SQLite DB and cursor
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # create test table
    cursor.execute(
        """
        CREATE TABLE sample (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            col1 TEXT,
            col2 INTEGER
        )
    """
    )
    conn.commit()

    # prepare insert command with reordered columns
    sql = "INSERT INTO sample (col2, col1) VALUES (?, ?)"
    insert_command = SqlCommand(command=sql, columns=["col2", "col1"])

    # create node
    node = Sqlite3FileNode(
        name="sample", parent=None, object_id="dummy-id", cursor=cursor
    )

    # call _insert_data with unordered column-value pairs
    data = {
        "col1": "value-A",
        "col2": 123,
    }
    node._insert_data(data, insert_command)
    conn.commit()

    # verify data inserted correctly
    cursor.execute("SELECT col1, col2 FROM sample")
    row = cursor.fetchone()
    assert row == ("value-A", 123)

    conn.close()


def test_list_children() -> None:
    """
    test method list_children by reading the children child1 and child2
    from a parent node
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # create table for parent node
    parent_name = "parent"
    cmd = create_saveables_object_table(parent_name)
    cursor.execute(cmd.command)
    conn.commit()

    # insert rows that simulate references to child nodes
    parent_id = "parent-uuid"
    children_info = [("child1", "123"), ("child2", "456")]
    columns = [
        column_name_object_id,
        column_name_data,
        column_name_meta_data,
        column_name_reference,
        column_name_reference_id,
    ]
    for index, (ref, ref_id) in enumerate(children_info):
        cursor.execute(
            f"""
            INSERT INTO {parent_name} ({', '.join(columns)})
            VALUES (?, NULL, ?, ?, ?)
        """,
            (parent_id, index, ref, ref_id),
        )
    conn.commit()

    # create the parent node
    parent_node = Sqlite3FileNode(
        name=parent_name, parent=None, object_id=parent_id, cursor=cursor
    )

    # call method
    children = parent_node.list_children()

    # check result
    assert isinstance(children, list)
    assert len(children) == 2

    child_names = {child.name for child in children}
    child_ids = {child._object_id for child in children}

    assert child_names == {children_info[0][0], children_info[1][0]}
    assert child_ids == {children_info[0][1], children_info[1][1]}

    conn.close()


def test_read_primitive_data() -> None:
    """
    test method read_primitive_data by reading the integer 42
    """

    # create cursor
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # create meta_data
    attr_name = "my_integer"
    meta_data_kwargs: dict[str, str] = {
        name: attr_name,
        role: attribute,
        python_type: python_type_literal_map[int],
        element_type: python_type_literal_map[int],
    }

    # create Sqlite3FileNode and read data
    node = Sqlite3FileNode(name="parent", parent=None, object_id="123", cursor=cursor)
    filedata = SqlLite3FileData("42", meta_data_kwargs=meta_data_kwargs, meta_data_id=1)
    data_field: DataField = node.read_primitive_data(filedata)

    # assert DataField contains correct data
    assert isinstance(data_field, DataField)
    assert data_field.value == 42
    assert isinstance(data_field.meta, MetaData)
    assert data_field.meta.name == attr_name
    assert data_field.meta.python_type == python_type_literal_map[int]
    assert data_field.meta.role == attribute
    assert data_field.meta.element_type == python_type_literal_map[int]

    conn.close()


def test_read_simple_iterable() -> None:
    """
    test method read_simple_iterable by reading a integer list [42, 43]
    """

    # constants
    attr_name = "my_integer_list"  # attribute name of integer list
    node_name = "my_node"  # name of node that holds the list
    object_id = "123"
    integer_list = [42, 43]
    python_type_ = python_type_literal_map[list]
    element_type_ = python_type_literal_map[int]

    # set up database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # create meta_data table and write meta data
    cursor.execute(create_meta_data_table().command)
    cmd = insert_meta_data()
    meta_dict: dict[str, str] = {
        name: attr_name,
        role: attribute,
        python_type: python_type_,
        element_type: element_type_,
    }
    row_meta = tuple([meta_dict[col] for col in cmd.columns])
    cursor.execute(cmd.command, row_meta)
    meta_id = cursor.lastrowid
    assert meta_id is not None
    conn.commit()

    # create Sqlite3FileNode for parent object
    node = Sqlite3FileNode(
        name=node_name, parent=None, object_id=object_id, cursor=cursor
    )

    # insert list into table
    cmd = insert_primitive_data(node.name)
    primitive_data_dict = {
        column_name_meta_data: meta_id,
        column_name_object_id: object_id,
    }
    for item in integer_list:
        primitive_data_dict[column_name_data] = str(item)
        row = tuple([primitive_data_dict[col] for col in cmd.columns])
        cursor.execute(cmd.command, row)

    # test read_simple_iterable
    filedata = SqlLite3FileData(
        str(integer_list[0]), meta_data_kwargs=meta_dict, meta_data_id=str(meta_id)
    )
    data_field: DataField = node.read_simple_iterable(filedata)

    # assert DataField contains correct data
    assert isinstance(data_field, DataField)
    assert data_field.value == integer_list
    assert isinstance(data_field.meta, MetaData)
    assert data_field.meta.name == attr_name
    assert data_field.meta.python_type == python_type_
    assert data_field.meta.role == attribute
    assert data_field.meta.element_type == element_type_

    # assert the list name has been marked as read
    assert attr_name in node._processed_iterables_and_dictionary_names

    # assert that when method is called the second time with an file data object
    # that belongs to the list, it does nothing
    filedata = SqlLite3FileData(
        str(integer_list[1]), meta_data_kwargs=meta_dict, meta_data_id=str(meta_id)
    )
    assert node.read_simple_iterable(filedata) is None

    conn.close()
