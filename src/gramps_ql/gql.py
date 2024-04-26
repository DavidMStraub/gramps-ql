"""Gramps Query Language."""

from __future__ import annotations  # can be removed at 3.8 EOL

import json
from collections.abc import Generator
from typing import Any, Optional, Union

import pyparsing as pp
from gramps.gen.db import DbReadBase
from gramps.gen.errors import HandleError
from gramps.gen.lib import PrimaryObject
from gramps.gen.lib.serialize import to_json

pp.ParserElement.enablePackrat()


def to_dict(obj: PrimaryObject) -> dict[str, Any]:
    """Convert a Gramps object to its dictionary representation."""
    obj_dict = json.loads(to_json(obj))
    obj_dict["class"] = obj_dict["_class"].lower()
    return obj_dict


def match(
    query: str,
    obj: Union[PrimaryObject, dict[str, Any]],
    db: Optional[DbReadBase] = None,
) -> bool:
    """Match a single object (optionally given as dictionary) to a query."""
    gq = GQLQuery(query=query, db=db)
    if isinstance(obj, PrimaryObject):
        obj_dict = to_dict(obj)
        return gq.match(obj_dict)
    return gq.match(obj)


def iter_objects(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    gq = GQLQuery(query=query, db=db)
    return gq.iter_objects()


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

    def __init__(self, query: str, db: Optional[DbReadBase] = None):
        self.query = query
        self.parsed = parse(self.query)
        self.db = db

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
            if i == 0 and isinstance(obj, dict):
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
            elif isinstance(part, str) and part.startswith("get_"):
                if not self.db:
                    raise ValueError("Database is needed for get")
                try:
                    if i == 0 and isinstance(obj, str):
                        result = obj
                    _obj = getattr(self.db, f"{part}_from_handle")(result)
                except (AttributeError, HandleError):
                    return False
                result = to_dict(_obj)
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
            if isinstance(result, str):
                rhs = str(rhs)
                return result.casefold() == rhs.casefold()
            return result == rhs
        if operator == "!=":
            if isinstance(result, str):
                rhs = str(rhs)
                return result.casefold() != rhs.casefold()
            return result != rhs
        if operator == "~":
            if isinstance(result, str):
                rhs = str(rhs)
                return rhs.casefold() in result.casefold()
            return rhs in result
        if operator == "!~":
            if isinstance(result, str):
                rhs = str(rhs)
                return rhs.casefold() in result.casefold()
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

    def iter_objects(self) -> Generator[PrimaryObject, None, None]:
        """Iterate over primary objects in a Gramps database."""
        if not self.db:
            raise ValueError("Database is needed for iterating objects!")
        for object_name, objects_name in GRAMPS_OBJECT_NAMES.items():
            iter_method = getattr(self.db, f"iter_{objects_name}")
            for obj in iter_method():
                obj_dict = to_dict(obj)
                if self.match(obj_dict):
                    yield obj
