"""
Integration test for AskChat API.
Tests the full flow: metadata loading, NL-to-SQL generation, rules engine, and graph visualization.
Requires the application to be running locally (docker-compose up -d).
"""
import pytest
import requests
from typing import Dict, Any

# Base URL for the running application
BASE_URL = "http://localhost:8000"


def is_api_running() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


@pytest.mark.skipif(not is_api_running(), reason="API is not running")
class TestIntegration:
    """Integration tests that require the full stack."""

    def test_health_check(self):
        """Test health endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "services" in data

    def test_root_endpoint(self):
        """Test root API overview."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert "nl2sql" in str(data["endpoints"])

    def test_load_metadata_json(self):
        """Test loading metadata from JSON."""
        payload = {
            "source_type": "json",
            "source_path": "sample_data/schema.json",
        }
        response = requests.post(f"{BASE_URL}/metadata/load", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["tables_loaded"] > 0
        assert data["graph_nodes"] > 0

    def test_nl2sql_basic(self):
        """Test basic NL-to-SQL query generation."""
        # Load metadata first
        self.test_load_metadata_json()

        payload = {
            "question": "Show me all customers",
            "max_results": 10,
            "use_llm": False,
        }
        response = requests.post(f"{BASE_URL}/query/nl2sql", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "generated_sql" in data
        assert "SELECT" in data["generated_sql"].upper()

    def test_nl2sql_with_filter(self):
        """Test NL-to-SQL with a filtered query."""
        payload = {
            "question": "Find customers from New York",
            "max_results": 10,
            "use_llm": False,
        }
        response = requests.post(f"{BASE_URL}/query/nl2sql", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "FROM" in data["generated_sql"].upper()

    def test_nl2sql_aggregate(self):
        """Test NL-to-SQL with aggregation."""
        payload = {
            "question": "How many orders are pending?",
            "max_results": 10,
            "use_llm": False,
        }
        response = requests.post(f"{BASE_URL}/query/nl2sql", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "COUNT" in data["generated_sql"].upper() or "count" in data["generated_sql"]

    def test_apply_rules(self):
        """Test business rules application."""
        payload = {
            "sql": "SELECT * FROM customers WHERE city = 'New York'",
        }
        response = requests.post(f"{BASE_URL}/rules/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "modified_sql" in data
        assert len(data["rules_applied"]) > 0

    def test_graph_visualize(self):
        """Test graph visualization generation."""
        # Ensure metadata is loaded
        self.test_load_metadata_json()

        payload = {
            "include_columns": True,
            "output_format": "html",
        }
        response = requests.post(f"{BASE_URL}/graph/visualize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "html_content" in data or "message" in data

    def test_get_schema_graph(self):
        """Test schema graph data retrieval."""
        response = requests.get(f"{BASE_URL}/graph/schema")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data

    def test_get_schema_tables(self):
        """Test table listing."""
        response = requests.get(f"{BASE_URL}/schema/tables")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data

    def test_nl2sql_with_visualization(self):
        """Test NL-to-SQL with visualization generation."""
        payload = {
            "question": "Show me all customers",
            "max_results": 5,
            "use_llm": False,
            "include_visualization": True,
        }
        response = requests.post(f"{BASE_URL}/query/nl2sql", json=payload)
        assert response.status_code == 200
        data = response.json()

    def test_full_workflow(self):
        """Test the complete workflow end-to-end."""
        # 1. Load metadata
        meta_response = requests.post(
            f"{BASE_URL}/metadata/load",
            json={"source_type": "json", "source_path": "sample_data/schema.json"},
        )
        assert meta_response.status_code == 200

        # 2. Generate SQL
        query_response = requests.post(
            f"{BASE_URL}/query/nl2sql",
            json={"question": "List all active customers", "max_results": 5, "use_llm": False},
        )
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert query_data["generated_sql"]

        # 3. Apply rules to the generated SQL
        rules_response = requests.post(
            f"{BASE_URL}/rules/apply",
            json={"sql": query_data["generated_sql"]},
        )
        assert rules_response.status_code == 200
        assert rules_response.json()["modified_sql"]

        # 4. Visualize
        vis_response = requests.post(
            f"{BASE_URL}/graph/visualize",
            json={"include_columns": True, "output_format": "html"},
        )
        assert vis_response.status_code == 200