"""
Database connection and operations layer.
Supports both local PostgreSQL and RDS PostgreSQL via Floci.
"""
import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.models.schemas import ColumnSchema, TableSchema

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
            )
        return self._engine

    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query safely and return results as list of dicts.
        Uses parameterized queries to prevent SQL injection.
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                if result.returns_rows:
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    return rows
                conn.commit()
                return []
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def get_table_schemas(self, schema_name: str = "public") -> List[TableSchema]:
        """Introspect database tables and return their schemas."""
        tables = []
        inspector = inspect(self.engine)
        try:
            table_names = inspector.get_table_names(schema=schema_name)
            for table_name in table_names:
                columns = []
                for col in inspector.get_columns(table_name, schema=schema_name):
                    col_schema = ColumnSchema(
                        name=col["name"],
                        data_type=str(col["type"]),
                        nullable=col.get("nullable", True),
                    )
                    columns.append(col_schema)

                # Get primary keys
                pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
                pk_columns = pk_constraint.get("constrained_columns", [])
                for col in columns:
                    if col.name in pk_columns:
                        col.is_primary_key = True

                # Get foreign keys
                fks = inspector.get_foreign_keys(table_name, schema=schema_name)
                for fk in fks:
                    for i, col_name in enumerate(fk["constrained_columns"]):
                        for col in columns:
                            if col.name == col_name:
                                col.is_foreign_key = True
                                col.referenced_table = fk["referred_table"]
                                col.referenced_column = (
                                    fk["referred_columns"][i] if i < len(fk["referred_columns"]) else None
                                )

                table = TableSchema(
                    name=table_name,
                    schema_name=schema_name,
                    columns=columns,
                )
                tables.append(table)

            logger.info(f"Loaded {len(tables)} tables from database")
            return tables
        except Exception as e:
            logger.error(f"Failed to introspect database: {e}")
            return []

    def execute_and_fetch(self, sql: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute SQL and return results."""
        return self.execute_query(sql, params)


# Singleton instance
db_manager = DatabaseManager()