"""
AskChat - Natural Language to SQL Platform
FastAPI Application Entry Point
"""
import logging
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings
from app.database import db_manager
from app.models import (
    GraphVisualizeRequest,
    GraphVisualizeResponse,
    HealthResponse,
    MetadataLoadRequest,
    MetadataLoadResponse,
    QueryRequest,
    QueryResponse,
    RuleApplyRequest,
    RuleApplyResponse,
)
from app.aws_utils import S3Manager
from app.local_llm import LocalLLM, get_llm_provider
from app.semantic_graph import semantic_graph
from app.fuzzy_matcher import fuzzy_matcher
from app.rules_engine import rules_engine
from app.query_generator import query_generator
from app.visualization import vis_service
from app.metadata import metadata_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Application start time
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info(f"Starting {settings.app_name} v1.0.0")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"AWS Endpoint: {settings.aws_endpoint_url or 'Real AWS'}")
    logger.info(f"LLM Provider: {settings.llm_provider}")

    # Initialize S3 bucket if needed
    if settings.app_env == "local":
        try:
            s3 = S3Manager()
            s3.ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"S3 initialization skipped: {e}")

    # Test database connection
    db_ok = db_manager.test_connection()
    if db_ok:
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: FAILED - queries will not execute until DB is available")

    # Check local LLM availability
    llm_provider = get_llm_provider()
    if isinstance(llm_provider, LocalLLM):
        if llm_provider.is_available:
            models = llm_provider.list_models()
            logger.info(f"Local LLM available. Models: {', '.join(models[:5]) or 'none loaded'}")
        else:
            logger.info("Local LLM not available. Run: ollama pull llama3.1:8b")
    elif llm_provider is not None:
        logger.info(f"LLM provider configured: {settings.llm_provider}")
    else:
        logger.info("No LLM provider - using heuristic-only mode")

    yield

    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-Powered Natural Language to SQL Platform",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins] if settings.cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    db_status = "ok" if db_manager.test_connection() else "unavailable"
    graph_status = "ok" if semantic_graph._built else "not_built"
    rules_status = "active" if settings.feature_rules_engine else "disabled"

    # Determine LLM status
    llm_provider = get_llm_provider()
    if isinstance(llm_provider, LocalLLM):
        llm_status = f"local: {settings.local_llm_model}" if llm_provider.is_available else "local: unavailable"
    elif llm_provider is not None:
        llm_status = f"bedrock: {settings.llm_provider}"
    else:
        llm_status = "disabled (heuristic only)"

    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        services={
            "database": db_status,
            "semantic_graph": graph_status,
            "llm": llm_status,
            "rules_engine": rules_status,
        },
        uptime_seconds=time.time() - _start_time,
    )


