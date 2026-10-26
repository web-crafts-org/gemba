"""Unit tests for the sync rules: the ownership map, the checks of an outgoing change, the report of an incoming one
and the lines of `gemba sync`, with plain data in place of git."""

import unittest

from gemba import obeya, sync

CONTEXT = sync.Context(me="manuel", initials="MR", members=("manuel", "ana", "bea"), workstreams=("support",))
FULL = "3c4d5e6" + "0" * 33
MR1 = "tasks/manuel/support/2026-10-20-MR-SUP-1-export.md"
MR2 = "tasks/manuel/support/2026-10-25-MR-SUP-2-invoices.md"
AG1 = "tasks/ana/support/2026-10-21-AG-SUP-1-login.md"


def task(ref, status="open"):
    return (
        f"---\nstatus: {status}\nref: {ref}\nupdated_at: 2026-10-20\nmetadata: {{}}\n---\n\nSome work.\n\n## Updates\n"
    )


def commit(short, *paths, author="Manuel Robles", subject="Some work"):
    return sync.Commit(id=short + "0" * 33, short=short, author=author, subject=subject, paths=paths)


def merge(short, author="Manuel Robles"):
    return sync.Commit(id=short + "0" * 33, short=short, author=author, subject="Merge", paths=())


def check(net, commits=(), merges=(), own_files=(), own_paths=(), confirmed=False):
    return sync.outgoing(net, commits, merges, own_files, own_paths, CONTEXT, confirmed)


class ClassifyTest(unittest.TestCase):
    def test_every_kind_of_path(self):
        expected = {
            MR1: sync.Owner("own"),
            "tasks/manuel/support/archive/.gitkeep": sync.Owner("own"),
            AG1: sync.Owner("member", "ana"),
            "tasks/bea/support/2026-10-01-BE-SUP-1-old.md": sync.Owner("member", "bea"),
            "gemba.local.yaml": sync.Owner("private"),
            "harnesses/support/2026-10-20-MR-SUP-1-export/notes/a.md": sync.Owner("private"),
            "gemba.yaml": sync.Owner("shared"),
            ".claude/skills/gemba-create/SKILL.md": sync.Owner("shared"),
            ".gitignore": sync.Owner("shared"),
            "tasks/.gitkeep": sync.Owner("shared"),
            "tasks/carl/support/2026-10-01-CR-SUP-1-x.md": sync.Owner("shared"),
            "tasks/manuel": sync.Owner("shared"),
            "docs/gemba.local.yaml": sync.Owner("shared"),
            "harnesses": sync.Owner("shared"),
        }
        for path, owner in expected.items():
            with self.subTest(path=path):
                self.assertEqual(sync.classify(path, "manuel", ("manuel", "ana", "bea")), owner)


