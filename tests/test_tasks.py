"""Unit tests for reading task files: every refusal, the display title and the description."""

import datetime
import tempfile
import textwrap
import unittest
from pathlib import Path

from gemba import metadata, tasks

NAME = "2026-09-30-SUP-1-login-fails-on-safari.md"

VALID = """\
---
status: open
ref: SUP-1
updated_at: 2026-09-30
metadata:
  client: acme
  project: [checkout, landing]
---

Login fails on Safari for the checkout app

## Updates
"""


class ReadTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.folder = self.root / tasks.TASKS_DIR / "support"
        self.folder.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, text, name=NAME):
        path = self.folder / name
        path.write_text(textwrap.dedent(text), encoding="utf-8")
        return path

    def read(self, text, name=NAME):
        return tasks.read(self.write(text, name), self.root, "support", archived=False)

    def assertRefused(self, text, message, name=NAME):
        with self.assertRaises(tasks.TaskError) as caught:
            self.read(text, name)
        self.assertEqual(str(caught.exception), message)


class ReadTest(ReadTestCase):
    def test_valid_file(self):
        task = self.read(VALID)
        self.assertEqual(
            task,
            tasks.Task(
                path=f"tasks/support/{NAME}",
                owner=None,
                workstream="support",
                archived=False,
                ref="SUP-1",
                date=datetime.date(2026, 9, 30),
                title="Login fails on safari",
                status="open",
                updated_at=datetime.date(2026, 9, 30),
                done_at=None,
                metadata={"client": "acme", "project": ["checkout", "landing"]},
                description="Login fails on Safari for the checkout app",
            ),
        )

    def test_done_at_read(self):
        text = VALID.replace("status: open", "status: done").replace(
            "updated_at: 2026-09-30", "updated_at: 2026-09-30\ndone_at: 2026-09-30"
        )
        self.assertEqual(self.read(text).done_at, datetime.date(2026, 9, 30))

    def test_quoted_iso_date_accepted(self):
        self.assertEqual(self.read(VALID.replace("2026-09-30", '"2026-09-30"')).updated_at, datetime.date(2026, 9, 30))

    def test_windows_line_endings(self):
        path = self.folder / NAME
        path.write_bytes(VALID.replace("\n", "\r\n").encode("utf-8"))
        task = tasks.read(path, self.root, "support", archived=False)
        self.assertEqual(task.description, "Login fails on Safari for the checkout app")

    def test_filename_pattern(self):
        for name in (
            "notes.md",
            "2026-09-30-login-fails.md",
            "2026-09-30-SUP-01-login.md",
            "2026-09-30-SUP-1-Login.md",
        ):
            with self.subTest(name=name):
                self.assertRefused(VALID, "filename does not match YYYY-MM-DD-<ref>-<slug>.md", name=name)

    def test_ref_with_initials(self):
        text = VALID.replace("ref: SUP-1", "ref: MR-SUP-1")
        task = self.read(text, name="2026-09-30-MR-SUP-1-login-fails-on-safari.md")
        self.assertEqual((task.ref, task.title), ("MR-SUP-1", "Login fails on safari"))
        for name in ("2026-09-30-mr-SUP-1-login.md", "2026-09-30-MR-SUP-01-login.md", "2026-09-30-A-B-C-1-login.md"):
            with self.subTest(name=name):
                self.assertRefused(text, "filename does not match YYYY-MM-DD-<ref>-<slug>.md", name=name)

    def test_owner_given_by_the_caller(self):
        path = self.write(VALID)
        self.assertIsNone(tasks.read(path, self.root, "support", archived=False).owner)
        self.assertEqual(tasks.read(path, self.root, "support", archived=False, owner="manuel").owner, "manuel")

    def test_filename_date(self):
        self.assertRefused(
            VALID, "filename date '2026-02-30' is not a valid date", name="2026-02-30-SUP-1-login-fails-on-safari.md"
        )

    def test_not_utf8(self):
        path = self.folder / NAME
        path.write_bytes(b"---\nstatus: \xff\n---\n")
        with self.assertRaises(tasks.TaskError) as caught:
            tasks.read(path, self.root, "support", archived=False)
        self.assertEqual(str(caught.exception), "the file is not UTF-8 text")

    def test_unreadable(self):
        path = self.folder / NAME
        path.mkdir()
        with self.assertRaises(tasks.TaskError) as caught:
            tasks.read(path, self.root, "support", archived=False)
        self.assertIn("the file cannot be read", str(caught.exception))

    def test_no_frontmatter(self):
        self.assertRefused("Login fails\n", "no frontmatter: the file does not start with a --- line")

    def test_empty_file(self):
        self.assertRefused("", "no frontmatter: the file does not start with a --- line")

    def test_frontmatter_not_closed(self):
        self.assertRefused("---\nstatus: open\n\nLogin fails\n", "frontmatter is not closed by a --- line")

    def test_frontmatter_not_yaml(self):
        text = VALID.replace("ref: SUP-1", "ref: SUP-1: urgent")
        self.assertRefused(text, "frontmatter is not valid YAML (line 3): mapping values are not allowed here")

    def test_frontmatter_impossible_date(self):
        # The message quotes the ValueError of the standard library, whose wording
        # differs between Python versions, so the test raises the same error itself.
        text = VALID.replace("updated_at: 2026-09-30", "updated_at: 2026-13-01")
        with self.assertRaises(ValueError) as impossible:
            datetime.date(2026, 13, 1)
        self.assertRefused(text, f"frontmatter is not valid YAML: {impossible.exception}")

    def test_frontmatter_not_a_map(self):
        for block in ("- open\n- SUP-1\n", "just text\n", ""):
            with self.subTest(block=block):
                self.assertRefused(f"---\n{block}---\n", "frontmatter must be a map")

    def test_status_missing(self):
        self.assertRefused(
            VALID.replace("status: open\n", ""), "status is missing (allowed: open, in-progress, blocked, done)"
        )

    def test_invalid_status(self):
        for written, shown in (("closed", "'closed'"), ("3", "3"), ("yes", "true")):
            with self.subTest(status=written):
                self.assertRefused(
                    VALID.replace("status: open", f"status: {written}"),
                    f"invalid status {shown} (allowed: open, in-progress, blocked, done)",
                )

    def test_ref_missing(self):
        self.assertRefused(VALID.replace("ref: SUP-1\n", ""), "ref is missing (the filename says 'SUP-1')")

    def test_ref_mismatch(self):
        self.assertRefused(
            VALID.replace("ref: SUP-1", "ref: SUP-4"),
            "ref 'SUP-4' in the frontmatter does not match 'SUP-1' in the filename",
        )

    def test_updated_at_missing(self):
        self.assertRefused(VALID.replace("updated_at: 2026-09-30\n", ""), "updated_at is missing")

    def test_updated_at_not_iso(self):
        for written, shown in (
            ("yesterday", "'yesterday'"),
            ('"2026-9-30"', "'2026-9-30'"),
            ("2026-09-30 10:00:00", "2026-09-30 10:00:00"),
        ):
            with self.subTest(updated_at=written):
                self.assertRefused(
                    VALID.replace("updated_at: 2026-09-30", f"updated_at: {written}"),
                    f"updated_at must be an ISO date (YYYY-MM-DD), not {shown}",
                )

    def test_done_at_not_iso(self):
        self.assertRefused(
            VALID.replace("updated_at: 2026-09-30", "updated_at: 2026-09-30\ndone_at: today"),
            "done_at must be an ISO date (YYYY-MM-DD), not 'today'",
        )

    def test_metadata_missing(self):
        text = VALID.replace("metadata:\n  client: acme\n  project: [checkout, landing]\n", "")
        self.assertRefused(text, "metadata is missing (it must be a map, {} when empty)")

    def test_metadata_not_a_map(self):
        for block, kind in (("[acme, checkout]", "a list"), ("acme", "a scalar"), ("null", "null")):
            with self.subTest(metadata=block):
                text = VALID.replace("metadata:\n  client: acme\n  project: [checkout, landing]", f"metadata: {block}")
                self.assertRefused(text, f"metadata must be a map, not {kind}")

    def test_metadata_key_not_a_string(self):
        self.assertRefused(VALID.replace("client: acme", "3: acme"), "metadata key 3 must be a string")

    def test_metadata_nested_value(self):
        for value in ("{name: Ana}", "[[checkout], [landing]]"):
            with self.subTest(value=value):
                self.assertRefused(
                    VALID.replace("client: acme", f"client: {value}"),
                    "metadata value of 'client' must be a scalar or a list of scalars",
                )

    def test_metadata_keys_not_checked_against_a_schema(self):
        self.assertEqual(self.read(VALID.replace("client: acme", "ticket_id: PROD-1")).metadata["ticket_id"], "PROD-1")


