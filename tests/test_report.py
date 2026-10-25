"""Unit tests for the report rules: groupings, their order, counts and exact sums."""

import datetime
import unittest

from gemba import report, tasks
from gemba.report import Sum

TYPES = {"client": "text", "project": "text", "billed": "boolean", "hours": "number", "due": "date"}
WORKSTREAMS = ("support", "operations")
DAY = datetime.date(2026, 9, 30)


TEAM = ("manuel", "ana")


def task(ref, workstream="support", status="open", owner=None, **metadata):
    return tasks.Task(
        f"tasks/{workstream}/2026-09-30-{ref}-t.md",
        owner,
        workstream,
        False,
        ref,
        DAY,
        "T",
        status,
        DAY,
        None,
        metadata,
        None,
    )


def aggregate(selected, by=(), sums=(), team=None):
    return report.aggregate(selected, list(by), list(sums), TYPES, WORKSTREAMS, team)


def keys(result):
    return [group.key for group in result.groups]


class InputsTest(unittest.TestCase):
    def test_groupings(self):
        for key in ("workstream", "status", "client", "billed"):
            with self.subTest(key=key):
                self.assertIsNone(report.grouping_problem(key, TYPES))
        self.assertEqual(
            report.grouping_problem("hours", TYPES),
            "cannot group by 'hours', a number field: group by workstream, status, owner, or a text or boolean field",
        )
        self.assertIn("cannot group by 'due', a date field", report.grouping_problem("due", TYPES) or "")
        self.assertEqual(
            report.grouping_problem("ticket", TYPES),
            "cannot group by 'ticket': it is not workstream, status, owner or a field the config declares",
        )

    def test_owner_only_with_a_team(self):
        self.assertIsNone(report.grouping_problem("owner", TYPES, TEAM))
        self.assertEqual(
            report.grouping_problem("owner", TYPES), "cannot group by 'owner': this obeya declares no team"
        )
        self.assertEqual(
            report.problems(["owner", "owner"], [], TYPES),
            [
                "cannot group by 'owner': this obeya declares no team",
                "'owner' is given more than once as a grouping",
            ],
        )

    def test_sums(self):
        self.assertIsNone(report.sum_problem("hours", TYPES))
        self.assertEqual(
            report.sum_problem("client", TYPES), "cannot sum 'client', a text field: only a number field is summed"
        )
        self.assertEqual(
            report.sum_problem("ticket", TYPES), "cannot sum 'ticket': no metadata schema of the config declares it"
        )
        self.assertIn("cannot sum 'status'", report.sum_problem("status", TYPES) or "")

    def test_every_problem_together(self):
        self.assertEqual(
            report.problems(["hours", "client", "client"], ["client", "hours", "hours"], TYPES),
            [
                "cannot group by 'hours', a number field: "
                "group by workstream, status, owner, or a text or boolean field",
                "'client' is given more than once as a grouping",
                "cannot sum 'client', a text field: only a number field is summed",
                "'hours' is given more than once as a sum",
            ],
        )


class OrderTest(unittest.TestCase):
    def test_workstreams_in_config_order_then_statuses_in_their_order(self):
        selected = [
            task("OPS-1", "operations", "done"),
            task("SUP-1", "support", "done"),
            task("OPS-2", "operations", "open"),
            task("SUP-2", "support", "blocked"),
            task("SUP-3", "support", "in-progress"),
            task("SUP-4", "support", "open"),
        ]
        self.assertEqual(
            [tuple(key.values()) for key in keys(aggregate(selected, ["workstream", "status"]))],
            [
                ("support", "open"),
                ("support", "in-progress"),
                ("support", "blocked"),
                ("support", "done"),
                ("operations", "open"),
                ("operations", "done"),
            ],
        )

    def test_booleans_false_first_then_null(self):
        selected = [task("SUP-1", billed=None), task("SUP-2", billed=True), task("SUP-3", billed=False)]
        self.assertEqual(keys(aggregate(selected, ["billed"])), [{"billed": False}, {"billed": True}, {"billed": None}])

    def test_text_by_code_point_then_null(self):
        selected = [
            task("SUP-1", client="acme"),
            task("SUP-2"),
            task("SUP-3", client="Globex"),
            task("SUP-4", client="é"),
        ]
        self.assertEqual(
            [key["client"] for key in keys(aggregate(selected, ["client"]))], ["Globex", "acme", "é", None]
        )

    def test_owners_in_the_order_of_the_team(self):
        selected = [
            task("AG-SUP-1", owner="ana", hours=3),
            task("MR-SUP-1", owner="manuel", hours=2),
            task("AG-OPS-1", "operations", owner="ana", hours=1),
        ]
        result = aggregate(selected, ["owner"], ["hours"], team=TEAM)
        self.assertEqual(keys(result), [{"owner": "manuel"}, {"owner": "ana"}])
        self.assertEqual([group.refs for group in result.groups], [["MR-SUP-1"], ["AG-SUP-1", "AG-OPS-1"]])
        self.assertEqual([group.sums["hours"] for group in result.groups], [Sum(2, 0), Sum(4, 0)])
        result = aggregate(selected, ["workstream", "owner"], team=TEAM)
        self.assertEqual(
            keys(result),
            [
                {"workstream": "support", "owner": "manuel"},
                {"workstream": "support", "owner": "ana"},
                {"workstream": "operations", "owner": "ana"},
            ],
        )

    def test_refs_in_listing_order(self):
        selected = [task("SUP-2", client="acme"), task("SUP-1", client="acme")]
        self.assertEqual(aggregate(selected, ["client"]).groups[0].refs, ["SUP-2", "SUP-1"])


