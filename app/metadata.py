"""
Metadata ingestion module.
Loads semantic-layer definitions from JSON, Excel, and RDS PostgreSQL metadata.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.database import db_manager
from app.models.schemas import ColumnSchema, MetadataLoadResponse, TableSchema
from app.semantic_graph import semantic_graph

logger = logging.getLogger(__name__)


class MetadataService:
    """
    Service for loading metadata from multiple sources:
    - JSON files (semantic definitions)
    - Excel files (.xlsx with table/column definitions)
    - RDS PostgreSQL introspection
    """

    def load_from_json(self, json_path: str) -> MetadataLoadResponse:
        """Load metadata from a JSON file."""
        errors = []
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            return MetadataLoadResponse(
                source_type="json",
                message="Failed to load JSON file",
                errors=[str(e)],
            )

        tables = data if isinstance(data, list) else data.get("tables", [])
        domain_keywords = data.get("domain_keywords", {})

        table_schemas = []
        for tbl in tables:
            columns = []
            for col in tbl.get("columns", []):
                columns.append(ColumnSchema(**col))
            table_schemas.append(
                TableSchema(
                    name=tbl["name"],
                    schema_name=tbl.get("schema", "public"),
                    columns=columns,
                    description=tbl.get("description", ""),
                    tags=tbl.get("tags", []),
                )
            )

        semantic_graph.build_from_tables(table_schemas, domain_keywords)
        graph_data = semantic_graph.to_dict()

        return MetadataLoadResponse(
            tables_loaded=len(table_schemas),
            columns_loaded=sum(len(t.columns) for t in table_schemas),
            source_type="json",
            graph_nodes=graph_data["node_count"],
            graph_edges=graph_data["edge_count"],
            message=f"Loaded {len(table_schemas)} tables from JSON",
            errors=errors,
        )

    def load_from_excel(self, excel_path: str) -> MetadataLoadResponse:
        """Load metadata from an Excel file."""
        errors = []
        try:
            excel_file = pd.ExcelFile(excel_path)
        except Exception as e:
            return MetadataLoadResponse(
                source_type="excel",
                message="Failed to load Excel file",
                errors=[str(e)],
            )

        tables_sheet = None
        columns_sheet = None
        keywords_sheet = None

        for sheet_name in excel_file.sheet_names:
            lower = sheet_name.lower()
            if "table" in lower:
                tables_sheet = pd.read_excel(excel_file, sheet_name)
            elif "column" in lower:
                columns_sheet = pd.read_excel(excel_file, sheet_name)
            elif "keyword" in lower:
                keywords_sheet = pd.read_excel(excel_file, sheet_name)

        if tables_sheet is None:
            return MetadataLoadResponse(
                source_type="excel",
                message="No 'tables' sheet found in Excel file",
                errors=errors,
            )

        # Build table schemas from Excel data
        table_map: Dict[str, TableSchema] = {}
        for _, row in tables_sheet.iterrows():
            name = str(row.get("name", row.get("table_name", "")))
            if name:
                table = TableSchema(
                    name=name,
                    schema_name=str(row.get("schema", "public")),
                    description=str(row.get("description", "")),
                    tags=str(row.get("tags", "")).split(",") if row.get("tags") else [],
                )
                table_map[name] = table

        if columns_sheet is not None:
            for _, row in columns_sheet.iterrows():
                table_name = str(row.get("table_name", row.get("table", "")))
                col_name = str(row.get("name", row.get("column_name", "")))
                if table_name in table_map and col_name:
                    col = ColumnSchema(
                        name=col_name,
                        data_type=str(row.get("data_type", "text")),
                        nullable=bool(row.get("nullable", True)),
                        is_primary_key=bool(row.get("is_pk", False)),
                        is_foreign_key=bool(row.get("is_fk", False)),
                        referenced_table=str(row.get("ref_table", "")) or None,
                        referenced_column=str(row.get("ref_column", "")) or None,
                        description=str(row.get("description", "")),
                    )
                    table_map[table_name].columns.append(col)

        domain_keywords = {}
        if keywords_sheet is not None:
            for _, row in keywords_sheet.iterrows():
                term = str(row.get("keyword", row.get("term", "")))
                target = str(row.get("target", row.get("table", "")))
                if term and target:
                    if term not in domain_keywords:
                        domain_keywords[term] = []
                    domain_keywords[term].append(target)

        table_schemas = list(table_map.values())
        semantic_graph.build_from_tables(table_schemas, domain_keywords)
        graph_data = semantic_graph.to_dict()

        return MetadataLoadResponse(
            tables_loaded=len(table_schemas),
            columns_loaded=sum(len(t.columns) for t in table_schemas),
            source_type="excel",
            graph_nodes=graph_data["node_count"],
            graph_edges=graph_data["edge_count"],
            message=f"Loaded {len(table_schemas)} tables from Excel",
            errors=errors,
        )

    def load_from_rds(self, schema_filter: Optional[str] = None) -> MetadataLoadResponse:
        """Load metadata by introspecting RDS PostgreSQL."""
        errors = []
        try:
            tables = db_manager.get_table_schemas(schema_filter or "public")
            if not tables:
                return MetadataLoadResponse(
                    source_type="rds",
                    message="No tables found in database",
                    errors=["Database introspection returned no tables. Is the database seeded?"],
                )

            semantic_graph.build_from_tables(tables)
            graph_data = semantic_graph.to_dict()

            return MetadataLoadResponse(
                tables_loaded=len(tables),
                columns_loaded=sum(len(t.columns) for t in tables),
                source_type="rds",
                graph_nodes=graph_data["node_count"],
                graph_edges=graph_data["edge_count"],
                message=f"Loaded {len(tables)} tables from RDS introspection",
                errors=errors,
            )
        except Exception as e:
            logger.error(f"RDS metadata loading failed: {e}")
            return MetadataLoadResponse(
                source_type="rds",
                message="Failed to load metadata from RDS",
                errors=[str(e)],
            )


# Singleton
metadata_service = MetadataService()