class ScanTest(ReadTestCase):
    def put(self, relative, text=VALID):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_unknown_folder_reported(self):
        self.put(f"tasks/legacy/{NAME}")
        self.put("tasks/notes.txt", "loose notes")
        self.put("tasks/.hidden/whatever.md")
        found, problems = tasks.scan(self.root, ["support"], False, configured=["support", "operations"])
        self.assertEqual(found, [])
        self.assertEqual(
            problems,
            [
                tasks.Problem("tasks/legacy", "folder is not a workstream of the config; its files are not listed"),
                tasks.Problem("tasks/notes.txt", "entry is not a workstream folder of the config"),
            ],
        )

    def test_unknown_folder_not_reported_without_the_catalogue(self):
        self.put(f"tasks/legacy/{NAME}")
        self.assertEqual(tasks.scan(self.root, ["support"], False), ([], []))

    def test_ignored_files(self):
        self.put(f"tasks/support/{NAME}")
        for name in (".gitkeep", ".draft.md", "notes.txt", "README"):
            self.put(f"tasks/support/{name}", "not a task")
        (self.folder / "drafts.md").mkdir()
        found, problems = tasks.scan(self.root, ["support"], False, configured=["support"])
        self.assertEqual([task.path for task in found], [f"tasks/support/{NAME}"])
        self.assertEqual(problems, [])

    def test_invalid_file_reported(self):
        self.put(f"tasks/support/{NAME}")
        self.put("tasks/support/2026-09-29-SUP-2-broken.md", "no frontmatter\n")
        found, problems = tasks.scan(self.root, ["support"], False)
        self.assertEqual([task.ref for task in found], ["SUP-1"])
        self.assertEqual(
            problems,
            [
                tasks.Problem(
                    "tasks/support/2026-09-29-SUP-2-broken.md",
                    "no frontmatter: the file does not start with a --- line",
                )
            ],
        )

    def test_missing_workstream_folder(self):
        self.put(f"tasks/support/{NAME}")
        found, problems = tasks.scan(self.root, ["support", "estimates"], True, configured=["support", "estimates"])
        self.assertEqual([task.ref for task in found], ["SUP-1"])
        self.assertEqual(problems, [])

    def test_missing_tasks_folder(self):
        self.folder.rmdir()
        (self.root / tasks.TASKS_DIR).rmdir()
        self.assertEqual(tasks.scan(self.root, ["support"], True, configured=["support"]), ([], []))

    def test_archive_only_on_request(self):
        self.put(f"tasks/support/{NAME}")
        self.put(
            "tasks/support/archive/2026-08-01-SUP-9-old-issue.md",
            VALID.replace("SUP-1", "SUP-9").replace("status: open", "status: done"),
        )
        active, _ = tasks.scan(self.root, ["support"], False)
        self.assertEqual([(task.ref, task.archived) for task in active], [("SUP-1", False)])
        everything, _ = tasks.scan(self.root, ["support"], True)
        self.assertEqual([(task.ref, task.archived) for task in everything], [("SUP-9", True), ("SUP-1", False)])

    def test_order_by_date_workstream_and_filename(self):
        ops = VALID.replace("SUP-", "OPS-")
        self.put("tasks/support/2026-09-10-SUP-1-a.md")
        self.put("tasks/operations/2026-09-10-OPS-3-b.md", ops.replace("OPS-1", "OPS-3"))
        self.put("tasks/operations/2026-09-10-OPS-2-c.md", ops.replace("OPS-1", "OPS-2"))
        self.put("tasks/operations/2026-09-05-OPS-1-d.md", ops)
        found, _ = tasks.scan(self.root, ["support", "operations"], False)
        self.assertEqual([task.ref for task in found], ["OPS-1", "OPS-2", "OPS-3", "SUP-1"])


class NextRefTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def touch(self, *paths):
        for relative in paths:
            path = self.root / tasks.TASKS_DIR / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    def test_no_task_yet(self):
        self.assertEqual(tasks.next_ref(self.root, "SUP"), "SUP-1")
        self.assertEqual(tasks.next_ref(self.root, "SUP", "MR"), "MR-SUP-1")

    def test_bare_prefix_and_initials_counted_apart(self):
        self.touch(
            "support/2026-09-01-SUP-7-a.md",
            "manuel/support/archive/2026-09-02-MR-SUP-2-b.md",
            "ana/support/2026-09-03-AG-SUP-5-c.md",
            "ana/operations/2026-09-04-AG-OPS-9-d.md",
        )
        self.assertEqual(tasks.next_ref(self.root, "SUP"), "SUP-8")
        self.assertEqual(tasks.next_ref(self.root, "SUP", "MR"), "MR-SUP-3")
        self.assertEqual(tasks.next_ref(self.root, "SUP", "AG"), "AG-SUP-6")
        self.assertEqual(tasks.next_ref(self.root, "OPS", "MR"), "MR-OPS-1")

    def test_initials_never_match_a_prefix(self):
        # A workstream whose prefix is another member's initials keeps a counter of its own.
        self.touch("manuel/research/2026-09-01-MR-4-a.md", "ana/support/2026-09-02-AG-MR-6-b.md")
        self.assertEqual(tasks.next_ref(self.root, "MR"), "MR-5")
        self.assertEqual(tasks.next_ref(self.root, "MR", "AG"), "AG-MR-7")
        self.assertEqual(tasks.next_ref(self.root, "MR", "MR"), "MR-MR-1")


