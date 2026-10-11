"""Traceability between the specs and the black-box cases.

Every case names the spec scenario it covers, so a case can only exist for a scenario
that exists. Every scenario has at least one case, unless `not-automated.yaml` lists it
with the reason; that map is the only exemption and must stay current.

The specs checked are the main specs with the delta specs of every active change
applied in memory, so the suite passes as soon as a change is implemented and gives the
same result once the change is archived and its deltas are synced. Only scenario titles
are tracked: `RENAMED` renames a requirement, `REMOVED` drops it, `MODIFIED` replaces
its scenarios and `ADDED` adds it, in that order. Set GEMBA_CHANGE to a change name to
apply that change only.
"""

import os
import re
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml
from test_cases import load_cases

TESTS_DIR = Path(__file__).resolve().parent
OPENSPEC_DIR = TESTS_DIR.parent / "openspec"
SPECS_DIR = OPENSPEC_DIR / "specs"
CHANGES_DIR = OPENSPEC_DIR / "changes"
ARCHIVE = "archive"
CHANGE_VARIABLE = "GEMBA_CHANGE"
EXEMPTIONS_FILE = TESTS_DIR / "not-automated.yaml"

SECTION_HEADING = re.compile(r"^## (.+?)\s*$")
REQUIREMENT_HEADING = re.compile(r"^### Requirement: (.+?)\s*$")
SCENARIO_HEADING = re.compile(r"^#### Scenario: (.+?)\s*$")
RENAME_LINE = re.compile(r"^\s*-\s*(FROM|TO):\s*`?###\s*Requirement:\s*(.+?)`?\s*$")


def read_blocks(text):
    """The scenario titles of each requirement, grouped by `##` section, and the renames."""
    sections = {}
    renames = []
    section = requirement = renamed_from = None
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif fenced:
            continue
        elif match := SECTION_HEADING.match(line):
            section, requirement = match.group(1), None
        elif match := REQUIREMENT_HEADING.match(line):
            requirement = match.group(1)
            sections.setdefault(section, {})[requirement] = []
        elif match := SCENARIO_HEADING.match(line):
            sections.setdefault(section, {}).setdefault(requirement, []).append(match.group(1))
        elif match := RENAME_LINE.match(line):
            if match.group(1) == "FROM":
                renamed_from = match.group(2)
            elif renamed_from is not None:
                renames.append((renamed_from, match.group(2)))
                renamed_from = None
    return sections, renames


def main_requirements(text):
    """Every requirement of a main spec with its scenario titles, whatever its section."""
    sections, _renames = read_blocks(text)
    return {name: titles for requirements in sections.values() for name, titles in requirements.items()}


def apply_delta(requirements, text):
    """Apply one delta spec to the requirements of its capability, in place; return the problems."""
    sections, renames = read_blocks(text)
    problems = []
    for old, new in renames:
        if old not in requirements:
            problems.append(f"RENAMED requirement '{old}' is not in the main spec")
            continue
        requirements[new] = requirements.pop(old)
    for name in sections.get("REMOVED Requirements", {}):
        if requirements.pop(name, None) is None:
            problems.append(f"REMOVED requirement '{name}' is not in the main spec")
    for name, titles in sections.get("MODIFIED Requirements", {}).items():
        if name not in requirements:
            problems.append(f"MODIFIED requirement '{name}' is not in the main spec")
            continue
        requirements[name] = list(titles)
    for name, titles in sections.get("ADDED Requirements", {}).items():
        requirements[name] = list(titles)
    return problems


