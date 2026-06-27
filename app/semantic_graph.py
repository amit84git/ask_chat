"""
Semantic Graph Analysis Module.
Builds a NetworkX graph from database metadata to enable intelligent
table/column selection for NL-to-SQL translation.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from app.config import settings
from app.database import db_manager
from app.models.schemas import (
    ColumnSchema,
    GraphEdge,
    GraphNode,
    TableSchema,
)

logger = logging.getLogger(__name__)


class SemanticGraph:
    """
    Builds and queries a semantic graph of database tables, columns, and relationships.
    
    The graph enables:
    - Finding related tables via foreign keys
    - Mapping natural language terms to schema objects
    - Understanding join paths between tables
    - Calculating semantic relevance scores
    """

    def __init__(self):
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._built = False

    def build_from_tables(self, tables: List[TableSchema], domain_keywords: Optional[Dict[str, List[str]]] = None):
        """
        Build the graph from a list of TableSchema objects.
        
        Args:
            tables: List of table schemas
            domain_keywords: Optional mapping of domain terms to table/column names
        """
        self.graph.clear()

        for table in tables:
            # Add table node
            table_node_id = f"table:{table.schema_name}.{table.name}"
            self.graph.add_node(
                table_node_id,
                label=table.name,
                node_type="table",
                schema=table.schema_name,
                description=table.description or "",
                tags=table.tags,
            )

            # Add column nodes and connect them to their table
            for col in table.columns:
                col_node_id = f"column:{table.schema_name}.{table.name}.{col.name}"
                self.graph.add_node(
                    col_node_id,
                    label=col.name,
                    node_type="column",
                    data_type=col.data_type,
                    nullable=col.nullable,
                    is_pk=col.is_primary_key,
                    is_fk=col.is_foreign_key,
                    description=col.description or "",
                )
                self.graph.add_edge(
                    table_node_id,
                    col_node_id,
                    relationship="contains",
                    weight=1.0,
                )

                # Add foreign key relationships
                if col.is_foreign_key and col.referenced_table:
                    ref_table_id = f"table:{table.schema_name}.{col.referenced_table}"
                    if self.graph.has_node(ref_table_id):
                        ref_col_id = f"column:{table.schema_name}.{col.referenced_table}.{col.referenced_column}"
                        self.graph.add_edge(
                            col_node_id,
                            ref_col_id,
                            relationship="references",
                            weight=2.0,
                        )
                        self.graph.add_edge(
                            table_node_id,
                            ref_table_id,
                            relationship="joins_via_fk",
                            weight=1.5,
                        )

        # Add domain keyword mappings if provided
        if domain_keywords:
            for term, targets in domain_keywords.items():
                keyword_id = f"keyword:{term}"
                self.graph.add_node(
                    keyword_id,
                    label=term,
                    node_type="keyword",
                )
                for target in targets:
                    # Try to find matching table or column node
                    found = False
                    for node in self.graph.nodes:
                        node_label = self.graph.nodes[node].get("label", "").lower()
                        if target.lower() == node_label or target.lower() in node:
                            self.graph.add_edge(
                                keyword_id,
                                node,
                                relationship="maps_to",
                                weight=1.0,
                            )
                            found = True
                    if not found:
                        logger.debug(f"Keyword '{term}' target '{target}' not found in graph")

        self._built = True
        logger.info(f"Built semantic graph with {self.graph.number_of_nodes()} nodes and "
                    f"{self.graph.number_of_edges()} edges")

    def find_closest_tables(self, terms: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find tables that are semantically closest to the given terms.
        Uses graph traversal to find related nodes.
        """
        if not self._built:
            return []

        scores: Dict[str, float] = {}
        
        for term in terms:
            term_lower = term.lower()
            best_score = 0.0
            best_table = None

            for node, data in self.graph.nodes(data=True):
                node_label = data.get("label", "").lower()
                node_type = data.get("node_type", "")

                if node_type == "keyword" and node_label == term_lower:
                    # Walk from keyword to connected tables
                    for neighbor in self.graph.successors(node):
                        neighbor_data = self.graph.nodes[neighbor]
                        if neighbor_data.get("node_type") == "table":
                            tbl = neighbor_data.get("label", "")
                            scores[tbl] = scores.get(tbl, 0) + 2.0
                        elif neighbor_data.get("node_type") == "column":
                            # Find parent table
                            for pred in self.graph.predecessors(neighbor):
                                if self.graph.nodes[pred].get("node_type") == "table":
                                    tbl = self.graph.nodes[pred].get("label", "")
                                    scores[tbl] = scores.get(tbl, 0) + 1.5

                elif node_type == "table" and (term_lower in node_label or node_label in term_lower):
                    scores[node_label] = scores.get(node_label, 0) + 3.0

                elif node_type == "column" and (term_lower in node_label or node_label in term_lower):
                    for pred in self.graph.predecessors(node):
                        if self.graph.nodes[pred].get("node_type") == "table":
                            tbl = self.graph.nodes[pred].get("label", "")
                            scores[tbl] = scores.get(tbl, 0) + 1.0

        sorted_tables = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_tables[:top_k]

    def find_join_path(self, table1: str, table2: str) -> List[str]:
        """Find the shortest join path between two tables."""
        if not self._built:
            return []

        node1 = None
        node2 = None
        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") == "table" and data.get("label", "").lower() == table1.lower():
                node1 = node
            if data.get("node_type") == "table" and data.get("label", "").lower() == table2.lower():
                node2 = node

        if node1 and node2:
            try:
                path = nx.shortest_path(self.graph, source=node1, target=node2)
                labels = []
                for n in path:
                    data = self.graph.nodes[n]
                    if data.get("node_type") == "table":
                        labels.append(data.get("label", ""))
                return labels
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return []

        return []

    def get_relevant_columns(self, table_name: str, terms: List[str]) -> List[str]:
        """Get columns from a table that match the given terms."""
        matching_columns = []
        table_node_id = None

        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") == "table" and data.get("label", "").lower() == table_name.lower():
                table_node_id = node
                break

        if not table_node_id:
            return []

        for _, child, edge_data in self.graph.out_edges(table_node_id, data=True):
            child_data = self.graph.nodes[child]
            if child_data.get("node_type") == "column":
                col_name = child_data.get("label", "")
                for term in terms:
                    if term.lower() in col_name.lower() or col_name.lower() in term.lower():
                        matching_columns.append(col_name)
                        break

        return matching_columns

    def to_pyvis_html(self, include_columns: bool = True) -> str:
        """Generate an interactive HTML visualization using Pyvis."""
        from pyvis.network import Network

        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
        net.set_options("""
        var options = {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -3000,
              "centralGravity": 0.3,
              "springLength": 200
            }
          }
        }
        """)

        added_nodes = set()
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            label = data.get("label", node)

            if node_type == "column" and not include_columns:
                continue

            color = {"table": "#00aaff", "column": "#ffaa00", "keyword": "#ff5500"}.get(node_type, "#888888")
            size = {"table": 30, "column": 15, "keyword": 25}.get(node_type, 20)
            title = json.dumps(data, indent=2)

            net.add_node(node, label=label, color=color, size=size, title=title)
            added_nodes.add(node)

        for source, target, edge_data in self.graph.edges(data=True):
            if source in added_nodes and target in added_nodes:
                rel = edge_data.get("relationship", "connected")
                color = {"references": "#ff6666", "contains": "#66ff66", "maps_to": "#6666ff"}.get(rel, "#cccccc")
                net.add_edge(source, target, title=rel, color=color)

        return net.generate_html()

    def to_dict(self) -> Dict[str, Any]:
        """Export graph data as a dictionary (for JSON serialization)."""
        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node,
                "label": data.get("label", node),
                "node_type": data.get("node_type", "unknown"),
                "metadata": {k: v for k, v in data.items() if k not in ("label", "node_type")},
            })

        edges = []
        for source, target, edge_data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relationship": edge_data.get("relationship", "connected"),
                "weight": edge_data.get("weight", 1.0),
            })

        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


# Singleton
semantic_graph = SemanticGraph()