from dataclasses import dataclass


@dataclass
class SqlLite3FileData:
    """
    object that is extracted from sqlite3 file for each attribute that does
    not represent a saveable object
    """

    data: str  # data of attribute converted as a string
    meta_data_kwargs: dict[str, str]  # keyword arguments to initialize
    # a MetaData objecst
    meta_data_id: int  # row id in meta data table
