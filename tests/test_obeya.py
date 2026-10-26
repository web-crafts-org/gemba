"""Unit tests for the layout gemba init writes: the config, the .gitignore and .gitattributes lines and the refusals."""

import tempfile
import unittest
from pathlib import Path

from gemba import config, obeya


class RenderConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, providers):
        (self.root / config.CONFIG_FILENAME).write_text(obeya.render_config(providers), encoding="utf-8")
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
        rendered = obeya.render_config(["claude"])
        self.assertIn("\nagent_providers: [claude]\n", rendered)
        self.assertNotIn(obeya.TEMPLATE_PROVIDERS_TOKEN, rendered)


class GitignoreTest(unittest.TestCase):
    LINES = "harnesses/\ngemba.local.yaml\n/update.md\n"

    def test_no_file(self):
        self.assertEqual(obeya.gitignore_text(None), self.LINES)

    def test_empty_file(self):
        self.assertEqual(obeya.gitignore_text(""), self.LINES)

    def test_file_without_any_line(self):
        self.assertEqual(obeya.gitignore_text("cli/.venv/\n"), f"cli/.venv/\n{self.LINES}")

    def test_file_without_a_final_newline(self):
        self.assertEqual(obeya.gitignore_text("cli/.venv/"), f"cli/.venv/\n{self.LINES}")

    def test_file_without_some_lines(self):
        self.assertEqual(obeya.gitignore_text("harnesses/\n"), self.LINES)
        self.assertEqual(obeya.gitignore_text("harnesses/"), self.LINES)
        self.assertEqual(obeya.gitignore_text("harnesses/\ngemba.local.yaml\n"), self.LINES)
        self.assertEqual(
            obeya.gitignore_text("gemba.local.yaml\ncli/.venv/\n"),
            "gemba.local.yaml\ncli/.venv/\nharnesses/\n/update.md\n",
        )

    def test_file_with_every_line(self):
        self.assertIsNone(obeya.gitignore_text(f"cli/.venv/\n{self.LINES}"))
        self.assertIsNone(obeya.gitignore_text("/update.md\ngemba.local.yaml\nharnesses/"))
        self.assertIsNone(obeya.gitignore_text("harnesses/\r\ngemba.local.yaml\r\n/update.md\r\n"))

    def test_similar_lines_do_not_count(self):
        text = "harnesses/old/\n/gemba.local.yaml.bak\nupdate.md\n"
        self.assertEqual(obeya.gitignore_text(text), f"{text}{self.LINES}")


class GitattributesTest(unittest.TestCase):
    BOTH = "*.md text eol=lf\n*.yaml text eol=lf\n"

    def test_no_file(self):
        self.assertEqual(obeya.gitattributes_text(None), self.BOTH)

    def test_empty_file(self):
        self.assertEqual(obeya.gitattributes_text(""), self.BOTH)

    def test_file_without_the_lines(self):
        self.assertEqual(obeya.gitattributes_text("*.png binary\n"), "*.png binary\n" + self.BOTH)
        self.assertEqual(obeya.gitattributes_text("*.png binary"), "*.png binary\n" + self.BOTH)

    def test_file_with_one_line(self):
        self.assertEqual(obeya.gitattributes_text("*.md text eol=lf\n"), self.BOTH)
        self.assertEqual(obeya.gitattributes_text("*.yaml text eol=lf\n"), "*.yaml text eol=lf\n*.md text eol=lf\n")

    def test_file_with_both_lines(self):
        self.assertIsNone(obeya.gitattributes_text(self.BOTH))
        self.assertIsNone(obeya.gitattributes_text("*.yaml text eol=lf\r\n*.png binary\r\n*.md text eol=lf"))

    def test_similar_lines_do_not_count(self):
        self.assertEqual(
            obeya.gitattributes_text("*.md text\n*.yaml text eol=lf\n"),
            "*.md text\n*.yaml text eol=lf\n*.md text eol=lf\n",
        )


class ProblemsTest(unittest.TestCase):
    KNOWN = "(known providers: claude, agents)"

    def test_known_providers_accepted(self):
        self.assertEqual(obeya.providers_problem(["claude", "agents"]), [])

    def test_unknown_identifier(self):
        self.assertEqual(obeya.providers_problem(["claude", "cursor"]), [f"unknown provider 'cursor' {self.KNOWN}"])

    def test_repeated_identifier_reported_once(self):
        self.assertEqual(
            obeya.providers_problem(["claude", "claude", "claude"]),
            [f"provider 'claude' is listed more than once {self.KNOWN}"],
        )

    def test_every_problem_reported(self):
        self.assertEqual(
            obeya.providers_problem(["cursor", "agents", "cursor", "agents"]),
            [f"unknown provider 'cursor' {self.KNOWN}", f"provider 'agents' is listed more than once {self.KNOWN}"],
        )

    def test_nested_problem_names_both_folders(self):
        message = obeya.nested_problem(Path("/srv/acme/notes"), Path("/srv/acme"))
        self.assertIn(f"{Path('/srv/acme/notes')} is inside the obeya {Path('/srv/acme')}", message)


