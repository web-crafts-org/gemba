"""Unit tests for the metadata rules: declarations, types, the effective schema and values."""

import datetime
import unittest

import yaml

from gemba import metadata, tasks
from gemba.metadata import Assignment, Field, MetadataError

SCHEMA = (
    Field("client", "text", required=True),
    Field("project", "text"),
    Field("hours", "number"),
    Field("billed", "boolean"),
    Field("due", "date"),
)


class DeclarationTest(unittest.TestCase):
    def parsed(self, declarations):
        """The fields of a list every declaration of which must parse."""
        fields, problems = metadata.parse_fields(declarations, "metadata")
        self.assertEqual(problems, [])
        return fields

    def refused(self, declarations, *fragments):
        """The one problem of a list with one bad declaration, which must hold every fragment."""
        _fields, problems = metadata.parse_fields(declarations, "metadata")
        self.assertEqual(len(problems), 1, problems)
        for fragment in fragments:
            self.assertIn(fragment, problems[0])
        return problems[0]

    def test_absent_list(self):
        self.assertEqual(metadata.parse_fields(None, "metadata"), ((), []))

    def test_minimal_declaration(self):
        self.assertEqual(self.parsed([{"name": "client", "type": "text"}]), (Field("client", "text"),))

    def test_every_type_accepted(self):
        declarations = [{"name": f"field_{kind}", "type": kind} for kind in metadata.TYPES]
        self.assertEqual([field.type for field in self.parsed(declarations)], list(metadata.TYPES))

    def test_complete_declaration(self):
        declaration = {
            "name": "merge_url",
            "type": "text",
            "required": True,
            "description": "Link to the merge request",
        }
        self.assertEqual(
            self.parsed([declaration]),
            (Field("merge_url", "text", required=True, description="Link to the merge request"),),
        )

    def test_not_a_list(self):
        self.refused({"name": "client"}, "metadata: must be a list")

    def test_not_a_map(self):
        self.refused(["client"], "metadata[0]", "must be a map")

    def test_no_name(self):
        self.refused([{"type": "text"}], "metadata[0]", "no name")

    def test_name_not_snake_case(self):
        for bad in ("Client", "merge-url", "merge__url", "_client", 7):
            with self.subTest(name=bad):
                self.refused([{"name": bad, "type": "text"}], "metadata[0]", repr(bad), "snake_case")

    def test_reserved_name(self):
        for name in metadata.RESERVED:
            with self.subTest(name=name):
                self.refused([{"name": name, "type": "text"}], f"field name '{name}' is reserved")

    def test_no_type(self):
        self.refused([{"name": "hours"}], "field 'hours' has no type", "types: text, number, boolean, date")

    def test_unknown_type(self):
        self.refused([{"name": "hours", "type": "integer"}], "unknown type 'integer'", "text, number, boolean, date")
        self.refused([{"name": "hours", "type": 3}], "unknown type 3")

    def test_unsupported_key(self):
        self.refused(
            [{"name": "client", "type": "text", "values": ["acme", "globex"]}],
            "field 'client' has unsupported keys values",
            "allowed: name, type, required, description",
        )

    def test_required_not_boolean(self):
        self.refused([{"name": "client", "type": "text", "required": "sometimes"}], "required must be true or false")

    def test_empty_description(self):
        self.refused([{"name": "client", "type": "text", "description": " "}], "description must be a non-empty")

    def test_repeated_name(self):
        declarations = [{"name": "client", "type": "text"}, {"name": "client", "type": "text"}]
        self.refused(declarations, "field 'client' is declared more than once")

    def test_every_bad_declaration_reported_with_the_fields_that_parsed(self):
        declarations = [
            {"name": "hours", "type": "integer"},
            {"name": "client", "type": "text"},
            {"name": "Due", "type": "date"},
            {"name": "project", "type": "text"},
        ]
        fields, problems = metadata.parse_fields(declarations, "metadata")
        self.assertEqual(fields, (Field("client", "text"), Field("project", "text")))
        self.assertEqual(len(problems), 2)
        self.assertIn("metadata[0]: field 'hours' has unknown type 'integer'", problems[0])
        self.assertIn("metadata[2]: field name 'Due' must be snake_case", problems[1])

    def test_repeated_name_reported_beside_its_first_declaration_problem(self):
        declarations = [{"name": "client", "type": "integer"}, {"name": "client", "type": "text"}]
        fields, problems = metadata.parse_fields(declarations, "metadata")
        self.assertEqual(fields, ())
        self.assertIn("unknown type 'integer'", problems[0])
        self.assertIn("field 'client' is declared more than once", problems[1])


