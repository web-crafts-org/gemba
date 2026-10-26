"""Relation rules: a task split from another, its parent, read over tasks already read.

The child names its parent and the parent never names its children, so they are found
by a scan; `tasks.py` reads and writes the `parent` key, and this module reads no file.
"""

from collections import defaultdict
from collections.abc import Iterable

from gemba import tasks


def subtree(found: Iterable[tasks.Task], root: str) -> frozenset[str]:
    """The refs of `root` and of every task below it in `found`, walked breadth first from parent to children.

    A parent written by hand may close a loop; a ref already visited is never walked
    again, so the walk always ends.
    """
    children: defaultdict[str, list[str]] = defaultdict(list)
    for task in found:
        if task.parent is not None:
            children[task.parent].append(task.ref)
    visited = {root}
    pending = [root]
    while pending:
        following = []
        for ref in pending:
            for child in children[ref]:
                if child not in visited:
                    visited.add(child)
                    following.append(child)
        pending = following
    return frozenset(visited)


def unknown_problem(name: str, ref: str) -> str:
    """The refusal of `ref`, given as `name`, when no task of the clone holds it: it may exist in another clone."""
    return f"{name} '{ref}' is not a task of this clone: if it was created in another clone, pull first"
