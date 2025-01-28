#
# Copyright 2018 BhaaL
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
Convert flat XML files to Gettext PO localization files.

This module handles conversion of flat XML files, which are XML files with a simple
key-value structure, into PO (Portable Object) format for translation.

Key Features:
1. Processes flat XML structures (key-value pairs)
2. Configurable XML element and attribute names
3. Optional XML namespace support
4. Preserves XML structure during conversion
5. Handles empty files gracefully
6. Command-line interface with customization options

Flat XML Structure Example:
    <root>
        <str key="greeting">Hello World</str>
        <str key="farewell">Goodbye</str>
    </root>

Usage:
    flatxml2po input.xml output.po --root=root --value=str --key=key

For detailed usage instructions and examples, see:
http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/flatxml2po.html
"""

from translate.convert import convert
from translate.storage import flatxml, po


class flatxml2po:
    """
    Converter for transforming flat XML files to PO format.
    
    This class handles the conversion of XML files with a simple structure
    where translatable strings are stored as values with unique keys.
    
    Attributes:
        SourceStoreClass: Class to handle XML input (FlatXMLFile)
        TargetStoreClass: Class to handle PO output (pofile)
        TargetUnitClass: Class for individual PO units (pounit)
    """

    SourceStoreClass = flatxml.FlatXMLFile
    TargetStoreClass = po.pofile
    TargetUnitClass = po.pounit

    def __init__(
        self,
        inputfile,
        outputfile,
        templatefile=None,
        root="root",
        value="str",
        key="key",
        ns=None,
    ):
        """
        Initialize the XML to PO converter.
        
        Args:
            inputfile: Source XML file
            outputfile: Target PO file
            templatefile: Template file (unused)
            root: Name of root XML element
            value: Name of elements containing translatable strings
            key: Name of attribute containing string identifier
            ns: XML namespace URI
        """
        self.inputfile = inputfile
        self.outputfile = outputfile

        self.source_store = self.SourceStoreClass(
            inputfile, root_name=root, value_name=value, key_name=key, namespace=ns
        )
        self.target_store = self.TargetStoreClass()

    def convert_unit(self, unit):
        """
        Convert a single XML unit to PO format.
        
        Takes a unit from the XML file (containing a translatable string
        and its key) and creates a corresponding PO unit.
        
        Args:
            unit: Source XML unit
            
        Returns:
            PO unit containing the translatable string
        """
        return self.TargetUnitClass.buildfromunit(unit)

    def convert_store(self):
        """
        Convert the entire XML file to PO format.
        
        Process:
        1. Iterate through all XML units
        2. Convert each unit to PO format
        3. Add converted units to target store
        """
        for source_unit in self.source_store.units:
            self.target_store.addunit(self.convert_unit(source_unit))

    def run(self):
        """
        Execute the conversion process.
        
        Process:
        1. Convert the XML store to PO
        2. Check if result is empty
        3. Serialize output if not empty
        
        Returns:
            1 if conversion successful and not empty
            0 if resulting PO file would be empty
        """
        self.convert_store()

        if self.target_store.isempty():
            return 0

        self.target_store.serialize(self.outputfile)
        return 1


def run_converter(
    inputfile,
    outputfile,
    templatefile=None,
    root="root",
    value="str",
    key="key",
    ns=None,
):
    """
    Convenience function to run the converter.
    
    Creates a converter instance and runs it with the given parameters.
    
    Args:
        inputfile: Source XML file
        outputfile: Target PO file
        templatefile: Template file (unused)
        root: Root element name
        value: Value element name
        key: Key attribute name
        ns: XML namespace
        
    Returns:
        Result of conversion (0 or 1)
    """
    return flatxml2po(inputfile, outputfile, templatefile, root, value, key, ns).run()


# Supported format pairs for conversion
formats = {
    "xml": ("po", run_converter),
}


def main(argv=None):
    """
    Command-line interface for the converter.
    
    Provides options to customize:
    - Root element name (-r, --root)
    - Value element name (-v, --value)
    - Key attribute name (-k, --key)
    - XML namespace (-n, --namespace)
    
    Example:
        flatxml2po -r root -v string -k id input.xml output.po
    """
    parser = convert.ConvertOptionParser(formats, description=__doc__)

    parser.add_option(
        "-r",
        "--root",
        action="store",
        dest="root",
        default="root",
        help='name of the XML root element (default: "root")',
    )
    parser.add_option(
        "-v",
        "--value",
        action="store",
        dest="value",
        default="str",
        help='name of the XML value element (default: "str")',
    )
    parser.add_option(
        "-k",
        "--key",
        action="store",
        dest="key",
        default="key",
        help='name of the XML key attribute (default: "key")',
    )
    parser.add_option(
        "-n",
        "--namespace",
        action="store",
        dest="ns",
        default=None,
        help="XML namespace uri (default: None)",
    )

    parser.passthrough.append("root")
    parser.passthrough.append("value")
    parser.passthrough.append("key")
    parser.passthrough.append("ns")

    parser.run(argv)


if __name__ == "__main__":
    main()
