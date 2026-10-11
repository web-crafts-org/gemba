"""Unit tests for config discovery, validation, the effective metadata schema and the effective blocks."""

import tempfile
import textwrap
import unittest
from pathlib import Path

from gemba import config, metadata

VALID = """\
default_workstream: operations
workstreams:
  support:
    prefix: SUP
    description: Investigate a client-reported problem
  operations:
    prefix: OPS
    description: Anything that does not fit another workstream
"""


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, text):
        (self.root / config.CONFIG_FILENAME).write_text(textwrap.dedent(text), encoding="utf-8")

    def load(self, text):
        self.write(text)
        return config.load(root=self.root)

    def assertRefused(self, text, *fragments):
        self.write(text)
        with self.assertRaises(config.ConfigError) as caught:
            config.load(root=self.root)
        message = str(caught.exception)
        for fragment in fragments:
            self.assertIn(fragment, message)
        return message


class DiscoveryTest(ConfigTestCase):
    def test_finds_config_from_nested_folder(self):
        self.write(VALID)
        nested = self.root / "runs" / "support" / "deep"
        nested.mkdir(parents=True)
        self.assertEqual(config.find_root(nested), self.root)
        self.assertEqual(config.load(cwd=nested).root, self.root)

    def test_no_config_found(self):
        nested = self.root / "empty" / "folder"
        nested.mkdir(parents=True)
        with self.assertRaises(config.ConfigError) as caught:
            config.find_root(nested)
        self.assertIn("no gemba config found", str(caught.exception))

    def test_explicit_root_without_config(self):
        with self.assertRaises(config.ConfigError) as caught:
            config.load(root=self.root)
        self.assertIn("no gemba config found", str(caught.exception))

    def test_explicit_root_overrides_discovery(self):
        self.write(VALID)
        other = self.root / "other"
        other.mkdir()
        (other / config.CONFIG_FILENAME).write_text(VALID.replace("SUP", "HLP"), encoding="utf-8")
        self.assertEqual(config.load(root=self.root, cwd=other).workstreams["support"].prefix, "SUP")