class HookScriptTest(unittest.TestCase):
    def test_each_script_runs_gemba_hook_with_its_name(self):
        for name in obeya.HOOKS:
            with self.subTest(hook=name):
                lines = obeya.hook_script(name).split("\n")
                self.assertEqual(lines[:2], ["#!/bin/sh", obeya.HOOK_MARKER])
                self.assertEqual(lines[-2:], [f'exec gemba hook {name} "$@"', ""])
                self.assertNotIn("\r", obeya.hook_script(name))

    def test_without_gemba_on_path_the_message_names_the_install_and_the_bypass(self):
        for name in obeya.HOOKS:
            with self.subTest(hook=name):
                script = obeya.hook_script(name)
                self.assertIn("if ! command -v gemba >/dev/null 2>&1; then\n", script)
                self.assertIn(
                    f"gemba hook {name}: gemba is not on PATH: install it with uv tool install gemba-cli", script
                )
                self.assertIn('git push --no-verify skips these checks" >&2\n', script)

    def test_only_pre_push_fails_closed(self):
        self.assertIn("  exit 1\nfi\n", obeya.hook_script("pre-push"))
        for name in ("post-merge", "post-rewrite"):
            with self.subTest(hook=name):
                self.assertIn("  exit 0\nfi\n", obeya.hook_script(name))


class HookStateTest(unittest.TestCase):
    def test_missing(self):
        self.assertEqual(obeya.hook_state("pre-push", None), "missing")

    def test_current(self):
        for name in obeya.HOOKS:
            with self.subTest(hook=name):
                self.assertEqual(obeya.hook_state(name, obeya.hook_script(name)), "current")

    def test_script_of_another_hook_is_not_current(self):
        self.assertEqual(obeya.hook_state("pre-push", obeya.hook_script("post-merge")), "earlier")

    def test_earlier(self):
        text = f"#!/bin/sh\n{obeya.HOOK_MARKER}\nexec gemba hook pre-push\n"
        self.assertEqual(obeya.hook_state("pre-push", text), "earlier")

    def test_chained(self):
        for text in (
            '#!/bin/sh\nlint-staged || exit 1\ngemba hook pre-push "$@"\n',
            '#!/bin/sh\nexec gemba hook pre-push "$@"\n',
            "#!/bin/sh\n  gemba hook pre-push $1 $2 || exit 1\nnpm test\n",
        ):
            with self.subTest(text=text):
                self.assertEqual(obeya.hook_state("pre-push", text), "chained")

    def test_other(self):
        for text in (
            "",
            "#!/bin/sh\nexec lint-staged\n",
            "#!/bin/sh\n# gemba hook pre-push\n",
            "#!/bin/sh\ngemba hook pre-pushed\n",
            '#!/bin/sh\ngemba hook post-merge "$@"\n',
        ):
            with self.subTest(text=text):
                self.assertEqual(obeya.hook_state("pre-push", text), "other")


class HookActionTest(unittest.TestCase):
    def test_on(self):
        expected: dict[obeya.HookState, obeya.HookAction | None] = {
            "missing": "written",
            "earlier": "updated",
            "current": "kept",
            "chained": "kept",
            "other": "refused",
        }
        for state, action in expected.items():
            with self.subTest(state=state):
                self.assertEqual(obeya.hook_action(state, on=True, redirected=False), action)

    def test_on_under_a_hooks_path(self):
        expected: dict[obeya.HookState, obeya.HookAction | None] = {
            "missing": "refused",
            "earlier": "refused",
            "current": "kept",
            "chained": "kept",
            "other": "refused",
        }
        for state, action in expected.items():
            with self.subTest(state=state):
                self.assertEqual(obeya.hook_action(state, on=True, redirected=True), action)

    def test_off(self):
        expected: dict[obeya.HookState, obeya.HookAction | None] = {
            "missing": None,
            "earlier": "removed",
            "current": "removed",
            "chained": None,
            "other": None,
        }
        for state, action in expected.items():
            with self.subTest(state=state):
                self.assertEqual(obeya.hook_action(state, on=False, redirected=False), action)

    def test_off_under_a_hooks_path_removes_nothing(self):
        states: tuple[obeya.HookState, ...] = ("missing", "earlier", "current", "chained", "other")
        for state in states:
            with self.subTest(state=state):
                self.assertIsNone(obeya.hook_action(state, on=False, redirected=True))

    def test_problems_name_the_hook_and_both_ways_out(self):
        self.assertEqual(
            obeya.hook_problem(".git/hooks/pre-push", "pre-push"),
            '.git/hooks/pre-push is a hook gemba did not write: run gemba hook pre-push "$@" from it, or turn the '
            "hooks off for this clone with git_hooks: false in gemba.local.yaml",
        )
        self.assertEqual(
            obeya.hook_problem(".githooks/post-merge", "post-merge", ".githooks"),
            'core.hooksPath is set to .githooks, where gemba writes no hook: run gemba hook post-merge "$@" from '
            ".githooks/post-merge, or turn the hooks off for this clone with git_hooks: false in gemba.local.yaml",
        )


if __name__ == "__main__":
    unittest.main()
