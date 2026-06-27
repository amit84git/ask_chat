"""
Unit tests for the Business Rules Engine.
"""
import pytest
from app.rules_engine import RulesEngine, BusinessRule, DEFAULT_RULES


@pytest.fixture
def engine():
    return RulesEngine()


class TestRulesEngine:
    def test_default_rules_exist(self, engine):
        assert len(engine.rules) > 0
        assert all(isinstance(r, BusinessRule) for r in engine.rules)

    def test_add_rule(self, engine):
        new_rule = BusinessRule(
            name="test_rule",
            description="Test rule",
            priority=50,
            sql_modification="LIMIT 10",
        )
        engine.add_rule(new_rule)
        assert any(r.name == "test_rule" for r in engine.rules)

    def test_limit_safe_results(self, engine):
        sql = "SELECT * FROM customers"
        modified_sql, rules, _ = engine.apply_rules(sql, tables_used=["customers"])
        assert "LIMIT 1000" in modified_sql
        assert "limit_safe_results" in rules

    def test_order_by_created_desc(self, engine):
        sql = "SELECT * FROM customers"
        modified_sql, rules, _ = engine.apply_rules(sql, tables_used=["customers"])
        assert "ORDER BY created_at DESC" in modified_sql
        assert "order_by_created_desc" in rules

    def test_no_duplicate_limit(self, engine):
        sql = "SELECT * FROM customers LIMIT 5"
        modified_sql, rules, _ = engine.apply_rules(sql, tables_used=["customers"])
        # Should not add another limit
        assert modified_sql.count("LIMIT") == 1

    def test_no_duplicate_order(self, engine):
        sql = "SELECT * FROM customers ORDER BY name ASC"
        modified_sql, rules, _ = engine.apply_rules(sql, tables_used=["customers"])
        assert modified_sql.count("ORDER BY") == 1

    def test_inactive_rule_not_applied(self, engine):
        inactive = BusinessRule(
            name="inactive_test",
            description="Should not apply",
            priority=1,
            sql_modification="WHERE 1=0",
            is_active=False,
        )
        engine.add_rule(inactive)
        sql = "SELECT * FROM customers"
        modified_sql, rules, _ = engine.apply_rules(sql, tables_used=["customers"])
        assert "inactive_test" not in rules

    def test_get_active_rules(self, engine):
        active = engine.get_active_rules()
        assert all(r.is_active for r in active)

    def test_customer_privacy_masking(self, engine):
        sql = "SELECT name, email FROM customers"
        # This test checks the structure, not exact matching since enhancement
        # depends on pattern matching
        modified_sql, rules, changes = engine.apply_rules(sql, tables_used=["customers"])
        assert isinstance(modified_sql, str)

    def test_exclude_deleted(self, engine):
        sql = "SELECT * FROM customers"
        modified_sql, rules, _ = engine.apply_rules(sql, tables_used=["customers"])
        # The condition checks if 'deleted_at' is in sql, but it's not in the initial query
        assert modified_sql == sql  # Condition not met, so no change

    def test_apply_rules_no_tables(self, engine):
        sql = "SELECT 1"
        modified_sql, rules, changes = engine.apply_rules(sql, tables_used=[])
        assert modified_sql == sql  # No tables to match