"""Metadata rules: field declarations and their types, the effective schema and values.

The type of a field tells every process how to read, write, compare and operate on a
value of it; what the field means belongs to the person who declared it. This module
knows nothing of task files, statuses, built-in dates or folders.
"""

import dataclasses
import datetime
import decimal
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import yaml

from gemba import values

TEXT = "text"
NUMBER = "number"
BOOLEAN = "boolean"
DATE = "date"
TYPES = (TEXT, NUMBER, BOOLEAN, DATE)
# Names a report groups tasks by, so no field may take them.
RESERVED = ("workstream", "status", "owner")

FIELD_NAME_PATTERN = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
FIELD_KEYS = ("name", "type", "required", "description")
# The key of the base list in the gemba config, which names it in a refusal.
BASE_LIST = "metadata"
# How a value of each type is typed on the command line; `null` clears a value of any type.
FORMS = {TEXT: "any text", NUMBER: "a decimal such as 3, 2.5 or -1", BOOLEAN: "true or false", DATE: "YYYY-MM-DD"}
NUMBER_PATTERN = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
NULL = "null"
SET = "="
ADD = "+="
# The types whose values are ordered, so that a selection may bound them.
BOUNDED = (NUMBER, DATE)


class MetadataError(Exception):
    """A declaration or a value breaks a metadata rule; the message names the field and the rule."""


@dataclass(frozen=True)
class Field:
    name: str
    type: str
    required: bool = False
    description: str | None = None


@dataclass(frozen=True)
class Assignment:
    """One assignment typed on the command line, its value as written."""

    key: str
    operator: str
    text: str


@dataclass(frozen=True)
class Change:
    """What the assignments did to one key, or a key of the schema the map lacked, added as null."""

    key: str
    old: object
    new: object
    added: bool = False

    @property
    def changed(self) -> bool:
        return self.added or show(self.old) != show(self.new)


@dataclass(frozen=True)
class Assigned:
    """The metadata map to write, what changed in it, and every problem that forbids writing it."""

    values: dict[str, object]
    changes: list[Change]
    problems: list[str]

    @property
    def changed(self) -> bool:
        return any(change.changed for change in self.changes)


@dataclass(frozen=True)
class Conditions:
    """Metadata conditions of a selection, each value converted by the type of its key.

    The equalities of one key are alternatives; every other condition must hold. Bounds
    are inclusive. `types` holds the declared type of every key with a condition.
    """

    equalities: Mapping[str, Sequence[object]] = dataclasses.field(default_factory=dict)
    lower: Mapping[str, object] = dataclasses.field(default_factory=dict)
    upper: Mapping[str, object] = dataclasses.field(default_factory=dict)
    types: Mapping[str, str] = dataclasses.field(default_factory=dict)

    def matches(self, values: Mapping[str, object], declared: Collection[str]) -> bool:
        """Whether a task with these metadata `values` meets every condition.

        `declared` holds the keys of the effective schema of the task's workstream: a key
        out of it never matches, and a declared key the task lacks reads as null. A value
        that does not match the type of its key never matches.
        """
        for key in self.types:
            if key not in declared:
                return False
            value = values.get(key)
            if value_problem(self.types[key], value) is not None:
                return False
            if key in self.equalities:
                candidates = value if isinstance(value, list) else [value]
                if not any(_same(candidate, wanted) for candidate in candidates for wanted in self.equalities[key]):
                    return False
            if key in self.lower or key in self.upper:
                if value is None:
                    return False
                ordered: Any = value  # a number or a date, as value_problem checked
                if key in self.lower and ordered < self.lower[key] or key in self.upper and ordered > self.upper[key]:
                    return False
        return True


def parse_fields(declarations: object, where: str) -> tuple[tuple[Field, ...], list[str]]:
    """The fields of one declaration list that parsed, and a problem for every declaration that did not.

    `where` names the list in a problem. A declaration whose name another one already
    took is reported as repeated and its other keys are not checked.
    """
    if declarations is None:
        return (), []
    if not isinstance(declarations, list):
        return (), [f"{where}: must be a list of field declarations"]

    fields = []
    problems = []
    seen = set()
    for index, declaration in enumerate(declarations):
        name = declaration.get("name") if isinstance(declaration, dict) else None
        if isinstance(name, str) and FIELD_NAME_PATTERN.match(name):
            if name in seen:
                problems.append(f"{where}: field '{name}' is declared more than once")
                continue
            seen.add(name)
        try:
            fields.append(_parse_field(declaration, f"{where}[{index}]"))
        except MetadataError as exc:
            problems.append(str(exc))
    return tuple(fields), problems


