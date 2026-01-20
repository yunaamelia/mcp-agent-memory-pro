"""
MemQL Query Parser
SQL-like query language for memories
"""

from typing import Any

from pyparsing import (
    CaselessKeyword,
    Combine,
    DelimitedList,
    Group,
    Literal,
    ParseException,
    QuotedString,
    Word,
    alphanums,
    alphas,
    nums,
)
from pyparsing import Optional as Opt


class MemQLParser:
    """Parser for MemQL query language"""

    def __init__(self):
        self._setup_grammar()

    def _setup_grammar(self):
        """Setup MemQL grammar"""

        # Keywords (case-insensitive)
        SELECT = CaselessKeyword("SELECT")
        FROM = CaselessKeyword("FROM")
        WHERE = CaselessKeyword("WHERE")
        ORDER = CaselessKeyword("ORDER")
        BY = CaselessKeyword("BY")
        LIMIT = CaselessKeyword("LIMIT")
        CaselessKeyword("GROUP")
        CaselessKeyword("HAVING")
        AND = CaselessKeyword("AND")
        OR = CaselessKeyword("OR")

        # Identifiers and values
        identifier = Word(alphas, alphanums + "_")
        string_value = QuotedString("'") | QuotedString('"')
        # Support integers and floats
        number = Combine(Word(nums) + Opt(Literal(".") + Word(nums)))

        # SELECT clause
        select_list = Literal("*") | DelimitedList(identifier)

        # FROM clause
        from_clause = FROM + identifier

        # WHERE clause
        comparison_op = (
            Literal("=")
            | Literal("!=")
            | Literal(">")
            | Literal("<")
            | Literal(">=")
            | Literal("<=")
            | CaselessKeyword("LIKE")
        )
        condition = Group(identifier + comparison_op + (string_value | number))
        where_clause = WHERE + condition + ((AND | OR) + condition)[...]

        # ORDER BY clause
        order_direction = CaselessKeyword("ASC") | CaselessKeyword("DESC")
        order_clause = ORDER + BY + identifier + Opt(order_direction)

        # LIMIT clause
        limit_clause = LIMIT + number

        # Complete query
        self.query_expr = (
            SELECT
            + Group(select_list)("select")
            + from_clause("from")
            + Opt(where_clause)("where")
            + Opt(order_clause)("order")
            + Opt(limit_clause)("limit")
        )

    def parse(self, query: str) -> dict[str, Any]:
        """
        Parse MemQL query

        Args:
            query: MemQL query string

        Returns:
            Parsed query structure

        Examples:
            SELECT * FROM memories WHERE type = 'code' ORDER BY importance DESC LIMIT 10
            SELECT content, project FROM memories WHERE importance > 0.8
        """

        try:
            result = self.query_expr.parse_string(query, parse_all=True)

            parsed = {
                "select": list(result.select),
                "from": result["from"][1],
                "where": self._parse_where(result.get("where", [])),
                "order": self._parse_order(result.get("order", [])),
                "limit": int(result.get("limit", [None, None])[1]) if result.get("limit") else None,
            }

            return parsed

        except ParseException as e:
            raise ValueError(f"MemQL syntax error at position {e.loc}: {e.msg}") from e

    def _parse_where(self, where_clause) -> dict[str, Any] | None:
        """Parse WHERE clause"""

        if not where_clause:
            return None

        conditions = []
        operators = []

        # Extract conditions and logical operators
        for item in where_clause:
            if isinstance(item, str) and item.upper() in ["AND", "OR"]:
                operators.append(item.upper())
            elif hasattr(item, "asList"):
                conditions.append({"field": item[0], "operator": item[1], "value": item[2]})

        if len(conditions) == 1:
            return conditions[0]

        return {"conditions": conditions, "operators": operators}

    def _parse_order(self, order_clause) -> dict[str, Any] | None:
        """Parse ORDER BY clause"""

        if not order_clause:
            return None

        # Extract field and direction
        field = None
        direction = "ASC"

        for item in order_clause:
            if isinstance(item, str):
                if item.upper() in ["ASC", "DESC"]:
                    direction = item.upper()
                elif item.upper() not in ["ORDER", "BY"]:
                    field = item

        if not field:
            return None

        return {"field": field, "direction": direction}
