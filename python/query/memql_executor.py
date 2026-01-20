"""
MemQL Query Executor
Executes parsed MemQL queries against database
"""

import sqlite3
from typing import Any

from query.memql_parser import MemQLParser


class MemQLExecutor:
    """Executes MemQL queries"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self.parser = MemQLParser()

    def execute(self, query: str) -> dict[str, Any]:
        """
        Execute MemQL query

        Args:
            query: MemQL query string

        Returns:
            Query results with metadata
        """

        # Parse query
        parsed = self.parser.parse(query)

        # Build SQL
        sql, params = self._build_sql(parsed)

        # Execute
        try:
            # enable row factory for dict-like access if not already
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.execute(sql, params)
        except sqlite3.Error as e:
            return {"error": str(e), "query": query, "sql": sql}

        # Fetch results
        rows = cursor.fetchall()

        # Format results
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        results = []
        for row in rows:
            results.append(dict(zip(columns, row, strict=False)))

        return {
            "query": query,
            "sql": sql,
            "count": len(results),
            "results": results,
            "columns": columns,
        }

    def _build_sql(self, parsed: dict[str, Any]) -> tuple[str, list]:
        """Build SQL from parsed query"""

        # SELECT clause
        if parsed["select"] == ["*"]:
            select_clause = "SELECT *"
        else:
            select_clause = f"SELECT {', '.join(parsed['select'])}"

        # FROM clause
        table = parsed["from"]
        from_clause = f"FROM {table}"

        # WHERE clause
        where_clause = ""
        params = []

        if parsed["where"]:
            where_sql, where_params = self._build_where(parsed["where"])
            where_clause = f"WHERE {where_sql}"
            params.extend(where_params)

        # ORDER BY clause
        order_clause = ""
        if parsed["order"]:
            order_clause = f"ORDER BY {parsed['order']['field']} {parsed['order']['direction']}"

        # LIMIT clause
        limit_clause = ""
        if parsed["limit"]:
            limit_clause = f"LIMIT {parsed['limit']}"

        # Combine
        sql = f"{select_clause} {from_clause} {where_clause} {order_clause} {limit_clause}".strip()

        return sql, params

    def _build_where(self, where: dict[str, Any]) -> tuple[str, list]:
        """Build WHERE clause"""

        params = []

        # Simple condition
        if "field" in where:
            field = where["field"]
            operator = where["operator"]
            value = where["value"]

            sql = f"{field} LIKE ?" if operator.upper() == "LIKE" else f"{field} {operator} ?"

            params.append(value)
            return sql, params

        # Complex conditions
        conditions = where.get("conditions", [])
        operators = where.get("operators", [])

        sql_parts = []

        for i, condition in enumerate(conditions):
            field = condition["field"]
            op = condition["operator"]
            value = condition["value"]

            if op.upper() == "LIKE":
                sql_parts.append(f"{field} LIKE ?")
            else:
                sql_parts.append(f"{field} {op} ?")

            params.append(value)

            # Add logical operator
            if i < len(operators):
                sql_parts.append(operators[i])

        return " ".join(sql_parts), params
