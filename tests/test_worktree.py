"""Unit tests for the worktree rules: the branch, the repositories folder, the porcelain records and the state."""

import unittest
from pathlib import Path

from gemba import worktree

PORCELAIN = """\
worktree /home/me/projects/nakatomi-web
HEAD 1111111111111111111111111111111111111111
branch refs/heads/main

worktree /home/me/tasks/harnesses/support/2026-09-30-SUP-1-login-fails/worktrees/nakatomi-web
HEAD 2222222222222222222222222222222222222222
branch refs/heads/gemba/nakatomi/SUP-1

worktree /home/me/tasks/harnesses/support/2026-09-30-SUP-2-checkout/worktrees/nakatomi-web
HEAD 3333333333333333333333333333333333333333
detached

worktree /home/me/tasks/harnesses/support/2026-09-30-SUP-3-gone/worktrees/nakatomi-web
HEAD 4444444444444444444444444444444444444444
branch refs/heads/gemba/nakatomi/SUP-3
prunable gitdir file points to non-existent location

"""


class BranchTest(unittest.TestCase):
    def test_default_prefix(self):
        self.assertEqual(
            worktree.branch_name(worktree.DEFAULT_BRANCH_PREFIX, "nakatomi", "SUP-1"), "gemba/nakatomi/SUP-1"
        )

    def test_given_prefix(self):
        self.assertEqual(worktree.branch_name("nk", "nakatomi", "SUP-1"), "nk/nakatomi/SUP-1")

    def test_paths(self):
        self.assertEqual(worktree.relative_path("nakatomi-web"), "worktrees/nakatomi-web")
        self.assertEqual(worktree.worktree_path(Path("/h"), "nakatomi-web"), Path("/h/worktrees/nakatomi-web"))


class ReposDirTest(unittest.TestCase):
    # An absolute path is printed in the form of the system, so the expected messages build it the same way.
    REPOS = Path("/r")

    def test_absolute(self):
        self.assertEqual(worktree.repos_dir(Path("/tasks"), "/srv/repos"), Path("/srv/repos"))

    def test_home(self):
        self.assertEqual(worktree.repos_dir(Path("/tasks"), "~/projects"), Path.home() / "projects")

    def test_relative_to_the_tasks_repo_root(self):
        self.assertEqual(worktree.repos_dir(Path("/tasks"), "repos"), Path("/tasks/repos"))
        self.assertEqual(worktree.repos_dir(Path("/tasks"), "../projects"), Path("/tasks/../projects"))

    def test_repository_found(self):
        self.assertIsNone(worktree.repo_problem(self.REPOS, "nakatomi-web", ["nakatomi-api", "nakatomi-web"]))

    def test_repository_missing_names_the_ones_found(self):
        self.assertEqual(
            worktree.repo_problem(self.REPOS, "other", ["nakatomi-web", "nakatomi-api"]),
            f"no repository named 'other' is at the root of {self.REPOS} "
            "(repositories there: nakatomi-api, nakatomi-web)",
        )

    def test_nested_name_is_not_at_the_root(self):
        problem = worktree.repo_problem(self.REPOS, "group/other", ["x"])
        self.assertIn("no repository named 'group/other'", problem or "")

    def test_no_repository_at_all(self):
        self.assertEqual(
            worktree.repo_problem(self.REPOS, "nakatomi-web", []),
            f"no repository named 'nakatomi-web' is at the root of {self.REPOS} (no repository is there)",
        )

    def test_folder_missing(self):
        self.assertEqual(
            worktree.repo_problem(self.REPOS, "nakatomi-web", None), f"repos_dir {self.REPOS} is not a folder"
        )

    def test_not_a_folder(self):
        self.assertEqual(worktree.not_a_folder_problem(self.REPOS), f"repos_dir {self.REPOS} is not a folder")

    def test_repos_dir_missing_names_its_file(self):
        self.assertEqual(
            worktree.missing_repos_dir_problem("gemba.local.yaml"),
            "no repos_dir declared: add repos_dir to gemba.local.yaml",
        )


class ParseWorktreesTest(unittest.TestCase):
    def test_records(self):
        records = worktree.parse_worktrees(PORCELAIN.splitlines())
        self.assertEqual(
            records,
            [
                worktree.Record("/home/me/projects/nakatomi-web", "1" * 40, "main", False),
                worktree.Record(
                    "/home/me/tasks/harnesses/support/2026-09-30-SUP-1-login-fails/worktrees/nakatomi-web",
                    "2" * 40,
                    "gemba/nakatomi/SUP-1",
                    False,
                ),
                worktree.Record(
                    "/home/me/tasks/harnesses/support/2026-09-30-SUP-2-checkout/worktrees/nakatomi-web",
                    "3" * 40,
                    None,
                    False,
                ),
                worktree.Record(
                    "/home/me/tasks/harnesses/support/2026-09-30-SUP-3-gone/worktrees/nakatomi-web",
                    "4" * 40,
                    "gemba/nakatomi/SUP-3",
                    True,
                ),
            ],
        )

    def test_without_trailing_empty_line(self):
        records = worktree.parse_worktrees(["worktree /r", "HEAD abc", "branch refs/heads/main"])
        self.assertEqual(records, [worktree.Record("/r", "abc", "main", False)])

    def test_nothing(self):
        self.assertEqual(worktree.parse_worktrees([]), [])


