"""
NL-to-SQL Query Generation Engine.
Converts natural language questions to PostgreSQL queries using:
1. LLM-based generation via local models (Ollama) or AWS Bedrock (Claude/Titan)
2. Heuristic fallback with template matching and semantic graph analysis
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.models.schemas import NL2SQLResult, QueryRequest
from app.semantic_graph import semantic_graph
from app.fuzzy_matcher import fuzzy_matcher
from app.rules_engine import rules_engine
from app.aws_utils import BedrockRuntime
from app.local_llm import LocalLLM, get_llm_provider

logger = logging.getLogger(__name__)

# SQL keyword mapping for heuristic generation
SQL_AGGREGATES = {
    "count": "COUNT",
    "total": "SUM",
    "sum": "SUM",
    "average": "AVG",
    "avg": "AVG",
    "minimum": "MIN",
    "min": "MIN",
    "maximum": "MAX",
    "max": "MAX",
}

SQL_COMPARISON_OPS = {
    "greater than": ">",
    "greater than or equal": ">=",
    ">= ": ">=",
    "less than": "<",
    "less than or equal": "<=",
    "<= ": "<=",
    "equal to": "=",
    "equals": "=",
    "not equal": "!=",
    "different": "!=",
}

TIME_PERIOD_MAP = {
    "today": "CURRENT_DATE",
    "yesterday": "CURRENT_DATE - INTERVAL '1 day'",
    "this week": "DATE_TRUNC('week', CURRENT_DATE)",
    "this month": "DATE_TRUNC('month', CURRENT_DATE)",
    "last month": "DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
    "this year": "DATE_TRUNC('year', CURRENT_DATE)",
    "last year": "DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')",
    "last 7 days": "CURRENT_DATE - INTERVAL '7 days'",
    "last 30 days": "CURRENT_DATE - INTERVAL '30 days'",
    "last 90 days": "CURRENT_DATE - INTERVAL '90 days'",
}


class QueryGenerator:
    """
    Generates PostgreSQL queries from natural language input.
    Uses local LLM (Ollama with open-source models), AWS Bedrock, 
    or heuristic fallback based on configuration.
    """

    def __init__(self):
        self._llm = None
        self._llm_available_cache = None

    @property
    def llm(self):
        """Lazy initialize the LLM provider."""
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    @property
    def llm_available(self) -> bool:
        """Check if any LLM is available (lazy check)."""
        if self._llm_available_cache is not None:
            return self._llm_available_cache
        try:
            if self.llm is not None:
                # Check availability differently based on provider type
                if isinstance(self.llm, LocalLLM):
                    self._llm_available_cache = self.llm.is_available
                elif isinstance(self.llm, BedrockRuntime):
                    result = self.llm.generate("Say 'ok'", max_tokens=10)
                    self._llm_available_cache = result is not None
                else:
                    self._llm_available_cache = False
            else:
                self._llm_available_cache = False
        except Exception:
            self._llm_available_cache = False
            logger.warning("LLM not available, will use heuristic fallback")
        return self._llm_available_cache

    def generate(self, request: QueryRequest) -> NL2SQLResult:
        """
        Generate SQL from a natural language question.
        
        Strategy:
        1. Extract keywords and identify candidate tables/columns
        2. Use LLM (local or Bedrock) if available and requested
        3. Fall back to heuristic generation
        4. Apply business rules
        5. Return result with confidence score
        """
        question = request.question.strip()
        tables_used = []
        columns_used = []

        # Step 1: Extract schema candidates using fuzzy matching
        candidate_tables = fuzzy_matcher.extract_tables_from_question(question)
        candidate_columns = fuzzy_matcher.extract_columns_from_question(question)

        tables_used = [t for t, _ in candidate_tables[:3]]
        columns_used = [col for _, col, _ in candidate_columns[:5]]

        # Step 2: Try LLM generation
        sql = None
        llm_generated = False

        if request.use_llm and self.llm_available:
            try:
                sql = self._generate_with_llm(question, candidate_tables, candidate_columns)
                if sql:
                    llm_generated = True
                    logger.info(f"LLM generated SQL: {sql}")
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}")

        # Step 3: Fallback to heuristic if LLM didn't produce output
        if not sql and settings.llm_fallback_to_heuristics:
            sql = self._generate_heuristic(question, candidate_tables, candidate_columns)
            logger.info(f"Heuristic generated SQL: {sql}")

        if not sql:
            return NL2SQLResult(
                sql="",
                tables_used=tables_used,
                columns_used=columns_used,
                confidence=0.0,
                explanation="Could not generate SQL from the question.",
                llm_generated=False,
            )

        # Step 4: Apply business rules
        enhanced_sql, applied_rules, _ = rules_engine.apply_rules(sql, tables_used)

        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(question, enhanced_sql, llm_generated)

        return NL2SQLResult(
            sql=enhanced_sql,
            tables_used=tables_used,
            columns_used=columns_used,
            confidence=confidence,
            explanation=self._generate_explanation(question, enhanced_sql, llm_generated, applied_rules),
            llm_generated=llm_generated,
            rules_applied=applied_rules,
        )

    def _generate_with_llm(self, question: str, candidate_tables: List[Tuple[str, float]],
                           candidate_columns: List[Tuple[str, str, float]]) -> Optional[str]:
        """Generate SQL using the configured LLM provider (local or Bedrock)."""
        schema_context = self._build_schema_prompt_context(candidate_tables, candidate_columns)

        prompt = f"""You are a PostgreSQL query generator. Convert natural language to SQL.

