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
Convert Gettext PO localization files to flat XML files.

This module handles conversion of PO (Portable Object) files back into flat XML
format, completing the round-trip translation workflow. It can either create new
XML files or update existing ones with translations.

Key Features:
1. Converts PO translations to XML key-value pairs
2. Optional template-based XML generation
3. Configurable XML structure and formatting
4. XML namespace support
5. Customizable indentation
6. Preserves untranslated strings
7. Updates existing XML files

XML Output Example:
    <root>
        <str key="greeting">Bonjour le monde</str>
        <str key="farewell">Au revoir</str>
    </root>

Usage:
    po2flatxml input.po output.xml --root=root --value=str --key=key

For detailed usage instructions and examples, see:
http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/flatxml2po.html
"""

from translate.convert import convert
from translate.storage import flatxml, po


class po2flatxml:
    """
    Converter for transforming PO files back to flat XML format.
    
    This class handles the conversion of translated PO files into XML files
    with a simple key-value structure. It can either create new XML files
    or update existing ones with translations.
    
    Features:
    - Template-based conversion
    - Configurable XML structure
    - Customizable indentation
    - Namespace support
    - Fallback to source for untranslated strings
    
    Attributes:
        TargetStoreClass: Class to handle XML output (FlatXMLFile)
        TargetUnitClass: Class for individual XML units (FlatXMLUnit)
    """

    TargetStoreClass = flatxml.FlatXMLFile
    TargetUnitClass = flatxml.FlatXMLUnit

    def __init__(
        self,
        inputfile,
        outputfile,
        templatefile=None,
        root="root",
        value="str",
        key="key",
        ns=None,
        indent=2,
    ):
        """
        Initialize the PO to XML converter.
        
        Args:
            inputfile: Source PO file with translations
            outputfile: Target XML file to create
            templatefile: Optional template XML file to update
            root: Name of root XML element
            value: Name of elements containing strings
            key: Name of attribute containing string identifier
            ns: XML namespace URI
            indent: Number of spaces for indentation (0 for none)
        """
        self.inputfile = inputfile
        self.outputfile = outputfile
        self.templatefile = templatefile

        self.value_name = value
        self.key_name = key
        self.namespace = ns

        indent_chars = None
        if indent > 0:
            indent_chars = " " * indent

        self.source_store = po.pofile(inputfile)
        self.target_store = self.TargetStoreClass(
            templatefile,
            root_name=root,
            value_name=value,
            key_name=key,
            namespace=ns,
            indent_chars=indent_chars,
        )

    def convert_unit(self, unit):
        """
        Convert a single PO unit to XML format.
        
        Creates a new XML unit with:
        - Source text as the key
        - Translated text as the value
        - Falls back to source text if no translation
        
        Args:
            unit: Source PO unit with translation
            
        Returns:
            XML unit containing the translated string
        """
        target_unit = self.TargetUnitClass(
            source=None,
            namespace=self.namespace,
            element_name=self.value_name,
            attribute_name=self.key_name,
        )
        target_unit.source = unit.source
        if unit.istranslated() or not bool(unit.source):
            target_unit.target = unit.target
        else:
            target_unit.target = unit.source
        return target_unit

    def convert_store(self):
        """
        Convert the entire PO file to XML format.
        
        Process:
        1. Iterate through all PO units
        2. Skip empty source strings
        3. Update existing XML units if found
        4. Create new XML units if needed
        5. Apply translations or fall back to source
        """
        for unit in self.source_store.units:
            key = unit.source
            if not key:
                continue
            target_unit = self.target_store.findid(key)
            if target_unit is None:
                target_unit = self.convert_unit(unit)
                self.target_store.addunit(target_unit)
            else:
                target_unit.target = unit.target

    def run(self):
        """
        Execute the conversion process.
        
        Process:
        1. Convert the PO store to XML
        2. Check if result is empty
        3. Serialize output if not empty
        
        Returns:
            1 if conversion successful and not empty
            0 if resulting XML file would be empty
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
    indent=2,
):
    """
    Convenience function to run the converter.
    
    Creates a converter instance and runs it with the given parameters.
    
    Args:
        inputfile: Source PO file
        outputfile: Target XML file
        templatefile: Template XML file (optional)
        root: Root element name
        value: Value element name
        key: Key attribute name
        ns: XML namespace
        indent: Indentation spaces
        
    Returns:
        Result of conversion (0 or 1)
    """
    return po2flatxml(
        inputfile, outputfile, templatefile, root, value, key, ns, indent
    ).run()


# Supported format pairs for conversion
formats = {
    ("po"): ("xml", run_converter),
    ("po", "xml"): ("xml", run_converter),
}


def main(argv=None):
    """
    Command-line interface for the converter.
    
    Provides options to customize:
    - Root element name (-r, --root)
    - Value element name (-v, --value)
    - Key attribute name (-k, --key)
    - XML namespace (-n, --namespace)
    - Indentation width (-w, --indent)
    
    Supports template-based conversion for updating
    existing XML files with translations.
    
    Example:
        po2flatxml -r root -v string -k id input.po output.xml
    """
    parser = convert.ConvertOptionParser(
        formats, usetemplates=True, description=__doc__
    )

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
    parser.add_option(
        "-w",
        "--indent",
        action="store",
        dest="indent",
        type="int",
        default=2,
        help="indent width in spaces, 0 for no indent (default: 2)",
    )

    parser.passthrough.append("root")
    parser.passthrough.append("value")
    parser.passthrough.append("key")
    parser.passthrough.append("ns")
    parser.passthrough.append("indent")

    parser.run(argv)


if __name__ == "__main__":
    main()
