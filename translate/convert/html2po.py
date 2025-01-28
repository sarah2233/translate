#
# Copyright 2004-2006 Zuza Software Foundation
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
#

"""
Convert HTML files to Gettext PO localization files.

This module provides tools for extracting translatable strings from HTML files
and converting them into the PO (Portable Object) format used by Gettext.

Key Features:
1. Extracts text from HTML tags and attributes
2. Preserves HTML comments as translator notes (optional)
3. Handles duplicate strings with configurable strategies
4. Supports single-file and multi-file processing
5. Processes HTML, HTM, and XHTML formats
6. Supports recursive directory processing

Common Use Cases:
- Localizing static HTML websites
- Converting HTML documentation for translation
- Extracting strings from web templates
- Processing multiple HTML files into a single PO file

For detailed usage instructions and examples, see:
http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/html2po.html
"""

from translate.convert import convert
from translate.storage import html, po


class html2po:
    """
    Converter class for transforming HTML files into PO format.
    
    This class handles the core conversion logic, including:
    - Parsing HTML files
    - Extracting translatable strings
    - Creating PO translation units
    - Managing metadata and comments
    """

    def convertfile(
        self,
        inputfile,
        filename,
        duplicatestyle="msgctxt",
        keepcomments=False,
    ):
        """
        Convert a single HTML file to PO format.
        
        Args:
            inputfile: HTML file to convert
            filename: Name of the input file (for reference)
            duplicatestyle: How to handle duplicate strings:
                - 'msgctxt': Use message context
                - 'merge': Combine units
                - 'keep': Keep duplicates
            keepcomments: Whether to preserve HTML comments
            
        Returns:
            A pofile object containing the extracted strings
        """
        thetargetfile = po.pofile()
        self.convertfile_inner(inputfile, thetargetfile, keepcomments)
        thetargetfile.removeduplicates(duplicatestyle)
        return thetargetfile

    @staticmethod
    def convertfile_inner(inputfile, outputstore, keepcomments):
        """
        Extract translation units from HTML and add to PO store.
        
        Process:
        1. Parse HTML using htmlfile parser
        2. Extract translatable units
        3. Create PO units with:
           - Source text
           - Locations (HTML elements/attributes)
           - Developer notes (from HTML comments)
        
        Args:
            inputfile: HTML file to process
            outputstore: PO store to add units to
            keepcomments: Whether to preserve HTML comments
        """
        htmlparser = html.htmlfile(inputfile=inputfile)
        for htmlunit in htmlparser.units:
            thepo = outputstore.addsourceunit(htmlunit.source)
            thepo.addlocations(htmlunit.getlocations())
            if keepcomments:
                thepo.addnote(htmlunit.getnotes(), "developer")


def converthtml(
    inputfile,
    outputfile,
    templates,
    pot=False,
    duplicatestyle="msgctxt",
    keepcomments=False,
):
    """
    Convert HTML to PO format using standard input/output.
    
    This is a convenience function that:
    1. Creates an html2po converter
    2. Processes the input file
    3. Writes output to the specified file
    
    Args:
        inputfile: Input HTML file
        outputfile: Output PO file
        templates: Template files (unused)
        pot: Whether to create POT file
        duplicatestyle: How to handle duplicates
        keepcomments: Whether to keep HTML comments
        
    Returns:
        1 on success (required by translate toolkit)
    """
    convertor = html2po()
    outputstore = convertor.convertfile(
        inputfile,
        getattr(inputfile, "name", "unknown"),
        duplicatestyle=duplicatestyle,
        keepcomments=keepcomments,
    )
    outputstore.serialize(outputfile)
    return 1


