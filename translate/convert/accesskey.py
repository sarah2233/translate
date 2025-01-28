"""
Functions for handling access keys in user interface strings.

This module provides tools for working with access keys (keyboard shortcuts) in
UI strings. Access keys are typically denoted by an ampersand (&) before the
shortcut letter, like "&File" for 'F' as the access key.

Key Features:
1. Extraction of access keys from strings
2. Combination of labels and access keys
3. Smart handling of XML entities
4. Case-sensitive and case-insensitive matching
5. Support for different access key markers
6. Mixing of separately defined labels and access keys

Common scenarios:
- Menu items: "&File", "&Edit", "&View"
- Buttons: "&Save", "&Cancel"
- Dialog labels: "Replace &with:"

Note: Access keys are crucial for keyboard navigation in applications
and must be preserved during translation while remaining meaningful
in the target language.
"""

from translate.storage.placeables.general import XMLEntityPlaceable

# Default marker for access keys in UI strings
DEFAULT_ACCESSKEY_MARKER = "&"


class UnitMixer:
    """
    Combines separately stored labels and access keys into single units.
    
    In some UI formats, labels and their access keys are stored separately.
    This class helps combine them into single strings with embedded access keys.
    
    Example:
        label: "Save As"
        accesskey: "A"
        combined: "Save &As"
    
    Args:
        labelsuffixes: List of suffixes that identify label strings
        accesskeysuffixes: List of suffixes that identify access key strings
    """

    def __init__(self, labelsuffixes, accesskeysuffixes):
        """
        Initialize with lists of suffixes for labels and access keys.
        
        Args:
            labelsuffixes: e.g., ['.label', '.title']
            accesskeysuffixes: e.g., ['.accesskey', '.accessKey']
        """
        self.labelsuffixes = labelsuffixes
        self.accesskeysuffixes = accesskeysuffixes

    def match_entities(self, index):
        """
        Find pairs of entities that represent label + access key combinations.
        
        Searches through the index for entities that have matching pairs:
        - One with a label suffix
        - One with an access key suffix
        
        Args:
            index: Dictionary of entity names to search
            
        Returns:
            Dictionary of matched entities
        """
        #: Entities which have a .label/.title and .accesskey combined
        mixedentities = {}
        for entity in index:
            for labelsuffix in self.labelsuffixes:
                if entity.endswith(labelsuffix):
                    entitybase = entity[: entity.rfind(labelsuffix)]
                    # see if there is a matching accesskey in this line,
                    # making this a mixed entity
                    for akeytype in self.accesskeysuffixes:
                        if (entitybase + akeytype) in index:
                            # add both versions to the list of mixed entities
                            mixedentities[entity] = {}
                            mixedentities[entitybase + akeytype] = {}
                    # check if this could be a mixed entity (labelsuffix and
                    # ".accesskey")
        return mixedentities

    @staticmethod
    def mix_units(label_unit, accesskey_unit, target_unit):
        """
        Combine label and access key translation units into one.
        
        Merges:
        - Source text and access key
        - Location information
        - Comments and notes
        - Message context
        
        Args:
            label_unit: Unit containing the label text
            accesskey_unit: Unit containing the access key
            target_unit: Unit to store the combined result
            
        Returns:
            Combined unit or None if combination failed
        """
        target_unit.addlocations(label_unit.getlocations())
        target_unit.addlocations(accesskey_unit.getlocations())
        target_unit.msgidcomment = (
            target_unit._extract_msgidcomments() + label_unit._extract_msgidcomments()
        )
        target_unit.msgidcomment = (
            target_unit._extract_msgidcomments()
            + accesskey_unit._extract_msgidcomments()
        )
        target_unit.addnote(label_unit.getnotes("developer"), "developer")
        target_unit.addnote(accesskey_unit.getnotes("developer"), "developer")
        target_unit.addnote(label_unit.getnotes("translator"), "translator")
        target_unit.addnote(accesskey_unit.getnotes("translator"), "translator")
        label = label_unit.source
        accesskey = accesskey_unit.source
        label = combine(label, accesskey)
        if label is None:
            return None
        target_unit.source = label
        target_unit.target = ""
        return target_unit

    def find_mixed_pair(self, mixedentities, store, unit):
        """
        Find the matching label/accesskey pair for a given unit.
        
        Search process:
        1. Check if unit is part of a mixed entity
        2. Find the corresponding label or access key
        3. Verify both parts exist in the store
        
        Args:
            mixedentities: Dict of known mixed entities
            store: Store containing all units
            unit: Unit to find pair for
            
        Returns:
            Tuple (label_entity, accesskey_entity) or (None, None)
        """
        entity = unit.getid()
        if entity not in mixedentities:
            return None, None

        # depending on what we come across first, work out the label
        # and the accesskey
        labelentity, accesskeyentity = None, None
        for labelsuffix in self.labelsuffixes:
            if entity.endswith(labelsuffix):
                entitybase = entity[: entity.rfind(labelsuffix)]
                for akeytype in self.accesskeysuffixes:
                    if (entitybase + akeytype) in store.id_index:
                        labelentity = entity
                        accesskeyentity = (
                            labelentity[: labelentity.rfind(labelsuffix)] + akeytype
                        )
                        break
        if labelentity is None:
            for akeytype in self.accesskeysuffixes:
                if entity.endswith(akeytype):
                    accesskeyentity = entity
                    for labelsuffix in self.labelsuffixes:
                        labelentity = (
                            accesskeyentity[: accesskeyentity.rfind(akeytype)]
                            + labelsuffix
                        )
                        if labelentity in store.id_index:
                            break
                    else:
                        labelentity = None
                        accesskeyentity = None
        return (labelentity, accesskeyentity)


