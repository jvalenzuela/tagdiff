"""This module generates the PDF report output."""

from reportlab.platypus import (
    ListFlowable,
    ListItem,
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


def generate(l5x, hashes, tags, diff):
    """Top level function to generate the entire report output."""
    doc = SimpleDocTemplate(FILENAME)
    story = []
    story.extend(summary(l5x, hashes))
    story.extend(differences(diff))
    story.extend(exclusions(l5x, tags))
    doc.build(story)


def tag_name(tag):
    """Formats a tag name and all additional members."""
    items = [tag.name]
    for member in tag.members:
        # Named members are separated by a period.
        if isinstance(member, str):
            items.append(".")
            items.append(member)

        # Array indices are represented as a tuple of integers.
        else:
            indices = ",".join(str(i) for i in member)
            items.append(f"[{indices}]")

    return Preformatted("".join(items), STYLES["Code"])


def heading(title):
    """Creates a section heading."""
    return Paragraph(title, STYLES["Heading1"])


def unordered_list(items, **kwargs):
    """Genertes an unordered list flowable."""
    return ListFlowable(
        items,
        bulletType="bullet",
        start="",
        leftIndent=0,
        **kwargs,
    )


def summary(l5x, hashes):
    """Generates the Summary section."""
    flowables = [
        heading("Summary"),
        Paragraph(
            """
            This report identifies differences structure tag .PRE
            member values, such as in timers and counters, between the two
            files listed below. All content other than .PRE values is
            excluded from comparison; add-on instruction local tags,
            even those with .PRE members, are also excluded.
            """,
            STYLES["Normal"],
        ),
    ]

    # Add file table.
    rows = [[Preformatted(s, STYLES["Heading3"]) for s in ["File Name", "MD5"]]]
    for f in l5x:
        rows.append([Preformatted(s, STYLES["Normal"]) for s in [f, hashes[f]]])
    flowables.append(Table(rows, spaceBefore=toLength("10 pt")))

    return flowables


def differences(diff):
    """Creates the Differences section."""
    flowables = [heading("Differences")]
    if diff:
        flowables.append(list_all_tags(diff))
    else:
        flowables.append(Paragraph("No differences found.", STYLES["Normal"]))

    return flowables


def exclusions(l5x, tags):
    """Creates the Exclusions section."""
    flowables = []

    # Only consider tags that exist in both projects as tags unique to
    # a single project are inherently excluded.
    excl_tags = tags[l5x[0]].no_data.intersection(tags[l5x[1]].no_data)

    if excl_tags:
        flowables.append(heading("Additional Exclusions"))
        flowables.append(
            Paragraph(
                """
                The tags listed below were not compared due to the lack of
                structured value information in the L5X file.
                """,
                STYLES["Normal"],
            )
        )
        flowables.append(list_all_tags(excl_tags))

    return flowables


def list_all_tags(tags):
    """Generates a list of tags organized by scope."""
    scopes = {t.scope for t in tags}
    items = []

    # List Controller tags first, if any.
    if "Controller" in scopes:
        items.extend(list_scope_tags("Controller", tags))
        scopes.remove("Controller")

    # Add program tags.
    for prg in sorted(scopes):
        items.extend(list_scope_tags(prg, tags))

    return unordered_list(items)


def list_scope_tags(scope, tags):
    """Lists tags from a single scope.

    Returns a list of flowables to be included in a ListFlowable.
    """
    items = []

    # Add a top-level item listing the scope name.
    items.append(
        ListItem(Paragraph(scope, STYLES["Heading3"]), spaceBefore=toLength("5 pt"))
    )

    # Add a nested list containing the tags in this scope.
    scope_tags = [tag_name(t) for t in sorted(tags) if t.scope == scope]
    items.append(unordered_list(scope_tags))

    return items