class Html2POOptionParser(convert.ConvertOptionParser):
    """
    Command line parser for HTML to PO conversion.
    
    Features:
    1. Handles multiple input formats (html, htm, xhtml)
    2. Supports directory recursion
    3. Configurable duplicate handling
    4. Optional comment preservation
    5. Single or multiple output file modes
    
    Command line options:
    --keepcomments: Preserve HTML comments
    --duplicates: Handle duplicate strings
    --multifile: Control output file creation
    """

    def __init__(self):
        """
        Initialize the parser with supported formats and options.
        
        Supported formats:
        - .html → .po
        - .htm → .po
        - .xhtml → .po
        
        Options:
        - Comment preservation
        - Duplicate handling
        - Multi-file processing
        """
        formats = {
            "html": ("po", self.convert),
            "htm": ("po", self.convert),
            "xhtml": ("po", self.convert),
            None: ("po", self.convert),
        }
        super().__init__(formats, usetemplates=False, usepots=True, description=__doc__)
        self.add_option(
            "--keepcomments",
            dest="keepcomments",
            default=False,
            action="store_true",
            help="preserve html comments as translation notes in the output",
        )
        self.passthrough.append("keepcomments")
        self.add_duplicates_option()
        self.add_multifile_option()
        self.passthrough.append("pot")

    def convert(
        self,
        inputfile,
        outputfile,
        templates,
        pot=False,
        duplicatestyle="msgctxt",
        multifilestyle="single",
        keepcomments=False,
    ):
        """
        Convert a single HTML file based on command line options.
        
        Handles two modes:
        1. Single file: Direct conversion to output
        2. Multi-file: Add to combined output store
        
        Args:
            inputfile: HTML file to convert
            outputfile: Where to write PO output
            templates: Template files (unused)
            pot: Create POT format
            duplicatestyle: Duplicate handling method
            multifilestyle: Output file organization
            keepcomments: Preserve HTML comments
        """
        convertor = html2po()
        if hasattr(self, "outputstore"):
            convertor.convertfile_inner(inputfile, self.outputstore, keepcomments)
        else:
            outputstore = convertor.convertfile(
                inputfile,
                getattr(inputfile, "name", "unknown"),
                duplicatestyle=duplicatestyle,
                keepcomments=keepcomments,
            )
            outputstore.serialize(outputfile)
        return 1

    def recursiveprocess(self, options):
        """
        Process HTML files in directory trees.
        
        Modes:
        1. onefile: Combine all HTML into single PO
        2. individual: Create PO file for each HTML
        
        Args:
            options: Command line options
        """
        if options.multifilestyle == "onefile":
            self.outputstore = po.pofile()
            super().recursiveprocess(options)
            if not self.outputstore.isempty():
                self.outputstore.removeduplicates(options.duplicatestyle)
                outputfile = super().openoutputfile(options, options.output)
                self.outputstore.serialize(outputfile)
                if options.output:
                    outputfile.close()
        else:
            super().recursiveprocess(options)

    def isrecursive(self, fileoption, filepurpose="input"):
        """
        Check if file processing should be recursive.
        
        Special handling for single-output mode where
        output is always treated as recursive.
        
        Args:
            fileoption: File option to check
            filepurpose: 'input' or 'output'
        """
        if hasattr(self, "outputstore") and filepurpose == "output":
            return True
        return super().isrecursive(fileoption, filepurpose=filepurpose)

    def checkoutputsubdir(self, options, subdir):
        """
        Manage output directory creation.
        
        Skip directory creation in single-file mode
        since all output goes to one file.
        
        Args:
            options: Command line options
            subdir: Subdirectory to check
        """
        if hasattr(self, "outputstore"):
            return
        super().checkoutputsubdir(options, subdir)

    def openoutputfile(self, options, fulloutputpath):
        """
        Open output file for writing.
        
        Skip in single-file mode since output is
        handled by the combined store.
        
        Args:
            options: Command line options
            fulloutputpath: Path to output file
        """
        if hasattr(self, "outputstore"):
            return None
        return super().openoutputfile(options, fulloutputpath)


def main(argv=None):
    parser = Html2POOptionParser()
    parser.run(argv)


if __name__ == "__main__":
    main()
