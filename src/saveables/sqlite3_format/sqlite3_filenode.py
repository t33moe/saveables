from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Generator

from saveables.base.base_file_node import BaseFileNode
from saveables.contracts.constants import (attribute, column_name_data,
                                           column_name_id,
                                           column_name_meta_data,
                                           column_name_object_id,
                                           column_name_reference,
                                           column_name_reference_id, dict_keys,
                                           dict_values, meta_data_table_name,
                                           n_object_id_chars, none_literal,
                                           python_type)
from saveables.contracts.data_type import (EmptyIterable,
                                           python_type_literal_map,
                                           python_type_literal_map_reversed)
from saveables.python_utils import generate_uuid
from saveables.saveable.data_field import DataField
from saveables.saveable.meta_data import MetaData
from saveables.saveable.utils import (is_simple_iterable,
                                      is_supported_primitive,
                                      list_meta_data_attribute_values,
                                      list_meta_data_attributes)
from saveables.sqlite3_format.sqlite3_commands import (
    SqlCommand, create_saveables_object_table, insert_meta_data,
    insert_primitive_data, insert_saveable_data, select_meta_data,
    select_python_attributes_from_table, select_row_id,
    select_saveable_attributes_from_table, select_simple_iterable_elements,
    table_exists)
from saveables.sqlite3_format.sqlite3filedata import SqlLite3FileData

if TYPE_CHECKING:
    from sqlite3 import Cursor
logger = getLogger(__file__)


