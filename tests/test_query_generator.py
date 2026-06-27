"""
Unit tests for the Query Generator module.
"""
import pytest
from app.query_generator import QueryGenerator
from app.models.schemas import QueryRequest


class TestQueryGenerator:
    def test_generator_initialization(self):
        gen = QueryGenerator()
        assert gen is not None

    def test_generate_heuristic_simple_select(self):
        gen = QueryGenerator()
        request = QueryRequest(question="Show me all customers", use_llm=False)
        result = gen.generate(request)
        assert result.sql is not None
        assert "SELECT" in result.sql.upper()
        assert "FROM" in result.sql.upper()

    def test_generate_heuristic_count(self):
        gen = QueryGenerator()
        request = QueryRequest(question="How many customers do we have?", use_llm=False)
        result = gen.generate(request)
        assert result.sql is not None
        assert "COUNT" in result.sql.upper()

    def test_generate_heuristic_with_table(self):
        gen = QueryGenerator()
        request = QueryRequest(question="List all orders with total amount", use_llm=False)
        result = gen.generate(request)
        assert result.sql is not None
        assert "SELECT" in result.sql.upper()
        assert "FROM" in result.sql.upper()

    def test_generate_heuristic_with_condition(self):
        gen = QueryGenerator()
        request = QueryRequest(question="Find customer with id 5", use_llm=False)
        result = gen.generate(request)
        assert result.sql is not None
        assert "WHERE" in result.sql.upper() or "LIMIT" in result.sql.upper()

    def test_generate_heuristic_top_n(self):
        gen = QueryGenerator()
        request = QueryRequest(question="Show top 10 products by price", use_llm=False)
        result = gen.generate(request)
        assert result.sql is not None
        assert "LIMIT 10" in result.sql

    def test_sql_safety(self):
        gen = QueryGenerator()
        assert gen._validate_sql_safe("SELECT * FROM customers") is True
        assert gen._validate_sql_safe("DROP TABLE customers") is False
        assert gen._validate_sql_safe("DELETE FROM customers") is False
        assert gen._validate_sql_safe("INSERT INTO customers VALUES (1)") is False

    def test_confidence_score(self):
        gen = QueryGenerator()
        score = gen._calculate_confidence("Show customers", "SELECT * FROM customers", False)
        assert 0.0 <= score <= 1.0
        assert score >= 0.5

        llm_score = gen._calculate_confidence("Show customers", "SELECT * FROM customers", True)
        assert llm_score > score

    def test_generate_with_rules(self):
        gen = QueryGenerator()
        request = QueryRequest(question="Show me all products", use_llm=False, max_results=50)
        result = gen.generate(request)
        assert result.rules_applied is not None

    def test_empty_question(self):
        gen = QueryGenerator()
        request = QueryRequest(question="", use_llm=False)
        with pytest.raises(Exception):
            gen.generate(request)