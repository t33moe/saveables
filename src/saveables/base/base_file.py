from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from saveables.base.base_file_node import BaseFileNode
from saveables.saveable.saveable import Saveable

if TYPE_CHECKING:
    from saveables.contracts.data_type import tFileMode


class BaseFile(ABC):
    """
    base class that provides save and load functionality for Saveable objects
    """

    def __init__(self, path: str | Path, mode: tFileMode):
        self.path = path if isinstance(path, Path) else Path(path)
        self.root: BaseFileNode | None = (
            None  # root file node. Needs to be set in method _initialize_root
        )
        self.mode = mode

    def save(self, saveable: Saveable):
        """
        save object to file

        Args:
            saveable (Saveable): object whose data are to be written to file

        Raises:
            ValueError: raises ValueError is root is not initialized. Most probable
                        cause for this that it has been forgotten to open the file
        """

        # check if root is initialized
        if self.root is None:
            raise ValueError("no root node initialized")

        # add data to top level node
        for data_field in saveable.iter_fields():
            self.root.write_data(data_field)

    def load(self, saveable: Saveable):
        """
        load data from file into given object

        Args:
            saveable (Saveable): object that is supposed to hold the data from the file

        Raises:
            ValueError: raises ValueError is root is not initialized. Most probable
                        cause for this that it has been forgotten to open the file
        """

        # check if root is initialized
        if self.root is None:
            raise ValueError("no root node initialized")

        # load data
        self.root.load(saveable)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    @abstractmethod
    def open(self):
        """
        prepares file for loading/writing
        """        
        pass

    @abstractmethod
    def close(self) -> bool:
        pass