def _parse_field(declaration: object, at: str) -> Field:
    """One field declaration, `at` naming it in a refusal, which names its first problem."""
    if not isinstance(declaration, dict):
        raise MetadataError(f"{at}: a field declaration must be a map with at least a name and a type")
    name = declaration.get("name")
    if name is None:
        raise MetadataError(f"{at}: field declaration has no name")
    if not isinstance(name, str) or not FIELD_NAME_PATTERN.match(name):
        raise MetadataError(
            f"{at}: field name {name!r} must be snake_case (lowercase letters, digits and single underscores)"
        )
    if name in RESERVED:
        raise MetadataError(
            f"{at}: field name '{name}' is reserved: a report groups every task by its {name} "
            f"(reserved: {', '.join(RESERVED)})"
        )
    unknown = [key for key in declaration if key not in FIELD_KEYS]
    if unknown:
        raise MetadataError(
            f"{at}: field '{name}' has unsupported keys {', '.join(map(str, unknown))} "
            f"(allowed: {', '.join(FIELD_KEYS)})"
        )
    kind = declaration.get("type")
    if kind is None:
        raise MetadataError(f"{at}: field '{name}' has no type (types: {', '.join(TYPES)})")
    if kind not in TYPES:
        shown = f"'{kind}'" if isinstance(kind, str) else repr(kind)
        raise MetadataError(f"{at}: field '{name}' has unknown type {shown} (types: {', '.join(TYPES)})")
    required = declaration.get("required", False)
    if not isinstance(required, bool):
        raise MetadataError(f"{at}: field '{name}' required must be true or false")
    description = declaration.get("description")
    if description is not None and (not isinstance(description, str) or not description.strip()):
        raise MetadataError(f"{at}: field '{name}' description must be a non-empty string")
    return Field(name=name, type=kind, required=required, description=description)


def effective(base: Sequence[Field], own: Sequence[Field]) -> list[Field]:
    """Union by name of the base fields and a workstream's own; the workstream declaration wins."""
    overrides = {field.name: field for field in own}
    schema = [overrides.pop(field.name, field) for field in base]
    schema.extend(overrides.values())
    return schema


def types(base: Sequence[Field], lists: Mapping[str, Sequence[Field]]) -> dict[str, str]:
    """Every declared name, base list first, mapped to its one type.

    `lists` maps each other declaration list, named as a refusal names it, to its
    fields. A name declared with two types is refused, naming the two lists: the
    callers at run time only ever see a config the validator accepted.
    """
    found, problems = _declared_types(base, lists)
    if problems:
        raise MetadataError(problems[0])
    return found


def type_problems(base: Sequence[Field], lists: Mapping[str, Sequence[Field]]) -> list[str]:
    """A problem for every declaration of a name with another type than its first one, naming both lists."""
    return _declared_types(base, lists)[1]


def _declared_types(base: Sequence[Field], lists: Mapping[str, Sequence[Field]]) -> tuple[dict[str, str], list[str]]:
    """Every declared name mapped to the type of its first declaration, and every disagreement with it."""
    found: dict[str, tuple[str, str]] = {}
    problems = []
    for where, fields in [(BASE_LIST, base), *lists.items()]:
        for field in fields:
            first = found.setdefault(field.name, (field.type, where))
            if first[0] != field.type:
                problems.append(
                    f"field '{field.name}' has type {first[0]} in {first[1]} and type {field.type} in {where}: "
                    "a field name has one type across the config"
                )
    return {name: kind for name, (kind, _where) in found.items()}, problems


def parse_assignments(texts: Sequence[str], allow_add: bool) -> tuple[list[Assignment], list[str]]:
    """Split each `key=value` text, and `key+=value` when `allow_add`, the value kept as written.

    No YAML is read.
    """
    assignments = []
    problems = []
    usage = "use key=value or key+=number" if allow_add else "use key=value"
    for text in texts:
        key, separator, value = text.partition(SET)
        operator = SET
        if allow_add and key.endswith("+"):
            key, operator = key[:-1], ADD
        key = key.strip()
        if not separator or not key or key.endswith("+"):
            problems.append(f"invalid metadata assignment '{text}': {usage}")
            continue
        assignments.append(Assignment(key, operator, value))
    return assignments, problems