class ValidationTest(ConfigTestCase):
    def test_valid_catalogue(self):
        loaded = self.load(VALID)
        self.assertEqual(loaded.default_workstream, "operations")
        self.assertEqual(list(loaded.workstreams), ["support", "operations"])
        self.assertEqual(loaded.workstreams["support"].prefix, "SUP")

    def test_malformed_yaml(self):
        self.assertRefused("workstreams: [unclosed\n", "malformed YAML")

    def test_not_a_map(self):
        self.assertRefused("- just\n- a list\n", "must be a map")

    def test_workstreams_missing(self):
        self.assertRefused("default_workstream: operations\n", "workstreams must be a non-empty map")

    def test_identifier_not_kebab_case(self):
        for bad in ("Code_Reviews", "code--reviews", "-support", "support-"):
            with self.subTest(identifier=bad):
                self.assertRefused(VALID.replace("  support:", f"  {bad}:"), f"workstream '{bad}'", "kebab-case")

    def test_invalid_prefix(self):
        for bad in ('""', "sup", "SUP1", "S-P"):
            with self.subTest(prefix=bad):
                self.assertRefused(VALID.replace("prefix: SUP", f"prefix: {bad}"), "workstream 'support'", "prefix")

    def test_prefix_read_as_boolean(self):
        self.assertRefused(VALID.replace("prefix: SUP", "prefix: NO"), "workstream 'support'", "quote it")

    def test_duplicate_prefix_names_both(self):
        self.assertRefused(VALID.replace("prefix: OPS", "prefix: SUP"), "'support'", "'operations'", "'SUP'")

    def test_missing_description(self):
        text = VALID.replace("    description: Investigate a client-reported problem\n", "")
        self.assertRefused(text, "workstream 'support'", "description")

    def test_empty_description(self):
        text = VALID.replace("description: Investigate a client-reported problem", 'description: "  "')
        self.assertRefused(text, "workstream 'support'", "description")

    def test_default_missing(self):
        self.assertRefused(VALID.replace("default_workstream: operations\n", ""), "default_workstream is missing")

    def test_default_not_in_catalogue(self):
        self.assertRefused(VALID.replace("default_workstream: operations", "default_workstream: ops"), "'ops'")

    def test_field_without_name(self):
        self.assertRefused(VALID + "metadata:\n  - required: true\n", "metadata[0]", "no name")

    def test_field_name_not_snake_case(self):
        for bad in ("Client", "merge-url", "merge__url", "_client"):
            with self.subTest(name=bad):
                text = VALID + f"metadata:\n  - {{ name: client, type: text }}\n  - {{ name: {bad}, type: text }}\n"
                self.assertRefused(text, "metadata[1]", repr(bad), "snake_case")

    def test_field_without_type(self):
        self.assertRefused(VALID + "metadata:\n  - { name: hours }\n", "metadata[0]", "field 'hours' has no type")

    def test_field_with_unknown_type(self):
        text = self.with_block("metadata:\n  - { name: hours, type: integer }\n")
        self.assertRefused(text, "workstream 'support' metadata[0]", "unknown type 'integer'", "text, number")

    def test_field_with_reserved_name(self):
        for name in ("workstream", "status"):
            with self.subTest(name=name):
                text = VALID + f"metadata:\n  - {{ name: {name}, type: text }}\n"
                self.assertRefused(text, "metadata[0]", f"field name '{name}' is reserved")

    def test_field_required_not_boolean(self):
        text = VALID + "metadata:\n  - { name: client, type: text, required: sometimes }\n"
        self.assertRefused(text, "field 'client'")

    def test_one_type_per_name_across_base_and_workstream(self):
        text = self.with_block("metadata:\n  - { name: hours, type: text }\n")
        text += "metadata:\n  - { name: hours, type: number }\n"
        self.assertRefused(
            text, "field 'hours' has type number in metadata and type text in workstream 'support' metadata"
        )

    def test_one_type_per_name_across_workstreams(self):
        text = self.with_block("metadata:\n  - { name: due, type: date }\n").replace(
            "    description: Anything that does not fit another workstream\n",
            "    description: Anything that does not fit another workstream\n"
            "    metadata:\n      - { name: due, type: text }\n",
        )
        self.assertRefused(text, "workstream 'support' metadata and type text in workstream 'operations' metadata")

    def test_repeated_name_in_base_list(self):
        text = VALID + "metadata:\n  - { name: client, type: text }\n  - { name: client, type: text }\n"
        self.assertRefused(text, "metadata", "field 'client' is declared more than once")

    def test_repeated_name_in_workstream_list(self):
        text = VALID.replace(
            "    description: Investigate a client-reported problem\n",
            "    description: Investigate a client-reported problem\n"
            "    metadata:\n      - { name: project, type: text }\n      - { name: project, type: text }\n",
        )
        self.assertRefused(text, "workstream 'support' metadata", "field 'project' is declared more than once")

    def test_create_rules_must_be_strings(self):
        text = VALID.replace(
            "    description: Investigate a client-reported problem\n",
            "    description: Investigate a client-reported problem\n    create:\n      rules: just one string\n",
        )
        self.assertRefused(text, "workstream 'support'", "create.rules")

    def with_block(self, block):
        return VALID.replace(
            "    description: Investigate a client-reported problem\n",
            f"    description: Investigate a client-reported problem\n{textwrap.indent(block, '    ')}",
        )

    def test_valid_list_block(self):
        text = self.with_block("list:\n  context: Clients call this area tickets\n  rules:\n    - mention the client\n")
        self.assertEqual(
            self.load(text).workstreams["support"].processes["list"],
            {"context": "Clients call this area tickets", "rules": ["mention the client"]},
        )

    def test_list_rules_must_be_strings(self):
        for rules in ("just one string", "['']", "[1, 2]"):
            with self.subTest(rules=rules):
                text = self.with_block(f"list:\n  rules: {rules}\n")
                self.assertRefused(text, "workstream 'support'", "list.rules must be a list of non-empty strings")

    def test_list_context_must_be_a_string(self):
        text = self.with_block("list:\n  context: [one, two]\n")
        self.assertRefused(text, "workstream 'support'", "list.context must be a string")

    def test_list_block_must_be_a_map(self):
        self.assertRefused(self.with_block("list: [rules]\n"), "workstream 'support'", "list must be a map")

    def test_record_rules_must_be_strings(self):
        text = self.with_block("record:\n  rules: name the client in every bullet\n")
        self.assertRefused(text, "workstream 'support'", "record.rules must be a list of non-empty strings")

    def test_report_context_must_be_a_string(self):
        text = self.with_block("report:\n  context: [one, two]\n")
        self.assertRefused(text, "workstream 'support'", "report.context must be a string")

    def test_mark_rules_must_be_strings(self):
        text = self.with_block("mark:\n  rules: before done, confirm the client was told\n")
        self.assertRefused(text, "workstream 'support'", "mark.rules must be a list of non-empty strings")

    def test_archive_context_must_be_a_string(self):
        text = self.with_block("archive:\n  context: [one, two]\n")
        self.assertRefused(text, "workstream 'support'", "archive.context must be a string")

    def test_set_block_validated(self):
        accepted = self.with_block("set:\n  context: Invoiced monthly\n  rules:\n    - set dates only when done\n")
        self.assertEqual(
            self.load(accepted).workstreams["support"].processes["set"],
            {"context": "Invoiced monthly", "rules": ["set dates only when done"]},
        )
        self.assertRefused(self.with_block("set:\n  rules: one string\n"), "workstream 'support'", "set.rules")
        self.assertRefused(self.with_block("set:\n  context: [a, b]\n"), "workstream 'support'", "set.context")

    def test_unknown_process_block_ignored(self):
        text = VALID.replace(
            "    description: Investigate a client-reported problem\n",
            "    description: Investigate a client-reported problem\n    publish:\n      anything: [goes, here]\n",
        )
        self.assertEqual(self.load(text).workstreams["support"].prefix, "SUP")

    def test_valid_harness_block(self):
        block = (
            "harness:\n"
            "  guide: Write for the client.\n"
            "  launch:\n    context: Clients call this area tickets\n"
            "  note:\n    rules:\n      - name the client\n"
            "  resolve:\n    context: Replies go to the client portal\n"
            "  remove:\n    rules:\n      - check the client report was sent\n"
        )
        self.assertEqual(
            self.load(self.with_block(block)).workstreams["support"].processes["harness"],
            {
                "guide": "Write for the client.",
                "launch": {"context": "Clients call this area tickets"},
                "note": {"rules": ["name the client"]},
                "resolve": {"context": "Replies go to the client portal"},
                "remove": {"rules": ["check the client report was sent"]},
            },
        )

    def test_harness_block_must_be_a_map(self):
        message = self.assertRefused(self.with_block("harness: [guide]\n"), "workstream 'support'", "harness must be")
        self.assertIn("allowed keys: guide, launch, note, resolve, remove", message)

    def test_harness_guide_must_be_a_non_empty_string(self):
        for guide in ("[one, two]", '"  "', "{text: hello}", "3"):
            with self.subTest(guide=guide):
                text = self.with_block(f"harness:\n  guide: {guide}\n")
                self.assertRefused(text, "workstream 'support'", "harness.guide must be a non-empty string")

    def test_harness_verb_blocks_are_validated_as_verb_blocks(self):
        for block, fragment in (
            ("note:\n    rules: just one string\n", "harness.note.rules must be a list of non-empty strings"),
            ("resolve:\n    context: [one, two]\n", "harness.resolve.context must be a string"),
            ("launch: [rules]\n", "harness.launch must be a map"),
            ("remove:\n    rules: just one string\n", "harness.remove.rules must be a list of non-empty strings"),
        ):
            with self.subTest(block=block):
                self.assertRefused(self.with_block(f"harness:\n  {block}"), "workstream 'support'", fragment)

    def test_unknown_key_inside_harness_refused(self):
        for key in ("rules", "context", "record"):
            with self.subTest(key=key):
                text = self.with_block(f"harness:\n  {key}: [anything]\n")
                self.assertRefused(
                    text,
                    "workstream 'support'",
                    f"harness.{key} is not a key of harness",
                    "allowed: guide, launch, note, resolve, remove",
                )

    def test_valid_worktree_block(self):
        block = (
            "worktree:\n"
            "  add:\n    rules:\n      - start from the branch deployed to production\n"
            "  list:\n    context: Each repository deploys its own branch\n"
            "  remove:\n    rules:\n      - check the report was sent\n"
        )
        self.assertEqual(
            self.load(self.with_block(block)).workstreams["support"].processes["worktree"],
            {
                "add": {"rules": ["start from the branch deployed to production"]},
                "list": {"context": "Each repository deploys its own branch"},
                "remove": {"rules": ["check the report was sent"]},
            },
        )

    def test_worktree_verb_blocks_are_validated_as_verb_blocks(self):
        for block, fragment in (
            ("add:\n    rules: just one string\n", "worktree.add.rules must be a list of non-empty strings"),
            ("list:\n    context: [one, two]\n", "worktree.list.context must be a string"),
            ("remove: [rules]\n", "worktree.remove must be a map"),
        ):
            with self.subTest(block=block):
                self.assertRefused(self.with_block(f"worktree:\n  {block}"), "workstream 'support'", fragment)

    def test_worktree_takes_no_guide(self):
        text = self.with_block("worktree:\n  guide: Check out the source branch.\n")
        self.assertRefused(
            text, "workstream 'support'", "worktree.guide is not a key of worktree", "(allowed: add, list, remove)"
        )

    def test_unknown_key_inside_worktree_refused(self):
        for key in ("rules", "context", "launch"):
            with self.subTest(key=key):
                text = self.with_block(f"worktree:\n  {key}: [anything]\n")
                self.assertRefused(text, "workstream 'support'", f"worktree.{key} is not a key of worktree")

    def test_worktree_block_must_be_a_map(self):
        message = self.assertRefused(self.with_block("worktree: [add]\n"), "workstream 'support'", "worktree must be")
        self.assertIn("(allowed keys: add, list, remove)", message)


