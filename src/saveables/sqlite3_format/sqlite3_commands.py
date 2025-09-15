from dataclasses import dataclass

from saveables.contracts.constants import (
    column_name_data,
    column_name_id,
    column_name_meta_data,
    column_name_object_id,
    column_name_reference,
    column_name_reference_id,
    column_names,
    meta_data_table_name,
)
from saveables.saveable.utils import list_meta_data_attributes


@dataclass
class SqlCommand:
    """return type of every function that creates an sql command"""

    command: str  # command ready to be executed with cursor
    columns: list[str]  # column names involved in command

    def get_column_index(self, column_name: str) -> int:
        """index of given column

        Args:
            column_name (str): name of column the index is requested

        Raises:
            ValueError: If no column with given name is used in sql command

        Returns:
            int: column index
        """
        try:
            return self.columns.index(column_name)
        except ValueError:
            raise ValueError(f'column "{column_name}" does not exist')


def table_exists() -> SqlCommand:
    """
    return an sql command that returns (1, ) when executed if a table with given
    name exists and None if it does not

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """
    cmd = """
        SELECT 1
        FROM sqlite_master
        WHERE type='table' AND name=?
        LIMIT 1;
    """

    return SqlCommand(command=cmd, columns=[])


def create_saveables_object_table(table_name: str) -> SqlCommand:
    """
    return command to execute from sqlite cursor object that
    creates a table which holds data of a saveable object. Each row
    represents an attribute of a saveable object. The row columns have the following
    meaning:
    id: primary database key
    object_id: an id that identfies the object. This helps the distinguish between
               multiple objects with the same name in the table. Each row with same
               object_id belong to the same saveable object
    data: value of the attribute as string if data is not a saveable object itself.
          if attribute is a saveable object itself, that entry is empty
    meta_data: row number where to find meta data information of the attribute in
               the meta data table
    reference: if attribute represents a saveable object, that entry represents the
               table name where the saveable object value is saved. If attribute
               does not represent a saveable object, that entry is empty
    reference_id: object_id of a saveable attribute value in reference table

    Args:
        table_name (str): name of table

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    namess
    """
    columns = [column_name_id] + column_names

    # define column type
    column_dict: dict[str, str | None] = {colname: None for colname in columns}
    column_dict[column_name_id] = "INTEGER PRIMARY KEY AUTOINCREMENT"
    column_dict[column_name_object_id] = "TEXT NOT NULL"
    column_dict[column_name_data] = "TEXT"
    column_dict[column_name_meta_data] = "INTEGER NOT NULL"
    column_dict[column_name_reference] = "TEXT"
    column_dict[column_name_reference_id] = "TEXT"

    # check any type definitions are missing
    missing_typedefs: list[str] = []
    for key, val in column_dict.items():
        if val is None:
            missing_typedefs.append(key)
    if len(missing_typedefs) > 0:
        raise ValueError(
            f"type definitions of the following"
            f'column are missing: {", ".join(missing_typedefs)}'
        )

    column_definitions = ", ".join(
        [f"{colname} {coltype}" for colname, coltype in column_dict.items()]
    )
    command = f"""CREATE TABLE {table_name} ({column_definitions}, 
                  FOREIGN KEY ({column_name_meta_data}) REFERENCES 
                  {meta_data_table_name}({column_name_id}))"""

    return SqlCommand(command, columns)


def create_meta_data_table() -> SqlCommand:
    """
    generate sql command the creates meta data table from meta data attributes

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    # generate for each attribute the table column definition
    column_definitions: list[str] = []
    for field_name in list_meta_data_attributes():
        column_definitions.append(f"{field_name} TEXT NOT NULL")

    # put sql command together that creates meta data table
    primary_key_definition = f"{column_name_id} INTEGER PRIMARY KEY AUTOINCREMENT"
    command = (
        f"CREATE TABLE {meta_data_table_name} ("
        + f" {primary_key_definition}, "
        + ", ".join(column_definitions)
        + ")"
    )
    return SqlCommand(command, [column_name_id] + list_meta_data_attributes())


def insert_meta_data() -> SqlCommand:
    """
    sql command that puts information from meta data object into table

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    # define table columns
    columns = ", ".join([field_name for field_name in list_meta_data_attributes()])

    # define placeholders
    placeholders = ", ".join(["?" for _ in list_meta_data_attributes()])

    # put command together and return
    command = (
        f"INSERT INTO {meta_data_table_name}"
        + f"( {columns} )"
        + "VALUES"
        + f"( {placeholders} )"
    )

    return SqlCommand(command, list_meta_data_attributes())


