"""This module generates the PDF report output."""

import os
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    Paragraph,
    Preformatted,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import toLength


FILENAME = "compare.pdf"


STYLES = getSampleStyleSheet()
STYLES["Normal"].fontSize = toLength("12 pt")
STYLES["Heading1"].spaceBefore = toLength("20 pt")
STYLES["Code"].fontSize = toLength("12 pt")
STYLES["Code"].leading = toLength("12 pt")
STYLES["Code"].leftIndent = 0


def generate(files, tags, diff):
    """Top level function to generate the entire report output."""
    doc = SimpleDocTemplate(FILENAME)
    story = []
    story.extend(summary())
    story.extend(differences(files, tags, diff))
    doc.build(story)


def tag_name(tag):
    """Formats a tag name and all additional members."""
    items = [tag.name]
    for member in tag.members:
        # Named members are separated by a period.
        if isinstance(member, str):
            items.append(".")
            items.append(member)

        # Array indices are represented as a tuple of integers,
        # and need to be reversed to match the order presented
        # in RSLogix.
        else:
            indices = ",".join(str(i) for i in reversed(member))
            items.append(f"[{indices}]")

    return Preformatted("".join(items), STYLES["Code"])


def heading(title):
    """Creates a section heading."""
    return Paragraph(title, STYLES["Heading1"])


def summary():
    """Generates the Summary section."""
    flowables = [
        heading("Summary"),
        Paragraph(
            """
            This report identifies differences in timer and counter
            preset(.PRE) values. All content other than .PRE values is
            excluded from comparison.
            """,
            STYLES["Normal"],
        ),
    ]

    return flowables


def differences(files, tags, diff):
    """Creates the Differences section."""
    flowables = [heading("Differences")]
    if diff:
        flowables.append(tag_value_table(files, tags, diff))
    else:
        flowables.append(Paragraph("No differences found.", STYLES["Normal"]))

    return flowables


def tag_value_table(files, tags, diff):
    """Generates a table listing the values of altered tags."""
    rows = []

    # Header row.
    header = [Preformatted(os.path.basename(path), STYLES["Normal"]) for path in files]
    header.insert(0, None)  # First column is empty.
    rows.append(header)

    scopes = {t.scope for t in diff}

    if "Controller" in scopes:
        rows.extend(tag_value_rows("Controller", files, tags, diff))
        scopes.remove("Controller")

    for prg in sorted(scopes):
        rows.extend(tag_value_rows(prg, files, tags, diff))

    return Table(rows)


def tag_value_rows(scope, files, tags, diff):
    """Generates table rows listing tag values in single scope."""
    rows = []

    # First row lists the scope name.
    rows.append([Preformatted(scope, STYLES["Heading3"]), None, None])

    scope_tags = [t for t in sorted(diff) if t.scope == scope]
    for tag in scope_tags:
        tag_row = [tag_name(tag)]
        tag_row.extend([tags[f][tag] for f in files])
        rows.append(tag_row)

    return rows
