"""Gramps Query Language."""

from typing import Any, Optional

import pyparsing as pp

pp.ParserElement.enablePackrat()


def match(query: str):
    gq = GQLQuery(query=query)
    return gq.parse()


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


def parse(query: str):
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

    def match(self, obj: dict[str, Any]):
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
            else:
                try:
                    result = result[part]
                except (KeyError, IndexError):
                    return False
            if result is None:
                return False
        if not operator:
            return bool(result)
        if operator == "=":
            return result == rhs
        if operator == "!=":
            return result != rhs
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
