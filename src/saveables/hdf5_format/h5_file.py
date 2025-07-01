import h5py  # type: ignore[import-untyped]

from saveables.base.base_file import BaseFile
from saveables.contracts.constants import read_mode, root, write_mode
from saveables.hdf5_format.h5_filenode import H5FileNode


class H5File(BaseFile):
    """HDF5 specific implementations to save and load Saveable objects"""

    def open(self):
        """
        prepares file for loading/writing

        Raises:
            ValueError: if unexpected file mode occurs
        """
        # open hdf5 file
        self._file = h5py.File(str(self.path), mode=self.mode)

        # create root node
        if self.mode == write_mode:
            group = self._file.create_group(root)
        elif self.mode == read_mode:
            group = self._file[root]
        else:
            raise ValueError(f"unknown file mode {self.mode}")
        self.root = H5FileNode(root, None, group)

    def close(self):
        self._file.close()
