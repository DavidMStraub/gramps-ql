"""Gramps Query Language."""

from __future__ import annotations  # can be removed at 3.8 EOL

import json
from collections.abc import Generator
from typing import Any, Optional

import pyparsing as pp
from gramps.gen.db import DbReadBase
from gramps.gen.lib import PrimaryObject
from gramps.gen.lib.serialize import to_json

pp.ParserElement.enablePackrat()


def match(query: str, obj: dict[str, Any]) -> bool:
    """Match a single object (given as dictionary) to a query."""
    gq = GQLQuery(query=query)
    return gq.match(obj)


def iter_objects(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    gq = GQLQuery(query=query)
    return gq.iter_objects(db)


word = pp.Word(pp.alphanums + "." + "_")
rhs = word | pp.dbl_quoted_string | pp.sgl_quoted_string
# lhs = pp.Word(pp.identchars, pp.identbodychars + "." + "_")
logical_and = pp.CaselessKeyword("and")
logical_or = pp.CaselessKeyword("or")
logical = logical_and | logical_or
operator = pp.one_of("= != < <= > >= ~ !~")


property_name = pp.Word(pp.identchars, pp.identbodychars + "_")
attribute = "." + property_name
index = "[" + pp.common.integer + "]"
lhs = property_name + (attribute | index) * ...

expression = pp.Combine(lhs("lhs*")) + (operator("operator*") + rhs("rhs*")) * ...

infix = pp.infix_notation(
    expression,
    [
        (logical_and, 2, pp.OpAssoc.LEFT),
        (logical_or, 2, pp.OpAssoc.LEFT),
    ],
)

GRAMPS_OBJECT_NAMES = {
    "person": "people",
    "family": "families",
    "event": "events",
    "place": "places",
    "citation": "citations",
    "source": "sources",
    "repository": "repositories",
    "media": "media",
    "note": "notes",
}


def parse(query: str):
    """Parse a query."""
    return infix.parse_string(query, parse_all=True)


def parse_lhs(query: str):
    return lhs.parse_string(query, parse_all=True)


class GQLQuery:
    """GQL query class."""

    def __init__(self, query: str):
        self.query = query
        self.parsed = parse(self.query)

    @staticmethod
    def _combine_logical(op: Optional[str], value1: bool, value2: bool) -> bool:
        """Combine booleans with a logical operator as string."""
        if op == "and":
            return value1 and value2
        elif op == "or":
            return value1 or value2
        # if op is None, return the second value
        return value2

    def _traverse(self, parsed_list: list, obj: dict[str, Any]):
        """Traverse a nested parsed list."""
        result = None
        op = None
        expression = []
        for i, item in enumerate(parsed_list):
            if isinstance(item, list) or item in ["and", "or"]:
                if expression:
                    value = self._match_single(obj, *expression)
                    result = self._combine_logical(op, result, value)
                    op = None
                expression = []
                if item in ["and", "or"]:
                    op = item
                elif isinstance(item, list):
                    value = self._traverse(item, obj)
                    result = self._combine_logical(op, result, value)
                    op = None
            else:
                expression.append(item)
        if expression:
            value = self._match_single(obj, *expression)
            result = self._combine_logical(op, result, value)
        return result

    def match(self, obj: dict[str, Any]) -> bool:
        """Match an object to the query."""
        parsed_list = self.parsed.as_list()
        return self._traverse(parsed_list, obj)

    def _match_single(
        self, obj: dict[str, Any], lhs: str, operator: str = "", rhs: str = ""
    ) -> bool:
        """Match an object to a single condition."""
        parsed = parse_lhs(lhs)
        if not parsed:
            raise ValueError(f"Unable to parse left-hand side: {lhs}")
        for i, part in enumerate(parsed):
            if i == 0:
                result = obj.get(parsed[0])
            elif part in ["[", "]", "."]:
                continue
            elif part == "length":
                result = len(result)
            elif part in ["all", "any"]:
                if i + 1 == len(parsed):  # last item
                    results = [
                        self._match_values(item, operator, rhs) for item in result
                    ]
                elif len(parsed) > i + 1 and parsed[i + 1] == ".":
                    lhs_rest = "".join(parsed[i + 2 :])
                    results = [
                        self._match_single(item, lhs_rest, operator, rhs)
                        for item in result
                    ]
                else:
                    raise ValueError(f"'any' cannot be followed by {parsed[i + 1]}")
                try:
                    if part == "all":
                        return results and all(results)  # because all([]) is True
                    else:
                        return any(results)
                except TypeError:
                    return False
            else:
                try:
                    result = result[part]
                except (KeyError, IndexError):
                    return False
            if result is None:
                return False
        return self._match_values(result, operator, rhs)

    def _match_values(self, result, operator: str = "", rhs: str = "") -> bool:
        """Match two values."""
        if not operator:
            return bool(result)
        if isinstance(rhs, str):
            if rhs.isdigit():
                rhs = int(rhs)
            else:
                rhs = rhs.strip("\"'")
        if operator == "=":
            return result == rhs
        if operator == "!=":
            return result != rhs
        if operator == "~":
            if isinstance(result, str):
                rhs = str(rhs)
            return rhs in result
        if operator == "!~":
            if isinstance(result, str):
                rhs = str(rhs)
            return rhs not in result
        try:
            if operator == "<":
                return result < rhs
            if operator == ">":
                return result > rhs
            if operator == "<=":
                return result <= rhs
            if operator == ">=":
                return result >= rhs
        except TypeError:
            return False

    def iter_objects(self, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
        """Iterate over primary objects in a Gramps database."""
        for object_name, objects_name in GRAMPS_OBJECT_NAMES.items():
            iter_method = getattr(db, f"iter_{objects_name}")
            for obj in iter_method():
                obj_dict = json.loads(to_json(obj))
                obj_dict["type"] = obj_dict["_class"].lower()
                if self.match(obj_dict):
                    yield obj
