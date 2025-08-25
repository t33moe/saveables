from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from saveables.contracts.constants import read_mode, write_mode
from saveables.sqlite3_format.sqlite3_file import Sqlite3File
from saveables.saveable.saveable import Saveable

# create subclasses of Saveable class that hold the data to be save.
# ALL attributes must have a default value. If the attribute is
# a list / tuple / set / Saveable, its default
# values MUST BE AN EMPTY list / tuple / set / Saveable.


@dataclass
class Address(Saveable):  # type: ignore[misc]
    street: Optional[str] = None
    house_number: Optional[str] = None
    zip_code: Optional[int] = None
    city: Optional[str] = None


@dataclass
class Person(Saveable):  # type: ignore[misc]
    name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    address: Address = field(default_factory=Address)
    children: list[str] = field(default_factory=list)


adr = Address("Evergreen Terrace", "742", 65619, "Springfield")
person = Person(
    "Homer", "Simpson", 48, adr, ["Bart Simpson", "Lisa Simpson", "Maggie Simpson"]
)

# delete path if file has been already been created from former run
path = Path(__file__).parent / "person.sqlite3"
if path.exists():
    Path.unlink(path)
if not path.exists():
    print(f"{path} has been deleted")

# to save data, instantiate a file object through a context manager and call
# method save
with Sqlite3File(path, write_mode) as f:
    f.save(person)

# to load data, instantiate an object that is supposed to
# hold the data from the file first.
person_loaded = Person()

# second, instantiate a file object through a context manager and
# call method load
with Sqlite3File(path, read_mode) as f:
    f.load(person_loaded)