class Sqlite3FileNode(BaseFileNode[SqlLite3FileData]):

    def __init__(
        self, name: str, parent: Sqlite3FileNode | None, cursor: Cursor, object_id: str
    ):
        super().__init__(name, parent)
        self._cursor = cursor
        self._object_id = object_id
        self._processed_iterables_and_dictionary_names: list[str] = []
        self._dict_keys_cache: dict[
            str, list[float] | list[str] | list[int] | list[bool]
        ] = dict()
        self._dict_values_cache: dict[
            str, list[float] | list[str] | list[int] | list[bool]
        ] = dict()

        # create table for filenode if neccessary
        self._create_table(self.name, create_saveables_object_table(self.name))

    def create_child_node(self, meta: MetaData) -> Sqlite3FileNode:
        """
        generate a child node from given meta data

        Args:
            meta (MetaData): meta data object that holds all the neccessary
                             information of the attribute the child node does
                             represent, like the attribute's name and type
                             for example

        Returns:
            Sqlite3FileNode: genereated child node
        """

        # create child node
        child = Sqlite3FileNode(
            meta.name, self, self._cursor, object_id=generate_uuid(n_object_id_chars)
        )

        # write meta data for child node
        meta_data_id = self._write_meta_data(meta)

        # write refrence into table
        insert_saveable_data_command = insert_saveable_data(self.name)
        data: dict[str, str | int] = {
            column_name_reference: meta.name,
            column_name_reference_id: child._object_id,
            column_name_object_id: self._object_id,
            column_name_meta_data: meta_data_id,
        }
        self._insert_data(data, insert_saveable_data_command)

        return child

    def _create_table(self, table_name: str, create_command: SqlCommand) -> None:
        """
        create a table if it does not exist already and log a message if table
        already exists

        Args:
            table_name (str): name of table that is supposed to be created
            create_command (SqlCommand): sql command used to create specified
        """

        # check if table already exists
        table_exists_command = table_exists()
        self._cursor.execute(table_exists_command.command, (table_name,))
        exists = self._cursor.fetchone() is not None

        # create table if it does not exists
        if not exists:
            self._cursor.execute(create_command.command)
        else:
            logger.info(f"table {table_name} already exists.")

    def _write_meta_data(self, meta: MetaData) -> int:
        """
        write meta data into table and return row id. If a row with given meta
        data exists already, this method will not create a new row.

        Args:
            meta (MetaData): meta data object whose data is written into table

        Raises:
            TypeError: if row id is not an integer

        Returns:
            int: row id of meta data table row that holds the meta data
        """
        row = tuple(list_meta_data_attribute_values(meta))

        # check if row already exists
        select_command = select_row_id(
            meta_data_table_name, list_meta_data_attributes()
        )
        self._cursor.execute(select_command.command, row)
        fetched = self._cursor.fetchone()
        row_exists = fetched is not None

        if not row_exists:
            # write data in table
            insert_command = insert_meta_data()
            data: dict[str, str | int] = {
                col: row_value for col, row_value in zip(insert_command.columns, row)
            }

            self._insert_data(data, insert_command)
            id_ = self._cursor.lastrowid
        else:
            # extract id from fetch
            id_ = fetched[select_command.get_column_index(column_name=column_name_id)]

        # satisfy mypy: check if id is an integer
        if not isinstance(id_, int):
            raise TypeError("meta data id must be an integer")

        return id_

    def write_primitive_data(self, data_field: DataField) -> None:
        """
        write primitve data as new row into sql table and create a new meta data
        entry if neccessary

        Args:
            data_field (DataField): datafield that holds primitive python data

        Raises:
            TypeError: if type of data field value is not supported
            ValueError: an error occured during cast into sting of data field value

        """
        if not is_supported_primitive(data_field.value):
            raise TypeError(
                f"unsupported primitive data type: {type(data_field.value)}"
            )

        # write meta data into table
        meta_data_id = self._write_meta_data(data_field.meta)

        # convert value to a string, since table schema assumes data to be TEXT
        value = str(data_field.value)

        # create sql command
        insert_command = insert_primitive_data(self.name)

        # insert data into table using insert sql command
        data: dict[str, str | int] = {
            column_name_object_id: self._object_id,
            column_name_meta_data: meta_data_id,
            column_name_data: value,
        }
        self._insert_data(data, insert_command)

    def _insert_data(
        self, data_dict: dict[str, str | int], insert_command: SqlCommand
    ) -> None:
        """
        write data into sql table using the passed sql command.
        The data is sorted automatically to match the order of columns in specified sql
        command

        Args:
            data_dict dict[str, str | int]: pairs column names and
                                            the data that is to be
                                            written in those columns
            insert_command (SqlCommand): insert sql command that will be used to inset
                                         data into database

        Raises:
            ValueError: if data for a required column is not provided
        """

        # build row in correct order of columns
        row: list[str | int] = []
        for col in insert_command.columns:
            try:
                row.append(data_dict[col])
            except KeyError:
                raise ValueError(
                    f"column {col} is required for "
                    f"command {insert_command.command} but data "
                    "is not provided"
                )

        # execute sql command with data
        self._cursor.execute(insert_command.command, tuple(row))

    def write_simple_iterable(self, data_field: DataField) -> None:
        """
        write list/tuple/set whose elements have all the same data type
        into sql table element-wise

        Args:
            data_field (DataField): data field whose value is a list / tuple / set

        Raises:
            TypeError: if data field value is not a list/tuple/set whose elements
                       have all the same data type
        """

        if not is_simple_iterable(data_field.value):
            raise TypeError(
                f"Attribute {data_field.meta.name} of {self.name} is "
                "expected to be a simple iterable"
            )

        for item in data_field.value:  # type: ignore[union-attr]
            data_field_ = DataField(value=item, meta=data_field.meta)
            self.write_primitive_data(data_field_)

    def __iter__(self) -> Generator[tuple[SqlLite3FileData, type], None, None]:
        """
        iterates through records in table that represent a native python attribute
        of the object represented by the node

        Raises:
            ValueError: if no meta data entry can be found for considered
                        attribute or if arguments missing that neccessary to
                        create a meta data object
        """

        # get all rows that belong to native python attributes of the current object
        select_attribute_cmd = select_python_attributes_from_table(self.name)
        self._cursor.execute(select_attribute_cmd.command, (self._object_id,))
        rows = self._cursor.fetchall()

        # create meta data query
        select_meta_data_cmd = select_meta_data()

        # get column indices of relevant information
        meta_data_column_index = select_attribute_cmd.get_column_index(
            column_name_meta_data
        )
        data_index = select_attribute_cmd.get_column_index(column_name_data)

        # iter though rows, extract information and yield sqlite3data object and type
        for row in rows:
            # get meta data for row
            meta_data_id = row[meta_data_column_index]
            self._cursor.execute(select_meta_data_cmd.command, (meta_data_id,))
            meta_data_row: tuple[str] = self._cursor.fetchone()
            if len(meta_data_row) == 0:
                raise ValueError(f"no meta data entry found for id: {meta_data_id}")

            # extract meta data keyword arguments
            meta_data_kwargs: dict[str, str] = {}
            meta_data_attr_names = list_meta_data_attributes()
            for column_name in select_meta_data_cmd.columns:
                if column_name in meta_data_attr_names:
                    index = select_meta_data_cmd.get_column_index(column_name)
                    meta_data_kwargs[column_name] = meta_data_row[index]

            # check if arguments are missing
            missing_args = set(meta_data_kwargs.keys()).difference(meta_data_attr_names)
            if len(missing_args) > 0:
                missing_args_joined = ", ".join(missing_args)
                raise ValueError(f"keyword arguments {missing_args_joined} are missng")

            # create SqlLite3FileData
            filedata = SqlLite3FileData(row[data_index], meta_data_kwargs, meta_data_id)

            # read pytnon type
            type_ = python_type_literal_map_reversed[meta_data_kwargs[python_type]]  # type: ignore[index] # noqa: E501

            yield filedata, type_

    def list_children(self) -> list[BaseFileNode[SqlLite3FileData]]:
        """
        list child nodes of current node

        Returns:
            list[Sqlite3FileNode]: list of child nodes

        """
        children: list[BaseFileNode[SqlLite3FileData]] = []
        # select rows from table that represent a saveable attribute
        command = select_saveable_attributes_from_table(self.name)
        self._cursor.execute(command.command, (self._object_id,))
        rows: list[tuple[str]] = self._cursor.fetchall()

        # get neccessary indices to extract data
        reference_name_index = command.get_column_index(column_name_reference)
        reference_id_index = command.get_column_index(column_name_reference_id)

        # iter though rows, extract reference information and create child node
        for row in rows:
            reference_id = row[reference_id_index]
            reference_name = row[reference_name_index]
            child = Sqlite3FileNode(
                name=reference_name,
                parent=self,
                cursor=self._cursor,
                object_id=reference_id,
            )
            children.append(child)

        return children

    def read_primitive_data(self, filedata: SqlLite3FileData) -> DataField:
        """
        read file data that represents primitive python data like int, str, float etc.

        Args:
            filedata (SqlLite3FileData): file data object that holds relevat information
                                         to parse data from file into a DataField object

        Returns:
            DataField: _description_
        """
        meta_data = MetaData(**filedata.meta_data_kwargs)  # type: ignore[arg-type]

        # cast string to correct type
        type_ = python_type_literal_map_reversed[meta_data.python_type]
        value = type_(filedata.data)

        # create DataField object
        return DataField(meta=meta_data, value=value)

    def read_simple_iterable(self, filedata: SqlLite3FileData) -> DataField | None:
        """
        read list, set or tuples whose elements have all the same type

        Args:
            filedata (SqlLite3FileData): file data object that holds relevat information
                                         to parse data from file into a DataField object

        Returns:
            DataField | None: returns a datafield that holds list / tuple / set
                              and its meta data if the list / tuple / set has not
                              been already read
        """

        # create mete data
        meta = MetaData(**filedata.meta_data_kwargs)  # type: ignore[arg-type]

        # check if iterable has already been read
        if meta.name in self._processed_iterables_and_dictionary_names:
            return None

        # select element rows in table
        select_iterable_command = select_simple_iterable_elements(self.name)
        self._cursor.execute(
            select_iterable_command.command, (filedata.meta_data_id, self._object_id)
        )
        rows = self._cursor.fetchall()

        # iter through rows and read iterable elements
        index = select_iterable_command.get_column_index(column_name_data)
        element_python_type_ = python_type_literal_map_reversed[meta.element_type]
        python_type_ = python_type_literal_map_reversed[meta.python_type]
        value_raw: list = []  # type: ignore[type-arg]
        if element_python_type_ != EmptyIterable:
            for row in rows:
                value_raw.append(element_python_type_(row[index]))

        # cast raw_value into correct iterable type
        value = python_type_(value_raw)

        # mark iterable as read
        self._processed_iterables_and_dictionary_names.append(meta.name)

        return DataField(meta, value)

    def read_simple_dictionary(self, filedata: SqlLite3FileData) -> DataField | None:
        """
        read list of keys / values of a dictonary and put them into cache. If
        both lists are read and in the cache, a data field object with the reconstructed
        dictionary is returned

        Args:
            filedata (SqlLite3FileData): file data object that holds relevat information
                                         to parse data from file into a DataField object

        Returns:
            DataField | None: Datfield that holds the reconstructed dictionary.
            If dictionary keys or values are missing, None is returned
        """

        # create meta data object
        meta = MetaData(**filedata.meta_data_kwargs)  # type: ignore[arg-type]

        # check if dictionary has already been read completely
        if meta.name in self._dict_keys_cache and meta.name in self._dict_values_cache:
            return None

        # check if keys have alread been read
        if meta.name in self._dict_keys_cache and meta.role == dict_keys:
            return None

        # check if values have already been read
        if meta.name in self._dict_values_cache and meta.role == dict_values:
            return None

        # get all elements from dictionary keys or values
        select_simple_iterable_elements_command = select_simple_iterable_elements(
            self.name
        )
        self._cursor.execute(
            select_simple_iterable_elements_command.command,
            (
                filedata.meta_data_id,
                self._object_id,
            ),
        )
        rows = self._cursor.fetchall()
        index = select_simple_iterable_elements_command.get_column_index(
            column_name_data
        )
        element_type_ = python_type_literal_map_reversed[meta.element_type]
        if element_type_ == EmptyIterable:
            elements = []
        else:
            elements = [element_type_(row[index]) for row in rows]

        # put elements into cache
        if meta.role == dict_keys:
            self._dict_keys_cache[meta.name] = elements

        if meta.role == dict_values:
            self._dict_values_cache[meta.name] = elements

        # create data field if keys and values have been read
        if meta.name in self._dict_keys_cache and meta.name in self._dict_values_cache:
            keys = self._dict_keys_cache[meta.name]
            values = self._dict_values_cache[meta.name]
            value_dict = {k: v for k, v in zip(keys, values)}
            meta_dict = MetaData(
                python_type=python_type_literal_map[dict],
                role=attribute,
                name=meta.name,
                element_type=python_type_literal_map[type(None)],  # type: ignore[arg-type] # noqa: E501
            )
            return DataField(value=value_dict, meta=meta_dict)
        else:
            return None

    def write_none(self, data_field: DataField) -> None:
        """
        write none value into sql table

        Args:
            data_field (DataField): data field that holds None as value

        Raises:
            TypeError: if data_field's value is not None
        """

        if data_field.value is not None:
            raise TypeError(f"value must be None but is {data_field.value}")

        # write none literal into sql table
        data_field_none = DataField(value=none_literal, meta=data_field.meta)
        self.write_primitive_data(data_field_none)
