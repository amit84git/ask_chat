"""
Unit tests for the Semantic Graph module.
"""
import pytest
from app.semantic_graph import SemanticGraph
from app.models.schemas import TableSchema, ColumnSchema


@pytest.fixture
def sample_tables():
    return [
        TableSchema(
            name="customers",
            schema_name="public",
            columns=[
                ColumnSchema(name="id", data_type="integer", is_primary_key=True),
                ColumnSchema(name="name", data_type="varchar"),
                ColumnSchema(name="email", data_type="varchar"),
                ColumnSchema(name="city", data_type="varchar"),
            ],
        ),
        TableSchema(
            name="orders",
            schema_name="public",
            columns=[
                ColumnSchema(name="id", data_type="integer", is_primary_key=True),
                ColumnSchema(
                    name="customer_id",
                    data_type="integer",
                    is_foreign_key=True,
                    referenced_table="customers",
                    referenced_column="id",
                ),
                ColumnSchema(name="total_amount", data_type="decimal"),
                ColumnSchema(name="order_date", data_type="date"),
            ],
        ),
    ]


class TestSemanticGraph:
    def test_build_graph(self, sample_tables):
        graph = SemanticGraph()
        graph.build_from_tables(sample_tables)
        assert graph._built is True
        assert graph.graph.number_of_nodes() > 0
        assert graph.graph.number_of_edges() > 0

    def test_find_closest_tables(self, sample_tables):
        graph = SemanticGraph()
        graph.build_from_tables(sample_tables)
        results = graph.find_closest_tables(["customer"])
        assert len(results) > 0
        assert "customers" in [r[0] for r in results]

    def test_find_join_path(self, sample_tables):
        graph = SemanticGraph()
        graph.build_from_tables(sample_tables)
        path = graph.find_join_path("customers", "orders")
        assert len(path) > 0
        assert "customers" in path
        assert "orders" in path

    def test_get_relevant_columns(self, sample_tables):
        graph = SemanticGraph()
        graph.build_from_tables(sample_tables)
        columns = graph.get_relevant_columns("customers", ["name", "email"])
        assert len(columns) > 0
        assert "name" in columns or "email" in columns

    def test_to_dict(self, sample_tables):
        graph = SemanticGraph()
        graph.build_from_tables(sample_tables)
        data = graph.to_dict()
        assert "nodes" in data
        assert "edges" in data
        assert data["node_count"] > 0
        assert data["edge_count"] > 0

    def test_to_pyvis_html(self, sample_tables):
        graph = SemanticGraph()
        graph.build_from_tables(sample_tables)
        html = graph.to_pyvis_html()
        assert "<!DOCTYPE html>" in html
        assert "pyvis" in html.lower() or "html" in html.lower()

    def test_no_graph_built(self):
        graph = SemanticGraph()
        assert graph._built is False
        results = graph.find_closest_tables(["test"])
        assert results == []

    def test_build_with_keywords(self, sample_tables):
        graph = SemanticGraph()
        keywords = {"client": ["customers"], "purchase": ["orders"]}
        graph.build_from_tables(sample_tables, domain_keywords=keywords)
        results = graph.find_closest_tables(["client"])
        assert len(results) > 0