Database Schema (available tables and columns):
{schema_context}

Rules:
- Generate ONLY valid PostgreSQL SELECT queries.
- Use ONLY tables and columns from the schema above.
- Use proper JOIN syntax when querying multiple tables.
- Use appropriate aggregate functions (COUNT, SUM, AVG, MIN, MAX) when asked.
- Use GROUP BY with aggregate functions.
- Use ORDER BY for sorting.
- Use LIMIT for limiting results.
- Use ILIKE for case-insensitive text matching.
- Use proper date functions for time-based queries.
- Do NOT include any explanation, only output the SQL query.

Question: {question}

SQL Query:"""

        if isinstance(self.llm, LocalLLM):
            # Use local Ollama model - supports generate() method
            result = self.llm.generate(prompt, max_tokens=500, temperature=0.1)
        elif isinstance(self.llm, BedrockRuntime):
            # Use AWS Bedrock
            result = self.llm.generate(prompt, max_tokens=500)
        else:
            logger.warning(f"Unknown LLM provider type: {type(self.llm)}")
            return None

        if result:
            sql = self._clean_sql_output(result)
            if sql and self._validate_sql_safe(sql):
                return sql
        return None

    def _generate_heuristic(self, question: str, candidate_tables: List[Tuple[str, float]],
                            candidate_columns: List[Tuple[str, str, float]]) -> str:
        """
        Generate SQL using heuristic patterns when LLM is unavailable.
        Builds query step by step based on question analysis.
        """
        question_lower = question.lower()
        words = question_lower.split()

        # Determine query type
        is_aggregate = any(agg in question_lower for agg in SQL_AGGREGATES)
        is_count = any(w in question_lower for w in ["how many", "count", "number of"])
        is_list = any(w in question_lower for w in ["list", "show", "find", "get", "display", "what"])
        is_top = any(w in question_lower for w in ["top", "first", "latest", "recent"])
        is_sort_asc = any(w in question_lower for w in ["ascending", "oldest", "earliest"])
        is_sort_desc = any(w in question_lower for w in ["descending", "newest", "latest", "recent"])
        is_distinct = any(w in question_lower for w in ["unique", "distinct", "different"])

        # Identify target table from candidates
        if candidate_tables:
            target_table = candidate_tables[0][0]
        else:
            # Try to extract table name from common patterns
            table_match = re.search(r'(?:from|in|of|for)\s+(\w+(?:_\w+)*)', question_lower)
            target_table = table_match.group(1).capitalize() if table_match else "items"
            # If the word might be singular, try pluralizing
            if not target_table.endswith("s"):
                target_table = target_table + "s"

        # Identify target columns
        select_cols = []
        if candidate_columns:
            # Use the top matching columns
            for table, col, score in candidate_columns[:3]:
                if score > 0.3:
                    select_cols.append(col)
        elif not is_aggregate:
            # Guess columns based on common patterns
            col_patterns = [
                (r"\b(name|title)\b", "name"),
                (r"\b(email|e-?mail)\b", "email"),
                (r"\b(price|cost|amount)\b", "price"),
                (r"\b(date|time|when)\b", "created_at"),
                (r"\b(status|state)\b", "status"),
                (r"\b(city|location|address)\b", "city"),
            ]
            for pattern, col_name in col_patterns:
                if re.search(pattern, question_lower):
                    select_cols.append(col_name)

        if not select_cols and not is_aggregate:
            select_cols = ["*"]
            is_count = False

        # Build the query
        select_items = []

        if is_count:
            if is_distinct:
                select_items.append(f"COUNT(DISTINCT {select_cols[0] if select_cols else 'id'})")
            else:
                select_items.append("COUNT(*)")
        elif is_aggregate:
            agg_func = None
            for word, func in SQL_AGGREGATES.items():
                if word in question_lower and func != "COUNT":
                    agg_func = func
                    break
            if not agg_func:
                agg_func = "COUNT"
            col = select_cols[0] if select_cols else "id"
            select_items.append(f"{agg_func}({col})")
        else:
            if is_distinct:
                select_items = [f"DISTINCT {col}" for col in select_cols[:3]]
            else:
                select_items = select_cols[:5]  # Limit to 5 columns

        sql = "SELECT " + ", ".join(select_items) if select_items else "SELECT *"
        sql += f" FROM {target_table}"

        # Identify WHERE conditions
        where_clauses = []
        
        # ID-based queries
        id_match = re.search(r'(?:id|number|#)\s*(?:is|=|:)?\s*(\d+)', question_lower)
        if id_match:
            where_clauses.append(f"id = {id_match.group(1)}")

        # Name-based queries
        for pattern in [r"['\"](\w+[\w\s]*\w+)['\"]", r"called\s+(\w+)", r"named\s+(\w+)"]:
            match = re.search(pattern, question_lower)
            if match:
                value = match.group(1)
                where_clauses.append(f"name ILIKE '%{value}%'")
                break

        # Status-based
        status_match = re.search(r'status\s*(?:is|=|:)?\s*(\w+)', question_lower)
        if status_match:
            where_clauses.append(f"status = '{status_match.group(1).lower()}'")

        # Comparison queries
        for phrase, op in SQL_COMPARISON_OPS.items():
            if phrase in question_lower:
                for col_pattern, col_name in [
                    (r"(\d+)\s*(?:dollars|usd|price)", "price"),
                    (r"(\d+)", "amount"),
                ]:
                    val_match = re.search(col_pattern, question_lower)
                    if val_match:
                        where_clauses.append(f"{col_name} {op} {val_match.group(1)}")
                        break
                break

        # Time period queries
        for period, sql_period in TIME_PERIOD_MAP.items():
            if period in question_lower:
                where_clauses.append(f"created_at >= {sql_period}")
                break

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # ORDER BY
        if is_sort_asc:
            order_col = "created_at" if "created_at" in sql else "id"
            sql += f" ORDER BY {order_col} ASC"
        elif is_sort_desc or is_top or is_count:
            order_col = "created_at" if "created_at" in sql else "id"
            sql += f" ORDER BY {order_col} DESC"

        # LIMIT
        if is_top:
            limit_match = re.search(r'(?:top|first|latest)\s*(\d+)', question_lower)
            limit = limit_match.group(1) if limit_match else "10"
            sql += f" LIMIT {limit}"
        elif request_has_max := getattr(self, '_request_max', 100):
            sql += f" LIMIT {request_has_max}"
        else:
            sql += " LIMIT 100"

        # GROUP BY (for aggregates with non-aggregated columns)
        if is_aggregate and select_cols and select_cols[0] != "*":
            sql += f" GROUP BY {select_cols[0]}"

        return sql

    def _clean_sql_output(self, text: str) -> Optional[str]:
        """Extract SQL from LLM output that may include markdown or explanations."""
        # Remove markdown code blocks
        text = re.sub(r'```sql\s*\n?', '', text)
        text = re.sub(r'```\s*\n?', '', text)

        # Extract first SQL statement
        lines = text.strip().split('\n')
        sql_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith(('SELECT', 'WITH', '--')):
                sql_lines.append(stripped)
            elif sql_lines:  # Continue if we've started collecting
                sql_lines.append(stripped)

        if sql_lines:
            return ' '.join(sql_lines)
        return None

    def _validate_sql_safe(self, sql: str) -> bool:
        """
        Validate that generated SQL is safe to execute.
        Prevents dangerous operations in PoC.
        """
        sql_upper = sql.upper().strip()
        forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
                     'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE', 'CALL',
                     'COPY', 'VACUUM', '--', '/*', '*/', ';']
        for keyword in forbidden:
            if keyword in sql_upper and keyword != 'SELECT':
                # Allow SELECT statements only
                if not sql_upper.startswith('SELECT'):
                    logger.warning(f"Blocked unsafe SQL: {sql}")
                    return False
        return True

    def _build_schema_prompt_context(self, tables: List[Tuple[str, float]],
                                     columns: List[Tuple[str, str, float]]) -> str:
        """Build a concise schema description for the LLM prompt."""
        lines = []
        seen_tables = set()
        for table_name, score in tables[:5]:
            if table_name not in seen_tables:
                seen_tables.add(table_name)
                lines.append(f"- Table: {table_name}")
        for table, col, score in columns[:5]:
            if table:
                lines.append(f"  - Column: {table}.{col}")
        return "\n".join(lines) if lines else "- Table: items\n  - Columns: id, name, created_at, updated_at"

    def _calculate_confidence(self, question: str, sql: str, llm_used: bool) -> float:
        """Calculate a confidence score for the generated SQL."""
        if not sql:
            return 0.0

        base = 0.5

        # LLM generation boosts confidence
        if llm_used:
            base += 0.3

        # Check if SQL has all required parts
        if sql.upper().startswith('SELECT'):
            base += 0.1
        if 'FROM' in sql.upper():
            base += 0.05
        if 'WHERE' in sql.upper() and any(w in question.lower() for w in ['where', 'with', 'for', 'in']):
            base += 0.05

        # Ensure we don't exceed 1.0
        return min(base, 1.0)

    def _generate_explanation(self, question: str, sql: str, llm_used: bool,
                              rules_applied: List[str]) -> str:
        """Generate a human-readable explanation of the SQL."""
        parts = []
        if llm_used:
            provider_name = settings.llm_provider
            parts.append(f"Generated by AI ({provider_name})")
        else:
            parts.append("Generated using heuristic pattern matching")

        parts.append(f"Query: {sql}")

        if rules_applied:
            parts.append(f"Business rules applied: {', '.join(rules_applied)}")

        return "\n".join(parts)

    def set_request_max(self, max_results: int):
        """Set the max results for the current request."""
        self._request_max = max_results


# Singleton
query_generator = QueryGenerator()