class StateTest(unittest.TestCase):
    def test_render_without_an_upstream(self):
        state = worktree.State("worktrees/nakatomi-web", branch="gemba/nakatomi/SUP-1")
        self.assertEqual(
            worktree.render_state(state),
            "worktrees/nakatomi-web\nbranch: gemba/nakatomi/SUP-1\nupstream: none\nuncommitted: 0\nunpushed: 0",
        )

    def test_render_with_an_upstream_and_pending_work(self):
        state = worktree.State(
            "worktrees/nakatomi-web",
            branch="gemba/nakatomi/SUP-1",
            upstream="origin/feature/login-fix",
            uncommitted=("a.txt", "b.txt"),
            unpushed=3,
        )
        self.assertEqual(
            worktree.render_state(state),
            "worktrees/nakatomi-web\nbranch: gemba/nakatomi/SUP-1\nupstream: origin/feature/login-fix\n"
            "uncommitted: 2\nunpushed: 3",
        )

    def test_render_detached(self):
        self.assertIn("\nbranch: detached\n", worktree.render_state(worktree.State("worktrees/nakatomi-web")))

    def test_render_not_a_worktree(self):
        state = worktree.State("worktrees/stray", kind="not a worktree")
        self.assertEqual(worktree.render_state(state), "worktrees/stray\nnot a worktree")

    def test_nothing_pending(self):
        self.assertEqual(worktree.pending_problems(worktree.State("worktrees/nakatomi-web", branch="b")), [])

    def test_one_path_and_one_commit(self):
        state = worktree.State("worktrees/nakatomi-web", branch="b", uncommitted=("notes.txt",), unpushed=1)
        self.assertEqual(
            worktree.pending_problems(state),
            [
                "worktrees/nakatomi-web has 1 uncommitted path: notes.txt",
                "worktrees/nakatomi-web has 1 commit not on any remote branch",
            ],
        )

    def test_several_paths_and_commits(self):
        state = worktree.State("worktrees/nakatomi-web", branch="b", uncommitted=("a.txt", "src/b.py"), unpushed=4)
        self.assertEqual(
            worktree.pending_problems(state),
            [
                "worktrees/nakatomi-web has 2 uncommitted paths: a.txt, src/b.py",
                "worktrees/nakatomi-web has 4 commits not on any remote branch",
            ],
        )

    def test_folder_that_is_not_a_worktree(self):
        state = worktree.State("worktrees/stray", kind="not a worktree")
        self.assertEqual(worktree.pending_problems(state), ["worktrees/stray is not a worktree"])

    def test_unreadable_worktree(self):
        state = worktree.State("worktrees/nakatomi-web", kind="unreadable")
        self.assertEqual(
            worktree.pending_problems(state), ["the state of worktrees/nakatomi-web could not be read with git"]
        )


class ProblemTest(unittest.TestCase):
    def test_orphan_without_unpushed_commits(self):
        self.assertIsNone(worktree.orphan_problem("nakatomi-web", "gemba/nakatomi/SUP-1", 0))

    def test_orphan_with_unpushed_commits(self):
        self.assertEqual(
            worktree.orphan_problem("nakatomi-web", "gemba/nakatomi/SUP-1", 2),
            "branch gemba/nakatomi/SUP-1 of nakatomi-web has 2 commits not on any remote branch and no worktree",
        )
        self.assertIn("has 1 commit not", worktree.orphan_problem("nakatomi-web", "gemba/nakatomi/SUP-1", 1) or "")

    def test_base_resolved(self):
        self.assertIsNone(worktree.base_problem(None, ["main", "feature/a"], "main"))
        self.assertIsNone(worktree.base_problem("feature/a", ["main", "feature/a"], "main"))
        self.assertIsNone(worktree.base_problem("feature/a", ["main", "feature/a"], None))

    def test_missing_remote_branch(self):
        self.assertEqual(worktree.base_problem("feature/none", ["main"], "main"), "origin has no branch feature/none")

    def test_default_branch_gone_from_the_remote(self):
        self.assertEqual(worktree.base_problem(None, ["develop"], "main"), "origin has no branch main")

    def test_no_default_branch(self):
        self.assertEqual(
            worktree.base_problem(None, ["main"], None),
            "the repository records no default branch for origin: --from names the base branch",
        )

    def test_outcome(self):
        self.assertEqual(
            worktree.render_outcome("worktrees/nakatomi-web", "gemba/nakatomi/SUP-1", "main", worktree.CREATED),
            "worktrees/nakatomi-web\nbranch: gemba/nakatomi/SUP-1\nfrom: origin/main\ncreated",
        )


if __name__ == "__main__":
    unittest.main()
