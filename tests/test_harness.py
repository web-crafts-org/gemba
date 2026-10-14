"""Unit tests for the harness layout, the harness config, the guide and the commit messages."""

import dataclasses
import datetime
import os
import stat
import tempfile
import unittest
from pathlib import Path

from gemba import harness, platform, worktree
from gemba.commands import harness as harness_command

CONFIG = harness.HarnessConfig(
    task="tasks/support/2026-09-30-SUP-1-login-fails.md",
    ref="SUP-1",
    workstream="support",
    agent_providers=("claude", "agents"),
    launched_at=datetime.date(2026, 9, 30),
    gemba_version="1.0",
)

GUIDE = "# Working in this harness\n\nRead `task.md`.\n"


class RenderConfigTest(unittest.TestCase):
    def test_fixed_key_order(self):
        self.assertEqual(
            harness.render_config(CONFIG),
            "task: tasks/support/2026-09-30-SUP-1-login-fails.md\n"
            "ref: SUP-1\n"
            "workstream: support\n"
            "agent_providers: [claude, agents]\n"
            "launched_at: 2026-09-30\n"
            'gemba_version: "1.0"\n',
        )

    def test_one_provider(self):
        rendered = harness.render_config(
            dataclasses.replace(CONFIG, agent_providers=("claude",), gemba_version="0.1.0")
        )
        self.assertIn("agent_providers: [claude]\n", rendered)
        self.assertIn('gemba_version: "0.1.0"\n', rendered)


class LayoutTest(unittest.TestCase):
    def test_harness_path(self):
        self.assertEqual(
            harness.harness_path(Path("/repo"), "support", "2026-09-30-SUP-1-login-fails"),
            Path("/repo/harnesses/support/2026-09-30-SUP-1-login-fails"),
        )

    def test_task_link_target(self):
        self.assertEqual(
            harness.task_link_target("tasks/support/2026-09-30-SUP-1-login-fails.md"),
            "../../../tasks/support/2026-09-30-SUP-1-login-fails.md",
        )

    def test_task_link_content_is_the_target_on_one_line(self):
        self.assertEqual(
            harness.task_link_content("tasks/support/2026-09-30-SUP-1-login-fails.md"),
            "../../../tasks/support/2026-09-30-SUP-1-login-fails.md\n",
        )

    def test_task_path_written_when_the_system_refuses_links(self):
        """Scenario: Task path written when the system refuses links."""

        def refuse(path, target):
            raise OSError(1, "A required privilege is not held by the client")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / harness.TASK_LINK
            harness_command.write_task_link(path, CONFIG.task, refuse)
            self.assertFalse(path.is_symlink())
            self.assertEqual(path.read_bytes(), b"../../../tasks/support/2026-09-30-SUP-1-login-fails.md\n")
            harness_command.write_task_link(path, "tasks/other.md", refuse)
            self.assertEqual(path.read_bytes(), b"../../../tasks/support/2026-09-30-SUP-1-login-fails.md\n")

    def test_task_linked_where_the_system_allows_it(self):
        made = []

        def record(path, target):
            made.append((path, target))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / harness.TASK_LINK
            harness_command.write_task_link(path, CONFIG.task, record)
            self.assertEqual(made, [(path, "../../../tasks/support/2026-09-30-SUP-1-login-fails.md")])
            self.assertFalse(path.exists())

    def test_link_target_resolves_from_the_harness(self):
        root = Path("/repo")
        folder = harness.harness_path(root, "support", "2026-09-30-SUP-1-login-fails")
        target = folder / harness.task_link_target("tasks/support/2026-09-30-SUP-1-login-fails.md")
        self.assertEqual(target.resolve(), (root / "tasks/support/2026-09-30-SUP-1-login-fails.md").resolve())

    def test_commit_messages(self):
        self.assertEqual(harness.launch_message("SUP-1"), "launch SUP-1")
        self.assertEqual(harness.note_message("finding", "login-trace"), "note finding login-trace")
        self.assertEqual(harness.resolve_message("login-trace"), "resolve login-trace")