class TeamScanTest(ReadTestCase):
    put = ScanTest.put
    MEMBER_NAME = "2026-09-30-MR-SUP-1-login-fails-on-safari.md"
    MEMBER_TASK = VALID.replace("ref: SUP-1", "ref: MR-SUP-1")

    def test_member_folders_scanned_with_their_owner(self):
        self.put(f"tasks/manuel/support/{self.MEMBER_NAME}", self.MEMBER_TASK)
        ana = "2026-09-29-AG-OPS-1-renew-domain.md"
        self.put(f"tasks/ana/operations/archive/{ana}", VALID.replace("ref: SUP-1", "ref: AG-OPS-1"))
        found, problems = tasks.scan(self.root, ["support", "operations"], False, owners=["manuel", "ana"])
        self.assertEqual([(task.ref, task.owner) for task in found], [("MR-SUP-1", "manuel")])
        self.assertEqual(problems, [])
        found, _problems = tasks.scan(self.root, ["support", "operations"], True, owners=["manuel", "ana"])
        self.assertEqual(
            [(task.path, task.owner, task.archived) for task in found],
            [
                (f"tasks/ana/operations/archive/{ana}", "ana", True),
                (f"tasks/manuel/support/{self.MEMBER_NAME}", "manuel", False),
            ],
        )

    def test_only_the_owners_given_are_scanned(self):
        self.put(f"tasks/manuel/support/{self.MEMBER_NAME}", self.MEMBER_TASK)
        self.put("tasks/ana/support/2026-09-29-AG-SUP-2-broken.md", "no frontmatter\n")
        found, problems = tasks.scan(self.root, ["support"], False, owners=["manuel"])
        self.assertEqual([task.ref for task in found], ["MR-SUP-1"])
        self.assertEqual(problems, [])

    def test_strays_of_a_team(self):
        self.put(f"tasks/bob/support/{self.MEMBER_NAME}", self.MEMBER_TASK)
        self.put("tasks/notes.txt", "loose notes")
        self.put(f"tasks/support/{NAME}")
        self.put(f"tasks/ana/legacy/{NAME}")
        self.put("tasks/ana/todo.txt", "loose notes")
        self.put("tasks/ana/.hidden/whatever.md")
        self.put("tasks/.hidden/whatever.md")
        found, problems = tasks.scan(self.root, ["support"], False, configured=["support"], owners=["manuel", "ana"])
        self.assertEqual(found, [])
        self.assertEqual(
            problems,
            [
                tasks.Problem("tasks/ana/legacy", "folder is not a workstream of the config; its files are not listed"),
                tasks.Problem("tasks/ana/todo.txt", "entry is not a workstream folder of the config"),
                tasks.Problem("tasks/bob", "folder is not a member of the team; its files are not listed"),
                tasks.Problem("tasks/notes.txt", "entry is not a member folder of the team"),
                tasks.Problem("tasks/support", "folder is not a member of the team; its files are not listed"),
            ],
        )

    def test_found_by_ref_in_a_member_folder(self):
        self.put(f"tasks/ana/support/archive/{self.MEMBER_NAME}", self.MEMBER_TASK)
        task = tasks.find_by_ref(self.root, ["support"], "MR-SUP-1", ["manuel", "ana"])
        assert task is not None
        self.assertEqual((task.owner, task.archived), ("ana", True))
        self.assertIsNone(tasks.find_by_ref(self.root, ["support"], "MR-SUP-1"))

    def test_owner_of_a_task_path(self):
        self.assertEqual(tasks.owner_of(f"tasks/ana/support/archive/{self.MEMBER_NAME}"), "ana")

    def test_archive_destination_in_the_folder_of_the_owner(self):
        path = f"tasks/ana/support/{self.MEMBER_NAME}"
        self.put(path, self.MEMBER_TASK)
        task = tasks.read(self.root / path, self.root, "support", False, "ana")
        self.assertEqual(str(tasks.archive_destination(task)), f"tasks/ana/support/archive/{self.MEMBER_NAME}")


class FindByRefTest(ReadTestCase):
    put = ScanTest.put

    def test_found_in_the_archive(self):
        self.put(f"tasks/support/archive/{NAME}")
        task = tasks.find_by_ref(self.root, ["support", "operations"], "SUP-1")
        assert task is not None
        self.assertEqual((task.path, task.archived), (f"tasks/support/archive/{NAME}", True))

    def test_found_in_another_workstream_folder(self):
        self.put(f"tasks/operations/{NAME}")
        task = tasks.find_by_ref(self.root, ["support", "operations"], "SUP-1")
        assert task is not None
        self.assertEqual(task.workstream, "operations")

    def test_not_found(self):
        self.put(f"tasks/support/{NAME}")
        self.assertIsNone(tasks.find_by_ref(self.root, ["support"], "SUP-2"))
        self.assertIsNone(tasks.find_by_ref(self.root, ["support"], "SUP-10"))

    def test_held_by_several_tasks(self):
        self.put(f"tasks/support/{NAME}")
        self.put(f"tasks/support/archive/{NAME}")
        with self.assertRaises(tasks.TaskError) as caught:
            tasks.find_by_ref(self.root, ["support"], "SUP-1")
        self.assertIn("ref 'SUP-1' is held by several tasks", str(caught.exception))