class SchemaTest(unittest.TestCase):
    def test_union_of_base_and_own(self):
        base = (Field("client", "text"), Field("hours", "number"))
        own = (Field("project", "text"),)
        self.assertEqual([field.name for field in metadata.effective(base, own)], ["client", "hours", "project"])

    def test_own_declaration_replaces_the_base_one_and_keeps_the_type(self):
        base = (Field("client", "text", description="Who pays"), Field("hours", "number"))
        own = (Field("client", "text", required=True),)
        self.assertEqual(
            metadata.effective(base, own), [Field("client", "text", required=True), Field("hours", "number")]
        )
        self.assertEqual(metadata.types(base, {"support": own}), {"client": "text", "hours": "number"})

    def test_types_base_first(self):
        base = (Field("client", "text"),)
        lists = {"one": (Field("due", "date"),), "two": (Field("client", "text"), Field("billed", "boolean"))}
        self.assertEqual(metadata.types(base, lists), {"client": "text", "due": "date", "billed": "boolean"})

    def test_base_and_list_disagree(self):
        with self.assertRaises(MetadataError) as caught:
            metadata.types((Field("hours", "number"),), {"workstream 'support' metadata": (Field("hours", "text"),)})
        self.assertEqual(
            str(caught.exception),
            "field 'hours' has type number in metadata and type text in workstream 'support' metadata: "
            "a field name has one type across the config",
        )

    def test_two_lists_disagree(self):
        lists = {"first": (Field("due", "date"),), "second": (Field("due", "text"),)}
        with self.assertRaises(MetadataError) as caught:
            metadata.types((), lists)
        self.assertIn("field 'due' has type date in first and type text in second", str(caught.exception))

    def test_type_problems_of_two_names(self):
        base = (Field("hours", "number"), Field("due", "date"))
        lists = {"first": (Field("hours", "text"),), "second": (Field("due", "text"), Field("hours", "boolean"))}
        self.assertEqual(
            metadata.type_problems(base, lists),
            [
                "field 'hours' has type number in metadata and type text in first: "
                "a field name has one type across the config",
                "field 'due' has type date in metadata and type text in second: "
                "a field name has one type across the config",
                "field 'hours' has type number in metadata and type boolean in second: "
                "a field name has one type across the config",
            ],
        )

    def test_no_type_problems(self):
        self.assertEqual(metadata.type_problems((Field("client", "text"),), {"one": (Field("client", "text"),)}), [])


class ConversionTest(unittest.TestCase):
    def test_text_kept_as_written(self):
        for text in ("acme", "Acme Corp", "no", "007", "3", "2026-10-01", "", " padded ", "{name: acme}", "[a, b]"):
            with self.subTest(text=text):
                self.assertEqual(metadata.convert("text", text), text)

    def test_number(self):
        for text, value in (("3", 3), ("0", 0), ("-1", -1), ("2.5", 2.5), ("-0.25", -0.25), ("10.0", 10.0)):
            with self.subTest(text=text):
                converted = metadata.convert("number", text)
                self.assertEqual(converted, value)
                self.assertIs(type(converted), type(value))

    def test_not_a_number(self):
        for text in ("three", "007", "+1", "1.", ".5", "1e3", "1,5", " 3", "true", ""):
            with self.subTest(text=text):
                with self.assertRaises(MetadataError) as caught:
                    metadata.convert("number", text)
                self.assertIn(f"must be a number (a decimal such as 3, 2.5 or -1), not '{text}'", str(caught.exception))

    def test_boolean(self):
        self.assertIs(metadata.convert("boolean", "true"), True)
        self.assertIs(metadata.convert("boolean", "false"), False)
        for text in ("yes", "no", "True", "1", "on"):
            with self.subTest(text=text), self.assertRaises(MetadataError):
                metadata.convert("boolean", text)

    def test_date(self):
        self.assertEqual(metadata.convert("date", "2026-10-15"), datetime.date(2026, 10, 15))
        for text in ("2026-13-01", "2026-10-1", "15/10/2026", "today"):
            with self.subTest(text=text), self.assertRaises(MetadataError):
                metadata.convert("date", text)

    def test_null_clears_every_type(self):
        for kind in metadata.TYPES:
            with self.subTest(kind=kind):
                self.assertIsNone(metadata.convert(kind, "null"))

    def test_text_reads_back_as_text(self):
        for text in ("no", "007", "2026-10-01", "3", "true", "null", "acme"):
            with self.subTest(text=text):
                written = tasks.dump_frontmatter({"value": metadata.convert("text", text) if text != "null" else text})
                self.assertEqual(yaml.safe_load(written), {"value": text})
                self.assertEqual(metadata.value_problem("text", yaml.safe_load(written)["value"]), None)

    def test_quoted_where_yaml_would_read_another_type(self):
        written = tasks.dump_frontmatter({"client": "no", "code": "007", "due": "2026-10-01", "hours": "3"})
        self.assertEqual(written, "client: 'no'\ncode: '007'\ndue: '2026-10-01'\nhours: '3'\n")


