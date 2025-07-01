import xml.etree.ElementTree as ET

from saveables.contracts.constants import attribute, name, python_type, saveable
from saveables.contracts.data_type import python_type_literal_map
from saveables.saveable.meta_data import MetaData
from saveables.xml_format.xml_filenode import XmlFileNode


def test_list_children_xml():
    """
    test that the children of xml file node are listed correctly
    """
    # set up XML structure
    root = ET.Element("root")

    # create element that should be recognized (has python_type="saveable")
    ET.SubElement(root, "item1", attrib={name: "child1", python_type: saveable})

    # create element that should NOT be recognized
    ET.SubElement(
        root,
        "item2",
        attrib={name: "child2", python_type: python_type_literal_map[int]},
    )

    # create another valid saveable element
    ET.SubElement(root, "item3", attrib={name: "child3", python_type: saveable})

    # instantiate node and list children
    node = XmlFileNode("root", parent=None, element=root)
    children = node.list_children()

    # check result
    child_names = sorted(child.name for child in children)
    assert child_names == ["child1", "child3"]


def test_write_primitive_data():
    """
    test that primitive data is written correctly into xml tag
    """

    # create root xml element
    root = ET.Element("root")

    # create xml file node to write data
    node = XmlFileNode("root", parent=None, element=root)

    # create data to write
    data = 42

    # create meta data
    meta = MetaData(
        name="myfield",
        python_type=python_type_literal_map[type(data)],
        role=attribute,
        element_type=python_type_literal_map[type(data)],
    )

    # write primitive data
    node._write_primitive_data(42, meta)

    # search for xml elmennt "myfield"
    elements = root.findall("myfield")
    assert len(elements) == 1

    # check xml element text which represents data
    el = elements[0]
    assert el.text == str(data)

    # check that meta data is written correctly as attributes
    for key, val in meta.__dict__.items():
        assert el.attrib[key] == str(val)