def convert(kind: str, text: str) -> object:
    """The value of a field of type `kind` typed as `text`, or None for `null`.

    Text is kept as written, a number is a decimal literal, a boolean is `true` or
    `false` and a date is ISO. A refusal reads after "metadata value of '<key>'".
    """
    if text == NULL:
        return None
    if kind == TEXT:
        return text
    if kind == NUMBER and NUMBER_PATTERN.match(text):
        return float(text) if "." in text else int(text)
    if kind == BOOLEAN and text in ("true", "false"):
        return text == "true"
    if kind == DATE and (day := values.iso_date(text)) is not None:
        return day
    raise MetadataError(f"must be a {kind} ({FORMS[kind]}), not '{text}'")


def value_problem(kind: str, value: object) -> str | None:
    """Why a stored value is not of type `kind`, read after "metadata value of '<key>'", or None.

    `null` is a value of every type, and only a text field holds a list, of strings.
    """
    if value is None or _of_type(kind, value):
        return None
    if kind == TEXT and isinstance(value, list) and all(isinstance(item, str) for item in value):
        return None
    return f"must be {'text' if kind == TEXT else f'a {kind}'}, not {show(value)}"


def shape_problem(value: object) -> str | None:
    """Why a stored value is not a scalar or a list of scalars, or None when it is."""
    if _is_scalar(value) or isinstance(value, list) and all(_is_scalar(item) for item in value):
        return None
    return "must be a scalar or a list of scalars"


def add(current: object, amount: object) -> int | float:
    """`current` plus `amount`, two numbers or null, added exactly in decimal from their text.

    Null counts as zero. A total with no fractional part is an int, any other a float
    rebuilt from the exact decimal, so that 0.1 plus 0.2 is 0.3.
    """
    total = _decimal(current) + _decimal(amount)
    if total == total.to_integral_value():
        return int(total)
    return float(total)


def show(value: object) -> str:
    """A value as it reads in YAML flow style: acme, 'no', 3, 2026-10-03, null or [checkout, landing]."""
    text = yaml.safe_dump(value, default_flow_style=True, allow_unicode=True, width=float("inf"))
    return text.removesuffix("\n").removesuffix("\n...")


def assign(
    schema: Sequence[Field], current: Mapping[str, object], assignments: Sequence[Assignment], where: str
) -> Assigned:
    """The metadata map after `assignments`, what changed in it, and every problem found.

    The map holds every key of `schema` in its order, with its assigned value, its value
    in `current` or null, followed by the keys of `current` that the schema does not
    declare, as they were. `where` names the schema in a problem, such as "'support'".
    """
    fields = {field.name: field for field in schema}
    problems = []
    undeclared = [key for key in dict.fromkeys(assignment.key for assignment in assignments) if key not in fields]
    if undeclared:
        declared = ", ".join(fields) if fields else "none"
        problems.append(f"undeclared metadata keys for {where}: {', '.join(undeclared)} (declared: {declared})")

    given: dict[str, list[Assignment]] = {}
    for assignment in assignments:
        if assignment.key in fields:
            given.setdefault(assignment.key, []).append(assignment)
    assigned: dict[str, object] = {}
    for key, group in given.items():
        try:
            assigned[key] = _assigned_value(fields[key], current.get(key), group)
        except MetadataError as exc:
            problems.append(str(exc))

    written = {name: assigned[name] if name in assigned else current.get(name) for name in fields}
    written.update((key, value) for key, value in current.items() if key not in fields)
    # A key whose assignment was refused is reported once, for that refusal.
    missing = [
        field.name
        for field in schema
        if field.required and written[field.name] is None and (field.name in assigned or field.name not in given)
    ]
    if missing:
        problems.append(f"missing required metadata keys for {where}: {', '.join(missing)}")

    changes = [Change(key, current.get(key), assigned[key]) for key in given if key in assigned]
    changes += [Change(name, None, None, added=True) for name in fields if name not in current and name not in given]
    return Assigned(written, changes, problems)