class AssignmentParsingTest(unittest.TestCase):
    def test_value_kept_as_written(self):
        parsed, problems = metadata.parse_assignments(
            ["client=Acme Corp", "url=https://x.invalid/?a=b", "note="], allow_add=False
        )
        self.assertEqual(problems, [])
        self.assertEqual(
            parsed,
            [
                Assignment("client", "=", "Acme Corp"),
                Assignment("url", "=", "https://x.invalid/?a=b"),
                Assignment("note", "=", ""),
            ],
        )

    def test_invalid_assignments(self):
        parsed, problems = metadata.parse_assignments(["client", "=acme", "hours+=2"], allow_add=False)
        self.assertEqual(parsed, [])
        self.assertEqual(
            problems,
            [
                "invalid metadata assignment 'client': use key=value",
                "invalid metadata assignment '=acme': use key=value",
                "invalid metadata assignment 'hours+=2': use key=value",
            ],
        )


class AssignTest(unittest.TestCase):
    def create(self, *texts, schema=SCHEMA):
        parsed, problems = metadata.parse_assignments(list(texts), allow_add=False)
        self.assertEqual(problems, [])
        return metadata.assign(schema, {}, parsed, "'support'")

    def test_values_by_type_in_schema_order(self):
        assigned = self.create("due=2026-10-15", "hours=3", "billed=false", "client=Acme Corp")
        self.assertEqual(assigned.problems, [])
        self.assertEqual(
            list(assigned.values.items()),
            [
                ("client", "Acme Corp"),
                ("project", None),
                ("hours", 3),
                ("billed", False),
                ("due", datetime.date(2026, 10, 15)),
            ],
        )

    def test_repeated_text_key_becomes_a_list(self):
        assigned = self.create("client=acme", "project=checkout", "project=landing", "project=3")
        self.assertEqual(assigned.problems, [])
        self.assertEqual(assigned.values["project"], ["checkout", "landing", "3"])

    def test_undeclared_keys(self):
        assigned = self.create("client=acme", "ticket=PROD-1", "colour=blue", "ticket=PROD-2")
        self.assertEqual(
            assigned.problems,
            ["undeclared metadata keys for 'support': ticket, colour (declared: client, project, hours, billed, due)"],
        )

    def test_undeclared_keys_without_schema(self):
        parsed, _problems = metadata.parse_assignments(["ticket=PROD-1"], allow_add=False)
        assigned = metadata.assign((), {}, parsed, "'support'")
        self.assertEqual(assigned.problems, ["undeclared metadata keys for 'support': ticket (declared: none)"])

    def test_values_of_the_wrong_type(self):
        assigned = self.create("client=acme", "hours=three", "due=2026-13-01", "billed=yes")
        self.assertEqual(
            assigned.problems,
            [
                "metadata value of 'hours' must be a number (a decimal such as 3, 2.5 or -1), not 'three'",
                "metadata value of 'due' must be a date (YYYY-MM-DD), not '2026-13-01'",
                "metadata value of 'billed' must be a boolean (true or false), not 'yes'",
            ],
        )

    def test_repeated_key_on_a_field_that_is_not_text(self):
        assigned = self.create("client=acme", "hours=1", "hours=2")
        self.assertEqual(
            assigned.problems,
            [
                "metadata key 'hours' is given more than once, but only a text field holds a list "
                "('hours' is a number field)"
            ],
        )

    def test_null_in_a_list(self):
        assigned = self.create("client=acme", "project=checkout", "project=null")
        self.assertEqual(
            assigned.problems,
            ["metadata key 'project' is given more than once with null, which clears the value alone"],
        )

    def test_required_missing_or_null(self):
        schema = (*SCHEMA, Field("owner", "text", required=True))
        self.assertEqual(
            self.create("client=null", schema=schema).problems,
            ["missing required metadata keys for 'support': client, owner"],
        )

    def test_required_refused_for_its_type_is_reported_once(self):
        schema = (Field("hours", "number", required=True),)
        self.assertEqual(
            self.create("hours=three", schema=schema).problems,
            ["metadata value of 'hours' must be a number (a decimal such as 3, 2.5 or -1), not 'three'"],
        )