class BaseBlocksTest(ConfigTestCase):
    def test_valid_base_blocks_kept(self):
        text = VALID + (
            "create:\n  context: Every task is billed to one client\n"
            "harness:\n  guide: Open the harness through its workspace.\n  note:\n    rules: [name the client]\n"
            "worktree:\n  add:\n    rules: [start from the default branch]\n"
        )
        loaded = self.load(text)
        self.assertEqual(
            loaded.processes,
            {
                "create": {"context": "Every task is billed to one client"},
                "harness": {"guide": "Open the harness through its workspace.", "note": {"rules": ["name the client"]}},
                "worktree": {"add": {"rules": ["start from the default branch"]}},
            },
        )
        self.assertEqual(loaded.workstreams["support"].processes, {})

    def test_no_base_blocks(self):
        self.assertEqual(self.load(VALID).processes, {})

    def test_only_process_keys_kept(self):
        loaded = self.load(VALID + "organization: nakatomi\nlist:\n  rules: [mention the client]\n")
        self.assertEqual(loaded.processes, {"list": {"rules": ["mention the client"]}})

    def test_malformed_verb_block_refused(self):
        self.assertRefused(
            VALID + "list:\n  rules: just one string\n", "top level", "list.rules must be a list of non-empty strings"
        )

    def test_malformed_group_block_refused(self):
        self.assertRefused(
            VALID + "worktree:\n  guide: Check out the source branch.\n",
            "top level",
            "worktree.guide is not a key of worktree",
        )
        self.assertRefused(VALID + "harness:\n  rules: [anything]\n", "top level", "harness.rules is not a key")

    def test_malformed_guide_refused(self):
        self.assertRefused(
            VALID + "harness:\n  guide: [one, two]\n", "top level", "harness.guide must be a non-empty string"
        )


