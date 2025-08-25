
## Project Purpose

This code allows you to serialize custom nested data structures and restore 
them without loss. It supports the following formats:

- **XML** (human-readable, text-based)
- **HDF5** (compact and performant, suited for large datasets)
- **Sqlite3** (table based database format)

---

## Examples

Example scripts are located in the examples folder

- `xml_examples.py` – Demonstrates writing and reading XML files
- `hdf5_examples.py` – Demonstrates writing and reading HDF5 files
- `sqlite3_examples.py` – Demonstrates writing and reading Sqlite3 files

---

## Project Structure
    .
    ├── examples: Example usage for XML, HDF5 and Sqlite3
    ├── resources: Development resources
    |   └──  vs_code: vs code configuration files               
    ├── src 
    |   └── saveables
    │       ├── base: Abstract base classes for file and node structure
    │       ├── contracts: Constants and type definitions
    │       ├── hdf5_format: HDF5-specific implementation
    │       ├── xml_format: XML-specific implementation
    |       ├── sqlite3_format: sqlite3-specific implementation  
    │       └── saveable: Interfaces and helpers to set up data structures
    └── tests
        ├── resources: Test data and mocks
        ├── test_integration: Integration tests for base components
        ├── test_unit: Unit tests for XML, HDF5 and Sqlite3 format 
        └── test_software: Tests for XML, HDF5 and Sqlite3 functionality

## Development setup for visual studio code

Create a new python environment named `.venv` in the project top level folder and install
the dependencies from file `resources/requirements.txt`

Create a folder `.vscode` in the project top level folder and copy `launch.json` from 
`resources\vs_code` into that folder. Do the same for the settings file that fits your
operating system and remove the operating system file name suffix. There must be now
two files `settings.json` and `launch.json` in the folder `.vscode` 

Before you can run tests, press ctrl+shift+p, select Python: Configure Tests and choose
`pytest`

## TODO

* Test coverage
  - write more unit tests for h5/xml/sqlite3 FileNode objects - in particular tests that check error cases
* Code quality
  - create method extract_meta_data in class XmlFileNode
  - add logging
  - split node interface into a interface for reading and an interface for writing
  - split file constants.py
* Features
  - allow lists/tuples/sets of Saveable objects



