"""Unit tests for the relation rules: the subtree of a task, and the refusal of a ref no task of the clone holds."""

import datetime
import unittest

from gemba import relations, tasks

DAY = datetime.date(2026, 10, 25)


def task(ref, parent=None, owner=None):
    return tasks.Task(
        f"tasks/support/2026-10-25-{ref}-t.md",
        owner,
        "support",
        False,
        ref,
        parent,
        DAY,
        "T",
        "open",
        DAY,
        None,
        {},
        None,
    )


class SubtreeTest(unittest.TestCase):
    def test_root_alone(self):
        found = [task("SUP-1"), task("SUP-2"), task("SUP-3", parent="SUP-2")]
        self.assertEqual(relations.subtree(found, "SUP-1"), frozenset({"SUP-1"}))

    def test_chain(self):
        found = [task("SUP-3", parent="SUP-2"), task("SUP-1"), task("SUP-2", parent="SUP-1"), task("SUP-4")]
        self.assertEqual(relations.subtree(found, "SUP-1"), frozenset({"SUP-1", "SUP-2", "SUP-3"}))
        self.assertEqual(relations.subtree(found, "SUP-2"), frozenset({"SUP-2", "SUP-3"}))

    def test_task_split_across_members(self):
        found = [
            task("MR-DEV-1", owner="manuel"),
            task("AG-DEV-1", parent="MR-DEV-1", owner="ana"),
            task("MR-OPS-1", parent="AG-DEV-1", owner="manuel"),
            task("MR-DEV-2", parent="MR-DEV-1", owner="manuel"),
            task("AG-SUP-1", owner="ana"),
        ]
        self.assertEqual(
            relations.subtree(found, "MR-DEV-1"), frozenset({"MR-DEV-1", "AG-DEV-1", "MR-OPS-1", "MR-DEV-2"})
        )

    def test_loop_written_by_hand_ends(self):
        found = [task("SUP-1", parent="SUP-3"), task("SUP-2", parent="SUP-1"), task("SUP-3", parent="SUP-2")]
        self.assertEqual(relations.subtree(found, "SUP-1"), frozenset({"SUP-1", "SUP-2", "SUP-3"}))

    def test_root_held_by_no_task(self):
        self.assertEqual(relations.subtree([task("SUP-2", parent="SUP-9")], "SUP-9"), frozenset({"SUP-9", "SUP-2"}))


class UnknownProblemTest(unittest.TestCase):
    def test_names_the_option_and_the_ref_and_suggests_a_pull(self):
        for name in ("parent", "--parent", "--under"):
            with self.subTest(name=name):
                self.assertEqual(
                    relations.unknown_problem(name, "SUP-9"),
                    f"{name} 'SUP-9' is not a task of this clone: if it was created in another clone, pull first",
                )


if __name__ == "__main__":
    unittest.main()
