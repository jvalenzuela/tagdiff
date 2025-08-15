"""This module handles extracting tag data from the source L5X files."""

import collections
import hashlib
import xml.sax


def parse(filename):
    """Extracts tag values from a single L5X file."""
    handler = PreExtractor()
    xml.sax.parse(filename, handler)
    return handler


def compute_md5(filename):
    """Calculates the MD5 of a file."""
    with open(filename, "rb") as f:
        digest = hashlib.file_digest(f, "md5")
    return digest.hexdigest()


def compare(a, b):
    """Compares tag values."""
    diffs = set()
    for key in a:
        try:
            if a[key] != b[key]:
                diffs.add(key)

        # Ignore tags that don't exist in both files.
        except KeyError:
            continue

    return diffs


# Data type containing information to fully identify a tag member.
Tag = collections.namedtuple(
    "Tag",
    [
        "scope",  # Controller or program name.
        "name",  # Top-level name of the parent tag.
        "members",  # Tuple of structure member names or array indices.
    ],
)


class PreExtractor(xml.sax.ContentHandler):
    """SAX content handler that captures values from .PRE tags."""

    # Disable non-snake_case naming because method names are derived from
    # XML element names.
    # pylint: disable=invalid-name

    # Disable public method limit because the public methods are defined
    # by the ContentHandler interface.
    # pylint: disable=too-many-public-methods

    def __init__(self):
        super().__init__()

        # When skipping elements this will be a list of element names
        # representing the XML path relative to the element when skipping
        # was started. Elements will be ignored until this list is emptied.
        self.ignored_elements = None

        # Items that will be stored in a Tag named tuple
        self.scope = None
        self.tag_name = None
        self.tag_members = None

        self.tag_has_decorated_data = False
        self.is_alias = False
        self.raw_tag_data = None
        self.values = {}  # Tag values keyed by Tag tuple.

        # Raw tag data for tags without a decorated data element,
        # keyed by Tag tuple.
        self.no_data = {}

    def startElement(self, name, attrs):
        try:
            self.ignored_elements.append(name)

        # Dispatch normally if not ignoring elements.
        except AttributeError:
            method_name = f"start_{name}"
            try:
                method = getattr(self, method_name)
            except AttributeError:
                return
            method(attrs)

    def endElement(self, name):
        try:
            self.ignored_elements.pop()

        # Dispatch normally if not ignoring elements(AttributeError) or
        # leaving the element where ignoring was started(IndexError).
        except (AttributeError, IndexError):
            self.ignored_elements = None
            method_name = f"end_{name}"
            try:
                method = getattr(self, method_name)
            except AttributeError:
                return
            method()

    def ignore_children(self):
        """Enables skipping all children of the current element."""
        if self.ignored_elements is None:
            self.ignored_elements = []
        else:
            raise AssertionError("Child element masking cannot be nested.")

    def start_AddOnInstructionDefinitions(self, _attrs):
        """Handler for the start of the AddOnInstructionDefinitions element.

        All content within AOI definitions is ignored because their local
        tag definitions may contain DataValueMember elements, which would
        otherwise be confused for an actual tag instance.
        """
        self.ignore_children()

    def start_Modules(self, _attrs):
        """Handler for the start of the Modules element.

        Module definitions need to be explicitly ignored because they
        may contain DataValueMember elements.
        """
        self.ignore_children()

    def start_Controller(self, _attrs):
        """Handler for the start of the Controller element."""
        self.scope = "Controller"

    def start_Program(self, attrs):
        """Handler for the start of a Program element."""
        self.scope = attrs.getValue("Name")

    def start_Tag(self, attrs):
        """Handler for the start of a Tag element."""
        if attrs.getValue("TagType") == "Alias":
            self.is_alias = True
        else:
            self.is_alias = False

        if self.is_alias:
            self.ignore_children()
        else:
            self.tag_name = attrs.getValue("Name")
            self.tag_members = []
            self.tag_has_decorated_data = False

    def end_Tag(self):
        """Handler for the closing of a Tag element."""
        if not self.is_alias and not self.tag_has_decorated_data:
            tag = Tag(self.scope, self.tag_name, ())
            data = bytes.fromhex("".join(self.raw_tag_data))
            self.no_data[tag] = data

        self.raw_tag_data = None

    def start_Data(self, attrs):
        """Handler for the start of a Data element.

        Captures that the current tag includes a decorated data element.
        """
        try:
            if attrs.getValue("Format") == "Decorated":
                self.tag_has_decorated_data = True

        except KeyError:
            self.raw_tag_data = []

    def characters(self, content):
        """Handler for element content."""
        # Capture raw tag data from raw Data elements.
        try:
            self.raw_tag_data.append(content)

        # Ignore content when not collecting raw tag data.
        except AttributeError:
            pass

    def start_Element(self, attrs):
        """Handler for the start of an Element element.

        These elements contain an array index, which is converted to
        a tuple of integers for correct sorting.
        """
        raw = attrs.getValue("Index")
        indices = raw[1:-1].split(",")  # Split excludes surrounding brackets.
        self.tag_members.append(tuple(int(i) for i in indices))

    def end_Element(self):
        """Handler for the end of an Element element."""
        self.end_named_member()

    def start_StructureMember(self, attrs):
        """Handler for the start of a StructureMember element."""
        self.append_named_member(attrs)

    def end_StructureMember(self):
        """Handler for the end of a StructureMember element."""
        self.end_named_member()

    def start_ArrayMember(self, attrs):
        """Handler for the start of an ArrayMember element."""
        self.append_named_member(attrs)

    def end_ArrayMember(self):
        """Handler for the end of an ArrayMember element."""
        self.end_named_member()

    def start_DataValueMember(self, attrs):
        """Handler for the start of a DataValueMember element."""
        self.append_named_member(attrs)

        # Store this tag if it's a .PRE structure member.
        if attrs.getValue("Name") == "PRE":
            tag = Tag(self.scope, self.tag_name, tuple(self.tag_members))
            self.values[tag] = self.get_value(attrs)

    def get_value(self, attrs):
        """Extracts a tag's integer value."""
        radix = attrs.getValue("Radix")
        if radix != "Decimal":
            raise ValueError(f"Unsupported radix: {radix}")
        raw = attrs.getValue("Value")
        return int(raw)

    def end_DataValueMember(self):
        """Handler for the end of a DataValueMember."""
        self.end_named_member()

    def append_named_member(self, attrs):
        """Adds a member name to the current tag."""
        name = attrs.getValue("Name")
        self.tag_members.append(name)

    def end_named_member(self):
        """Removes a member name from the current tag."""
        self.tag_members.pop()
