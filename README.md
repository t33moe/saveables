
## Project Purpose

This code allows you to serialize arbitrary Python objects — 
such as dictionaries, lists, or custom classes — into structured files and restore 
them without loss. It supports the following formats:

- **XML** (human-readable, text-based)
- **HDF5** (compact and performant, suited for large datasets)

---

## Examples

Example scripts are located in the examples folder

- `xml_examples.py` – Demonstrates writing and reading XML files
- `hdf5_examples.py` – Demonstrates writing and reading HDF5 files

---

## Project Structure
    .
    ├── examples: Example usage for XML and HDF5
    ├── resources: Development resources
    |   ├── vs_code: vs code configuration files               
    ├── src 
    │   ├── base: Abstract base classes for file and node structure
    │   ├── contracts: Constants and type definitions
    │   ├── hdf5_format: HDF5-specific implementation
    │   ├── xml_format: XML-specific implementation
    │   └── saveable: Interfaces and helpers for saveable objects
    └── tests
        ├── resources: Test data and mocks
        ├── test_integration: Integration tests for base components
        ├── test_unit: Unit tests for XML and HDF5 format 
        └── test_software: Tests for XML and HDF5 functionality

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
  - write tests for File-Objects and Saveable-Objects 
  - write more unit tests for h5/xml FileNode objects - in particular tests that check error cases
  - write unit tests for utils functions
* Build script
  - write script that builds a python library from code
* Code quality
  - create method extract_meta_data in class XmlFileNode
  - add logging
* Features
  - support sqlite3 file format
  - allow lists/tuples/sets of Saveable objects