class GuideTest(unittest.TestCase):
    def test_level_with_a_guide(self):
        self.assertEqual(
            config.guide({"harness": {"guide": "Write for the client.", "note": {}}}), "Write for the client."
        )

    def test_level_without_a_guide(self):
        self.assertIsNone(config.guide({}))
        self.assertIsNone(config.guide({"create": {"rules": ["name the client"]}}))
        self.assertIsNone(config.guide({"harness": {"note": {"rules": ["name the client"]}}}))


class WorktreeKeysTest(ConfigTestCase):
    def test_absent(self):
        loaded = self.load(VALID)
        self.assertIsNone(loaded.organization)
        self.assertIsNone(loaded.repos_dir)
        self.assertEqual(loaded.branch_prefix, "gemba")

    def test_accepted(self):
        loaded = self.load(VALID + "organization: naka-tomi2\nrepos_dir: ~/projects\nbranch_prefix: nk\n")
        self.assertEqual(loaded.organization, "naka-tomi2")
        self.assertEqual(loaded.repos_dir, "~/projects")
        self.assertEqual(loaded.branch_prefix, "nk")

    def test_repos_dir_kept_as_declared(self):
        for declared in ("/srv/repos", "repos", "../projects"):
            with self.subTest(repos_dir=declared):
                self.assertEqual(self.load(VALID + f"repos_dir: {declared}\n").repos_dir, declared)

    def test_malformed_names(self):
        for key in ("organization", "branch_prefix"):
            for declaration in ('"Nakatomi Corp"', '""', "[nakatomi]", "Gemba/", "naka--tomi", "-web", "3", "true"):
                with self.subTest(key=key, declaration=declaration):
                    self.assertRefused(VALID + f"{key}: {declaration}\n", f"{key} must be kebab-case")

    def test_malformed_repos_dir(self):
        for declaration in ('""', '"   "', "[~/projects]", "{path: ~/projects}", "3", "true"):
            with self.subTest(declaration=declaration):
                self.assertRefused(VALID + f"repos_dir: {declaration}\n", "repos_dir must be a non-empty string")