class TransitionTest(unittest.TestCase):
    DAY = datetime.date(2026, 10, 3)
    METADATA: dict[str, object] = {"client": "acme", "project": ["checkout", "landing"]}

    def task(self, status, updated_at="2026-10-01", done_at=None, body="\nLogin fails\n\n## Updates\n"):
        done = f"done_at: {done_at}\n" if done_at else ""
        return (
            f"---\nstatus: {status}\nref: SUP-1\nupdated_at: {updated_at}\n{done}"
            f"metadata:\n  client: acme\n  project: [checkout, landing]\n---\n{body}"
        )

    def test_each_destination_from_each_source(self):
        for source in tasks.STATUSES:
            for destination in tasks.STATUSES:
                if source == destination:
                    continue
                with self.subTest(source=source, destination=destination):
                    done_at = "2026-10-01" if source == "done" else None
                    after, moved = tasks.transition(self.task(source, done_at=done_at), destination, self.DAY)
                    expected_done_at = "2026-10-03" if destination == "done" else None
                    self.assertEqual(after, self.task(destination, "2026-10-03", expected_done_at))
                    self.assertEqual(
                        moved,
                        tasks.Transition(
                            source,
                            destination,
                            datetime.date(2026, 10, 1),
                            self.DAY,
                            self.DAY if destination == "done" else None,
                            source == "done",
                        ),
                    )
                    self.assertTrue(moved.changed)

    def test_done_at_set_before_metadata(self):
        after, moved = tasks.transition(self.task("in-progress"), "done", self.DAY)
        self.assertIn("\nupdated_at: 2026-10-03\ndone_at: 2026-10-03\nmetadata:\n", after)
        self.assertEqual((moved.done_at, moved.done_at_removed), (self.DAY, False))

    def test_done_at_removed_on_leaving_done(self):
        after, moved = tasks.transition(self.task("done", done_at="2026-10-01"), "open", self.DAY)
        self.assertNotIn("done_at", after)
        self.assertEqual((moved.done_at, moved.done_at_removed), (None, True))

    def test_fixed_key_order_with_and_without_done_at(self):
        shuffled = "---\nmetadata: {}\nupdated_at: 2026-10-01\nref: SUP-1\nstatus: blocked\n---\n\n## Updates\n"
        after, _moved = tasks.transition(shuffled, "done", self.DAY)
        self.assertEqual(
            after,
            "---\nstatus: done\nref: SUP-1\nupdated_at: 2026-10-03\ndone_at: 2026-10-03\nmetadata: {}\n---\n"
            "\n## Updates\n",
        )
        after, _moved = tasks.transition(after, "in-progress", self.DAY)
        self.assertEqual(
            after, "---\nstatus: in-progress\nref: SUP-1\nupdated_at: 2026-10-03\nmetadata: {}\n---\n\n## Updates\n"
        )

    def test_same_status_returns_the_text_unchanged(self):
        for status in tasks.STATUSES:
            with self.subTest(status=status):
                before = self.task(status, done_at="2026-10-01" if status == "done" else None)
                after, moved = tasks.transition(before, status, self.DAY)
                self.assertEqual(after, before)
                self.assertFalse(moved.changed)
                self.assertEqual(moved.new_updated_at, datetime.date(2026, 10, 1))
                self.assertIsNone(moved.done_at)
                self.assertFalse(moved.done_at_removed)

    def test_updated_at_kept_when_later_than_the_day(self):
        after, moved = tasks.transition(self.task("in-progress", updated_at="2026-10-05"), "done", self.DAY)
        self.assertEqual(after, self.task("done", "2026-10-05", "2026-10-03"))
        self.assertEqual((moved.old_updated_at, moved.new_updated_at), (datetime.date(2026, 10, 5),) * 2)

    def test_unknown_status_refused(self):
        with self.assertRaises(tasks.TaskError) as caught:
            tasks.transition(self.task("open"), "closed", self.DAY)
        self.assertEqual(str(caught.exception), "invalid status 'closed' (allowed: open, in-progress, blocked, done)")

    def test_body_kept_byte_for_byte(self):
        body = "\nLogin fails\r\n\n  - trace:   kept  \n\n## Updates\n\n### 2026-09-30\n\n- Nothing yet.\n"
        after, _moved = tasks.transition(self.task("blocked", body=body), "done", self.DAY)
        self.assertTrue(after.endswith(f"\n---\n{body}"))
        self.assertEqual(tasks.split(after)[1], body)

    def test_windows_line_endings_of_the_body_kept(self):
        before = (
            "---\r\nstatus: open\r\nref: SUP-1\r\nupdated_at: 2026-09-30\r\nmetadata: {}\r\n---\r\n\r\n## Updates\r\n"
        )
        after, _moved = tasks.transition(before, "blocked", self.DAY)
        self.assertEqual(
            after, "---\nstatus: blocked\nref: SUP-1\nupdated_at: 2026-10-03\nmetadata: {}\n---\n\r\n## Updates\r\n"
        )


class SetMetadataTest(unittest.TestCase):
    def test_only_the_metadata_changes(self):
        body = "\nLogin fails\n\nTicket: https://example.invalid/t/1\n\n## Updates\n\n### 2026-09-30\n\n- A\n"
        text = (
            "---\nstatus: done\nref: SUP-1\nupdated_at: 2026-10-01\ndone_at: 2026-10-01\n"
            "metadata:\n  hours: 3\n  project: [checkout, landing]\n---\n" + body
        )
        values = {"hours": 5, "project": ["checkout", "landing"], "invoiced": datetime.date(2026, 10, 3)}
        self.assertEqual(
            tasks.set_metadata(text, values),
            "---\nstatus: done\nref: SUP-1\nupdated_at: 2026-10-01\ndone_at: 2026-10-01\n"
            "metadata:\n  hours: 5\n  project: [checkout, landing]\n  invoiced: 2026-10-03\n---\n" + body,
        )

    def test_frontmatter_in_the_fixed_key_order(self):
        text = "---\nmetadata: {}\nupdated_at: 2026-09-30\nref: SUP-1\nstatus: open\n---\n\n## Updates\n"
        self.assertEqual(
            tasks.set_metadata(text, {"client": "no"}),
            "---\nstatus: open\nref: SUP-1\nupdated_at: 2026-09-30\nmetadata:\n  client: 'no'\n---\n\n## Updates\n",
        )

    def test_windows_line_endings_of_the_body_kept(self):
        body = "\r\nLogin fails\r\n\r\n## Updates\r\n\r\n### 2026-09-30\r\n\r\n- A\r\n"
        text = "---\r\nstatus: open\r\nref: SUP-1\r\nupdated_at: 2026-09-30\r\nmetadata: {}\r\n---\r\n" + body
        self.assertEqual(
            tasks.set_metadata(text, {"hours": 1}),
            "---\nstatus: open\nref: SUP-1\nupdated_at: 2026-09-30\nmetadata:\n  hours: 1\n---\n" + body,
        )


