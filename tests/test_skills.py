"""Unit tests for the skill registry, rendering and the classification of a skill on disk."""

import tempfile
import unittest
from pathlib import Path

import yaml

from gemba import skills

FIXTURE = """\
---
name: demo
description: A demo skill.
---

# Demo

Do the thing.
"""
# SHA-256 of FIXTURE exactly as written above.
FIXTURE_HASH = "a553dff3cc253d6dc39fcd80d69fdf5876d90c46e6d9deac3072a55206bb3b6c"

STAMPED = f"""\
---
name: demo
description: A demo skill.
metadata:
  generatedBy: "1.0.0"
  contentHash: "{FIXTURE_HASH}"
---

# Demo

Do the thing.
"""

OLDER = FIXTURE.replace("Do the thing.", "Do the old thing.")

NAMES = [skill.name for skill in skills.SKILLS]


class StampTest(unittest.TestCase):
    def test_known_hash(self):
        self.assertEqual(skills.content_hash(FIXTURE), FIXTURE_HASH)

    def test_stamp_appends_the_provenance_map(self):
        self.assertEqual(skills.stamp(FIXTURE, "1.0.0"), STAMPED)

    def test_removing_the_metadata_map_gives_back_the_asset(self):
        self.assertEqual(skills.content(STAMPED), FIXTURE)
        self.assertEqual(skills.content_hash(STAMPED), FIXTURE_HASH)

    def test_only_the_metadata_map_is_removed(self):
        text = STAMPED.replace("description: A demo skill.\n", "description: A demo skill.\nlicense: MIT\n")
        self.assertEqual(skills.content(text), FIXTURE.replace("---\n\n", "license: MIT\n---\n\n"))

    def test_line_endings_are_normalized(self):
        self.assertEqual(skills.content(STAMPED.replace("\n", "\r\n")), FIXTURE)
        self.assertEqual(skills.content_hash(FIXTURE.replace("\n", "\r")), FIXTURE_HASH)

    def test_text_without_frontmatter_is_refused(self):
        with self.assertRaises(ValueError):
            skills.stamp("# Demo\n", "1.0.0")

    def test_asset_with_a_metadata_map_is_refused(self):
        with self.assertRaises(ValueError):
            skills.stamp(STAMPED, "1.0.0")


class InspectTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "demo" / skills.SKILL_FILE
        self.path.parent.mkdir()
        self.current = skills.stamp(FIXTURE, "2.0.0")

    def tearDown(self):
        self._tmp.cleanup()

    def state(self, text=None):
        if text is not None:
            self.path.write_bytes(text.encode("utf-8"))
        return skills.inspect(self.path, self.current)

    def test_missing(self):
        self.assertEqual(self.state(), "missing")

    def test_unchanged_ignores_the_generating_version(self):
        self.assertEqual(self.state(STAMPED), "unchanged")
        self.assertEqual(self.state(self.current), "unchanged")

    def test_unchanged_with_other_line_endings(self):
        self.assertEqual(self.state(STAMPED.replace("\n", "\r\n")), "unchanged")

    def test_outdated(self):
        self.assertEqual(self.state(skills.stamp(OLDER, "1.0.0")), "outdated")

    def test_outdated_when_only_the_metadata_map_differs(self):
        self.assertEqual(self.state(STAMPED.replace('  generatedBy: "1.0.0"\n', "")), "outdated")

    def test_edited_body(self):
        self.assertEqual(self.state(STAMPED.replace("Do the thing.", "Do my thing.")), "edited")

    def test_edited_without_metadata(self):
        self.assertEqual(self.state(FIXTURE), "edited")

    def test_edited_with_a_wrong_hash(self):
        self.assertEqual(self.state(STAMPED.replace(FIXTURE_HASH, "0" * 64)), "edited")

    def test_edited_without_frontmatter(self):
        self.assertEqual(self.state("# Demo\n"), "edited")

    def test_edited_with_a_malformed_metadata_map(self):
        self.assertEqual(self.state(STAMPED.replace("  generatedBy:", "  generatedBy: [")), "edited")


