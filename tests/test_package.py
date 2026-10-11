"""Unit tests for the metadata the package declares in pyproject.toml."""

import tomllib
import unittest
from pathlib import Path

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


class MetadataTest(unittest.TestCase):
    """Scenario: Metadata declared."""

    @classmethod
    def setUpClass(cls):
        cls.project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]

    def test_name_and_command(self):
        self.assertEqual(self.project["name"], "gemba-cli")
        self.assertEqual(self.project["scripts"], {"gemba": "gemba.cli:main"})

    def test_readme_and_license(self):
        self.assertEqual(self.project["readme"], "README.md")
        self.assertEqual(self.project["license"], "MIT")
        self.assertEqual(self.project["license-files"], ["LICENSE"])

    def test_authors_and_urls(self):
        self.assertTrue(self.project["authors"], "authors must name at least one")
        self.assertEqual(set(self.project["urls"]), {"Repository", "Changelog", "Issues"})
        for url in self.project["urls"].values():
            self.assertTrue(url.startswith("https://github.com/web-crafts-org/gemba"), url)

    def test_classifiers_and_python(self):
        self.assertTrue(self.project["classifiers"], "classifiers must not be empty")
        self.assertFalse([c for c in self.project["classifiers"] if c.startswith("License ::")])
        self.assertEqual(self.project["requires-python"], ">=3.11")
        self.assertTrue(self.project["keywords"], "keywords must not be empty")