class ArchiveTest(unittest.TestCase):
    def task(self, path=f"tasks/support/{NAME}", archived=False, status="done"):
        return tasks.Task(
            path=path,
            owner=None,
            workstream="support",
            archived=archived,
            ref="SUP-1",
            date=datetime.date(2026, 9, 30),
            title="Login fails on safari",
            status=status,
            updated_at=datetime.date(2026, 10, 1),
            done_at=None,
            metadata={},
            description=None,
        )

    def test_destination_under_the_archive_of_the_workstream(self):
        self.assertEqual(str(tasks.archive_destination(self.task())), f"tasks/support/archive/{NAME}")

    def test_any_status_archived(self):
        for status in tasks.STATUSES:
            with self.subTest(status=status):
                self.assertIsNone(tasks.archive_problem(self.task(status=status), None, False))

    def test_already_archived_refused(self):
        task = self.task(path=f"tasks/support/archive/{NAME}", archived=True)
        self.assertEqual(
            tasks.archive_problem(task, None, False), f"is already archived (tasks/support/archive/{NAME})"
        )

    def test_task_with_a_harness_refused(self):
        folder = "harnesses/support/2026-09-30-SUP-1-login-fails-on-safari"
        self.assertEqual(
            tasks.archive_problem(self.task(), folder, False),
            f"has a harness at {folder}: remove it first with gemba harness remove SUP-1",
        )

    def test_existing_destination_refused(self):
        self.assertEqual(
            tasks.archive_problem(self.task(), None, True),
            f"cannot move to tasks/support/archive/{NAME}: a file is already there",
        )


class StartTest(unittest.TestCase):
    TODAY = datetime.date(2026, 10, 2)

    def test_rendered_file_differs_only_in_the_two_values(self):
        metadata: dict[str, object] = {"client": "acme", "project": ["checkout", "landing"], "hours": None}
        before = tasks.render("open", "SUP-1", datetime.date(2026, 9, 30), metadata, "Login fails")
        after, moved = tasks.start(before, self.TODAY)
        self.assertTrue(moved.changed)
        self.assertEqual(
            after,
            tasks.render("in-progress", "SUP-1", self.TODAY, metadata, "Login fails"),
        )
        self.assertEqual(
            [line for line in after.split("\n") if line not in before.split("\n")],
            ["status: in-progress", "updated_at: 2026-10-02"],
        )

    def test_body_kept_byte_for_byte(self):
        body = "\nLogin fails\r\n\n  - trace:   kept  \n\n## Updates\n\n### 2026-09-30\n\nNothing yet.\n"
        before = f"---\nstatus: open\nref: SUP-1\nupdated_at: 2026-09-30\nmetadata: {{}}\n---\n{body}"
        after, _moved = tasks.start(before, self.TODAY)
        self.assertEqual(
            after, f"---\nstatus: in-progress\nref: SUP-1\nupdated_at: 2026-10-02\nmetadata: {{}}\n---\n{body}"
        )

    def test_frontmatter_written_in_the_fixed_key_order(self):
        before = "---\nref: SUP-1\nmetadata: {}\nupdated_at: 2026-09-30\nstatus: open\n---\n\n## Updates\n"
        after, _moved = tasks.start(before, self.TODAY)
        self.assertEqual(
            after, "---\nstatus: in-progress\nref: SUP-1\nupdated_at: 2026-10-02\nmetadata: {}\n---\n\n## Updates\n"
        )

    def test_updated_at_never_moves_backwards(self):
        before = tasks.render("open", "SUP-1", datetime.date(2026, 10, 5), {})
        after, moved = tasks.start(before, self.TODAY)
        self.assertTrue(moved.changed)
        self.assertEqual(after, tasks.render("in-progress", "SUP-1", datetime.date(2026, 10, 5), {}))

    def test_only_open_moves(self):
        for status in ("in-progress", "blocked", "done"):
            with self.subTest(status=status):
                before = tasks.render(status, "SUP-1", datetime.date(2026, 9, 30), {})
                after, moved = tasks.start(before, self.TODAY)
                self.assertEqual(after, before)
                self.assertFalse(moved.changed)
                self.assertEqual((moved.old_status, moved.new_status), (status, status))


class UpdatesProblemTest(unittest.TestCase):
    def test_valid_section(self):
        body = "\nLogin fails\n\n## Updates\n\n### 2026-09-30\n\n- Reproduced\n\n### 2026-10-01\n\n- Traced\n"
        self.assertIsNone(tasks.updates_problem(body))
        self.assertIsNone(tasks.updates_problem("\n## Updates\n"))

    def test_lines_under_a_date_heading_not_checked(self):
        body = "\n## Updates\n\n### 2026-09-30\n\nFree text, # a hash, #### a deeper heading\n"
        self.assertIsNone(tasks.updates_problem(body))

    def test_heading_missing(self):
        self.assertEqual(tasks.updates_problem("\nLogin fails\n"), "has no '## Updates' section")

    def test_heading_repeated(self):
        problem = tasks.updates_problem("\n## Updates\n\n### 2026-09-30\n\n- Reproduced\n\n## Updates\n")
        self.assertIn("holds '## Updates' more than once", str(problem))

    def test_section_after_the_updates(self):
        problem = tasks.updates_problem("\n## Updates\n\n## Links\n\n- https://example.invalid\n")
        self.assertIn("has '## Links' after '## Updates', which must be the last section", str(problem))

    def test_heading_that_is_not_a_date(self):
        for heading in ("### Monday", "### 2026-13-01", "### 2026-10-01 morning"):
            with self.subTest(heading=heading):
                problem = tasks.updates_problem(f"\n## Updates\n\n{heading}\n\n- Reproduced\n")
                self.assertIn(f"has '{heading}' under '## Updates', which is not a date heading", str(problem))

    def test_dates_out_of_order(self):
        problem = tasks.updates_problem("\n## Updates\n\n### 2026-10-02\n\n- A\n\n### 2026-10-01\n\n- B\n")
        self.assertIn("has '### 2026-10-01' under '## Updates', which follows '### 2026-10-02'", str(problem))
        self.assertIn("strictly increasing", str(problem))

    def test_date_repeated(self):
        problem = tasks.updates_problem("\n## Updates\n\n### 2026-10-01\n\n- A\n\n### 2026-10-01\n\n- B\n")
        self.assertIn("has '### 2026-10-01' under '## Updates', which repeats a date", str(problem))