def effective_scenarios(specs_dir=SPECS_DIR, changes_dir=CHANGES_DIR, only=None):
    """Every `<capability>: <scenario title>` once the active changes are applied, and the problems."""
    capabilities = {
        spec.parent.name: main_requirements(spec.read_text(encoding="utf-8"))
        for spec in sorted(specs_dir.glob("*/spec.md"))
    }
    problems = []
    active = []
    if changes_dir.is_dir():
        active = sorted(
            path.name
            for path in changes_dir.iterdir()
            if path.is_dir() and path.name != ARCHIVE and not path.name.startswith(".")
        )
    if only:
        if only not in active:
            problems.append(f"{CHANGE_VARIABLE}={only} is not an active change (active: {', '.join(active) or 'none'})")
        active = [only] if only in active else []
    for change in active:
        for delta in sorted((changes_dir / change / "specs").glob("*/spec.md")):
            capability = delta.parent.name
            requirements = capabilities.setdefault(capability, {})
            for problem in apply_delta(requirements, delta.read_text(encoding="utf-8")):
                problems.append(f"change '{change}', capability '{capability}': {problem}")
    scenarios = {
        f"{capability}: {title}"
        for capability, requirements in capabilities.items()
        for titles in requirements.values()
        for title in titles
    }
    return scenarios, problems


def case_scenarios():
    """Every scenario named by a case, mapped to the cases that name it."""
    named = {}
    for _test_name, source, case in load_cases():
        named.setdefault(case.get("scenario"), []).append(f"{source} [{case.get('name', '?')}]")
    return named


def exemptions():
    data = yaml.safe_load(EXEMPTIONS_FILE.read_text(encoding="utf-8")) or {}
    return data


class TraceabilityTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.declared, cls.problems = effective_scenarios(only=os.environ.get(CHANGE_VARIABLE))
        cls.named = case_scenarios()
        cls.exempt = exemptions()

    def test_specs_folder_exists(self):
        self.assertTrue(SPECS_DIR.is_dir(), f"main specs not found at {SPECS_DIR}")
        self.assertTrue(self.declared, f"no scenario headings found under {SPECS_DIR}")

    def test_active_changes_apply_to_the_main_specs(self):
        self.assertEqual(self.problems, [], "delta specs of active changes that cannot be applied")

    def test_every_case_names_an_existing_scenario(self):
        orphans = {scenario: cases for scenario, cases in self.named.items() if scenario not in self.declared}
        self.assertEqual(orphans, {}, "cases naming a scenario that is not in the specs")

    def test_every_scenario_has_a_case_or_a_reason(self):
        uncovered = sorted(self.declared - set(self.named) - set(self.exempt))
        self.assertEqual(uncovered, [], f"scenarios without a case and not listed in {EXEMPTIONS_FILE.name}")

    def test_exemptions_are_current(self):
        for scenario, reason in self.exempt.items():
            with self.subTest(scenario=scenario):
                self.assertIsInstance(reason, str, "the reason must be a string")
                self.assertTrue(reason.strip(), "the reason must not be empty")
                self.assertTrue(scenario in self.declared, f"exempted scenario {scenario!r} is not in the specs")
                self.assertFalse(scenario in self.named, f"exempted scenario {scenario!r} already has a case")


MAIN_SPEC = """\
# billing Specification

## Purpose

Invoices.

## Requirements

### Requirement: Invoice numbering
Invoices are numbered.

#### Scenario: First invoice
- **WHEN** no invoice exists
- **THEN** the first one is 1

#### Scenario: Next invoice
- **WHEN** the last invoice is 4
- **THEN** the next one is 5

### Requirement: Invoice currency
Invoices carry a currency.

#### Scenario: Default currency
- **WHEN** none is given
- **THEN** the default is used
"""