class IdeTest(ConfigTestCase):
    def test_absent(self):
        self.assertIsNone(self.load(VALID).ide)

    def test_command_with_arguments(self):
        self.assertEqual(self.load(VALID + 'ide: "code -n"\n').ide, "code -n")

    def test_malformed(self):
        for declaration in ('""', '"   "', "[code, -n]", "{command: code}", "3", "true"):
            with self.subTest(declaration=declaration):
                self.assertRefused(VALID + f"ide: {declaration}\n", "ide must be a non-empty string")


class AgentProvidersTest(ConfigTestCase):
    KNOWN = "known providers: claude, agents"

    def test_absent(self):
        self.assertIsNone(self.load(VALID).agent_providers)

    def test_known_providers_in_order(self):
        self.assertEqual(self.load(VALID + "agent_providers: [agents, claude]\n").agent_providers, ("agents", "claude"))

    def test_unknown_provider(self):
        self.assertRefused(VALID + "agent_providers: [claude, cursor]\n", "agent_providers", "'cursor'", self.KNOWN)

    def test_repeated_provider(self):
        text = VALID + "agent_providers: [claude, claude]\n"
        self.assertRefused(text, "agent_providers", "'claude' is listed more than once", self.KNOWN)

    def test_malformed(self):
        for declaration in ("claude", "[]", "{claude: true}", "[claude, 1]", "[[claude]]"):
            with self.subTest(declaration=declaration):
                text = VALID + f"agent_providers: {declaration}\n"
                self.assertRefused(text, "agent_providers must be a non-empty list", self.KNOWN)


class EffectiveSchemaTest(ConfigTestCase):
    def schema(self, text, workstream_id):
        return self.load(text).effective_schema(workstream_id)

    def test_union_of_base_and_workstream(self):
        text = (
            VALID.replace(
                "    description: Investigate a client-reported problem\n",
                "    description: Investigate a client-reported problem\n"
                "    metadata:\n      - { name: project, type: text }\n",
            )
            + "metadata:\n  - { name: client, type: text }\n  - { name: hours, type: number }\n"
        )
        self.assertEqual([field.name for field in self.schema(text, "support")], ["client", "hours", "project"])

    def test_workstream_overrides_base(self):
        text = (
            VALID.replace(
                "    description: Investigate a client-reported problem\n",
                "    description: Investigate a client-reported problem\n"
                "    metadata:\n      - { name: client, type: text, required: true }\n",
            )
            + "metadata:\n  - { name: client, type: text, description: Who pays }\n"
        )
        loaded = self.load(text)
        self.assertEqual(loaded.effective_schema("support"), [metadata.Field("client", "text", required=True)])
        self.assertEqual(
            loaded.effective_schema("operations"), [metadata.Field("client", "text", description="Who pays")]
        )

    def test_empty_schema(self):
        self.assertEqual(self.schema(VALID, "support"), [])

    def test_types_of_every_declared_name(self):
        text = (
            VALID.replace(
                "    description: Investigate a client-reported problem\n",
                "    description: Investigate a client-reported problem\n"
                "    metadata:\n      - { name: invoiced, type: date }\n      - { name: client, type: text }\n",
            )
            + "metadata:\n  - { name: client, type: text }\n  - { name: hours, type: number }\n"
        )
        self.assertEqual(self.load(text).types(), {"client": "text", "hours": "number", "invoiced": "date"})