def extract(string, accesskey_marker=DEFAULT_ACCESSKEY_MARKER):
    """
    Split a combined string into label and access key.
    
    Process:
    1. Find the access key marker
    2. Extract the following character as access key
    3. Remove marker and key from label
    4. Handle special cases:
       - XML entities (e.g., &amp;)
       - End of string
       - Invalid access keys (space)
    
    Args:
        string: Combined string (e.g., "&File")
        accesskey_marker: Character marking the access key
        
    Returns:
        Tuple (label, accesskey)
        Example: ("File", "F") from "&File"
    """
    assert isinstance(string, str)
    assert isinstance(accesskey_marker, str)
    assert len(accesskey_marker) == 1
    if not string:
        return "", ""
    accesskey = ""
    label = string
    marker_pos = 0
    while marker_pos >= 0:
        marker_pos = string.find(accesskey_marker, marker_pos)
        if marker_pos != -1:
            marker_pos += 1
            if marker_pos == len(string):
                break
            if accesskey_marker == "&" and XMLEntityPlaceable.regex.match(
                string[marker_pos - 1 :]
            ):
                continue
            # FIXME This is weak filtering, we should have a richer set of
            # invalid accesskeys, not just space.
            if string[marker_pos] != " ":
                label = string[: marker_pos - 1] + string[marker_pos:]
                accesskey = string[marker_pos]
    return label, accesskey


def combine(label, accesskey, accesskey_marker=DEFAULT_ACCESSKEY_MARKER):
    """
    Create a combined string from separate label and access key.
    
    Process:
    1. Find the access key character in the label
    2. Try exact case match first
    3. Try alternate case if exact not found
    4. Insert marker before the matched character
    5. Handle special cases:
       - XML entities
       - Missing matches
       - Empty strings
    
    Args:
        label: Text without access key (e.g., "File")
        accesskey: Single character access key (e.g., "F")
        accesskey_marker: Character to mark the access key
        
    Returns:
        Combined string or None if combination impossible
        Example: "&File" from ("File", "F")
    """
    assert isinstance(label, str)
    assert isinstance(accesskey, str)

    if len(accesskey) == 0:
        return None

    searchpos = 0
    accesskeypos = -1
    in_entity = False
    accesskeyaltcasepos = -1

    accesskey_alt_case = accesskey.lower() if accesskey.isupper() else accesskey.upper()

    while (accesskeypos < 0) and searchpos < len(label):
        searchchar = label[searchpos]
        if searchchar == "&":
            in_entity = True
        elif searchchar in {";", " "}:
            in_entity = False
        if not in_entity:
            if searchchar == accesskey:  # Prefer supplied case
                accesskeypos = searchpos
            elif searchchar == accesskey_alt_case:  # Other case otherwise
                if accesskeyaltcasepos == -1:
                    # only want to remember first altcasepos
                    accesskeyaltcasepos = searchpos
                    # note: we keep on looping through in hope
                    # of exact match
        searchpos += 1

    # if we didn't find an exact case match, use an alternate one if available
    if accesskeypos == -1:
        accesskeypos = accesskeyaltcasepos

    # now we want to handle whatever we found...
    if accesskeypos >= 0:
        return label[:accesskeypos] + accesskey_marker + label[accesskeypos:]
    # can't currently mix accesskey if it's not in label
    return None