class OutgoingTest(unittest.TestCase):
    def test_own_valid_task_goes_out(self):
        verdict = check([MR2], [commit("1a2b3c4", MR2)], own_files=[sync.OwnFile(MR2, task("MR-SUP-2"))])
        self.assertEqual(verdict, sync.Outgoing(problems=(), shared=()))

    def test_another_members_folder(self):
        for change in ("added", "edited", "deleted"):
            with self.subTest(change=change):
                verdict = check([AG1], [commit("1a2b3c4", AG1)])
                self.assertEqual(
                    verdict.problems, (f"1a2b3c4 changes {AG1}, in the folder of ana: only ana writes it",)
                )

    def test_private_paths(self):
        verdict = check(["gemba.local.yaml"], [commit("1a2b3c4", "gemba.local.yaml")])
        self.assertEqual(
            verdict.problems,
            ("1a2b3c4 changes gemba.local.yaml, private to each clone: it never leaves the clone",),
        )

    def test_private_path_added_and_removed_again(self):
        commits = [commit("1a2b3c4", "gemba.local.yaml"), commit("5d6e7f8", "gemba.local.yaml")]
        verdict = check([], commits)
        self.assertEqual(
            verdict.problems,
            (
                "1a2b3c4 changes gemba.local.yaml, private to each clone: it never leaves the clone",
                "5d6e7f8 changes gemba.local.yaml, private to each clone: it never leaves the clone",
            ),
        )

    def test_private_path_of_a_merge_only(self):
        verdict = check(["harnesses/support/x/notes/a.md"], [commit("1a2b3c4", MR1)], [merge("7e8f9a0")])
        self.assertEqual(
            verdict.problems,
            ("merge 7e8f9a0 changes harnesses/support/x/notes/a.md, private to each clone: it never leaves the clone",),
        )

    def test_change_to_another_members_file_made_and_undone_left_unreported(self):
        verdict = check(
            [MR2],
            [commit("1a2b3c4", AG1), commit("5d6e7f8", AG1, MR2)],
            own_files=[sync.OwnFile(MR2, task("MR-SUP-2"))],
        )
        self.assertEqual(verdict, sync.Outgoing(problems=(), shared=()))

    def test_own_file_outside_a_workstream_folder(self):
        for path in ("tasks/manuel/2026-10-25-MR-SUP-2-x.md", "tasks/manuel/sales/2026-10-25-MR-SAL-1-x.md"):
            with self.subTest(path=path):
                verdict = check([path], [commit("1a2b3c4", path)], own_files=[sync.OwnFile(path, task("MR-SUP-2"))])
                self.assertEqual(verdict.problems, (f"{path} is not in a workstream folder of tasks/manuel/",))

    def test_own_file_in_the_archive_accepted(self):
        path = "tasks/manuel/support/archive/2026-10-20-MR-SUP-1-export.md"
        verdict = check([path], [commit("1a2b3c4", path)], own_files=[sync.OwnFile(path, task("MR-SUP-1", "done"))])
        self.assertEqual(verdict.problems, ())

    def test_unreadable_own_task(self):
        text = "---\nref: MR-SUP-2\nupdated_at: 2026-10-25\nmetadata: {}\n---\n"
        verdict = check([MR2], [commit("1a2b3c4", MR2)], own_files=[sync.OwnFile(MR2, text)])
        self.assertEqual(len(verdict.problems), 1)
        self.assertTrue(verdict.problems[0].startswith(f"{MR2} is not a valid task: status is missing"))

    def test_task_of_other_initials(self):
        path = "tasks/manuel/support/2026-10-25-AG-SUP-4-x.md"
        verdict = check([path], [commit("1a2b3c4", path)], own_files=[sync.OwnFile(path, task("AG-SUP-4"))])
        self.assertEqual(verdict.problems, (f"{path} holds AG-SUP-4, without the initials of manuel (MR)",))

    def test_task_without_initials(self):
        path = "tasks/manuel/support/2026-10-25-SUP-4-x.md"
        verdict = check([path], [commit("1a2b3c4", path)], own_files=[sync.OwnFile(path, task("SUP-4"))])
        self.assertEqual(verdict.problems, (f"{path} holds SUP-4, without the initials of manuel (MR)",))

    def test_deleted_or_other_own_files_not_read(self):
        notes = "tasks/manuel/support/notes.txt"
        verdict = check([MR1, notes], [commit("1a2b3c4", MR1, notes)], own_files=[sync.OwnFile(MR1, None)])
        self.assertEqual(verdict.problems, ())

    def test_own_file_that_is_not_utf8(self):
        own = sync.OwnFile(MR2, None, unreadable="the file is not UTF-8 text")
        verdict = check([MR2], [commit("1a2b3c4", MR2)], own_files=[own])
        self.assertEqual(verdict.problems, (f"{MR2} is not a valid task: the file is not UTF-8 text",))

    def test_own_task_file_changed_by_a_merge_only(self):
        text = "---\nref: MR-SUP-1\n---\n"
        verdict = check([MR1], [commit("1a2b3c4", MR2)], [merge("7e8f9a0")], own_files=[sync.OwnFile(MR1, text)])
        self.assertEqual(len(verdict.problems), 1)
        self.assertTrue(verdict.problems[0].startswith(f"{MR1} is not a valid task:"))

    def test_duplicate_ref_with_a_file_in_the_net_change(self):
        other = "tasks/manuel/support/2026-10-24-MR-SUP-3-reports.md"
        mine = "tasks/manuel/support/2026-10-25-MR-SUP-3-invoices.md"
        verdict = check(
            [mine], [commit("1a2b3c4", mine)], own_files=[sync.OwnFile(mine, task("MR-SUP-3"))], own_paths=[other, mine]
        )
        self.assertEqual(verdict.problems, (f"MR-SUP-3 is held by {other} and {mine}: a ref is never held twice",))

    def test_duplicate_ref_without_a_file_in_the_net_change(self):
        other = "tasks/manuel/support/2026-10-24-MR-SUP-3-reports.md"
        archived = "tasks/manuel/support/archive/2026-10-01-MR-SUP-3-old.md"
        verdict = check(
            [MR2],
            [commit("1a2b3c4", MR2)],
            own_files=[sync.OwnFile(MR2, task("MR-SUP-2"))],
            own_paths=[other, archived],
        )
        self.assertEqual(verdict.problems, ())

    def test_shared_files_need_a_confirmation(self):
        verdict = check(
            ["gemba.yaml", ".gitignore"], [commit("1a2b3c4", "gemba.yaml"), commit("5d6e7f8", ".gitignore")]
        )
        self.assertEqual(verdict.problems, ())
        self.assertEqual(
            verdict.shared,
            ("5d6e7f8 changes the shared file .gitignore", "1a2b3c4 changes the shared file gemba.yaml"),
        )
        self.assertEqual(
            verdict.lines(FULL),
            [
                "5d6e7f8 changes the shared file .gitignore",
                "1a2b3c4 changes the shared file gemba.yaml",
                f"confirm them with git -c gemba.shared={FULL} push",
            ],
        )

    def test_confirmation_lifts_the_shared_lines_only(self):
        verdict = check(["gemba.yaml", AG1], [commit("1a2b3c4", "gemba.yaml", AG1)], confirmed=True)
        self.assertEqual(verdict.shared, ())
        self.assertEqual(verdict.problems, (f"1a2b3c4 changes {AG1}, in the folder of ana: only ana writes it",))
        self.assertEqual(verdict.lines(FULL), list(verdict.problems))

    def test_confirmation_of_the_commit_pushed_and_of_another(self):
        self.assertTrue(sync.confirmed([FULL], FULL))
        self.assertTrue(sync.confirmed(["0" * 40, FULL], FULL))
        self.assertFalse(sync.confirmed(["1a2b3c4" + "0" * 33], FULL))
        self.assertFalse(sync.confirmed([FULL[:7]], FULL))
        self.assertFalse(sync.confirmed([], FULL))
        self.assertEqual(sync.confirm_command(FULL), f"git -c gemba.shared={FULL} push")

    def test_path_changed_by_several_commits_named_in_one_line(self):
        commits = [commit("1a2b3c4", AG1), commit("5d6e7f8", MR2), commit("9a0b1c2", AG1), commit("3d4e5f6", AG1)]
        verdict = check([AG1], commits)
        self.assertEqual(
            verdict.problems,
            (f"1a2b3c4, 9a0b1c2 and 3d4e5f6 change {AG1}, in the folder of ana: only ana writes it",),
        )
        verdict = check([AG1], commits[:1] + commits[2:3])
        self.assertTrue(verdict.problems[0].startswith(f"1a2b3c4 and 9a0b1c2 change {AG1},"))

    def test_path_changed_only_by_a_merge_names_the_merge(self):
        verdict = check([AG1], [commit("1a2b3c4", MR1)], [merge("7e8f9a0")])
        self.assertEqual(verdict.problems, (f"merge 7e8f9a0 changes {AG1}, in the folder of ana: only ana writes it",))
        verdict = check(["gemba.yaml"], [], [merge("7e8f9a0"), merge("1b2c3d4")])
        self.assertEqual(verdict.shared, ("merges 7e8f9a0 and 1b2c3d4 change the shared file gemba.yaml",))

    def test_every_problem_at_once_in_order(self):
        bad = "tasks/manuel/support/2026-10-25-AG-SUP-4-x.md"
        mine = "tasks/manuel/support/2026-10-25-MR-SUP-1-again.md"
        net = [AG1, "gemba.local.yaml", bad, mine, "README.md"]
        commits = [commit("1a2b3c4", AG1, "gemba.local.yaml"), commit("5d6e7f8", bad, mine, "README.md")]
        own_files = [sync.OwnFile(bad, task("AG-SUP-4")), sync.OwnFile(mine, task("MR-SUP-1"))]
        verdict = check(net, commits, own_files=own_files, own_paths=[MR1, bad, mine])
        self.assertEqual(
            verdict.lines(FULL),
            [
                f"1a2b3c4 changes {AG1}, in the folder of ana: only ana writes it",
                "1a2b3c4 changes gemba.local.yaml, private to each clone: it never leaves the clone",
                f"{bad} holds AG-SUP-4, without the initials of manuel (MR)",
                f"MR-SUP-1 is held by {MR1} and {mine}: a ref is never held twice",
                "5d6e7f8 changes the shared file README.md",
                f"confirm them with git -c gemba.shared={FULL} push",
            ],
        )


