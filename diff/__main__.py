"""Top-level entry point for running the package."""

import argparse
import hashlib

from . import l5x
from . import report


def get_args():
    """Gets command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("l5x", nargs=2, help="L5X files to be compared.")
    return parser.parse_args()


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


if __name__ == "__main__":
    args = get_args()
    hashes = {f: compute_md5(f) for f in args.l5x}
    tags = {f: l5x.parse(f) for f in args.l5x}
    diff = compare(tags[args.l5x[0]].values, tags[args.l5x[1]].values)

    # Excluded tags are those without decorated data but have differing
    # raw values.
    excl = compare(*[t.no_data for t in tags.values()])

    report.generate(args.l5x, hashes, tags, diff, excl)