class StoredValueTest(unittest.TestCase):
    def test_values_of_their_type(self):
        for kind, value in (
            ("text", "acme"),
            ("text", ["checkout", "landing"]),
            ("text", []),
            ("number", 3),
            ("number", 2.5),
            ("boolean", False),
            ("date", datetime.date(2026, 10, 3)),
        ):
            with self.subTest(kind=kind, value=value):
                self.assertIsNone(metadata.value_problem(kind, value))
        for kind in metadata.TYPES:
            with self.subTest(kind=kind):
                self.assertIsNone(metadata.value_problem(kind, None))

    def test_values_of_another_type(self):
        for kind, value, shown in (
            ("number", "3", "'3'"),
            ("number", True, "true"),
            ("number", [1, 2], "[1, 2]"),
            ("text", 7, "7"),
            ("text", ["a", 1], "[a, 1]"),
            ("boolean", "yes", "'yes'"),
            ("boolean", 1, "1"),
            ("date", "2026-10-03", "'2026-10-03'"),
            ("date", datetime.datetime(2026, 10, 3, 10, 0), "2026-10-03 10:00:00"),
        ):
            with self.subTest(kind=kind, value=value):
                expected = "must be text" if kind == "text" else f"must be a {kind}"
                self.assertEqual(metadata.value_problem(kind, value), f"{expected}, not {shown}")

    def test_shape(self):
        for value in (None, "a", 1, 2.5, True, datetime.date(2026, 10, 3), [], ["a", 1, None]):
            with self.subTest(value=value):
                self.assertIsNone(metadata.shape_problem(value))
        for value in ({"name": "acme"}, ["a", ["b"]], [{"a": 1}]):
            with self.subTest(value=value):
                self.assertEqual(metadata.shape_problem(value), "must be a scalar or a list of scalars")

    def test_show(self):
        for value, shown in (
            ("acme", "acme"),
            ("no", "'no'"),
            ("Acme Corp", "Acme Corp"),
            (3, "3"),
            (14.5, "14.5"),
            (None, "null"),
            (True, "true"),
            (datetime.date(2026, 10, 3), "2026-10-03"),
            (["checkout", "landing"], "[checkout, landing]"),
        ):
            with self.subTest(value=value):
                self.assertEqual(metadata.show(value), shown)


TYPES = {"client": "text", "project": "text", "hours": "number", "billed": "boolean", "due": "date"}
DECLARED = tuple(TYPES)


