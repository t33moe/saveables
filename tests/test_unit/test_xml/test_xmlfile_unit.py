from pathlib import Path

from saveables.contracts.constants import root, write_mode
from saveables.xml_format.xml_file import XmlFile
from saveables.xml_format.xml_filenode import XmlFileNode


def test_xmlfile_open(local_tmp: Path) -> None:
    """
    test xmlfile creates root node upon opening

    Args:
        local_tmp (Path): temporary test directory
    """

    # create file object and open it
    tmpfile = local_tmp / "test.xml"
    xmlfile = XmlFile(path=tmpfile, mode=write_mode)
    xmlfile.open()

    # check that root node has been created correctly
    assert isinstance(xmlfile.root, XmlFileNode)
    assert xmlfile.root.name == root
    assert xmlfile.root.parent is None
    assert xmlfile.root._element.tag == root
