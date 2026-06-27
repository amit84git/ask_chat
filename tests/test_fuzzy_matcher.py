"""
Unit tests for the Fuzzy Matcher module.
"""
import pytest
from app.fuzzy_matcher import FuzzyMatcher


@pytest.fixture
def matcher():
    m = FuzzyMatcher()
    m.load_schema(
        tables=["customers", "orders", "products", "order_items"],
        columns=[
            ("customers", "id", "integer"),
            ("customers", "name", "varchar"),
            ("customers", "email", "varchar"),
            ("customers", "city", "varchar"),
            ("customers", "status", "varchar"),
            ("orders", "id", "integer"),
            ("orders", "customer_id", "integer"),
            ("orders", "total_amount", "decimal"),
            ("orders", "status", "varchar"),
            ("orders", "order_date", "date"),
            ("products", "id", "integer"),
            ("products", "name", "varchar"),
            ("products", "price", "decimal"),
            ("products", "category", "varchar"),
            ("order_items", "id", "integer"),
            ("order_items", "order_id", "integer"),
            ("order_items", "product_id", "integer"),
            ("order_items", "quantity", "integer"),
        ],
    )
    return m


class TestFuzzyMatcher:
    def test_extract_keywords(self, matcher):
        keywords = matcher.extract_keywords("Show me all customers from New York")
        assert len(keywords) > 0
        assert "customers" in keywords or "customer" in keywords

    def test_find_best_table_match_exact(self, matcher):
        result = matcher.find_best_table_match("customers")
        assert result is not None
        assert result[0] == "customers"
        assert result[1] == 1.0

    def test_find_best_table_match_fuzzy(self, matcher):
        result = matcher.find_best_table_match("client")
        assert result is not None
        # Should find something similar to customers

    def test_find_best_column_match(self, matcher):
        result = matcher.find_best_column_match("email")
        assert result is not None
        assert "email" in result[1]
        assert result[2] >= 0.5

    def test_extract_tables_from_question(self, matcher):
        tables = matcher.extract_tables_from_question("List all orders with their total amount")
        assert len(tables) > 0
        table_names = [t[0] for t in tables]
        assert "orders" in table_names

    def test_extract_columns_from_question(self, matcher):
        columns = matcher.extract_columns_from_question("What is the total amount of orders?")
        assert len(columns) > 0
        # Should find total_amount or similar
        col_names = [c[1] for c in columns]

    def test_get_common_phrases(self, matcher):
        phrases = matcher.get_common_phrases()
        assert "list" in phrases
        assert phrases["list"] == "SELECT"
        assert "count" in phrases
        assert phrases["count"] == "COUNT"

    def test_no_match(self, matcher):
        result = matcher.find_best_table_match("xyznonexistent123")
        assert result is None

    def test_empty_schema(self):
        empty = FuzzyMatcher()
        result = empty.find_best_table_match("test")
        assert result is None