def _assigned_value(field: Field, old: object, group: Sequence[Assignment]) -> object:
    """The value the assignments of one declared key give it, `old` being its value before them.

    A key repeated with `=` gives a text list; `+=` adds a number to `old`, null counting
    as zero.
    """
    key = field.name
    if len({assignment.operator for assignment in group}) > 1:
        raise MetadataError(f"metadata key '{key}' is given with both {SET} and {ADD}: give one or the other")
    if len(group) > 1 and field.type != TEXT:
        raise MetadataError(
            f"metadata key '{key}' is given more than once, but only a text field holds a list "
            f"('{key}' is a {field.type} field)"
        )
    if group[0].operator == ADD:
        if field.type != NUMBER:
            raise MetadataError(f"metadata key '{key}' is a {field.type} field: {ADD} adds to a number field only")
        text = group[0].text
        if text == NULL or not NUMBER_PATTERN.match(text):
            raise MetadataError(f"metadata value of '{key}' must be a number ({FORMS[NUMBER]}), not '{text}'")
        if value_problem(NUMBER, old) is not None:
            raise MetadataError(
                f"cannot add to '{key}': its value {show(old)} is not a number; set it with {key}=<number>"
            )
        return add(old, convert(NUMBER, text))
    if len(group) == 1:
        try:
            return convert(field.type, group[0].text)
        except MetadataError as exc:
            raise MetadataError(f"metadata value of '{key}' {exc}") from None
    items = [assignment.text for assignment in group]
    if NULL in items:
        raise MetadataError(f"metadata key '{key}' is given more than once with null, which clears the value alone")
    return items


def _decimal(value: object) -> decimal.Decimal:
    return decimal.Decimal(0) if value is None else decimal.Decimal(str(value))


def _of_type(kind: str, value: object) -> bool:
    if kind == TEXT:
        return isinstance(value, str)
    if kind == NUMBER:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == BOOLEAN:
        return isinstance(value, bool)
    return isinstance(value, datetime.date) and not isinstance(value, datetime.datetime)


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, datetime.date))


def parse_conditions(
    equalities: Sequence[str], lower: Sequence[str], upper: Sequence[str], types: Mapping[str, str]
) -> tuple[Conditions, list[str]]:
    """The conditions of `key=value` equalities and inclusive bounds, and every problem found.

    `types` maps every name declared in the config to its type. A key no schema declares,
    a value that does not convert to the type of its key, a bound on a key that is not a
    number or a date, a null bound and a second bound of one kind on a key are refused.
    """
    problems: list[str] = []
    undeclared: list[str] = []
    found_equalities: dict[str, list[object]] = {}
    bounds: tuple[dict[str, object], dict[str, object]] = ({}, {})
    for role, texts, bound in (
        ("condition", equalities, None),
        ("lower bound", lower, bounds[0]),
        ("upper bound", upper, bounds[1]),
    ):
        for text in texts:
            key, separator, value_text = text.partition(SET)
            key = key.strip()
            if not separator or not key:
                problems.append(f"invalid {role} '{text}': use key=value")
                continue
            kind = types.get(key)
            if kind is None:
                if key not in undeclared:
                    undeclared.append(key)
                continue
            invalid = f"invalid {role} {key}={value_text}"
            if bound is not None and kind not in BOUNDED:
                problems.append(f"{invalid}: a bound takes a number or date field, and '{key}' is a {kind} field")
                continue
            try:
                value = convert(kind, value_text)
            except MetadataError as exc:
                problems.append(f"{invalid}: metadata value of '{key}' {exc}")
                continue
            if bound is None:
                found_equalities.setdefault(key, []).append(value)
            elif value is None:
                problems.append(f"{invalid}: a bound takes a value, not null")
            elif key in bound:
                problems.append(f"{invalid}: '{key}' takes one {role} at most")
            else:
                bound[key] = value
    declared = ", ".join(types) if types else "none"
    problems += [
        f"undeclared metadata key '{key}': no metadata schema of the config declares it (declared: {declared})"
        for key in undeclared
    ]
    keys = [*found_equalities, *bounds[0], *bounds[1]]
    conditions = Conditions(
        equalities=found_equalities,
        lower=bounds[0],
        upper=bounds[1],
        types={key: types[key] for key in keys},
    )
    return conditions, problems


def _same(value: object, wanted: object) -> bool:
    """Equality of two values of one type: `3` equals `3.0`, and `true` never equals `1`."""
    return value == wanted and isinstance(value, bool) == isinstance(wanted, bool)