class EffectiveBlockTest(ConfigTestCase):
    SUPPORT = "    description: Investigate a client-reported problem\n"

    def with_support(self, base, own):
        """VALID with `base` appended at the top level and `own` inside the support block."""
        return VALID.replace(self.SUPPORT, self.SUPPORT + textwrap.indent(own, "    ")) + base

    def test_declared_at_neither_level(self):
        self.assertEqual(self.load(VALID).effective_block("support", "create"), config.Block(context=None, rules=()))

    def test_declared_at_one_level(self):
        loaded = self.load(self.with_support("create:\n  context: Every task has a client\n", ""))
        self.assertEqual(loaded.effective_block("support", "create"), config.Block("Every task has a client", ()))
        loaded = self.load(self.with_support("", "create:\n  rules: [ask for the client]\n"))
        self.assertEqual(loaded.effective_block("support", "create"), config.Block(None, ("ask for the client",)))
        self.assertEqual(loaded.effective_block("operations", "create"), config.Block(None, ()))

    def test_declared_at_both_levels(self):
        text = self.with_support(
            "create:\n  context: |\n    Every task has a client.\n  rules: [ask who requested the work]\n",
            "create:\n  context: |\n    Support work comes from a ticket.\n  rules: [ask for the ticket]\n",
        )
        block = self.load(text).effective_block("support", "create")
        self.assertEqual(block.context, "Every task has a client.\n\nSupport work comes from a ticket.\n")
        self.assertEqual(block.rules, ("ask who requested the work", "ask for the ticket"))

    def test_blank_context_counts_as_not_declared(self):
        text = self.with_support('create:\n  context: "  "\n', "create:\n  context: Support work\n")
        self.assertEqual(self.load(text).effective_block("support", "create").context, "Support work")

    def test_verb_of_a_group(self):
        text = self.with_support(
            "worktree:\n  add:\n    rules: [start from the default branch]\n",
            "worktree:\n  add:\n    rules: [start from the branch deployed to production]\n",
        )
        loaded = self.load(text)
        self.assertEqual(
            loaded.effective_block("support", "worktree", "add").rules,
            ("start from the default branch", "start from the branch deployed to production"),
        )
        self.assertEqual(loaded.effective_block("support", "worktree", "remove"), config.Block(None, ()))

    def test_unknown_verb_refused(self):
        loaded = self.load(VALID)
        for process, verb in (("worktree", None), ("create", "add"), ("harness", "guide")):
            with self.subTest(process=process, verb=verb), self.assertRaises(ValueError):
                loaded.effective_block("support", process, verb)

    def test_guide(self):
        loaded = self.load(self.with_support("harness:\n  guide: Write for the client.\n", ""))
        self.assertEqual(loaded.effective_guide("support"), config.Guide("Write for the client.", None))
        loaded = self.load(
            self.with_support("harness:\n  guide: Write for the client.\n", "harness:\n  guide: Cite it.\n")
        )
        self.assertEqual(loaded.effective_guide("support"), config.Guide("Write for the client.", "Cite it."))
        self.assertEqual(loaded.effective_guide("operations"), config.Guide("Write for the client.", None))

    def test_every_process_present_without_any_block(self):
        empty = {"context": None, "rules": []}
        self.assertEqual(
            self.load(VALID).effective_processes("operations"),
            {
                "create": empty,
                "list": empty,
                "record": empty,
                "report": empty,
                "mark": empty,
                "archive": empty,
                "set": empty,
                "harness": {
                    "guide": {"organization": None, "workstream": None},
                    "launch": empty,
                    "note": empty,
                    "resolve": empty,
                    "remove": empty,
                },
                "worktree": {"add": empty, "list": empty, "remove": empty},
            },
        )

    def test_processes_carry_the_effective_blocks(self):
        text = self.with_support(
            "harness:\n  guide: Write for the client.\n  note:\n    rules: [name the client]\n",
            "harness:\n  guide: Cite the ticket.\n",
        )
        processes = self.load(text).effective_processes("support")
        harness = processes["harness"]
        assert isinstance(harness, dict)
        self.assertEqual(harness["guide"], {"organization": "Write for the client.", "workstream": "Cite the ticket."})
        self.assertEqual(harness["note"], {"context": None, "rules": ["name the client"]})


if __name__ == "__main__":
    unittest.main()