class DeltaApplicationTest(unittest.TestCase):
    """Unit tests for applying delta specs; the fixtures are one main spec and small deltas."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.specs = root / "specs"
        self.changes = root / "changes"
        self.write(self.specs / "billing" / "spec.md", MAIN_SPEC)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")

    def delta(self, text, change="next", capability="billing"):
        self.write(self.changes / change / "specs" / capability / "spec.md", text)

    def scenarios(self, only=None):
        return effective_scenarios(self.specs, self.changes, only)

    def test_main_specs_alone(self):
        self.assertEqual(
            self.scenarios(),
            ({"billing: First invoice", "billing: Next invoice", "billing: Default currency"}, []),
        )

    def test_added(self):
        self.delta("""\
            ## ADDED Requirements

            ### Requirement: Invoice due date
            #### Scenario: Due in thirty days
            """)
        self.delta(
            "## ADDED Requirements\n\n### Requirement: Payout\n#### Scenario: Weekly payout\n", capability="payouts"
        )
        declared, problems = self.scenarios()
        self.assertIn("billing: Due in thirty days", declared)
        self.assertIn("payouts: Weekly payout", declared)
        self.assertEqual(problems, [])

    def test_modified_replaces_the_scenarios(self):
        self.delta("""\
            ## MODIFIED Requirements

            ### Requirement: Invoice numbering
            #### Scenario: First invoice
            #### Scenario: Numbering per year
            """)
        declared, problems = self.scenarios()
        self.assertEqual(
            declared, {"billing: First invoice", "billing: Numbering per year", "billing: Default currency"}
        )
        self.assertEqual(problems, [])

    def test_removed(self):
        self.delta("## REMOVED Requirements\n\n### Requirement: Invoice currency\n**Reason**: single currency\n")
        declared, problems = self.scenarios()
        self.assertEqual(declared, {"billing: First invoice", "billing: Next invoice"})
        self.assertEqual(problems, [])

    def test_renamed_keeps_the_scenarios(self):
        self.delta("""\
            ## RENAMED Requirements

            - FROM: `### Requirement: Invoice currency`
            - TO: `### Requirement: Invoice money`
            """)
        declared, problems = self.scenarios()
        self.assertEqual(declared, {"billing: First invoice", "billing: Next invoice", "billing: Default currency"})
        self.assertEqual(problems, [])

    def test_renamed_then_modified(self):
        self.delta("""\
            ## RENAMED Requirements

            - FROM: `### Requirement: Invoice currency`
            - TO: `### Requirement: Invoice money`

            ## MODIFIED Requirements

            ### Requirement: Invoice money
            #### Scenario: Default currency
            #### Scenario: Currency per client
            """)
        declared, problems = self.scenarios()
        self.assertIn("billing: Currency per client", declared)
        self.assertEqual(problems, [])

    def test_missing_requirement(self):
        for section, body in (
            ("RENAMED", "- FROM: `### Requirement: Taxes`\n- TO: `### Requirement: Duties`\n"),
            ("REMOVED", "### Requirement: Taxes\n"),
            ("MODIFIED", "### Requirement: Taxes\n#### Scenario: Tax included\n"),
        ):
            with self.subTest(section=section):
                self.delta(f"## {section} Requirements\n\n{body}")
                _declared, problems = self.scenarios()
                self.assertEqual(
                    problems,
                    [f"change 'next', capability 'billing': {section} requirement 'Taxes' is not in the main spec"],
                )

    def test_only_narrows_to_one_change(self):
        self.delta("## ADDED Requirements\n\n### Requirement: A\n#### Scenario: From next\n", change="next")
        self.delta("## ADDED Requirements\n\n### Requirement: B\n#### Scenario: From later\n", change="later")
        self.assertTrue({"billing: From next", "billing: From later"} <= self.scenarios()[0])
        declared, problems = self.scenarios(only="later")
        self.assertIn("billing: From later", declared)
        self.assertNotIn("billing: From next", declared)
        self.assertEqual(problems, [])

    def test_only_names_an_unknown_change(self):
        self.delta("## ADDED Requirements\n\n### Requirement: A\n#### Scenario: From next\n")
        declared, problems = self.scenarios(only="nope")
        self.assertNotIn("billing: From next", declared)
        self.assertEqual(problems, [f"{CHANGE_VARIABLE}=nope is not an active change (active: next)"])

    def test_archived_changes_are_not_read(self):
        self.delta("## REMOVED Requirements\n\n### Requirement: Invoice currency\n", change=ARCHIVE)
        self.assertIn("billing: Default currency", self.scenarios()[0])

    def test_headings_inside_code_fences_are_ignored(self):
        self.delta("""\
            ## ADDED Requirements

            ### Requirement: Examples
            #### Scenario: Real one
            ```markdown
            #### Scenario: Only an example
            ```
            """)
        declared, _problems = self.scenarios()
        self.assertIn("billing: Real one", declared)
        self.assertNotIn("billing: Only an example", declared)


if __name__ == "__main__":
    unittest.main()
