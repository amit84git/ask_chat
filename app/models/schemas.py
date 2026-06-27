"""
Pydantic models for API request/response schemas.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Represents a database column."""
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    referenced_table: Optional[str] = None
    referenced_column: Optional[str] = None
    description: Optional[str] = None
    sample_values: List[str] = Field(default_factory=list)


class TableSchema(BaseModel):
    """Represents a database table with metadata."""
    name: str
    schema_name: str = "public"
    columns: List[ColumnSchema] = Field(default_factory=list)
    description: Optional[str] = None
    row_count_estimate: int = 0
    tags: List[str] = Field(default_factory=list)


class BusinessRule(BaseModel):
    """A business rule that modifies or enhances query generation."""
    name: str
    description: str = ""
    priority: int = 100
    table_pattern: Optional[str] = None
    column_pattern: Optional[str] = None
    sql_modification: Optional[str] = None
    query_enhancement: Optional[str] = None
    condition: Optional[str] = None
    is_active: bool = True


class GraphNode(BaseModel):
    """Node in the semantic graph."""
    id: str
    label: str
    node_type: str = "table"  # table, column, domain, keyword
    group: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge connecting nodes in the semantic graph."""
    source: str
    target: str
    relationship: str = "references"  # references, contains, maps_to
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    """Natural language query request."""
    question: str = Field(..., min_length=1, max_length=2000,
                          description="Natural language question in English")
    context: Optional[str] = Field(None, description="Optional context or hint about tables")
    max_results: int = Field(100, ge=1, le=10000)
    use_llm: bool = True
    include_explanation: bool = True
    include_visualization: bool = False


class QueryResponse(BaseModel):
    """Response for a natural language to SQL query."""
    question: str
    generated_sql: str
    explanation: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    execution_time_ms: float = 0.0
    llm_used: bool = False
    rules_applied: List[str] = Field(default_factory=list)
    tables_used: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    visualization_html: Optional[str] = None
    error: Optional[str] = None


class NL2SQLResult(BaseModel):
    """Intermediate result from the NL to SQL engine."""
    sql: str
    tables_used: List[str] = Field(default_factory=list)
    columns_used: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    explanation: Optional[str] = None
    llm_generated: bool = False
    rules_applied: List[str] = Field(default_factory=list)


class MetadataLoadRequest(BaseModel):
    """Request to load semantic-layer metadata."""
    source_type: str = Field(..., pattern="^(json|excel|rds)$")
    source_path: Optional[str] = None
    rds_table_filter: Optional[str] = None
    include_sample_data: bool = True


class MetadataLoadResponse(BaseModel):
    """Response after loading metadata."""
    tables_loaded: int = 0
    columns_loaded: int = 0
    source_type: str
    graph_nodes: int = 0
    graph_edges: int = 0
    message: str = ""
    errors: List[str] = Field(default_factory=list)


class GraphVisualizeRequest(BaseModel):
    """Request to generate graph visualization."""
    include_columns: bool = True
    output_format: str = "html"
    max_depth: int = 2
    highlight_tables: Optional[List[str]] = None


class GraphVisualizeResponse(BaseModel):
    """Response containing visualization output."""
    html_content: Optional[str] = None
    output_path: Optional[str] = None
    node_count: int = 0
    edge_count: int = 0
    message: str = ""


class RuleApplyRequest(BaseModel):
    """Request to apply business rules to a SQL query."""
    sql: str = Field(..., description="The SQL query to process")
    rules: Optional[List[BusinessRule]] = None
    context: Optional[Dict[str, Any]] = None


class RuleApplyResponse(BaseModel):
    """Response after applying business rules."""
    original_sql: str
    modified_sql: str
    rules_applied: List[str] = Field(default_factory=list)
    changes: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: str = ""
    services: Dict[str, str] = Field(default_factory=dict)
    uptime_seconds: float = 0.0