@app.post("/query/nl2sql", response_model=QueryResponse)
async def natural_language_to_sql(request: QueryRequest):
    """
    Convert a natural language question to a SQL query and execute it.
    
    Example request:
    ```json
    {
        "question": "Show me all customers from New York",
        "max_results": 50,
        "use_llm": true
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Set max results on generator
        query_generator.set_request_max(request.max_results)

        # Generate SQL
        nl2sql_result = query_generator.generate(request)

        if not nl2sql_result.sql:
            return QueryResponse(
                question=request.question,
                generated_sql="",
                explanation=nl2sql_result.explanation or "Could not generate SQL",
                error="Query generation failed",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Execute the query
        results = []
        try:
            results = db_manager.execute_query(nl2sql_result.sql)
        except Exception as e:
            logger.warning(f"Query execution failed (showing generated SQL anyway): {e}")

        # Generate visualization if requested
        vis_html = None
        if request.include_visualization and results:
            try:
                vis_html = vis_service.generate_data_chart(
                    results[:50],
                    title=f"Results for: {request.question}",
                )
            except Exception as e:
                logger.warning(f"Visualization generation failed: {e}")

        return QueryResponse(
            question=request.question,
            generated_sql=nl2sql_result.sql,
            explanation=nl2sql_result.explanation,
            results=results[:request.max_results] if results else None,
            row_count=len(results) if results else 0,
            execution_time_ms=(time.time() - start_time) * 1000,
            llm_used=nl2sql_result.llm_generated,
            rules_applied=nl2sql_result.rules_applied,
            tables_used=nl2sql_result.tables_used,
            confidence_score=nl2sql_result.confidence,
            visualization_html=vis_html,
        )

    except Exception as e:
        logger.exception("NL2SQL processing failed")
        return QueryResponse(
            question=request.question,
            generated_sql="",
            error=f"Processing error: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000,
        )


@app.post("/metadata/load", response_model=MetadataLoadResponse)
async def load_metadata(request: MetadataLoadRequest):
    """
    Load metadata from JSON, Excel, or RDS to build the semantic graph.
    
    Example request:
    ```json
    {
        "source_type": "json",
        "source_path": "sample_data/schema.json"
    }
    ```
    """
    try:
        if request.source_type == "json":
            source_path = request.source_path or "sample_data/schema.json"
            return metadata_service.load_from_json(source_path)
        elif request.source_type == "excel":
            source_path = request.source_path or "sample_data/schema.xlsx"
            return metadata_service.load_from_excel(source_path)
        elif request.source_type == "rds":
            return metadata_service.load_from_rds(request.rds_table_filter)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {request.source_type}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/visualize", response_model=GraphVisualizeResponse)
async def visualize_graph(request: GraphVisualizeRequest):
    """
    Generate an interactive HTML visualization of the semantic schema graph.
    
    Example request:
    ```json
    {
        "include_columns": true,
        "output_format": "html"
    }
    ```
    """
    try:
        if not semantic_graph._built:
            return GraphVisualizeResponse(
                message="Semantic graph not built. Load metadata first using /metadata/load"
            )

        if request.output_format == "html":
            html_content = semantic_graph.to_pyvis_html(include_columns=request.include_columns)
            # Save to file as well
            filename = f"schema_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = vis_service.save_html(html_content, filename)

            graph_dict = semantic_graph.to_dict()
            return GraphVisualizeResponse(
                html_content=html_content,
                output_path=filepath,
                node_count=graph_dict["node_count"],
                edge_count=graph_dict["edge_count"],
                message=f"Graph visualization generated with {graph_dict['node_count']} nodes",
            )
        else:
            graph_dict = semantic_graph.to_dict()
            return GraphVisualizeResponse(
                node_count=graph_dict["node_count"],
                edge_count=graph_dict["edge_count"],
                message="Graph data exported as JSON (use HTML for interactive visualization)",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rules/apply", response_model=RuleApplyResponse)
async def apply_business_rules(request: RuleApplyRequest):
    """
    Apply business rules to an existing SQL query.
    
    Example request:
    ```json
    {
        "sql": "SELECT * FROM customers WHERE city = 'New York'",
        "context": {"user_role": "analyst"}
    }
    ```
    """
    try:
        # Extract table names from SQL for rule matching
        import re
        table_names = re.findall(r'\bFROM\s+(\w+)|JOIN\s+(\w+)', request.sql, re.IGNORECASE)
        tables = [t[0] or t[1] for t in table_names]

        # Use custom rules if provided, otherwise use defaults
        engine = rules_engine
        if request.rules:
            engine = type(rules_engine)(request.rules)

        modified_sql, applied_rules, changes = engine.apply_rules(
            request.sql,
            tables_used=tables,
            context=request.context,
        )

        return RuleApplyResponse(
            original_sql=request.sql,
            modified_sql=modified_sql,
            rules_applied=applied_rules,
            changes=changes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/schema")
async def get_schema_graph():
    """Get the schema graph as JSON data."""
    if not semantic_graph._built:
        return {"message": "Graph not built", "nodes": [], "edges": []}
    return semantic_graph.to_dict()


@app.get("/schema/tables")
async def list_tables():
    """List available database tables from introspection."""
    try:
        tables = db_manager.get_table_schemas()
        return {
            "tables": [t.model_dump() for t in tables],
            "count": len(tables),
        }
    except Exception as e:
        return {"tables": [], "count": 0, "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint with API overview."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "endpoints": {
            "health": "GET /health",
            "nl2sql": "POST /query/nl2sql",
            "load_metadata": "POST /metadata/load",
            "visualize_graph": "POST /graph/visualize",
            "apply_rules": "POST /rules/apply",
            "schema_graph": "GET /graph/schema",
            "list_tables": "GET /schema/tables",
        },
        "docs": "/docs",
        "openapi": "/openapi.json",
    }