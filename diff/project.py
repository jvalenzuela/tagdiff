"""This module handles extracting tag data from the source L5K files."""

import collections
import copy
import itertools

import l5k


# Reference to a single member of a tag structure member, e.g., .PRE.
Tag = collections.namedtuple(
    "Tag",
    [
        "scope",  # Controller or program name.
        "name",  # Top-level name of the parent tag.
        "members",  # Tuple of structure member names or array indices.
    ],
)


def parse(filename):
    """Loads an L5K file to get tag values to be compared."""
    ctl = l5k.parse(filename)
    types = find_target_types(ctl)

    # Find tags of the target types.
    tags = find_target_tags("Controller", ctl.tags, types)
    for prg in ctl.programs:
        tags.update(find_target_tags(prg, ctl.programs[prg].tags, types))

    # Get the values for selected tags.
    values = {}
    for tag in tags:
        try:
            scope = ctl.programs[tag.scope].tags
        except KeyError:
            scope = ctl.tags
        values[tag] = get_value(tag, scope)
    return values


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


def find_target_types(ctl):
    """Determines data types to be captured."""
    # Initial data types to be located. This will be expanded to include
    # all types containing any of these types.
    target_types = {
        "TIMER": {("PRE",)},
        "COUNTER": {("PRE",)},
    }

    all_types = copy.copy(ctl.datatypes)
    all_types.update(ctl.aois)

    # Locating nested types, e.g., a UDT with a TIMER member, is done by
    # looping through all data types. Each loop will add types with
    # any members of a target type. All target types have been found when
    # the loop concludes with no further types added.
    while True:
        start = len(target_types)

        for type_name in all_types:
            # Evaluate UDT members and AOI local tags; AOI parameters are
            # excluded because input and output parameters cannot be
            # structures.
            try:
                members = all_types[type_name].members
            except AttributeError:
                members = all_types[type_name].local_tags

            for mname, member in members.items():
                try:
                    target_paths = target_types[member.datatype]

                # Ignore UDT bit members and unrelated data types.
                except (AttributeError, KeyError):
                    continue

                try:
                    paths = target_types[type_name]
                except KeyError:
                    paths = set()
                    target_types[type_name] = paths

                for path in target_paths:
                    p = [mname]
                    if member.dim:
                        p.append(member.dim)
                    p.extend(path)
                    paths.add(tuple(p))

        # Iteration is complete when no further types have been added.
        if len(target_types) == start:
            return target_types


def find_target_tags(scope, tags, types):
    """Locates instances of the target data types."""
    targets = set()
    for name, tag in tags.items():
        try:
            paths = types[tag.datatype]
        except KeyError:
            continue
        for path in paths:
            if tag.dim:
                path = list(path)
                path.insert(0, tag.dim)

            for p in expand_dims(path):
                targets.add(Tag(scope, name, p))

    return targets


def expand_dims(path):
    """Generates paths for all array members."""
    # Create iterators for array indices(tuple of ints) in a path.
    # These iterators will be used to generate an index for every element
    # in each array.
    indices = []  # Path index where each dimension is located.
    products = []  # Dimensional product iterators.
    for i, dim in enumerate(path):
        if isinstance(dim, tuple):
            indices.append(i)
            products.append(itertools.product(*[range(d) for d in dim]))

    # Create paths for every combination of array dimensions, i.e. the
    # product of products.
    combos = set()
    template = list(path)
    for dims in itertools.product(*products):
        for i, dim in enumerate(dims):
            template[indices[i]] = dim
        combos.add(tuple(template))

    return combos


def get_value(tag, scope):
    """Acquires the value of a single structure member."""
    value = scope[tag.name].value
    for member in tag.members:
        if isinstance(member, tuple):
            # Dimensions need to be reversed so the most-significant
            # index is applied first.
            for dim in reversed(member):
                value = value[dim]
        else:
            value = value[member]
    return value
