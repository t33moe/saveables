import xml.etree.ElementTree as ET
from xml.dom import minidom

from src.base.base_file import BaseFile
from src.contracts.constants import root, write_mode
from src.xml_format.xml_filenode import XmlFileNode


class XmlFile(BaseFile):
    def open(self):
        if self.mode == write_mode:
            self._root_element = ET.Element(root)
        else:
            tree = ET.parse(self.path)
            self._root_element = tree.getroot()
        self.root = XmlFileNode(root, None, self._root_element)

    def close(self):
        if self.mode == write_mode:
            rough_string = ET.tostring(self._root_element, "utf-8")
            reparsed = minidom.parseString(rough_string)
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(reparsed.toprettyxml(indent="  "))
