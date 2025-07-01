import xml.etree.ElementTree as ET
from xml.dom import minidom

from saveables.base.base_file import BaseFile
from saveables.contracts.constants import root, write_mode
from saveables.xml_format.xml_filenode import XmlFileNode


class XmlFile(BaseFile):
    """XML specific implementations to save and load Saveable objects"""

    def open(self) -> None:
        if self.mode == write_mode:
            # initialize root xml element
            self._root_element = ET.Element(root)
        else:
            # parse xml file and get root
            tree = ET.parse(self.path)
            self._root_element = tree.getroot()
        self.root = XmlFileNode(root, None, self._root_element)

    def close(self) -> None:
        if self.mode == write_mode:
            # recursively dump data into file
            rough_string = ET.tostring(self._root_element, "utf-8")
            reparsed = minidom.parseString(rough_string)
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(reparsed.toprettyxml(indent="  "))