class ConditionsTest(unittest.TestCase):
    def conditions(self, equalities=(), lower=(), upper=()):
        conditions, problems = metadata.parse_conditions(list(equalities), list(lower), list(upper), TYPES)
        self.assertEqual(problems, [])
        return conditions

    def matches(self, conditions, declared=DECLARED, **values):
        return conditions.matches(values, declared)

    def test_equality_by_type(self):
        self.assertTrue(self.matches(self.conditions(["client=no"]), client="no"))
        self.assertTrue(self.matches(self.conditions(["billed=false"]), billed=False))
        self.assertFalse(self.matches(self.conditions(["billed=false"]), billed=0))
        due = datetime.date(2026, 10, 15)
        self.assertTrue(self.matches(self.conditions(["due=2026-10-15"]), due=due))
        self.assertFalse(self.matches(self.conditions(["due=2026-10-15"]), due="2026-10-15"))

    def test_numbers_compared_numerically(self):
        self.assertTrue(self.matches(self.conditions(["hours=3"]), hours=3.0))
        self.assertTrue(self.matches(self.conditions(["hours=3.0"]), hours=3))
        self.assertFalse(self.matches(self.conditions(["hours=3"]), hours="3"))
        self.assertFalse(self.matches(self.conditions(["hours=1"]), hours=True))

    def test_list_membership_and_alternatives(self):
        conditions = self.conditions(["project=landing", "project=billing"])
        self.assertTrue(self.matches(conditions, project=["checkout", "landing"]))
        self.assertTrue(self.matches(conditions, project="billing"))
        self.assertFalse(self.matches(conditions, project=["checkout"]))

    def test_null(self):
        conditions = self.conditions(["client=null"])
        self.assertTrue(self.matches(conditions, client=None))
        self.assertFalse(self.matches(conditions, client="acme"))
        self.assertFalse(self.matches(conditions, client=[]))

    def test_missing_key_reads_as_null_only_when_declared(self):
        conditions = self.conditions(["client=null"])
        self.assertTrue(self.matches(conditions))
        self.assertFalse(self.matches(conditions, declared=("hours",)))
        self.assertFalse(self.matches(self.conditions(["client=acme"]), declared=("hours",), client="acme"))

    def test_bounds_on_numbers(self):
        conditions = self.conditions(lower=["hours=2"], upper=["hours=5"])
        found = [hours for hours in (1, 2, 2.5, 5, 5.0, 6, None) if self.matches(conditions, hours=hours)]
        self.assertEqual(found, [2, 2.5, 5, 5.0])
        self.assertTrue(self.matches(self.conditions(lower=["hours=-1.5"]), hours=-1))

    def test_bounds_on_dates(self):
        conditions = self.conditions(lower=["due=2026-09-01"], upper=["due=2026-09-30"])
        days = [datetime.date(2026, 8, 31), datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)]
        days.append(datetime.date(2026, 10, 1))
        self.assertEqual([day for day in days if self.matches(conditions, due=day)], days[1:3])
        self.assertFalse(self.matches(conditions, due=None))
        self.assertFalse(self.matches(conditions))

    def test_value_of_another_type_matches_nothing(self):
        self.assertFalse(self.matches(self.conditions(["hours=null"]), hours="3"))
        self.assertFalse(self.matches(self.conditions(lower=["hours=1"]), hours="3"))
        self.assertFalse(self.matches(self.conditions(["due=null"]), due=datetime.datetime(2026, 10, 3, 10, 0)))

    def test_conditions_on_several_keys_all_hold(self):
        conditions = self.conditions(["client=acme"], lower=["hours=2"])
        self.assertTrue(self.matches(conditions, client="acme", hours=3))
        self.assertFalse(self.matches(conditions, client="acme", hours=1))
        self.assertFalse(self.matches(conditions, client="globex", hours=3))

    def test_no_condition_matches_everything(self):
        self.assertTrue(metadata.Conditions().matches({"anything": {"nested": 1}}, ()))

    def test_refused_conditions_reported_together(self):
        _conditions, problems = metadata.parse_conditions(
            ["hours=three", "client", "ticket=PROD-1", "colour=red", "ticket=PROD-2"],
            ["client=a", "hours=1", "hours=1", "due=null"],
            ["billed=true", "due=2026-13-01"],
            TYPES,
        )
        self.assertEqual(
            problems,
            [
                "invalid condition hours=three: metadata value of 'hours' must be a number "
                "(a decimal such as 3, 2.5 or -1), not 'three'",
                "invalid condition 'client': use key=value",
                "invalid lower bound client=a: a bound takes a number or date field, and 'client' is a text field",
                "invalid lower bound hours=1: 'hours' takes one lower bound at most",
                "invalid lower bound due=null: a bound takes a value, not null",
                "invalid upper bound billed=true: a bound takes a number or date field, "
                "and 'billed' is a boolean field",
                "invalid upper bound due=2026-13-01: metadata value of 'due' must be a date (YYYY-MM-DD), "
                "not '2026-13-01'",
                "undeclared metadata key 'ticket': no metadata schema of the config declares it "
                "(declared: client, project, hours, billed, due)",
                "undeclared metadata key 'colour': no metadata schema of the config declares it "
                "(declared: client, project, hours, billed, due)",
            ],
        )


