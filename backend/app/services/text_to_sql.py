"""
DataVista+ Text-to-SQL Engine
Converts NLPResult into optimized, safe SQL queries
"""
import re
import logging
from typing import Dict, List, Optional, Any

from app.services.nlp_engine import NLPEngine, NLPResult

logger = logging.getLogger(__name__)


class TextToSQLEngine:
    """
    Generates SQL from NLP analysis results.
    Supports SELECT, aggregate queries, JOINs, filters, grouping, and ordering.
    """

    # Default schema for the sample database
    DEFAULT_SCHEMA = {
        "sales_orders": [
            "order_id", "customer_id", "product_id", "order_date",
            "quantity", "unit_price", "total_amount", "region", "status"
        ],
        "products": [
            "product_id", "product_name", "category", "unit_price", "stock_quantity"
        ],
        "customers": [
            "customer_id", "customer_name", "email", "city", "country", "segment"
        ],
        "employees": [
            "employee_id", "first_name", "last_name", "email", "department_id",
            "salary", "hire_date", "job_title", "performance_score"
        ],
        "departments": [
            "department_id", "department_name", "manager_id", "budget"
        ],
        "transactions": [
            "transaction_id", "date", "amount", "category", "type", "description"
        ],
    }

    # Join relationships between tables
    JOIN_MAP = {
        ("sales_orders", "products"): ("sales_orders.product_id", "products.product_id"),
        ("sales_orders", "customers"): ("sales_orders.customer_id", "customers.customer_id"),
        ("employees", "departments"): ("employees.department_id", "departments.department_id"),
    }

    # Aggregate function to SELECT expression mapping
    AGG_COLUMN_MAP = {
        "revenue": "SUM(total_amount)",
        "sales": "SUM(total_amount)",
        "orders": "COUNT(order_id)",
        "customers": "COUNT(DISTINCT customer_id)",
        "employees": "COUNT(employee_id)",
        "salary": "AVG(salary)",
        "transactions": "COUNT(transaction_id)",
        "amount": "SUM(amount)",
    }

    def __init__(self, schema: Optional[Dict] = None):
        self.schema = schema or self.DEFAULT_SCHEMA
        self.nlp_engine = NLPEngine(schema=self.schema)

    def convert(self, natural_query: str, dataset_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main method: convert natural language query to SQL.

        Returns:
            {
                "sql": str,
                "explanation": str,
                "intent": str,
                "confidence": float,
                "nlp_result": dict,
                "warnings": list,
            }
        """
        if dataset_context:
            # Update schema from dataset context
            self.schema = dataset_context.get("schema", self.schema)
            self.nlp_engine = NLPEngine(schema=self.schema)

        nlp_result = self.nlp_engine.process(natural_query)
        sql, warnings = self._build_sql(nlp_result)
        explanation = self._generate_explanation(nlp_result, sql)

        logger.info(f"NLQ: '{natural_query}' → SQL generated with confidence {nlp_result.confidence}")

        return {
            "sql": sql,
            "explanation": explanation,
            "intent": nlp_result.intent,
            "confidence": nlp_result.confidence,
            "nlp_result": {
                "tables": nlp_result.tables,
                "columns": nlp_result.columns,
                "filters": nlp_result.filters,
                "groupby": nlp_result.groupby,
                "aggregation": nlp_result.aggregation,
                "limit": nlp_result.limit,
                "keywords": nlp_result.keywords[:10],
            },
            "warnings": warnings,
        }

    def _build_sql(self, r: NLPResult) -> tuple:
        """Build SQL from NLP result components."""
        warnings = []
        table = r.tables[0] if r.tables else list(self.schema.keys())[0]
        columns_in_table = self.schema.get(table, [])

        # ── SELECT clause ──────────────────────────────────────────────────
        select_parts = []

        if r.aggregation:
            # Build aggregation select
            agg_col = self._pick_aggregation_column(r, columns_in_table)
            select_parts.append(f"{r.aggregation}({agg_col}) AS {r.aggregation.lower()}_result")
        elif r.intent in ("AGGREGATE_COUNT",):
            select_parts.append("COUNT(*) AS total_count")
        elif r.intent in ("AGGREGATE_SUM",):
            agg_col = self._find_numeric_column(columns_in_table, ["total_amount", "amount", "salary"])
            select_parts.append(f"SUM({agg_col}) AS total_sum")
        elif r.intent in ("AGGREGATE_AVG",):
            agg_col = self._find_numeric_column(columns_in_table, ["salary", "unit_price", "total_amount"])
            select_parts.append(f"AVG({agg_col}) AS average_value")
        elif r.intent in ("AGGREGATE_MAX",):
            agg_col = self._find_numeric_column(columns_in_table, ["total_amount", "salary", "unit_price"])
            select_parts.append(f"MAX({agg_col}) AS max_value")
        elif r.intent in ("AGGREGATE_MIN",):
            agg_col = self._find_numeric_column(columns_in_table, ["total_amount", "salary", "unit_price"])
            select_parts.append(f"MIN({agg_col}) AS min_value")
        else:
            # Regular select
            if r.columns:
                detected_in_table = [c for c in r.columns if c in columns_in_table]
                select_parts = detected_in_table if detected_in_table else ["*"]
            else:
                select_parts = ["*"]

        # Add GROUP BY columns to SELECT if needed
        if r.groupby:
            for grp in r.groupby:
                actual = self._resolve_column(grp, columns_in_table)
                if actual not in select_parts:
                    select_parts.insert(0, actual)

        select_clause = ", ".join(select_parts)

        # ── FROM + JOIN clause ─────────────────────────────────────────────
        from_clause = table
        if len(r.tables) > 1:
            for i in range(1, len(r.tables)):
                join_table = r.tables[i]
                join_key = self._find_join_key(table, join_table)
                if join_key:
                    left_col, right_col = join_key
                    from_clause += f"\n    INNER JOIN {join_table} ON {left_col} = {right_col}"
                else:
                    warnings.append(f"Could not determine join condition between {table} and {join_table}")

        # ── WHERE clause ───────────────────────────────────────────────────
        where_parts = []
        for f in r.filters:
            col = self._resolve_column(f.get("column", ""), columns_in_table)
            op = f.get("operator", "=")
            val = f.get("value", "")
            if isinstance(val, str):
                where_parts.append(f"{col} {op} '{val}'")
            else:
                where_parts.append(f"{col} {op} {val}")

        if r.time_filter:
            date_col = self._find_date_column(columns_in_table)
            where_parts.append(f"{date_col} >= {r.time_filter}")

        where_clause = f"\nWHERE {' AND '.join(where_parts)}" if where_parts else ""

        # ── GROUP BY clause ────────────────────────────────────────────────
        group_clause = ""
        if r.groupby:
            group_cols = [self._resolve_column(g, columns_in_table) for g in r.groupby]
            group_clause = f"\nGROUP BY {', '.join(group_cols)}"

        # ── ORDER BY clause ────────────────────────────────────────────────
        order_clause = ""
        if r.orderby:
            if select_parts and select_parts[0] != "*":
                order_col = select_parts[0]
            elif r.groupby:
                order_col = self._find_numeric_column(columns_in_table, ["total_amount", "salary", "amount"])
            else:
                order_col = "1"
            order_clause = f"\nORDER BY {order_col} {r.orderby}"

        # ── LIMIT clause ───────────────────────────────────────────────────
        limit_clause = f"\nLIMIT {r.limit}" if r.limit else ""

        # ── Assemble SQL ───────────────────────────────────────────────────
        sql = f"SELECT {select_clause}\nFROM {from_clause}{where_clause}{group_clause}{order_clause}{limit_clause}"

        return sql.strip(), warnings

    def _pick_aggregation_column(self, r: NLPResult, columns: List[str]) -> str:
        """Pick the best column for aggregation based on context keywords."""
        for keyword in r.keywords:
            for key, candidates in {
                "revenue": ["total_amount", "amount", "revenue"],
                "salary": ["salary"],
                "order": ["order_id"],
                "quantity": ["quantity", "qty"],
            }.items():
                if key in keyword:
                    for c in candidates:
                        if c in columns:
                            return c
        return self._find_numeric_column(columns, ["total_amount", "amount", "salary", "quantity"])

    def _find_numeric_column(self, columns: List[str], preferred: List[str]) -> str:
        """Return first preferred column found, or fallback to any column."""
        for p in preferred:
            if p in columns:
                return p
        return columns[0] if columns else "*"

    def _find_date_column(self, columns: List[str]) -> str:
        """Find a date/timestamp column."""
        for col in columns:
            if any(d in col for d in ["date", "time", "created", "timestamp"]):
                return col
        return "date"

    def _resolve_column(self, name: str, columns: List[str]) -> str:
        """Resolve a logical column name to actual schema column."""
        if name in columns:
            return name
        # Try partial match
        for col in columns:
            if name in col or col in name:
                return col
        return name

    def _find_join_key(self, table1: str, table2: str) -> Optional[tuple]:
        """Look up the join condition between two tables."""
        key = (table1, table2)
        if key in self.JOIN_MAP:
            return self.JOIN_MAP[key]
        rev_key = (table2, table1)
        if rev_key in self.JOIN_MAP:
            left, right = self.JOIN_MAP[rev_key]
            return right, left
        return None

    def _generate_explanation(self, r: NLPResult, sql: str) -> str:
        """Generate a human-readable explanation of the generated SQL."""
        parts = []

        intent_descriptions = {
            "SELECT": "Retrieving records",
            "AGGREGATE_COUNT": "Counting records",
            "AGGREGATE_SUM": "Summing up values",
            "AGGREGATE_AVG": "Calculating average",
            "AGGREGATE_MAX": "Finding the maximum value",
            "AGGREGATE_MIN": "Finding the minimum value",
            "FILTER": "Filtering records",
            "GROUP": "Grouping data",
            "TREND": "Analyzing trend over time",
        }
        parts.append(intent_descriptions.get(r.intent, "Querying data"))

        if r.tables:
            parts.append(f"from the **{', '.join(r.tables)}** table(s)")

        if r.filters:
            conds = [f"{f['column']} {f['operator']} {f['value']}" for f in r.filters]
            parts.append(f"where {' and '.join(conds)}")

        if r.groupby:
            parts.append(f"grouped by {', '.join(r.groupby)}")

        if r.orderby:
            direction = "highest first" if r.orderby == "DESC" else "lowest first"
            parts.append(f"sorted {direction}")

        if r.limit:
            parts.append(f"limited to top {r.limit} results")

        return ". ".join(parts) + "."