class ParseBulletsTest(unittest.TestCase):
    def test_bullets_with_a_continuation_line(self):
        text = "\n\n- Reproduced the failure\n  on Safari 17.\n- Traced it to the cookie.\n\n"
        self.assertEqual(
            tasks.parse_bullets(text),
            (["- Reproduced the failure", "  on Safari 17.", "- Traced it to the cookie."], []),
        )

    def test_windows_line_endings_dropped(self):
        self.assertEqual(tasks.parse_bullets("- One\r\n- Two\r\n"), (["- One", "- Two"], []))

    def test_non_bullet_lines(self):
        bullets, problems = tasks.parse_bullets("- Reproduced\nA paragraph.\n- Traced\n # heading\n")
        self.assertEqual(bullets, [])
        self.assertEqual(problems, ["lines 2, 4 are neither a '- ' bullet nor a continuation indented by two spaces"])

    def test_continuation_before_any_bullet(self):
        _bullets, problems = tasks.parse_bullets("  indented\n- Reproduced\n")
        self.assertEqual(problems, ["line 1 is neither a '- ' bullet nor a continuation indented by two spaces"])

    def test_empty_draft(self):
        for text in ("", "\n\n  \n"):
            with self.subTest(text=text):
                self.assertEqual(
                    tasks.parse_bullets(text), ([], ["holds no bullet: write each one on a line starting with '- '"])
                )

    def test_paragraph_only(self):
        _bullets, problems = tasks.parse_bullets("Reproduced the failure.\n")
        self.assertEqual(len(problems), 2)


class RecordTest(unittest.TestCase):
    CREATED = datetime.date(2026, 9, 30)
    TODAY = datetime.date(2026, 10, 3)
    FRONTMATTER = "---\nstatus: in-progress\nref: SUP-1\nupdated_at: {}\nmetadata: {{}}\n---\n"

    def task(self, body, updated_at="2026-09-30"):
        return self.FRONTMATTER.format(updated_at) + body

    def record(self, text, day, bullets=("- Done",)):
        return tasks.record(text, self.CREATED, self.TODAY, datetime.date.fromisoformat(day), list(bullets))

    def test_first_subsection(self):
        text, previous, updated_at = self.record(self.task("\nLogin fails\n\n## Updates\n"), "2026-10-01")
        self.assertEqual(
            text, self.task("\nLogin fails\n\n## Updates\n\n### 2026-10-01\n\n- Done\n", updated_at="2026-10-01")
        )
        self.assertEqual((previous, updated_at), (datetime.date(2026, 9, 30), datetime.date(2026, 10, 1)))

    def test_inserted_before_a_later_date(self):
        before = "\n## Updates\n\n### 2026-09-30\n\n- A\n\n\n### 2026-10-02\n\n- C\n"
        text, _previous, _updated_at = self.record(self.task(before, "2026-10-02"), "2026-10-01")
        self.assertEqual(
            text,
            self.task(
                "\n## Updates\n\n### 2026-09-30\n\n- A\n\n### 2026-10-01\n\n- Done\n\n### 2026-10-02\n\n- C\n",
                "2026-10-02",
            ),
        )

    def test_inserted_before_the_first_date(self):
        text, _previous, _updated_at = self.record(self.task("\n## Updates\n\n### 2026-10-02\n\n- C\n"), "2026-10-01")
        self.assertEqual(
            text, self.task("\n## Updates\n\n### 2026-10-01\n\n- Done\n\n### 2026-10-02\n\n- C\n", "2026-10-01")
        )

    def test_inserted_at_the_end(self):
        before = "\n## Updates\n\n### 2026-09-30\n\n- A\n\n\n"
        text, _previous, _updated_at = self.record(self.task(before), "2026-10-01")
        self.assertEqual(
            text, self.task("\n## Updates\n\n### 2026-09-30\n\n- A\n\n### 2026-10-01\n\n- Done\n", "2026-10-01")
        )

    def test_merged_after_the_last_non_blank_line_of_its_block(self):
        before = "\n## Updates\n\n### 2026-10-01\n\n- A\n  continued\n\n\n### 2026-10-02\n\n- C\n"
        text, _previous, _updated_at = self.record(self.task(before, "2026-10-02"), "2026-10-01", ["- B"])
        self.assertEqual(
            text,
            self.task(
                "\n## Updates\n\n### 2026-10-01\n\n- A\n  continued\n- B\n\n\n### 2026-10-02\n\n- C\n", "2026-10-02"
            ),
        )

    def test_merged_into_the_last_block(self):
        text, _previous, _updated_at = self.record(self.task("\n## Updates\n\n### 2026-10-01\n\n- A\n\n"), "2026-10-01")
        self.assertEqual(text, self.task("\n## Updates\n\n### 2026-10-01\n\n- A\n- Done\n", "2026-10-01"))

    def test_merged_into_an_empty_subsection(self):
        text, _previous, _updated_at = self.record(self.task("\n## Updates\n\n### 2026-10-01\n"), "2026-10-01")
        self.assertEqual(text, self.task("\n## Updates\n\n### 2026-10-01\n\n- Done\n", "2026-10-01"))

    def test_updated_at_kept_when_later_than_the_day(self):
        text, previous, updated_at = self.record(self.task("\n## Updates\n", "2026-10-02"), "2026-10-01")
        self.assertEqual((previous, updated_at), (datetime.date(2026, 10, 2), datetime.date(2026, 10, 2)))
        self.assertIn("\nupdated_at: 2026-10-02\n", text)

    def test_status_and_metadata_kept(self):
        frontmatter = (
            "---\nstatus: blocked\nref: SUP-1\nupdated_at: {}\nmetadata:\n  project: [checkout, landing]\n---\n"
        )
        body = "\nLogin fails\n\n## Updates\n"
        text, _previous, _updated_at = self.record(frontmatter.format("2026-09-30") + body, "2026-10-01")
        self.assertEqual(text, frontmatter.format("2026-10-01") + body + "\n### 2026-10-01\n\n- Done\n")

    def test_day_after_today_refused(self):
        with self.assertRaises(tasks.TaskError) as caught:
            self.record(self.task("\n## Updates\n"), "2026-10-04")
        self.assertIn("date 2026-10-04 is after today, 2026-10-03", str(caught.exception))

    def test_day_before_the_creation_date_refused(self):
        with self.assertRaises(tasks.TaskError) as caught:
            self.record(self.task("\n## Updates\n"), "2026-09-29")
        self.assertIn("date 2026-09-29 is before 2026-09-30, the creation date of the task", str(caught.exception))

    def test_invalid_section_refused(self):
        with self.assertRaises(tasks.TaskError) as caught:
            self.record(self.task("\nLogin fails\n"), "2026-10-01")
        self.assertIn("has no '## Updates' section", str(caught.exception))

    def test_windows_line_endings_kept_outside_the_written_range(self):
        before = (
            "\r\nLogin fails\r\n\r\n## Updates\r\n\r\n### 2026-09-30\r\n\r\n- A\r\n\r\n### 2026-10-02\r\n\r\n- C\r\n"
        )
        text, _previous, _updated_at = self.record(self.task(before, "2026-10-02"), "2026-10-01")
        self.assertEqual(
            text,
            self.task(
                "\r\nLogin fails\r\n\r\n## Updates\r\n\r\n### 2026-09-30\r\n\r\n- A\r\n"
                "\n### 2026-10-01\n\n- Done\n\n### 2026-10-02\r\n\r\n- C\r\n",
                "2026-10-02",
            ),
        )


