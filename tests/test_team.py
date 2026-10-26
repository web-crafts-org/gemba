"""Unit tests for the team: who may write a task, and the layout a team requires."""

import datetime
import tempfile
import unittest
from pathlib import Path

from gemba import tasks, team

WORKSTREAMS = ("support", "operations", "estimates")
MEMBERS = {"manuel": team.Member("manuel", "MR"), "ana": team.Member("ana", "AG", active=False)}


def task(ref, owner):
    day = datetime.date(2026, 10, 25)
    return tasks.Task(
        f"tasks/{owner}/support/2026-10-25-{ref}-t.md",
        owner,
        "support",
        False,
        ref,
        None,
        day,
        "T",
        "open",
        day,
        None,
        {},
        None,
    )


class WriteProblemsTest(unittest.TestCase):
    def test_no_team(self):
        self.assertEqual(team.write_problems(None, None, task("SUP-1", None), "personal.yaml"), [])

    def test_owner_writes(self):
        self.assertEqual(team.write_problems(MEMBERS, "manuel", None, "personal.yaml"), [])
        self.assertEqual(team.write_problems(MEMBERS, "manuel", task("MR-SUP-1", "manuel"), "personal.yaml"), [])

    def test_no_member_declared_names_the_file_given_and_the_members(self):
        self.assertEqual(
            team.write_problems(MEMBERS, None, task("AG-SUP-1", "ana"), "personal.yaml"),
            ["no member declared for this clone: add me to personal.yaml, the personal config (members: manuel, ana)"],
        )

    def test_inactive_member(self):
        self.assertEqual(
            team.write_problems(MEMBERS, "ana", task("AG-SUP-1", "ana"), "personal.yaml"),
            ["me is ana, an inactive member of the team, who writes no task"],
        )
        self.assertEqual(
            team.write_problems(MEMBERS, "ana", None, "personal.yaml"),
            ["me is ana, an inactive member of the team, who writes no task"],
        )

    def test_task_of_another_member(self):
        self.assertEqual(
            team.write_problems(MEMBERS, "manuel", task("AG-SUP-1", "ana"), "personal.yaml"),
            ["AG-SUP-1 belongs to ana: only its owner writes it"],
        )


class LayoutProblemTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def folders(self, *names):
        for name in names:
            (self.root / "tasks" / name).mkdir(parents=True)

    def test_no_tasks_folder(self):
        self.assertIsNone(team.layout_problem(self.root, WORKSTREAMS))

    def test_member_folders_only(self):
        self.folders("manuel/support", "ana", ".hidden")
        self.assertIsNone(team.layout_problem(self.root, WORKSTREAMS))

    def test_hidden_folder_and_file_named_after_a_workstream_ignored(self):
        (self.root / "tasks").mkdir()
        (self.root / "tasks" / "support").write_text("", encoding="utf-8")
        self.folders(".operations")
        self.assertIsNone(team.layout_problem(self.root, (*WORKSTREAMS, ".operations")))

    def test_one_workstream_folder(self):
        self.folders("manuel", "support")
        self.assertEqual(
            team.layout_problem(self.root, WORKSTREAMS),
            "team is declared, but tasks/ holds tasks/support, the folder of an obeya without a team: a team starts "
            "in a new obeya, and the gemba-migrate skill brings earlier tasks into it",
        )

    def test_workstream_folders_named_in_order_as_posix_paths(self):
        self.folders("support/archive", "operations")
        problem = team.layout_problem(self.root, WORKSTREAMS) or ""
        self.assertTrue(
            problem.startswith("team is declared, but tasks/ holds tasks/operations and tasks/support, the folders of"),
            problem,
        )
        self.folders("estimates")
        problem = team.layout_problem(self.root, WORKSTREAMS) or ""
        self.assertIn("tasks/estimates, tasks/operations and tasks/support, the folders of", problem)


if __name__ == "__main__":
    unittest.main()
