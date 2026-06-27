#!/usr/bin/env python3
"""
Utility script to generate sample Excel metadata file for AskChat.
Creates a schema.xlsx with tables, columns, and keywords sheets.
"""
import pandas as pd
from pathlib import Path


def generate_excel(output_path: str = "sample_data/schema.xlsx"):
    """Generate a sample Excel metadata file matching the JSON schema."""
    
    # Tables sheet
    tables_data = {
        "name": ["customers", "orders", "products", "order_items"],
        "schema": ["public", "public", "public", "public"],
        "description": [
            "Customer information and profiles",
            "Customer order records",
            "Product catalog",
            "Line items within orders",
        ],
        "tags": [
            "core,customer",
            "core,sales",
            "core,inventory",
            "core,sales",
        ],
    }
    df_tables = pd.DataFrame(tables_data)

    # Columns sheet
    columns_data = {
        "table_name": [
            "customers", "customers", "customers", "customers", "customers",
            "orders", "orders", "orders", "orders",
            "products", "products", "products", "products",
            "order_items", "order_items", "order_items", "order_items",
        ],
        "name": [
            "id", "name", "email", "city", "status",
            "id", "customer_id", "total_amount", "status",
            "id", "name", "price", "category",
            "id", "order_id", "product_id", "quantity",
        ],
        "data_type": [
            "integer", "varchar(100)", "varchar(255)", "varchar(100)", "varchar(20)",
            "integer", "integer", "decimal(10,2)", "varchar(20)",
            "integer", "varchar(200)", "decimal(10,2)", "varchar(100)",
            "integer", "integer", "integer", "integer",
        ],
        "nullable": [False, False, False, True, True, False, False, True, True,
                     False, False, True, True, False, False, False, True],
        "is_pk": [True, False, False, False, False, True, False, False, False,
                  True, False, False, False, True, False, False, False],
        "is_fk": [False, False, False, False, False, False, True, False, False,
                  False, False, False, False, False, True, True, False],
        "ref_table": ["", "", "", "", "", "", "customers", "", "", "", "", "", "", "", "orders", "products", ""],
        "ref_column": ["", "", "", "", "", "", "id", "", "", "", "", "", "", "", "id", "id", ""],
        "description": [
            "Primary key", "Customer full name", "Email address (PII)", "City", "Status",
            "Primary key", "FK to customers", "Total order amount", "Order status",
            "Primary key", "Product name", "Unit price", "Product category",
            "Primary key", "FK to orders", "FK to products", "Quantity ordered",
        ],
    }
    df_columns = pd.DataFrame(columns_data)

    # Keywords sheet
    keywords_data = {
        "keyword": ["client", "purchase", "revenue", "inventory", "location", "catalog", "user"],
        "target": ["customers", "orders", "orders", "products", "customers", "products", "customers"],
        "description": [
            "Customer synonym", "Order synonym", "Money synonym", "Stock synonym",
            "Geographic synonym", "Product listing synonym", "Account synonym",
        ],
    }
    df_keywords = pd.DataFrame(keywords_data)

    # Write to Excel
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_tables.to_excel(writer, sheet_name="tables", index=False)
        df_columns.to_excel(writer, sheet_name="columns", index=False)
        df_keywords.to_excel(writer, sheet_name="keywords", index=False)

    print(f"Generated Excel metadata file: {output_path}")
    print(f"  Tables sheet: {len(df_tables)} rows")
    print(f"  Columns sheet: {len(df_columns)} rows")
    print(f"  Keywords sheet: {len(df_keywords)} rows")


if __name__ == "__main__":
    generate_excel()