class IncomingTest(unittest.TestCase):
    PATCH = "diff --git a/x b/x\n@@ -2 +2 @@\n-status: open\n+status: blocked\n"

    def test_report_of_own_shared_and_private_paths(self):
        commits = [
            commit("1a2b3c4", MR1, "gemba.yaml", author="Ana Gómez"),
            commit("5d6e7f8", "gemba.local.yaml", author="Ana Gómez"),
        ]
        net = [MR1, "gemba.yaml", "gemba.local.yaml"]
        report = sync.incoming(net, commits, [], self.PATCH, CONTEXT, pulled=True)
        self.assertTrue(report.listed)
        self.assertEqual(
            report.lines,
            (
                "- your tasks:",
                f"  {MR1}, by 1a2b3c4 (Ana Gómez)",
                "    diff --git a/x b/x",
                "    @@ -2 +2 @@",
                "    -status: open",
                "    +status: blocked",
                "- shared files:",
                "  gemba.yaml, by 1a2b3c4 (Ana Gómez)",
                "- gemba.local.yaml, private to each clone, by 5d6e7f8 (Ana Gómez): the pull wrote it over yours",
            ),
        )

    def test_private_path_before_a_pull(self):
        commits = [commit("5d6e7f8", "gemba.local.yaml", author="Ana Gómez")]
        report = sync.incoming(["gemba.local.yaml"], commits, [], "", CONTEXT, pulled=False)
        self.assertEqual(
            report.lines,
            ("- gemba.local.yaml, private to each clone, by 5d6e7f8 (Ana Gómez): a pull writes it over yours",),
        )

    def test_change_brought_by_a_merge(self):
        commits = [commit("1a2b3c4", AG1, author="Ana Gómez")]
        report = sync.incoming([MR1, AG1], commits, [merge("7e8f9a0", "Ana Gómez")], self.PATCH, CONTEXT, pulled=True)
        self.assertEqual(report.lines[:2], ("- your tasks:", f"  {MR1}, by merge 7e8f9a0 (Ana Gómez)"))
        self.assertEqual(report.lines[-1], "- 1 commit changes only the tasks of other members")

    def test_count_of_other_members(self):
        bea = "tasks/bea/support/2026-10-01-BE-SUP-1-old.md"
        commits = [commit("1a2b3c4", AG1), commit("5d6e7f8", AG1, bea), commit("9a0b1c2", AG1, "README.md")]
        report = sync.incoming([AG1, bea, "README.md"], commits, [], "", CONTEXT, pulled=True)
        self.assertEqual(report.lines[-1], "- 2 commits change only the tasks of other members")
        self.assertEqual(report.lines[:2], ("- shared files:", "  README.md, by 9a0b1c2 (Manuel Robles)"))

    def test_nothing_listed_when_only_other_members_changed(self):
        report = sync.incoming([AG1], [commit("1a2b3c4", AG1)], [], "", CONTEXT, pulled=True)
        self.assertFalse(report.listed)
        self.assertEqual(report.lines, ("- 1 commit changes only the tasks of other members",))
        self.assertEqual(sync.came_in("post-merge", 1), "gemba hook post-merge: 1 commit came in")


