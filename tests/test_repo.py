"""Unit tests for the layout gemba init writes: the config, the .gitignore and .gitattributes lines and the refusals."""

import tempfile
import unittest
from pathlib import Path

from gemba import config, repo


class RenderConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, providers):
        (self.root / config.CONFIG_FILENAME).write_text(repo.render_config(providers), encoding="utf-8")
        return config.load(root=self.root)

    def test_rendered_config_loads_with_the_default_workstream(self):
        loaded = self.load(["claude", "agents"])
        self.assertEqual(loaded.default_workstream, "default")
        self.assertEqual(list(loaded.workstreams), ["default"])
        self.assertEqual(loaded.workstreams["default"].prefix, "TASK")
        self.assertEqual(loaded.agent_providers, ("claude", "agents"))

    def test_given_providers_in_their_order(self):
        self.assertEqual(self.load(["agents"]).agent_providers, ("agents",))
        self.assertEqual(self.load(["agents", "claude"]).agent_providers, ("agents", "claude"))

    def test_token_replaced_by_a_flow_list(self):
        rendered = repo.render_config(["claude"])
        self.assertIn("\nagent_providers: [claude]\n", rendered)
        self.assertNotIn(repo.TEMPLATE_PROVIDERS_TOKEN, rendered)


class GitignoreTest(unittest.TestCase):
    def test_no_file(self):
        self.assertEqual(repo.gitignore_text(None), "harnesses/\n")

    def test_empty_file(self):
        self.assertEqual(repo.gitignore_text(""), "harnesses/\n")

    def test_file_without_the_line(self):
        self.assertEqual(repo.gitignore_text("cli/.venv/\n"), "cli/.venv/\nharnesses/\n")

    def test_file_without_a_final_newline(self):
        self.assertEqual(repo.gitignore_text("cli/.venv/"), "cli/.venv/\nharnesses/\n")

    def test_file_with_the_line(self):
        self.assertIsNone(repo.gitignore_text("cli/.venv/\nharnesses/\n"))
        self.assertIsNone(repo.gitignore_text("harnesses/"))
        self.assertIsNone(repo.gitignore_text("harnesses/\r\n"))

    def test_similar_lines_do_not_count(self):
        self.assertEqual(repo.gitignore_text("harnesses/old/\n"), "harnesses/old/\nharnesses/\n")


class GitattributesTest(unittest.TestCase):
    BOTH = "*.md text eol=lf\n*.yaml text eol=lf\n"

    def test_no_file(self):
        self.assertEqual(repo.gitattributes_text(None), self.BOTH)

    def test_empty_file(self):
        self.assertEqual(repo.gitattributes_text(""), self.BOTH)

    def test_file_without_the_lines(self):
        self.assertEqual(repo.gitattributes_text("*.png binary\n"), "*.png binary\n" + self.BOTH)
        self.assertEqual(repo.gitattributes_text("*.png binary"), "*.png binary\n" + self.BOTH)

    def test_file_with_one_line(self):
        self.assertEqual(repo.gitattributes_text("*.md text eol=lf\n"), self.BOTH)
        self.assertEqual(repo.gitattributes_text("*.yaml text eol=lf\n"), "*.yaml text eol=lf\n*.md text eol=lf\n")

    def test_file_with_both_lines(self):
        self.assertIsNone(repo.gitattributes_text(self.BOTH))
        self.assertIsNone(repo.gitattributes_text("*.yaml text eol=lf\r\n*.png binary\r\n*.md text eol=lf"))

    def test_similar_lines_do_not_count(self):
        self.assertEqual(
            repo.gitattributes_text("*.md text\n*.yaml text eol=lf\n"),
            "*.md text\n*.yaml text eol=lf\n*.md text eol=lf\n",
        )


class ProblemsTest(unittest.TestCase):
    KNOWN = "(known providers: claude, agents)"

    def test_known_providers_accepted(self):
        self.assertEqual(repo.providers_problem(["claude", "agents"]), [])

    def test_unknown_identifier(self):
        self.assertEqual(repo.providers_problem(["claude", "cursor"]), [f"unknown provider 'cursor' {self.KNOWN}"])

    def test_repeated_identifier_reported_once(self):
        self.assertEqual(
            repo.providers_problem(["claude", "claude", "claude"]),
            [f"provider 'claude' is listed more than once {self.KNOWN}"],
        )

    def test_every_problem_reported(self):
        self.assertEqual(
            repo.providers_problem(["cursor", "agents", "cursor", "agents"]),
            [f"unknown provider 'cursor' {self.KNOWN}", f"provider 'agents' is listed more than once {self.KNOWN}"],
        )

    def test_nested_problem_names_both_folders(self):
        message = repo.nested_problem(Path("/srv/acme/notes"), Path("/srv/acme"))
        self.assertIn(f"{Path('/srv/acme/notes')} is inside the tasks repo {Path('/srv/acme')}", message)


if __name__ == "__main__":
    unittest.main()