class SetModeTest(unittest.TestCase):
    def set(self, current, *texts, schema=SCHEMA):
        parsed, problems = metadata.parse_assignments(list(texts), allow_add=True)
        self.assertEqual(problems, [])
        return metadata.assign(schema, current, parsed, "'support'")

    def current(self, **values):
        return {"client": "acme", "project": None, "hours": None, "billed": None, "due": None, **values}

    def test_parse_with_add(self):
        parsed, problems = metadata.parse_assignments(["hours+=2.5", "client=a+b", "x++=1", "y"], allow_add=True)
        self.assertEqual(parsed, [Assignment("hours", "+=", "2.5"), Assignment("client", "=", "a+b")])
        self.assertEqual(
            problems,
            [
                "invalid metadata assignment 'x++=1': use key=value or key+=number",
                "invalid metadata assignment 'y': use key=value or key+=number",
            ],
        )

    def test_add_to_a_number(self):
        assigned = self.set(self.current(hours=12), "hours+=2.5")
        self.assertEqual(assigned.problems, [])
        self.assertEqual(assigned.values["hours"], 14.5)
        self.assertEqual(assigned.changes, [metadata.Change("hours", 12, 14.5)])

    def test_null_or_missing_counts_as_zero(self):
        self.assertEqual(self.set(self.current(), "hours+=2").values["hours"], 2)
        current = self.current()
        del current["hours"]
        self.assertEqual(self.set(current, "hours+=-1.5").values["hours"], -1.5)

    def test_add_refused(self):
        cases = (
            (
                self.current(hours="3"),
                "hours+=1",
                "cannot add to 'hours': its value '3' is not a number; set it with hours=<number>",
            ),
            (self.current(), "due+=1", "metadata key 'due' is a date field: += adds to a number field only"),
            (
                self.current(),
                "hours+=null",
                "metadata value of 'hours' must be a number (a decimal such as 3, 2.5 or -1), not 'null'",
            ),
            (
                self.current(),
                "hours+=two",
                "metadata value of 'hours' must be a number (a decimal such as 3, 2.5 or -1), not 'two'",
            ),
        )
        for current, text, problem in cases:
            with self.subTest(text=text):
                assigned = self.set(current, text)
                self.assertEqual(assigned.problems, [problem])

    def test_set_and_add_on_one_key_refused(self):
        self.assertEqual(
            self.set(self.current(), "hours=1", "hours+=2").problems,
            ["metadata key 'hours' is given with both = and +=: give one or the other"],
        )

    def test_add_twice_refused(self):
        self.assertIn("is given more than once", self.set(self.current(), "hours+=1", "hours+=2").problems[0])

    def test_required_field_not_cleared(self):
        self.assertEqual(
            self.set(self.current(), "client=null").problems, ["missing required metadata keys for 'support': client"]
        )

    def test_required_field_still_missing_on_an_older_task(self):
        self.assertEqual(
            self.set({"hours": 1}, "hours=2").problems, ["missing required metadata keys for 'support': client"]
        )

    def test_schema_order_missing_keys_added_and_undeclared_kept_after(self):
        assigned = self.set({"ticket_id": "PROD-1", "hours": 3, "client": "acme"}, "client=globex")
        self.assertEqual(assigned.problems, [])
        self.assertEqual(
            list(assigned.values.items()),
            [
                ("client", "globex"),
                ("project", None),
                ("hours", 3),
                ("billed", None),
                ("due", None),
                ("ticket_id", "PROD-1"),
            ],
        )
        self.assertEqual(
            assigned.changes,
            [
                metadata.Change("client", "acme", "globex"),
                metadata.Change("project", None, None, added=True),
                metadata.Change("billed", None, None, added=True),
                metadata.Change("due", None, None, added=True),
            ],
        )

    def test_changes_in_the_order_given(self):
        assigned = self.set(self.current(hours=2), "hours=2", "client=acme", "project=a", "project=b")
        self.assertEqual(
            [(change.key, change.changed) for change in assigned.changes],
            [("hours", False), ("client", False), ("project", True)],
        )
        self.assertTrue(assigned.changed)
        self.assertFalse(self.set(self.current(), "client=acme").changed)

    def test_same_number_written_another_way_is_a_change(self):
        self.assertTrue(self.set(self.current(hours=2), "hours=2.0").changed)


class AddTest(unittest.TestCase):
    def test_exact_in_decimal(self):
        self.assertEqual(metadata.add(0.1, 0.2), 0.3)
        self.assertEqual(metadata.add(0.3, -0.1), 0.2)

    def test_integral_total_is_an_integer(self):
        total = metadata.add(1.5, 0.5)
        self.assertEqual(total, 2)
        self.assertIs(type(total), int)

    def test_null_counts_as_zero(self):
        self.assertEqual(metadata.add(None, 2.5), 2.5)
        self.assertIs(type(metadata.add(None, 3)), int)


if __name__ == "__main__":
    unittest.main()
