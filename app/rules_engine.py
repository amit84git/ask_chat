"""
Business Rules Engine for query enhancement.
Applies configurable domain-specific rules to modify or enhance generated SQL queries.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.models.schemas import BusinessRule

logger = logging.getLogger(__name__)

# Default business rules for the PoC
DEFAULT_RULES = [
    BusinessRule(
        name="exclude_deleted_records",
        description="Exclude soft-deleted records from all queries",
        priority=10,
        table_pattern=r".*",
        sql_modification="WHERE deleted_at IS NULL",
        query_enhancement="AND deleted_at IS NULL",
        condition="table_has_column:deleted_at",
        is_active=True,
    ),
    BusinessRule(
        name="order_by_created_desc",
        description="Order results by created_at descending when no ORDER BY is specified",
        priority=50,
        table_pattern=r".*",
        sql_modification="ORDER BY created_at DESC",
        query_enhancement="",
        condition="table_has_column:created_at AND no_order_by",
        is_active=True,
    ),
    BusinessRule(
        name="limit_safe_results",
        description="Limit results to safe maximum to prevent overload",
        priority=200,
        table_pattern=r".*",
        sql_modification="LIMIT 1000",
        query_enhancement="LIMIT 1000",
        condition="no_limit_clause",
        is_active=True,
    ),
    BusinessRule(
        name="customer_privacy",
        description="Mask PII fields for non-admin queries",
        priority=30,
        table_pattern=r"(customer|user|person|employee)",
        column_pattern=r"(email|phone|ssn|credit_card|password)",
        query_enhancement="CONCAT(LEFT(%column%, 3), '****') AS %column%",
        condition="",
        is_active=True,
    ),
    BusinessRule(
        name="date_range_default",
        description="Apply last 30 days filter for date columns when no date filter is present",
        priority=60,
        table_pattern=r".*",
        column_pattern=r"(created_at|updated_at|date|timestamp)",
        query_enhancement="AND %column% >= CURRENT_DATE - INTERVAL '30 days'",
        condition="column_exists:%column% AND no_date_filter",
        is_active=True,
    ),
    BusinessRule(
        name="aggregate_alias",
        description="Alias aggregate functions for readability",
        priority=150,
        table_pattern=r".*",
        sql_modification="",
        query_enhancement="",
        condition="",
        is_active=True,
    ),
]


class RulesEngine:
    """
    Applies business rules to SQL queries.
    
    Rules can:
    - Add WHERE clauses (e.g., soft delete filters)
    - Add ORDER BY clauses
    - Add LIMIT clauses
    - Transform columns (e.g., masking PII)
    - Rewrite query structure
    """

    def __init__(self, rules: Optional[List[BusinessRule]] = None):
        self.rules = rules or DEFAULT_RULES
        self.rules.sort(key=lambda r: r.priority)

    def add_rule(self, rule: BusinessRule):
        """Add a new rule and re-sort."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)

    def apply_rules(self, sql: str, tables_used: List[str] = None,
                    context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[str], List[str]]:
        """
        Apply all active rules to a SQL query.
        
        Args:
            sql: Original SQL query
            tables_used: Tables referenced in the query
            context: Additional context (e.g., user role, tenant)
            
        Returns:
            Tuple of (modified_sql, rules_applied_names, change_descriptions)
        """
        if not settings.feature_rules_engine:
            return sql, [], []

        modified_sql = sql
        applied_rules = []
        changes = []
        tables_used = tables_used or []
        context = context or {}

        for rule in self.rules:
            if not rule.is_active:
                continue

            try:
                # Check if rule applies to any of the tables used
                table_match = False
                if rule.table_pattern:
                    for table in tables_used:
                        if re.search(rule.table_pattern, table, re.IGNORECASE):
                            table_match = True
                            break
                    if not table_match and tables_used:
                        continue
                elif not rule.table_pattern:
                    table_match = True

                if not table_match:
                    continue

                # Check condition if specified
                if rule.condition:
                    if not self._evaluate_condition(rule.condition, modified_sql, context):
                        continue

                # Apply SQL modification
                if rule.sql_modification:
                    new_sql = self._apply_modification(modified_sql, rule)
                    if new_sql != modified_sql:
                        changes.append(f"Applied rule '{rule.name}': {rule.description}")
                        modified_sql = new_sql
                        applied_rules.append(rule.name)

                # Apply query enhancement
                if rule.query_enhancement:
                    new_sql = self._apply_enhancement(modified_sql, rule)
                    if new_sql != modified_sql:
                        changes.append(f"Enhanced by rule '{rule.name}': {rule.description}")
                        modified_sql = new_sql
                        applied_rules.append(rule.name)

            except Exception as e:
                logger.warning(f"Error applying rule '{rule.name}': {e}")

        return modified_sql, applied_rules, changes

    def _evaluate_condition(self, condition: str, sql: str, context: Dict[str, Any]) -> bool:
        """Evaluate a rule condition string."""
        # Simple condition evaluator for common cases
        if condition.startswith("table_has_column:"):
            col_name = condition.split(":", 1)[1]
            return col_name in sql.lower()

        if condition == "no_order_by":
            return "order by" not in sql.lower()

        if condition == "no_limit_clause":
            return "limit" not in sql.lower()

        if condition.startswith("column_exists:"):
            col_name = condition.split(":", 1)[1]
            return col_name.lower() in sql.lower()

        if condition == "no_date_filter":
            date_keywords = ["date", "timestamp", "interval", "current_date"]
            return not any(kw in sql.lower() for kw in date_keywords)

        # Default: condition passes
        return True

    def _apply_modification(self, sql: str, rule: BusinessRule) -> str:
        """Apply a SQL modification."""
        mod = rule.sql_modification
        if not mod:
            return sql

        upper_sql = sql.strip().upper()

        # Handle WHERE clause additions
        if mod.upper().startswith("WHERE"):
            if "WHERE" in upper_sql:
                # Add as AND clause
                where_clause = mod[5:].strip()  # Remove "WHERE"
                where_pos = upper_sql.index("WHERE")
                insert_pos = sql.lower().index("where") + 5
                # Find the end of the WHERE clause
                remaining = sql[insert_pos:].strip()
                sql = sql[:insert_pos] + " " + where_clause + " AND " + remaining
            else:
                # Add WHERE clause before ORDER BY, LIMIT, or at end
                for clause in ["ORDER BY", "LIMIT", "GROUP BY", "HAVING"]:
                    pos = upper_sql.find(clause)
                    if pos >= 0:
                        before = sql[:pos]
                        after = sql[pos:]
                        return before.strip() + " " + mod + " " + after.strip()
                sql = sql.rstrip(";") + " " + mod

        # Handle LIMIT clause
        elif mod.upper().startswith("LIMIT"):
            if "LIMIT" in upper_sql:
                return sql  # Already has a limit
            sql = sql.rstrip(";") + " " + mod

        # Handle ORDER BY
        elif mod.upper().startswith("ORDER BY"):
            if "ORDER BY" in upper_sql:
                return sql  # Already has an order
            sql = sql.rstrip(";") + " " + mod

        return sql

    def _apply_enhancement(self, sql: str, rule: BusinessRule) -> str:
        """Apply a query enhancement (e.g., column masking, additional filters)."""
        enhancement = rule.query_enhancement
        if not enhancement:
            return sql

        # Replace placeholder patterns
        if rule.column_pattern and "%column%" in enhancement:
            # Find matching columns in the SQL
            col_matches = re.findall(r'\b(\w+)\b', sql)
            for col_match in col_matches:
                if re.search(rule.column_pattern, col_match, re.IGNORECASE):
                    enhancement_filled = enhancement.replace("%column%", col_match)
                    # Replace the column reference in SELECT clause
                    sql = re.sub(
                        rf'\b{re.escape(col_match)}\b',
                        enhancement_filled,
                        sql,
                        count=1,
                    )

        # Add AND conditions (e.g., date range filters)
        elif enhancement.upper().startswith("AND"):
            if "WHERE" in sql.upper():
                # Insert after WHERE clause
                where_match = re.search(r'WHERE\s+', sql, re.IGNORECASE)
                if where_match:
                    insert_at = where_match.end()
                    sql = sql[:insert_at] + enhancement[4:].strip() + " AND " + sql[insert_at:]
            else:
                # Add WHERE clause
                for clause in ["ORDER BY", "LIMIT", "GROUP BY"]:
                    pos = sql.upper().find(clause)
                    if pos >= 0:
                        before = sql[:pos]
                        after = sql[pos:]
                        sql = before.strip() + " WHERE " + enhancement[4:].strip() + " " + after.strip()
                        break
                else:
                    sql = sql.rstrip(";") + " WHERE " + enhancement[4:].strip()

        return sql

    def get_active_rules(self) -> List[BusinessRule]:
        """Get all active rules."""
        return [r for r in self.rules if r.is_active]


# Singleton with default rules
rules_engine = RulesEngine()