class GitHintsTest(unittest.TestCase):
    def test_identity_hint(self):
        problem = "git commit --quiet -m launch SUP-1 failed: Author identity unknown\n*** Please tell me who you are."
        self.assertEqual(harness.git_hints(problem), [harness.IDENTITY_HINT])
        self.assertEqual(
            harness.git_hints("fatal: empty ident name (for <>) not allowed; set user.email"), [harness.IDENTITY_HINT]
        )

    def test_long_path_hint(self):
        problem = "git worktree add failed: error: unable to create file a/very/long/path.txt: Filename too long"
        self.assertEqual(harness.git_hints(problem), [harness.LONG_PATH_HINT])
        self.assertIn("core.longpaths", harness.LONG_PATH_HINT)

    def test_no_hint(self):
        self.assertEqual(harness.git_hints("git add -A failed: fatal: not a git repository"), [])
        self.assertEqual(harness.git_hints(""), [])

    def test_both_hints_in_order(self):
        problem = "Author identity unknown; unable to create file: Filename too long"
        self.assertEqual(harness.git_hints(problem), [harness.IDENTITY_HINT, harness.LONG_PATH_HINT])


class FindRootTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.harness = harness.harness_path(self.root, "support", "2026-09-30-SUP-1-login-fails")
        self.harness.mkdir(parents=True)
        (self.harness / harness.CONFIG_FILENAME).write_text(harness.render_config(CONFIG), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_from_the_harness_root(self):
        self.assertEqual(harness.find_root(self.harness), self.harness)

    def test_from_a_nested_folder(self):
        nested = self.harness / harness.NOTES_DIR / "drafts"
        nested.mkdir(parents=True)
        self.assertEqual(harness.find_root(nested), self.harness)

    def test_from_outside(self):
        outside = self.root / "tasks" / "support"
        outside.mkdir(parents=True)
        with self.assertRaises(harness.HarnessError) as caught:
            harness.find_root(outside)
        self.assertIn("no harness found", str(caught.exception))

    def test_a_folder_named_harness_yaml_is_no_marker(self):
        other = self.root / "harnesses" / "support" / "other"
        (other / harness.CONFIG_FILENAME).mkdir(parents=True)
        with self.assertRaises(harness.HarnessError):
            harness.find_root(other)


class ReadConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def read(self, text):
        (self.root / harness.CONFIG_FILENAME).write_text(text, encoding="utf-8")
        return harness.read_config(self.root, ["claude", "agents"])

    def test_rendered_config_reads_back(self):
        self.assertEqual(self.read(harness.render_config(CONFIG)), CONFIG)

    def test_invalid_config_refused(self):
        rendered = harness.render_config(CONFIG)
        for text, fragment in (
            (rendered.replace("[claude, agents]", "[claude, cursor]"), "agent_providers must be"),
            (rendered.replace("[claude, agents]", "[]"), "agent_providers must be"),
            (rendered.replace("launched_at: 2026-09-30", "launched_at: yesterday"), "launched_at must be"),
            (rendered.replace("ref: SUP-1\n", ""), "ref must be"),
            ("- not a map\n", "must be a map"),
            ("task: [unclosed\n", "malformed YAML"),
        ):
            with self.subTest(text=text):
                with self.assertRaises(harness.HarnessError) as caught:
                    self.read(text)
                self.assertIn(fragment, str(caught.exception))

    def test_missing_config(self):
        with self.assertRaises(harness.HarnessError):
            harness.read_config(self.root, ["claude"])


class RemovalTest(unittest.TestCase):
    ROOT = Path("/repo/harnesses/support/2026-09-30-SUP-1-login-fails")
    INSIDE = "the working directory is inside the harness: run the command from outside it, such as the tasks repo root"

    HEAD = (
        "harnesses/support/2026-09-30-SUP-1-login-fails\n"
        "task: tasks/support/2026-09-30-SUP-1-login-fails.md\n"
        "launched_at: 2026-09-30\nnotes: 2\nassets: 1\ncommits: 3\nworktrees: 2\n"
    )

    def manifest(self, uncommitted: tuple[str, ...] | None) -> harness.Manifest:
        return harness.Manifest(
            path="harnesses/support/2026-09-30-SUP-1-login-fails",
            task="tasks/support/2026-09-30-SUP-1-login-fails.md",
            launched_at=datetime.date(2026, 9, 30),
            notes=2,
            assets=1,
            commits=3,
            worktrees=2,
            uncommitted=uncommitted,
        )

    def test_manifest_rendered_in_order(self):
        self.assertEqual(harness.render_manifest(self.manifest(())), self.HEAD + "uncommitted: 0")

    def test_manifest_lists_uncommitted_paths(self):
        self.assertEqual(
            harness.render_manifest(self.manifest(("notes/draft.md", "update.md"))),
            self.HEAD + "uncommitted: 2\n- notes/draft.md\n- update.md",
        )

    def test_manifest_with_unreadable_status(self):
        self.assertEqual(harness.render_manifest(self.manifest(None)), self.HEAD + "uncommitted: unknown")

    def test_uncommitted_paths(self):
        lines = ["?? notes/draft.md", " M CLAUDE.md", "", "A  assets/har.txt", "  ", "?? update.md"]
        self.assertEqual(
            harness.uncommitted_paths(lines), ("notes/draft.md", "CLAUDE.md", "assets/har.txt", "update.md")
        )
        self.assertEqual(harness.uncommitted_paths([]), ())

    def test_working_directory_outside_the_harness(self):
        for folder in ("/repo", "/repo/harnesses/support", "/repo/harnesses/support/2026-09-30-SUP-1-login-fails-2"):
            with self.subTest(folder=folder):
                self.assertEqual(harness.removal_problems(Path(folder), self.ROOT, []), [])

    def test_working_directory_at_or_inside_the_harness(self):
        for folder in (self.ROOT, self.ROOT / "notes", self.ROOT / "worktrees" / "app"):
            with self.subTest(folder=folder):
                self.assertEqual(harness.removal_problems(folder, self.ROOT, []), [self.INSIDE])

    def test_uncommitted_paths_never_refuse(self):
        lines = ["?? notes/draft.md", " M CLAUDE.md", "A  assets/har.txt", "?? update.md"]
        self.assertEqual(harness.removal_problems(Path("/repo"), self.ROOT, lines), [])

    def test_unreadable_status(self):
        self.assertEqual(
            harness.removal_problems(self.ROOT / "notes", self.ROOT, None),
            [self.INSIDE, "the state of the harness repository could not be read with git status"],
        )

    CLEAN = worktree.State("worktrees/nakatomi-web", branch="gemba/nakatomi/SUP-1")
    PENDING = worktree.State(
        "worktrees/nakatomi-api", branch="gemba/nakatomi/SUP-1", uncommitted=("a.txt",), unpushed=2
    )
    STRAY = worktree.State("worktrees/stray", kind="not a worktree")

    def test_clean_worktree(self):
        self.assertEqual(harness.removal_problems(Path("/repo"), self.ROOT, [], [self.CLEAN]), [])

    def test_pending_worktree(self):
        self.assertEqual(
            harness.removal_problems(Path("/repo"), self.ROOT, [], [self.CLEAN, self.PENDING]),
            [
                "worktrees/nakatomi-api has 1 uncommitted path: a.txt",
                "worktrees/nakatomi-api has 2 commits not on any remote branch",
            ],
        )

    def test_pending_worktree_forced(self):
        self.assertEqual(harness.removal_problems(Path("/repo"), self.ROOT, [], [self.PENDING], force=True), [])

    def test_orphan_without_unpushed_commits(self):
        orphans = [("nakatomi-web", "gemba/nakatomi/SUP-1", 0)]
        self.assertEqual(harness.removal_problems(Path("/repo"), self.ROOT, [], orphans=orphans), [])

    def test_orphan_with_unpushed_commits(self):
        orphans = [("nakatomi-web", "gemba/nakatomi/SUP-1", 1)]
        self.assertEqual(
            harness.removal_problems(Path("/repo"), self.ROOT, [], orphans=orphans),
            ["branch gemba/nakatomi/SUP-1 of nakatomi-web has 1 commit not on any remote branch and no worktree"],
        )
        self.assertEqual(harness.removal_problems(Path("/repo"), self.ROOT, [], orphans=orphans, force=True), [])

    def test_stray_folder(self):
        self.assertEqual(
            harness.removal_problems(Path("/repo"), self.ROOT, [], [self.STRAY]), ["worktrees/stray is not a worktree"]
        )
        self.assertEqual(harness.removal_problems(Path("/repo"), self.ROOT, [], [self.STRAY], force=True), [])

    def test_force_does_not_cover_the_working_directory(self):
        self.assertEqual(
            harness.removal_problems(self.ROOT, self.ROOT, ["?? notes/draft.md"], [self.PENDING], force=True),
            [self.INSIDE],
        )
        self.assertEqual(
            harness.removal_problems(Path("/repo"), self.ROOT, None, force=True),
            ["the state of the harness repository could not be read with git status"],
        )

    def test_harness_problems_come_first(self):
        orphans = [("nakatomi-web", "gemba/nakatomi/SUP-1", 3)]
        self.assertEqual(
            harness.removal_problems(Path("/repo"), self.ROOT, None, [self.STRAY], orphans),
            [
                "the state of the harness repository could not be read with git status",
                "worktrees/stray is not a worktree",
                "branch gemba/nakatomi/SUP-1 of nakatomi-web has 3 commits not on any remote branch and no worktree",
            ],
        )


class DeleteTreeTest(unittest.TestCase):
    """Scenarios: Read-only files deleted; Path held by another program reported; Worktree path held by another
    program reported (the message both removals share)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self._tmp.name).resolve() / "harness"
        self.read_only = self.folder / ".git" / "objects" / "ab" / "cdef"
        self.held = self.folder / "notes" / "open.md"
        for path in (self.read_only, self.held):
            path.parent.mkdir(parents=True)
            path.write_bytes(b"x")
        self.read_only.chmod(stat.S_IREAD)
        self.calls = []
        self.slept = []

    def tearDown(self):
        if self.read_only.exists():
            self.read_only.chmod(stat.S_IWRITE | stat.S_IREAD)
        self._tmp.cleanup()

    def report(self, options, function, path, error):
        """Call the error handler of rmtree as the running Python does, with `onexc` or with `onerror`."""
        if "onexc" in options:
            options["onexc"](function, str(path), error)
        else:
            options["onerror"](function, str(path), (type(error), error, None))

    def rmtree_read_only_then_held(self, path, **options):
        """A fake rmtree: the first call reports a read-only file, every call reports a held file."""
        self.calls.append(Path(path))
        if len(self.calls) == 1:
            self.report(options, os.unlink, self.read_only, PermissionError(13, "Access is denied"))
        self.report(options, os.unlink, self.held, PermissionError(13, "Access is denied"))

    def test_read_only_file_deleted_and_held_path_reported_after_the_retries(self):
        problem = harness_command.delete_tree(
            self.folder, rmtree=self.rmtree_read_only_then_held, sleep=self.slept.append
        )
        self.assertFalse(self.read_only.exists(), "the read-only bit is cleared and the unlink retried")
        self.assertEqual(self.slept, list(platform.HELD_RETRY_DELAYS))
        self.assertEqual(len(self.calls), 1 + len(platform.HELD_RETRY_DELAYS))
        self.assertIsNotNone(problem)
        assert problem is not None
        self.assertIn("notes/open.md", problem)
        self.assertIn("held by another program", problem)

    def test_held_path_released_during_the_retries(self):
        def rmtree(path, **options):
            self.calls.append(Path(path))
            if len(self.calls) < 3:
                self.report(options, os.unlink, self.held, PermissionError(13, "Access is denied"))

        problem = harness_command.delete_tree(self.folder, rmtree=rmtree, sleep=self.slept.append)
        self.assertIsNone(problem)
        self.assertEqual(self.slept, list(platform.HELD_RETRY_DELAYS[:2]))

    def test_folder_left_because_of_a_held_file_is_not_an_error(self):
        def rmtree(path, **options):
            self.calls.append(Path(path))
            self.report(options, os.unlink, self.held, PermissionError(13, "Access is denied"))
            self.report(options, os.rmdir, self.held.parent, OSError(41, "The directory is not empty"))
            self.report(options, os.rmdir, self.folder, OSError(41, "The directory is not empty"))

        problem = harness_command.delete_tree(self.folder, rmtree=rmtree, sleep=self.slept.append)
        assert problem is not None
        self.assertIn("notes/open.md", problem)
        self.assertNotIn("not empty", problem)

    def test_other_errors_reported_as_they_are(self):
        def rmtree(path, **options):
            self.calls.append(Path(path))
            self.report(options, os.unlink, self.held, OSError(5, "Input/output error"))

        problem = harness_command.delete_tree(self.folder, rmtree=rmtree, sleep=self.slept.append)
        assert problem is not None
        self.assertIn("Input/output error", problem)
        self.assertEqual(self.slept, [])

    def test_real_rmtree_deletes_a_read_only_file(self):
        self.assertIsNone(harness_command.delete_tree(self.folder, sleep=self.slept.append))
        self.assertFalse(self.folder.exists())
        self.assertEqual(self.slept, [])

    def test_removal_message_names_the_cause_and_the_way_to_finish(self):
        left = "notes/open.md is held by another program"
        message = harness.not_removed_completely("harnesses/support/x", left, "gemba harness remove SUP-1 --yes")
        self.assertIn("harnesses/support/x was not removed completely: notes/open.md", message)
        self.assertIn("an IDE window or a terminal open on it is the likely cause", message)
        self.assertIn("run gemba harness remove SUP-1 --yes again to finish it", message)

    def test_worktree_message_shares_the_cause_and_the_way_to_finish(self):
        git_said = "git worktree remove failed: fatal: failed to delete 'worktrees/nakatomi-web': Permission denied"
        self.assertTrue(harness.is_held(git_said))
        self.assertFalse(harness.is_held("git worktree remove failed: fatal: 'x' is not a working tree"))
        self.assertEqual(harness.git_hints(git_said), [harness.HELD_CAUSE])
        message = harness.not_removed("worktrees/nakatomi-web", git_said, "gemba worktree remove nakatomi-web --yes")
        self.assertIn("worktrees/nakatomi-web was not removed: git worktree remove failed", message)
        self.assertIn(harness.HELD_CAUSE, message)
        self.assertIn("run gemba worktree remove nakatomi-web --yes again to finish it", message)


class RenderGuideTest(unittest.TestCase):
    def test_without_a_section(self):
        self.assertEqual(harness.render_guide(GUIDE, None, None), GUIDE)
        self.assertEqual(harness.render_guide(GUIDE, None, "  \n"), GUIDE)

    def test_with_a_workstream_section(self):
        self.assertEqual(
            harness.render_guide(GUIDE, None, "Write for the client.\n"),
            "# Working in this harness\n\nRead `task.md`.\n\n## Your workstream\n\nWrite for the client.\n",
        )

    def test_section_text_kept_verbatim(self):
        text = "Write for the client.\n\n- Name the ticket.\n  - Quote it.\n"
        self.assertTrue(harness.render_guide(GUIDE, None, text).endswith(f"## Your workstream\n\n{text}"))
        self.assertTrue(harness.render_guide(GUIDE, text, None).endswith(f"## Your organization\n\n{text}"))

    def test_with_an_organization_section(self):
        self.assertEqual(
            harness.render_guide(GUIDE, "Open the harness through its workspace.\n", None),
            "# Working in this harness\n\nRead `task.md`.\n\n"
            "## Your organization\n\nOpen the harness through its workspace.\n",
        )

    def test_organization_section_before_the_workstream_section(self):
        self.assertEqual(
            harness.render_guide(GUIDE, "Open the harness through its workspace.", "Write for the client."),
            "# Working in this harness\n\nRead `task.md`.\n\n"
            "## Your organization\n\nOpen the harness through its workspace.\n\n"
            "## Your workstream\n\nWrite for the client.\n",
        )

    def test_blank_organization_text(self):
        self.assertEqual(harness.render_guide(GUIDE, "  \n", None), GUIDE)
        self.assertEqual(
            harness.render_guide(GUIDE, "  \n", "Write for the client."),
            harness.render_guide(GUIDE, None, "Write for the client."),
        )


class GateTest(unittest.TestCase):
    def test_gate_per_type(self):
        expected = {
            ("finding", False): (False, None),
            ("blocker", False): (False, None),
            ("summary", False): (False, None),
            ("decision", False): (False, None),
            ("decision", True): (True, None),
            ("external-action", False): (True, None),
            ("external-action", True): (True, None),
        }
        for (note_type, approval), outcome in expected.items():
            with self.subTest(type=note_type, approval=approval):
                self.assertEqual(
                    (harness.is_gated(note_type, approval), harness.approval_problem(note_type, approval)), outcome
                )

    def test_approval_refused_for_ungated_types(self):
        for note_type in ("finding", "blocker", "summary"):
            with self.subTest(type=note_type):
                self.assertEqual(
                    harness.approval_problem(note_type, True),
                    f"type '{note_type}' takes no approval: --approval is for decision notes",
                )

    def test_every_type_has_a_definition(self):
        self.assertEqual(list(harness.NOTE_TYPES), ["finding", "blocker", "decision", "summary", "external-action"])
        for note_type in harness.NOTE_TYPES.values():
            self.assertTrue(note_type.definition)


class NoteNameTest(unittest.TestCase):
    def test_filename_sorts_in_filing_order(self):
        now = datetime.datetime(2026, 9, 30, 15, 30, 12, 999)
        self.assertEqual(harness.note_filename(now, "login-trace"), "2026-09-30-153012-login-trace.md")

    def test_filed_slug(self):
        self.assertEqual(harness.filed_slug("2026-09-30-153012-login-trace.md"), "login-trace")
        for name in ("login-trace.md", "2026-09-30-1530-login-trace.md", "2026-09-30-153012-Login.md"):
            with self.subTest(name=name):
                self.assertIsNone(harness.filed_slug(name))


class NoteFrontmatterTest(unittest.TestCase):
    PLAIN = harness.NoteFrontmatter("finding", datetime.date(2026, 9, 30), "15:30:12")

    def test_plain_note(self):
        self.assertEqual(
            harness.render_note_frontmatter(self.PLAIN),
            '---\ntype: finding\ndate: 2026-09-30\ntime: "15:30:12"\n---\n',
        )

    def test_gated_note_with_assets(self):
        frontmatter = dataclasses.replace(
            self.PLAIN, type="external-action", approved=False, assets=("assets/1-a.log", "assets/2-b.png")
        )
        self.assertEqual(
            harness.render_note_frontmatter(frontmatter),
            '---\ntype: external-action\ndate: 2026-09-30\ntime: "15:30:12"\napproved: false\n'
            "assets: [assets/1-a.log, assets/2-b.png]\n---\n",
        )

    def test_assets_without_approval_and_resolution_last(self):
        self.assertEqual(
            harness.render_note_frontmatter(dataclasses.replace(self.PLAIN, assets=("assets/1-a.log",))),
            '---\ntype: finding\ndate: 2026-09-30\ntime: "15:30:12"\nassets: [assets/1-a.log]\n---\n',
        )
        resolved = dataclasses.replace(self.PLAIN, type="decision", approved=True, resolved_at="2026-09-30T16:02:45")
        self.assertTrue(
            harness.render_note_frontmatter(resolved).endswith(
                'approved: true\nresolved_at: "2026-09-30T16:02:45"\n---\n'
            )
        )

    def test_rendered_frontmatter_reads_back(self):
        frontmatter = dataclasses.replace(
            self.PLAIN,
            type="external-action",
            approved=True,
            assets=("assets/1-a.log",),
            resolved_at="2026-09-30T16:02:45",
        )
        block, rest = harness.split_note(harness.render_note_frontmatter(frontmatter) + "\nBody\n")
        assert block is not None
        self.assertEqual(harness.parse_note_frontmatter(block), frontmatter)
        self.assertEqual(rest, "\nBody\n")

    def test_split_without_frontmatter(self):
        self.assertEqual(harness.split_note("Body\n"), (None, "Body\n"))
        with self.assertRaises(harness.HarnessError):
            harness.split_note("---\ntype: finding\nBody\n")

    def test_frontmatter_gemba_would_not_write_is_refused(self):
        for block, fragment in (
            ("type: idea\ndate: 2026-09-30\ntime: '15:30:12'", "not a note type"),
            ("type: finding\ndate: 2026-09-30\ntime: 15:30:12", "time must be"),
            ("type: finding\ndate: 2026-09-30\ntime: '15:30:12'\napproved: yes please", "approved must be"),
            ("type: finding\ndate: 2026-09-30\ntime: '15:30:12'\nowner: me", "keys gemba does not write: owner"),
            ("- finding", "must be a map"),
        ):
            with self.subTest(block=block):
                with self.assertRaises(harness.HarnessError) as caught:
                    harness.parse_note_frontmatter(block)
                self.assertIn(fragment, str(caught.exception))

    def test_resolvable(self):
        gated = dataclasses.replace(self.PLAIN, type="external-action", approved=True)
        self.assertIsNone(harness.check_resolvable(gated))
        for frontmatter, fragment in (
            (self.PLAIN, "is not gated"),
            (dataclasses.replace(gated, approved=False), "is not approved"),
            (
                dataclasses.replace(gated, resolved_at="2026-09-30T16:02:45"),
                "is already resolved, at 2026-09-30T16:02:45",
            ),
        ):
            with self.subTest(frontmatter=frontmatter):
                problem = harness.check_resolvable(frontmatter)
                assert problem is not None
                self.assertIn(fragment, problem)


class NoteFilesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        for folder in (harness.NOTES_DIR, harness.ASSETS_DIR):
            (self.root / folder).mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, relative, text="Body\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_draft(self):
        self.assertEqual(harness.check_draft(self.put("notes/login-trace.md"), self.root), [])

    def test_draft_with_a_frontmatter(self):
        path = self.put("notes/login-trace.md", "---\ntype: finding\n---\n\nBody\n")
        self.assertEqual(harness.check_draft(path, self.root), ["is already filed: it starts with a frontmatter"])

    def test_draft_with_a_name_that_is_not_a_slug(self):
        for name in ("Login_Trace.md", "login-trace.txt", "login--trace.md"):
            with self.subTest(name=name):
                problems = harness.check_draft(self.put(f"notes/{name}"), self.root)
                self.assertEqual(len(problems), 1)
                self.assertIn("is not a slug followed by .md", problems[0])

    def test_draft_with_a_reserved_name(self):
        for name in ("aux.md", "com1.md", "nul.md"):
            with self.subTest(name=name):
                problems = harness.check_draft(self.put(f"notes/{name}"), self.root)
                self.assertEqual(
                    problems, ["is named with a slug reserved on Windows, where it could not be a file name"]
                )
        problems = harness.check_draft(self.put("drafts/aux.md"), self.root)
        self.assertEqual(len(problems), 2, "reported together with the other problems of the call")

    def test_draft_outside_notes(self):
        for relative in ("login-trace.md", "notes/drafts/login-trace.md", "assets/login-trace.md"):
            with self.subTest(relative=relative):
                problems = harness.check_draft(self.put(relative), self.root)
                self.assertEqual(len(problems), 1)
                self.assertIn("is not directly under notes/", problems[0])

    def test_missing_draft(self):
        self.assertEqual(harness.check_draft(self.root / "notes" / "login-trace.md", self.root), ["does not exist"])

    def test_assets(self):
        self.put("assets/1759350491-console.log")
        self.put("assets/screens/1759350491-login.png")
        self.put("1759350491-console.log")
        relative, problems = harness.check_assets(
            [
                "assets/1759350491-console.log",
                "assets/screens/1759350491-login.png",
                "1759350491-console.log",
                "assets/../1759350491-console.log",
                "assets/1759350491-missing.log",
                "assets",
            ],
            self.root,
        )
        self.assertEqual(relative, ["assets/1759350491-console.log", "assets/screens/1759350491-login.png"])
        self.assertEqual(
            problems,
            [
                "asset 1759350491-console.log is not under assets/ of the harness",
                "asset assets/../1759350491-console.log is not under assets/ of the harness",
                "asset assets/1759350491-missing.log does not exist",
                "asset assets is not under assets/ of the harness",
            ],
        )

    def test_filed_note(self):
        name = "notes/2026-09-30-153012-push-fix.md"
        self.assertEqual(harness.check_filed(self.put(name, "---\ntype: decision\n---\n"), self.root), [])
        self.assertEqual(
            harness.check_filed(self.put(name, "Body\n"), self.root), ["is not filed: it has no frontmatter"]
        )
        problems = harness.check_filed(self.put("notes/push-fix.md", "---\n---\n"), self.root)
        self.assertEqual(problems, ["is not named as a filed note (YYYY-MM-DD-HHMMSS-<slug>.md)"])


if __name__ == "__main__":
    unittest.main()