class MatchesTest(unittest.TestCase):
    def task(self, **metadata):
        day = datetime.date(2026, 9, 30)
        return tasks.Task(
            f"tasks/support/{NAME}", None, "support", False, "SUP-1", day, "T", "open", day, None, metadata, None
        )

    def filters(self, declared, **equalities):
        types = {"billed": "boolean", "client": "text", "due": "date"}
        conditions = metadata.Conditions(equalities=equalities, types={key: types[key] for key in equalities})
        return tasks.Filters(metadata=conditions, schemas={"support": declared})

    def test_metadata_conditions_by_type(self):
        self.assertTrue(tasks.matches(self.task(billed=False), self.filters(["billed"], billed=[False])))
        self.assertFalse(tasks.matches(self.task(billed=0), self.filters(["billed"], billed=[False])))
        due = datetime.date(2026, 10, 15)
        self.assertTrue(tasks.matches(self.task(due=due), self.filters(["due"], due=[due])))
        self.assertFalse(tasks.matches(self.task(due="2026-10-15"), self.filters(["due"], due=[due])))

    def test_missing_key_reads_as_null_for_the_schema_of_its_workstream(self):
        self.assertTrue(tasks.matches(self.task(), self.filters(["client"], client=[None])))
        self.assertFalse(tasks.matches(self.task(), self.filters([], client=[None])))
        conditions = self.filters(["client"], client=[None]).metadata
        self.assertFalse(tasks.matches(self.task(), tasks.Filters(metadata=conditions)))


class DisplayTitleTest(unittest.TestCase):
    def test_strips_date_ref_and_extension(self):
        self.assertEqual(tasks.display_title(NAME, "SUP-1"), "Login fails on safari")

    def test_slug_starting_with_a_digit(self):
        self.assertEqual(tasks.display_title("2026-09-30-SUP-12-2fa-codes-expire.md", "SUP-12"), "2fa codes expire")


class DescriptionTest(unittest.TestCase):
    def test_extracted(self):
        body = "\nLogin fails on Safari for the checkout app\n\nhttps://example.com/t/1\n\n## Updates\n"
        self.assertEqual(tasks.description(body), "Login fails on Safari for the checkout app")

    def test_absent(self):
        self.assertIsNone(tasks.description("\n## Updates\n\n### 2026-09-30\n\n- Reproduced\n"))

    def test_empty_body(self):
        self.assertIsNone(tasks.description(""))

    def test_paragraph_over_several_lines(self):
        self.assertEqual(
            tasks.description("\nLogin fails on Safari\nfor the checkout app\n\n## Updates\n"),
            "Login fails on Safari\nfor the checkout app",
        )


if __name__ == "__main__":
    unittest.main()
