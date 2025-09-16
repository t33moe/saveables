import sqlite3
from pathlib import Path

from saveables.base.base_file import BaseFile
from saveables.contracts.constants import (column_name_id,
                                           column_name_object_id,
                                           meta_data_table_name,
                                           n_object_id_chars, read_mode, root,
                                           write_mode)
from saveables.contracts.data_type import tFileMode
from saveables.python_utils import generate_uuid
from saveables.sqlite3_format.sqlite3_commands import (create_meta_data_table,
                                                       get_first_row_of_table,
                                                       table_exists)
from saveables.sqlite3_format.sqlite3_filenode import Sqlite3FileNode


class Sqlite3File(BaseFile):
    def __init__(self, path: str | Path, mode: tFileMode):
        super().__init__(path, mode)
        self.conn: sqlite3.Connection | None = None

    def open(self) -> None:
        """
        prepares file for writing or loading sqlite3 files
        """

        if self.mode == write_mode:
            self._open_to_write()
        elif self.mode == read_mode:
            self._open_to_read()
        else:
            raise ValueError(f"unknown read mode: {self.mode}")

    def _open_to_write(self) -> None:
        """
        open file for write operation
        """

        # open a sqlite3 file
        conn = sqlite3.connect(self.path)
        self.conn = conn
        cursor = conn.cursor()

        # create table for meta data objects
        cursor.execute(create_meta_data_table().command)

        # create root file node
        node = Sqlite3FileNode(
            name=root,
            parent=None,
            cursor=cursor,
            object_id=generate_uuid(n_object_id_chars),
        )
        self.root = node

    def _open_to_read(self) -> None:
        """
        open file for read operation

        Raises:
            ValueError: If root table or meta table in file is empty or does not exist
        """

        # open a sqlite3 file
        conn = sqlite3.connect(self.path)
        self.conn = conn
        cursor = conn.cursor()

        # check if neccessary tables exist
        cmd = table_exists()
        cursor.execute(cmd.command, (root,))
        if cursor.fetchone() is None:
            raise ValueError(f"table {root} does not exist in database {self.path}")
        cursor.execute(cmd.command, (meta_data_table_name,))
        if cursor.fetchone() is None:
            raise ValueError(
                f"table {meta_data_table_name} does not exist in database {self.path}"
            )

        # check if tables are not empty
        cmd = get_first_row_of_table(root, [column_name_id])
        cursor.execute(cmd.command)
        if cursor.fetchone() is None:
            raise ValueError(
                f"table {root} exists in database {self.path} but is empty"
            )

        cmd = get_first_row_of_table(meta_data_table_name, [column_name_id])
        cursor.execute(cmd.command)
        if cursor.fetchone() is None:
            raise ValueError(
                f"table {meta_data_table_name} exists in "
                f"database {self.path} but is empty"
            )

        # extract object id of root file node from table
        # this must be the object id column of the first row in root table
        cmd = get_first_row_of_table(root, [column_name_object_id])
        cursor.execute(cmd.command)
        row = cursor.fetchone()
        index = cmd.get_column_index(column_name_object_id)
        object_id = row[index]

        # create root node
        self.root = Sqlite3FileNode(
            name=root, parent=None, cursor=cursor, object_id=object_id
        )

    def close(self) -> None:
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
        else:
            raise ValueError(f"sqlite3 file {self.path} has not been opened")