class RegistryTest(unittest.TestCase):
    def frontmatter(self, text):
        _empty, block, _body = text.split("---\n", 2)
        return yaml.safe_load(block)

    def test_every_registered_asset_is_named_after_its_folder(self):
        for name in NAMES:
            with self.subTest(skill=name):
                frontmatter = self.frontmatter(skills.asset(name))
                self.assertEqual(sorted(frontmatter), ["description", "name"])
                self.assertEqual(frontmatter["name"], name)

    def test_rendered_skill_carries_its_provenance(self):
        for name in NAMES:
            with self.subTest(skill=name):
                rendered = skills.render(name, "9.9.9")
                metadata = self.frontmatter(rendered)["metadata"]
                self.assertEqual(metadata["generatedBy"], "9.9.9")
                self.assertEqual(metadata["contentHash"], skills.content_hash(skills.asset(name)))
                self.assertEqual(skills.content(rendered), skills.asset(name))

    def test_every_asset_names_the_published_install(self):
        """Scenario: No development path in a skill."""
        for skill in skills.SKILLS:
            with self.subTest(skill=skill.name):
                text = skills.asset(skill.name)
                self.assertIn("uv tool install gemba-cli", text)
                self.assertNotIn("./cli", text)
                self.assertNotIn("uv tool install -e", text)

    def test_unregistered_name_is_refused(self):
        with self.assertRaises(ValueError):
            skills.asset("gemba-skills")

    def test_scopes_and_providers(self):
        self.assertEqual(
            {skill.name: skill.scope for skill in skills.SKILLS},
            {
                "gemba-create": "repo",
                "gemba-list": "repo",
                "gemba-harness": "both",
                "gemba-record": "both",
                "gemba-report": "repo",
                "gemba-mark": "both",
                "gemba-archive": "repo",
                "gemba-set": "both",
                "gemba-worktree": "harness",
                "gemba-init": "repo",
                "gemba-config": "repo",
            },
        )
        self.assertEqual(len(set(NAMES)), len(NAMES))
        self.assertEqual(
            {name: (provider.skills_dir, provider.guide) for name, provider in skills.PROVIDERS.items()},
            {"claude": (".claude/skills", "CLAUDE.md"), "agents": (".agents/skills", "AGENTS.md")},
        )


class PlanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def names(self, scope):
        return [skill.name for skill in skills.SKILLS if skill.scope in (scope, "both")]

    def test_one_action_per_provider_and_skill(self):
        names = self.names("repo")
        actions = skills.plan(self.root, ["agents", "claude"], "9.9.9", "repo")
        self.assertEqual(
            [action.path for action in actions],
            [f".agents/skills/{name}/SKILL.md" for name in names]
            + [f".claude/skills/{name}/SKILL.md" for name in names],
        )
        self.assertEqual({action.state for action in actions}, {"missing"})
        self.assertEqual(actions[0].content, skills.render(names[0], "9.9.9"))

    def test_only_the_skills_of_the_target(self):
        for scope in ("repo", "harness"):
            with self.subTest(scope=scope):
                actions = skills.plan(self.root, ["claude"], "9.9.9", scope)
                self.assertEqual(
                    [action.path for action in actions],
                    [f".claude/skills/{name}/SKILL.md" for name in self.names(scope)],
                )

    def test_states_are_read_from_disk(self):
        names = self.names("repo")
        path = self.root / ".claude" / "skills" / names[0] / skills.SKILL_FILE
        path.parent.mkdir(parents=True)
        path.write_text(skills.render(names[0], "1.0.0"), encoding="utf-8")
        actions = skills.plan(self.root, ["claude"], "9.9.9", "repo")
        self.assertEqual([action.state for action in actions], ["unchanged"] + ["missing"] * (len(names) - 1))

    def test_outcomes(self):
        expected: dict[tuple[skills.State, bool], str] = {
            ("missing", False): "written",
            ("outdated", False): "updated",
            ("unchanged", False): "kept",
            ("edited", False): "kept",
            ("missing", True): "written",
            ("outdated", True): "updated",
            ("unchanged", True): "kept",
            ("edited", True): "overwritten",
        }
        for (state, force), outcome in expected.items():
            with self.subTest(state=state, force=force):
                self.assertEqual(skills.Action(path="x", state=state, content="").outcome(force), outcome)


if __name__ == "__main__":
    unittest.main()
