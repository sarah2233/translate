#
# Copyright 2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
Factory methods for converting between different localization file formats.

This module provides a flexible and extensible system for converting between
different file formats used in localization. It implements a factory pattern
to dynamically handle various file format conversions.

Key Features:
1. Dynamic converter registration and discovery
2. Support for template-based conversions
3. Automatic file format detection
4. Flexible output format selection
5. Temporary file handling for conversion process

The conversion system supports:
- Direct format conversions (e.g., PO → XLIFF)
- Template-based conversions (e.g., using original files as templates)
- Multiple output formats for a single input format
- Custom conversion options

Usage:
    converter = get_converter('po', 'xliff')
    converter(input_file, output_file, template_file, **options)
"""

import os

# Global registry of available converters
converters = {}

class UnknownExtensionError(Exception):
    """
    Raised when unable to determine the file extension/format.
    
    This typically happens when:
    1. File has no extension
    2. File name is not accessible
    3. File is not in a recognized format
    """
    def __init__(self, afile):
        self.file = afile

    def __str__(self):
        return f"Unable to find extension for file: {self.file}"


class UnsupportedConversionError(Exception):
    """
    Raised when requested conversion is not supported.
    
    This can happen when:
    1. No converter exists for the input format
    2. No converter can produce the requested output format
    3. Template format is not supported for the conversion
    
    Args:
        in_ext: Input file extension/format
        out_ext: Desired output format
        templ_ext: Template format (if used)
    """
    def __init__(self, in_ext=None, out_ext=None, templ_ext=None):
        self.in_ext = in_ext
        self.out_ext = out_ext
        self.templ_ext = templ_ext

    def __str__(self):
        msg = f"Unsupported conversion from {self.in_ext} to {self.out_ext}"
        if self.templ_ext:
            msg += f" with template {self.templ_ext}"
        return msg


def get_extension(filename):
    """
    Extract the file extension from a filename.
    
    Handles various file naming patterns:
    - Standard extensions (file.ext)
    - Multiple extensions (file.tar.gz)
    - No extension (file)
    
    Args:
        filename: Name or path of file
        
    Returns:
        Extension without leading dot, or None if no extension
    """
    path, fname = os.path.split(filename)
    ext = fname.split(os.extsep)[-1]
    if ext == fname:
        return None
    return ext


def get_converter(in_ext, out_ext=None, templ_ext=None):
    """
    Find an appropriate converter for the given formats.
    
    Search process:
    1. Check for template-specific converter if template used
    2. Look for direct converter matching input format
    3. Try generic converter for input format
    4. Select first available output format if none specified
    
    Args:
        in_ext: Input file format/extension
        out_ext: Desired output format (optional)
        templ_ext: Template format (optional)
        
    Returns:
        Converter function that can perform the requested conversion
        
    Raises:
        UnsupportedConversionError: If no suitable converter found
    """
    convert_candidates = None
    if templ_ext:
        if (in_ext, templ_ext) in converters:
            convert_candidates = converters[in_ext, templ_ext]
        else:
            raise UnsupportedConversionError(in_ext, out_ext, templ_ext)
    elif in_ext in converters:
        convert_candidates = converters[in_ext]
    elif (in_ext,) in converters:
        convert_candidates = converters[in_ext,]
    else:
        raise UnsupportedConversionError(in_ext, out_ext)

    convert_fn = None
    if not out_ext:
        out_ext, convert_fn = convert_candidates[0]
    else:
        for ext, func in convert_candidates:
            if ext == out_ext:
                convert_fn = func
                break

    if not convert_fn:
        raise UnsupportedConversionError(in_ext, out_ext, templ_ext)
    return convert_fn


def get_output_extensions(ext):
    """
    Find all possible output formats for a given input format.
    
    Searches the converter registry to find all registered converters
    that can handle the input format, collecting their possible
    output formats.
    
    Args:
        ext: Input file extension/format
        
    Returns:
        List of possible output extensions/formats
    """
    out_exts = []
    for key, converter in converters.items():
        in_ext = key
        if isinstance(key, tuple):
            in_ext = key[0]
        if in_ext == ext:
            for out_ext, convert_fn in converter:
                out_exts.append(out_ext)
    return out_exts


def convert(inputfile, template=None, options=None, convert_options=None):
    """
    Convert a file from one format to another.
    
    Main conversion workflow:
    1. Determine input/output/template formats
    2. Find appropriate converter
    3. Create temporary output file
    4. Perform conversion
    5. Return output file and format
    
    Format Detection:
    1. Check options dictionary
    2. Look for file extensions
    3. Use first available output format if not specified
    
    Args:
        inputfile: File to convert
        template: Optional template file
        options: Conversion configuration options:
            - in_ext: Input format
            - out_ext: Output format
            - templ_ext: Template format
            - in_fname: Input filename (for format detection)
            - templ_fname: Template filename
        convert_options: Options passed to converter
        
    Returns:
        Tuple (output_file, output_extension)
        
    Note:
        The caller is responsible for cleaning up the temporary output file
    """
    in_ext, out_ext, templ_ext = None, None, None

    # Get extensions from options
    if options is None:
        options = {}
    else:
        if "in_ext" in options:
            in_ext = options["in_ext"]
        if "out_ext" in options:
            out_ext = options["out_ext"]
        if template and "templ_ext" in options:
            templ_ext = options["templ_ext"]

        # If we still do not have extensions, try and get it from the *_fname options
        if not in_ext and "in_fname" in options:
            in_ext = get_extension(options["in_fname"])
        if template and not templ_ext and "templ_fname" in options:
            templ_ext = get_extension(options["templ_fname"])

    # If we still do not have extensions, get it from the file names
    if not in_ext and hasattr(inputfile, "name"):
        in_ext = get_extension(inputfile.name)
    if template and not templ_ext and hasattr(template, "name"):
        templ_ext = get_extension(template.name)

    if not in_ext:
        raise UnknownExtensionError(inputfile)
    if template and not templ_ext:
        raise UnknownExtensionError(template)

    out_ext_candidates = get_output_extensions(in_ext)
    if not out_ext_candidates:
        # No converters registered for the in_ext we have
        raise UnsupportedConversionError(in_ext=in_ext, templ_ext=templ_ext)
    if out_ext and out_ext not in out_ext_candidates:
        # If out_ext has a value at this point, it was given in options, so
        # we just take a second to make sure that the conversion is supported.
        raise UnsupportedConversionError(in_ext, out_ext, templ_ext)

    if not out_ext and templ_ext in out_ext_candidates:
        # If we're using a template, chances are (pretty damn) good that the
        # output file will be of the same type
        out_ext = templ_ext
    else:
        # As a last resort, we'll just use the first possible output format
        out_ext = out_ext_candidates[0]

    # XXX: We are abusing tempfile.mkstemp() below: we are only using it to
    #      obtain a temporary file name to use the normal open() with. This is
    #      done because a tempfile.NamedTemporaryFile simply gave too many
    #      issues when being closed (and deleted) by the rest of the toolkit
    #      (eg. TranslationStore.savefile()). Therefore none of mkstemp()'s
    #      security features are being utilised.
    import tempfile

    tempfd, tempfname = tempfile.mkstemp(
        prefix="ttk_convert", suffix=os.extsep + out_ext
    )
    os.close(tempfd)

    if convert_options is None:
        convert_options = {}
    with open(tempfname, "w") as output_file:
        get_converter(in_ext, out_ext, templ_ext)(
            inputfile, output_file, template, **convert_options
        )
    return output_file, out_ext
