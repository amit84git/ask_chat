# AskChat Example Prompts and Expected SQL Output

This document contains example natural language questions and their expected SQL output,
demonstrating the NL-to-SQL conversion capabilities of AskChat.

## Basic Queries

### 1. Simple Select

**Question:** "Show me all customers"
**Expected SQL:**

```sql
SELECT * FROM customers ORDER BY created_at DESC LIMIT 100
```

### 2. Select Specific Columns

**Question:** "List customer names and emails"
**Expected SQL:**

```sql
SELECT name, email FROM customers ORDER BY created_at DESC LIMIT 100
```

### 3. Simple Count

**Question:** "How many customers do we have?"
**Expected SQL:**

```sql
SELECT COUNT(*) FROM customers ORDER BY created_at DESC LIMIT 100
```

## Filtered Queries

### 4. Text Filter

**Question:** "Find customers from New York"
**Expected SQL:**

```sql
SELECT * FROM customers WHERE city = 'New York' ORDER BY created_at DESC LIMIT 100
```

### 5. Status Filter

**Question:** "Show all active customers"
**Expected SQL:**

```sql
SELECT * FROM customers WHERE status = 'active' ORDER BY created_at DESC LIMIT 100
```

### 6. ID Lookup

**Question:** "Get customer with id 5"
**Expected SQL:**

```sql
SELECT * FROM customers WHERE id = 5 ORDER BY created_at DESC LIMIT 100
```

## Aggregate Queries

### 7. Sum/Aggregate

**Question:** "What is the total revenue from orders?"
**Expected SQL:**

```sql
SELECT SUM(total_amount) FROM orders ORDER BY created_at DESC LIMIT 100
```

### 8. Average

**Question:** "What is the average order amount?"
**Expected SQL:**

```sql
SELECT AVG(total_amount) FROM orders ORDER BY created_at DESC LIMIT 100
```

### 9. Count with Filter

**Question:** "How many orders are pending?"
**Expected SQL:**

```sql
SELECT COUNT(*) FROM orders WHERE status = 'pending' ORDER BY created_at DESC LIMIT 100
```

## Top N Queries

### 10. Top N

**Question:** "Show me the top 10 most expensive products"
**Expected SQL:**

```sql
SELECT * FROM products ORDER BY price DESC LIMIT 10
```

### 11. Top Customers

**Question:** "Show top 5 customers by order total"
**Expected SQL:**

```sql
SELECT customers.name, SUM(orders.total_amount) as total
FROM customers
JOIN orders ON customers.id = orders.customer_id
GROUP BY customers.name
ORDER BY total DESC
LIMIT 5
```

## Multi-Table Queries

### 12. Simple Join

**Question:** "Show me all orders with customer names"
**Expected SQL:**

```sql
SELECT orders.*, customers.name as customer_name
FROM orders
JOIN customers ON orders.customer_id = customers.id
ORDER BY orders.created_at DESC
LIMIT 100
```

### 13. Three-Table Join

**Question:** "List all products that have been ordered, with order counts"
**Expected SQL:**

```sql
SELECT products.name, COUNT(order_items.id) as order_count
FROM products
JOIN order_items ON products.id = order_items.product_id
GROUP BY products.name
ORDER BY order_count DESC
LIMIT 100
```

## Time-Based Queries

### 14. Date Range

**Question:** "Show orders from the last 30 days"
**Expected SQL:**

```sql
SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY order_date DESC LIMIT 100
```

### 15. Recent Customers

**Question:** "Show me customers who signed up this month"
**Expected SQL:**

```sql
SELECT * FROM customers
WHERE signup_date >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY signup_date DESC LIMIT 100
```

## Business Rules Applied

### 16. With Rules Enhancement

**Question:** "List all customers"
**After rules applied:** (Adds ordering, limit, and date range)

```sql
SELECT name, email
FROM customers
WHERE deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 1000
```

## Distinct Queries

### 17. Unique Values

**Question:** "What are the different product categories?"
**Expected SQL:**

```sql
SELECT DISTINCT category FROM products ORDER BY created_at DESC LIMIT 100
```

## Sample API Request/Response

### Request

```json
POST /query/nl2sql
Content-Type: application/json

{
    "question": "Show me all customers from New York",
    "max_results": 50,
    "use_llm": false,
    "include_visualization": false
}
```

### Response

```json
{
  "question": "Show me all customers from New York",
  "generated_sql": "SELECT * FROM customers WHERE city = 'New York' ORDER BY created_at DESC LIMIT 50",
  "explanation": "Generated using heuristic pattern matching\nQuery: SELECT * FROM customers WHERE city = 'New York' ORDER BY created_at DESC LIMIT 50\nBusiness rules applied: order_by_created_desc",
  "results": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "city": "New York",
      "state": "NY",
      "country": "USA",
      "status": "active",
      "signup_date": "2024-01-15"
    }
  ],
  "row_count": 1,
  "execution_time_ms": 45.2,
  "llm_used": false,
  "rules_applied": ["order_by_created_desc", "limit_safe_results"],
  "tables_used": ["customers"],
  "confidence_score": 0.65
}
```

### Metadata Load Request

```json
POST /metadata/load
Content-Type: application/json

{
    "source_type": "json",
    "source_path": "sample_data/schema.json"
}
```

### Graph Visualization Request

```json
POST /graph/visualize
Content-Type: application/json

{
    "include_columns": true,
    "output_format": "html"
}
```

### Rules Apply Request

```json
POST /rules/apply
Content-Type: application/json

{
    "sql": "SELECT * FROM customers WHERE city = 'New York'",
    "context": {"user_role": "analyst"}
}
```