class GroupingTest(unittest.TestCase):
    def test_text_list_in_each_group_and_once_in_the_total(self):
        selected = [
            task("SUP-1", project=["checkout", "landing", "checkout"], hours=2),
            task("SUP-2", project="landing", hours=3),
        ]
        result = aggregate(selected, ["project"], ["hours"])
        self.assertEqual(
            [(group.key, group.refs, group.sums) for group in result.groups],
            [
                ({"project": "checkout"}, ["SUP-1"], {"hours": Sum(2, 0)}),
                ({"project": "landing"}, ["SUP-1", "SUP-2"], {"hours": Sum(5, 0)}),
            ],
        )
        self.assertEqual((result.tasks, result.sums), (2, {"hours": Sum(5, 0)}))

    def test_empty_list_under_null(self):
        self.assertEqual(keys(aggregate([task("SUP-1", project=[])], ["project"])), [{"project": None}])

    def test_values_of_another_type_under_null_and_missing(self):
        selected = [
            task("SUP-1", client=7, hours="two"),
            task("SUP-2", client="acme", hours=True),
            task("SUP-3", client="acme"),
            task("SUP-4", client="acme", hours=1),
        ]
        result = aggregate(selected, ["client"], ["hours"])
        self.assertEqual(
            [(group.key, group.tasks, group.sums) for group in result.groups],
            [
                ({"client": "acme"}, 3, {"hours": Sum(1, 2)}),
                ({"client": None}, 1, {"hours": Sum(0, 1)}),
            ],
        )
        self.assertEqual(result.sums, {"hours": Sum(1, 3)})

    def test_no_grouping_is_one_group_with_an_empty_key(self):
        selected = [task("SUP-1", hours=1), task("OPS-1", "operations", hours=2)]
        result = aggregate(selected, sums=["hours"])
        self.assertEqual(result.groups, [report.Group({}, 2, ["SUP-1", "OPS-1"], {"hours": Sum(3, 0)})])
        self.assertEqual((result.tasks, result.sums), (2, {"hours": Sum(3, 0)}))

    def test_nothing_selected(self):
        result = aggregate([], ["client"], ["hours"])
        self.assertEqual((result.groups, result.tasks, result.sums), ([], 0, {"hours": Sum(0, 0)}))
        self.assertEqual(aggregate([]).groups, [])


class SumTest(unittest.TestCase):
    def total(self, *values):
        return aggregate([task(f"SUP-{index}", hours=value) for index, value in enumerate(values, 1)], sums=["hours"])

    def test_exact_in_decimal(self):
        self.assertEqual(self.total(0.1, 0.2).sums["hours"], Sum(0.3, 0))
        self.assertEqual(self.total(0.1, 0.2, 0.3).sums["hours"], Sum(0.6, 0))

    def test_integral_total_is_an_integer(self):
        total = self.total(1.5, 0.5).sums["hours"].total
        self.assertEqual(total, 2)
        self.assertIs(type(total), int)
        self.assertIs(type(self.total(2.0).sums["hours"].total), int)

    def test_negative_and_mixed(self):
        self.assertEqual(self.total(3, -1.25, None).sums["hours"], Sum(1.75, 1))


if __name__ == "__main__":
    unittest.main()