class ReportTest(unittest.TestCase):
    def test_lines_of_sync(self):
        incoming = sync.incoming([MR1], [commit("1a2b3c4", MR1, author="Ana Gómez")], [], "", CONTEXT, pulled=False)
        going = [commit("3c4d5e6", MR2, subject="Add MR-SUP-2")]
        verdict = check([MR2], going, own_files=[sync.OwnFile(MR2, task("MR-SUP-2"))])
        lines = sync.report(
            "main", "origin/main", 1, incoming, going, verdict, FULL, ["README.md", AG1, MR2], CONTEXT, None
        )
        self.assertEqual(
            lines,
            [
                "branch main, upstream origin/main",
                "incoming: 1 commit",
                "- your tasks:",
                f"  {MR1}, by 1a2b3c4 (Ana Gómez)",
                "outgoing: 1 commit",
                "- 3c4d5e6 Manuel Robles: Add MR-SUP-2",
                "uncommitted:",
                f"- yours: {MR2}",
                f"- of ana: {AG1}",
                "- shared: README.md",
                "push: ready",
            ],
        )

    def test_verdicts(self):
        empty = sync.Outgoing(problems=(), shared=())
        refused = sync.Outgoing(problems=("p",), shared=("s",))
        to_confirm = sync.Outgoing(problems=(), shared=("s",))
        going = [commit("3c4d5e6", MR2)]
        none = sync.Incoming(lines=(), listed=False)
        for verdict, commits, last in (
            (empty, [], "push: nothing to push"),
            (empty, going, "push: ready"),
            (refused, going, "push: refused"),
            (to_confirm, going, f"push: needs confirmation: git -c gemba.shared={FULL} push"),
        ):
            with self.subTest(last=last):
                lines = sync.report("main", "origin/main", 0, none, commits, verdict, FULL, [], CONTEXT, None)
                self.assertEqual(lines[-1], last)

    def test_hooks_line(self):
        installed: dict[str, obeya.HookState] = {
            "pre-push": "current",
            "post-merge": "earlier",
            "post-rewrite": "chained",
        }
        self.assertIsNone(sync.hooks_line(True, installed))
        self.assertEqual(
            sync.hooks_line(True, {"pre-push": "missing", "post-merge": "other", "post-rewrite": "current"}),
            "hooks: on for this clone, but pre-push and post-merge not installed: run gemba init",
        )
        self.assertEqual(
            sync.hooks_line(False, installed),
            "hooks: off for this clone, but pre-push and post-merge written by gemba still there: run gemba init",
        )
        self.assertIsNone(
            sync.hooks_line(False, {"pre-push": "missing", "post-merge": "chained", "post-rewrite": "other"})
        )

    def test_refusal_of_a_ref(self):
        self.assertEqual(
            sync.refusal("refs/heads/main", ["one", "two"]),
            ["gemba hook pre-push: push to refs/heads/main refused:", "- one", "- two"],
        )


if __name__ == "__main__":
    unittest.main()