def select_row_id(tablename: str, column_names: list[str]) -> SqlCommand:
    """
    sql command that selects the id of a row with certain column values from
    a given table

    Args:
        tablename (str): name of table
        column_names (list[str]): list of table column names

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    namess
    """
    columns = " AND ".join([f"{column_name} = ?" for column_name in column_names])
    cmd = f"SELECT {column_name_id} FROM {tablename} WHERE " + columns
    return SqlCommand(cmd, [column_name_id])


def insert_primitive_data(table_name: str) -> SqlCommand:
    """
    sql command that adds a row to a given table that represents a primitive
    data type

    Args:
        table_name (str): name of table the row is to be added

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    # column names string
    column_names_ = [col for col in column_names if not col.startswith("reference")]
    columns = ", ".join(column_names_)

    # column values: Set reference columns to NULL since they are not required
    values = ", ".join(["?" for col in column_names_])

    # put command together and return
    return SqlCommand(
        f"INSERT INTO {table_name} ({columns}) VALUES ({values})", column_names_
    )


def insert_saveable_data(table_name: str) -> SqlCommand:
    """
    sql command that adds a row to a given table that represents a saveable datatype

    Args:
        table_name (str): name of table the row is to be added

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    # column names string
    column_names_ = [col for col in column_names if col != column_name_data]
    columns = ", ".join(column_names_)

    # column values: set data column to NULL since it is not required for a saveable
    values = ", ".join(["?" for col in column_names_])

    # put command together and return
    return SqlCommand(
        f"INSERT INTO {table_name} ({columns}) VALUES ({values})", column_names_
    )


def select_python_attributes_from_table(table_name: str) -> SqlCommand:
    """
    Select all rows that belong to a certain object and represent
    a native python type. The row represents a native python type
    if the reference columns are empty. The object of interest is
    specified by object_id
    Args:
        table_name (str): name of table

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """
    # define columns that are relevant
    columns = ", ".join([column_name_data, column_name_meta_data])

    # build select command
    command = (
        f"SELECT {columns} FROM {table_name} "
        f"WHERE {column_name_object_id} = ? "
        f"AND {column_name_reference} IS NULL "
        f"AND {column_name_reference_id} IS NULL"
    )
    return SqlCommand(command, columns.split(", "))


def select_meta_data() -> SqlCommand:
    """
    get an sql command that selects a row from meta data table with
    that has certain id

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """
    # define relevant columns
    columns = ", ".join(list_meta_data_attributes())
    columns = "id, " + columns

    # put command together
    cmd = f"SELECT {columns} FROM {meta_data_table_name} WHERE id = ?"
    return SqlCommand(cmd, columns.split(", "))


def select_saveable_attributes_from_table(table_name: str) -> SqlCommand:
    """
    select all rows in a given table that belong to a certain object.

    Args:
        table_name (str): name of table to search for rows

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    # define columns that are relevant
    columns = ", ".join([column_name_reference, column_name_reference_id])

    # build select command
    command = (
        f"SELECT {columns} FROM {table_name} "
        f"WHERE {column_name_object_id} = ? "
        f"AND {column_name_reference} IS NOT NULL "
        f"AND {column_name_reference_id} IS NOT NULL"
    )
    return SqlCommand(command, columns.split(", "))


def select_simple_iterable_elements(table_name: str) -> SqlCommand:
    """
    select all rows that belong to a element in a simple iterable

    Args:
        table_name (str): name of table

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    columns = [column_name_data]

    command = (
        f"SELECT {columns[0]} FROM {table_name} "
        f"WHERE {column_name_meta_data} = ? "
        f"AND {column_name_object_id} = ? "
    )

    return SqlCommand(command, columns)


def get_first_row_of_table(table_name: str, columns: list[str]) -> SqlCommand:
    """
    get specified columns of the first row in a given table

    Args:
        table_name (str): table the first column is choosen from
        columns (list[str]): specified columns

    Returns:
        SqlCommand: object that holds sql command as string and relevant column
                    names
    """

    columns_string = ", ".join(columns)
    cmd = f"SELECT {columns_string} FROM {table_name} LIMIT 1"
    return SqlCommand(cmd, columns)
