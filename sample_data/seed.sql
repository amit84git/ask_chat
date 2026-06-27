-- ============================================================
-- AskChat - Sample Database Seed
-- Creates tables with realistic e-commerce data for PoC
-- ============================================================

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50) DEFAULT 'USA',
    signup_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP DEFAULT NULL
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date DATE DEFAULT CURRENT_DATE,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10,2) DEFAULT 0.00,
    stock_quantity INTEGER DEFAULT 0,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items (junction table)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);

-- ============================================================
-- Sample Data
-- ============================================================

-- Customers (50 sample records)
INSERT INTO customers (name, email, phone, city, state, country, signup_date, status, created_at) VALUES
('Alice Johnson', 'alice@example.com', '555-0101', 'New York', 'NY', 'USA', '2024-01-15', 'active', '2024-01-15 10:00:00'),
('Bob Smith', 'bob@example.com', '555-0102', 'Los Angeles', 'CA', 'USA', '2024-02-01', 'active', '2024-02-01 11:00:00'),
('Carol White', 'carol@example.com', '555-0103', 'Chicago', 'IL', 'USA', '2024-02-15', 'active', '2024-02-15 09:30:00'),
('David Brown', 'david@example.com', '555-0104', 'Houston', 'TX', 'USA', '2024-03-01', 'active', '2024-03-01 14:00:00'),
('Eve Davis', 'eve@example.com', '555-0105', 'Phoenix', 'AZ', 'USA', '2024-03-10', 'active', '2024-03-10 08:00:00'),
('Frank Miller', 'frank@example.com', '555-0106', 'Philadelphia', 'PA', 'USA', '2024-03-20', 'active', '2024-03-20 10:30:00'),
('Grace Wilson', 'grace@example.com', '555-0107', 'San Antonio', 'TX', 'USA', '2024-04-01', 'active', '2024-04-01 12:00:00'),
('Henry Moore', 'henry@example.com', '555-0108', 'San Diego', 'CA', 'USA', '2024-04-10', 'active', '2024-04-10 15:00:00'),
('Ivy Taylor', 'ivy@example.com', '555-0109', 'Dallas', 'TX', 'USA', '2024-04-20', 'active', '2024-04-20 11:45:00'),
('Jack Anderson', 'jack@example.com', '555-0110', 'San Jose', 'CA', 'USA', '2024-05-01', 'active', '2024-05-01 09:00:00'),
('Karen Thomas', 'karen@example.com', '555-0111', 'Austin', 'TX', 'USA', '2024-05-10', 'inactive', '2024-05-10 10:00:00'),
('Leo Jackson', 'leo@example.com', '555-0112', 'Jacksonville', 'FL', 'USA', '2024-05-15', 'active', '2024-05-15 13:00:00'),
('Maria Garcia', 'maria@example.com', '555-0113', 'Fort Worth', 'TX', 'USA', '2024-05-20', 'active', '2024-05-20 14:30:00'),
('Nathan Hall', 'nathan@example.com', '555-0114', 'Columbus', 'OH', 'USA', '2024-06-01', 'active', '2024-06-01 08:30:00'),
('Olivia Young', 'olivia@example.com', '555-0115', 'Charlotte', 'NC', 'USA', '2024-06-10', 'active', '2024-06-10 11:00:00'),
('Paul King', 'paul@example.com', '555-0116', 'Indianapolis', 'IN', 'USA', '2024-06-15', 'active', '2024-06-15 10:15:00'),
('Quinn Lee', 'quinn@example.com', '555-0117', 'San Francisco', 'CA', 'USA', '2024-06-20', 'active', '2024-06-20 09:45:00'),
('Rachel Wright', 'rachel@example.com', '555-0118', 'Seattle', 'WA', 'USA', '2024-07-01', 'active', '2024-07-01 12:30:00'),
('Sam Lopez', 'sam@example.com', '555-0119', 'Denver', 'CO', 'USA', '2024-07-10', 'suspended', '2024-07-10 15:00:00'),
('Tina Hill', 'tina@example.com', '555-0120', 'Nashville', 'TN', 'USA', '2024-07-15', 'active', '2024-07-15 08:00:00'),
('Uma Scott', 'uma@example.com', '555-0121', 'Memphis', 'TN', 'USA', '2024-07-20', 'active', '2024-07-20 11:30:00'),
('Victor Green', 'victor@example.com', '555-0122', 'Louisville', 'KY', 'USA', '2024-08-01', 'active', '2024-08-01 10:00:00'),
('Wendy Adams', 'wendy@example.com', '555-0123', 'Portland', 'OR', 'USA', '2024-08-10', 'active', '2024-08-10 14:00:00'),
('Xavier Baker', 'xavier@example.com', '555-0124', 'Oklahoma City', 'OK', 'USA', '2024-08-15', 'active', '2024-08-15 09:00:00'),
('Yara Nelson', 'yara@example.com', '555-0125', 'Las Vegas', 'NV', 'USA', '2024-08-20', 'inactive', '2024-08-20 13:45:00'),
('Zack Carter', 'zack@example.com', '555-0126', 'Baltimore', 'MD', 'USA', '2024-09-01', 'active', '2024-09-01 08:30:00'),
('Amy Mitchell', 'amy@example.com', '555-0127', 'Milwaukee', 'WI', 'USA', '2024-09-10', 'active', '2024-09-10 10:00:00'),
('Ben Roberts', 'ben@example.com', '555-0128', 'Albuquerque', 'NM', 'USA', '2024-09-15', 'active', '2024-09-15 11:00:00'),
('Cathy Turner', 'cathy@example.com', '555-0129', 'Tucson', 'AZ', 'USA', '2024-09-20', 'active', '2024-09-20 14:30:00'),
('Dan Phillips', 'dan@example.com', '555-0130', 'Fresno', 'CA', 'USA', '2024-10-01', 'active', '2024-10-01 09:15:00'),
('Ella Campbell', 'ella@example.com', '555-0131', 'Sacramento', 'CA', 'USA', '2024-10-05', 'active', '2024-10-05 12:00:00'),
('Finn Parker', 'finn@example.com', '555-0132', 'Kansas City', 'MO', 'USA', '2024-10-10', 'active', '2024-10-10 10:30:00'),
('Gemma Evans', 'gemma@example.com', '555-0133', 'Atlanta', 'GA', 'USA', '2024-10-15', 'active', '2024-10-15 08:45:00'),
('Hank Edwards', 'hank@example.com', '555-0134', 'Omaha', 'NE', 'USA', '2024-10-20', 'active', '2024-10-20 11:00:00'),
('Iris Collins', 'iris@example.com', '555-0135', 'Raleigh', 'NC', 'USA', '2024-10-25', 'active', '2024-10-25 14:00:00'),
('Jake Stewart', 'jake@example.com', '555-0136', 'Miami', 'FL', 'USA', '2024-11-01', 'active', '2024-11-01 09:30:00'),
('Kara Morris', 'kara@example.com', '555-0137', 'Richmond', 'VA', 'USA', '2024-11-05', 'active', '2024-11-05 10:00:00'),
('Liam Rogers', 'liam@example.com', '555-0138', 'Cleveland', 'OH', 'USA', '2024-11-10', 'active', '2024-11-10 13:00:00'),
('Maya Reed', 'maya@example.com', '555-0139', 'Tampa', 'FL', 'USA', '2024-11-15', 'active', '2024-11-15 08:00:00'),
('Noah Cook', 'noah@example.com', '555-0140', 'Pittsburgh', 'PA', 'USA', '2024-11-20', 'active', '2024-11-20 11:30:00'),
('Piper Bell', 'piper@example.com', '555-0141', 'Lexington', 'KY', 'USA', '2024-11-25', 'active', '2024-11-25 14:45:00'),
('Quincy Murphy', 'quincy@example.com', '555-0142', 'Stockton', 'CA', 'USA', '2024-12-01', 'active', '2024-12-01 09:00:00'),
('Rita Cooper', 'rita@example.com', '555-0143', 'Corpus Christi', 'TX', 'USA', '2024-12-05', 'active', '2024-12-05 10:15:00'),
('Shane Howard', 'shane@example.com', '555-0144', 'Buffalo', 'NY', 'USA', '2024-12-10', 'active', '2024-12-10 12:00:00'),
('Tara Ward', 'tara@example.com', '555-0145', 'Madison', 'WI', 'USA', '2024-12-15', 'active', '2024-12-15 08:30:00'),
('Ulysses Brooks', 'ulysses@example.com', '555-0146', 'New Orleans', 'LA', 'USA', '2024-12-20', 'active', '2024-12-20 11:00:00'),
('Vivian Gray', 'vivian@example.com', '555-0147', 'Cincinnati', 'OH', 'USA', '2025-01-01', 'active', '2025-01-01 10:00:00'),
('Will James', 'will@example.com', '555-0148', 'Anchorage', 'AK', 'USA', '2025-01-05', 'active', '2025-01-05 14:00:00'),
('Xena Clark', 'xena@example.com', '555-0149', 'Boise', 'ID', 'USA', '2025-01-10', 'active', '2025-01-10 09:30:00'),
('Yoel Foster', 'yoel@example.com', '555-0150', 'Honolulu', 'HI', 'USA', '2025-01-15', 'active', '2025-01-15 08:00:00');

-- Products (20 sample products)
INSERT INTO products (name, category, price, stock_quantity, description, is_active) VALUES
('Wireless Mouse', 'Electronics', 29.99, 150, 'Ergonomic wireless mouse with USB receiver', TRUE),
('Bluetooth Keyboard', 'Electronics', 49.99, 100, 'Full-size Bluetooth keyboard with numeric keypad', TRUE),
('USB-C Hub', 'Electronics', 34.99, 200, '7-in-1 USB-C hub with HDMI, USB-A, SD card reader', TRUE),
('Noise Cancelling Headphones', 'Electronics', 199.99, 50, 'Over-ear ANC headphones with 30hr battery', TRUE),
('Webcam HD', 'Electronics', 79.99, 75, '1080p HD webcam with built-in microphone', TRUE),
('Desk Lamp LED', 'Home Office', 39.99, 120, 'Adjustable LED desk lamp with wireless charging base', TRUE),
('Ergonomic Chair', 'Furniture', 399.99, 25, 'Full mesh ergonomic office chair with lumbar support', TRUE),
('Standing Desk', 'Furniture', 599.99, 15, 'Electric height-adjustable standing desk 60x30', TRUE),
('Monitor Stand', 'Furniture', 49.99, 80, 'Adjustable dual monitor stand with gas spring', TRUE),
('Coffee Mug Warmer', 'Home Office', 19.99, 200, 'USB-powered coffee mug warmer pad', TRUE),
('Notebook Set', 'Stationery', 14.99, 300, 'Pack of 3 premium lined notebooks, A5 size', TRUE),
('Pen Set', 'Stationery', 24.99, 250, 'Set of 12 premium gel pens assorted colors', TRUE),
('Desk Organizer', 'Stationery', 29.99, 180, 'Bamboo desk organizer with 7 compartments', TRUE),
('Whiteboard', 'Office Supplies', 89.99, 40, '36x24 inch magnetic whiteboard with markers', TRUE),
('Paper Shredder', 'Office Supplies', 69.99, 35, 'Cross-cut paper shredder 8-sheet capacity', TRUE),
('Laptop Stand', 'Furniture', 34.99, 90, 'Adjustable aluminum laptop stand, folds flat', TRUE),
('External SSD 1TB', 'Electronics', 129.99, 60, '1TB portable SSD, USB-C, read 1050MB/s', TRUE),
('Mechanical Keyboard', 'Electronics', 149.99, 45, 'RGB mechanical keyboard with Cherry MX switches', TRUE),
('Gaming Mouse', 'Electronics', 59.99, 70, 'Wired gaming mouse 16000 DPI, RGB', TRUE),
('Cable Management Kit', 'Office Supplies', 15.99, 400, 'Cable ties, clips, and sleeve set 100 pieces', TRUE);

-- Orders (100 sample orders)
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_city, shipping_state, created_at) VALUES
(1, '2024-06-01', 79.98, 'delivered', 'New York', 'NY', '2024-06-01 10:00:00'),
(2, '2024-06-02', 49.99, 'delivered', 'Los Angeles', 'CA', '2024-06-02 11:30:00'),
(3, '2024-06-05', 199.99, 'delivered', 'Chicago', 'IL', '2024-06-05 09:15:00'),
(4, '2024-06-08', 34.99, 'delivered', 'Houston', 'TX', '2024-06-08 14:00:00'),
(5, '2024-06-10', 599.99, 'delivered', 'Phoenix', 'AZ', '2024-06-10 08:30:00'),
(6, '2024-06-12', 29.99, 'delivered', 'Philadelphia', 'PA', '2024-06-12 10:45:00'),
(7, '2024-06-15', 79.98, 'delivered', 'San Antonio', 'TX', '2024-06-15 12:00:00'),
(8, '2024-06-18', 149.99, 'delivered', 'San Diego', 'CA', '2024-06-18 15:30:00'),
(9, '2024-06-20', 399.99, 'delivered', 'Dallas', 'TX', '2024-06-20 11:00:00'),
(10, '2024-06-22', 49.98, 'delivered', 'San Jose', 'CA', '2024-06-22 09:45:00'),
(1, '2024-07-01', 129.99, 'delivered', 'New York', 'NY', '2024-07-01 10:00:00'),
(11, '2024-07-03', 29.99, 'delivered', 'Austin', 'TX', '2024-07-03 11:00:00'),
(12, '2024-07-05', 199.98, 'delivered', 'Jacksonville', 'FL', '2024-07-05 13:30:00'),
(13, '2024-07-08', 39.99, 'shipped', 'Fort Worth', 'TX', '2024-07-08 14:00:00'),
(14, '2024-07-10', 89.99, 'shipped', 'Columbus', 'OH', '2024-07-10 08:00:00'),
(2, '2024-07-15', 149.99, 'shipped', 'Los Angeles', 'CA', '2024-07-15 11:30:00'),
(15, '2024-07-18', 79.98, 'shipped', 'Charlotte', 'NC', '2024-07-18 10:00:00'),
(16, '2024-07-20', 59.99, 'shipped', 'Indianapolis', 'IN', '2024-07-20 12:15:00'),
(17, '2024-07-22', 299.98, 'shipped', 'San Francisco', 'CA', '2024-07-22 09:30:00'),
(18, '2024-07-25', 34.99, 'shipped', 'Seattle', 'WA', '2024-07-25 14:45:00'),
(3, '2024-08-01', 499.99, 'pending', 'Chicago', 'IL', '2024-08-01 10:00:00'),
(19, '2024-08-03', 14.99, 'pending', 'Denver', 'CO', '2024-08-03 11:00:00'),
(20, '2024-08-05', 129.99, 'pending', 'Nashville', 'TN', '2024-08-05 08:30:00'),
(21, '2024-08-08', 24.99, 'pending', 'Memphis', 'TN', '2024-08-08 14:00:00'),
(22, '2024-08-10', 69.99, 'delivered', 'Louisville', 'KY', '2024-08-10 10:15:00'),
(4, '2024-08-15', 159.98, 'delivered', 'Houston', 'TX', '2024-08-15 09:00:00'),
(23, '2024-08-18', 44.98, 'delivered', 'Portland', 'OR', '2024-08-18 12:30:00'),
(24, '2024-08-20', 199.99, 'delivered', 'Oklahoma City', 'OK', '2024-08-20 11:45:00'),
(25, '2024-08-22', 79.99, 'shipped', 'Las Vegas', 'NV', '2024-08-22 14:00:00'),
(26, '2024-08-25', 34.99, 'shipped', 'Baltimore', 'MD', '2024-08-25 08:00:00'),
(5, '2024-09-01', 899.98, 'pending', 'Phoenix', 'AZ', '2024-09-01 10:00:00'),
(27, '2024-09-03', 29.99, 'pending', 'Milwaukee', 'WI', '2024-09-03 11:00:00'),
(28, '2024-09-05', 149.99, 'pending', 'Albuquerque', 'NM', '2024-09-05 09:30:00'),
(29, '2024-09-08', 39.99, 'delivered', 'Tucson', 'AZ', '2024-09-08 14:00:00'),
(30, '2024-09-10', 84.98, 'delivered', 'Fresno', 'CA', '2024-09-10 10:45:00'),
(6, '2024-09-15', 229.98, 'cancelled', 'Philadelphia', 'PA', '2024-09-15 12:00:00'),
(31, '2024-09-18', 59.99, 'cancelled', 'Sacramento', 'CA', '2024-09-18 08:30:00'),
(32, '2024-09-20', 399.99, 'delivered', 'Kansas City', 'MO', '2024-09-20 11:00:00'),
(33, '2024-09-22', 99.99, 'delivered', 'Atlanta', 'GA', '2024-09-22 14:15:00'),
(34, '2024-09-25', 29.99, 'delivered', 'Omaha', 'NE', '2024-09-25 09:00:00'),
(7, '2024-10-01', 119.98, 'delivered', 'San Antonio', 'TX', '2024-10-01 10:00:00'),
(35, '2024-10-03', 199.99, 'delivered', 'Raleigh', 'NC', '2024-10-03 11:30:00'),
(36, '2024-10-05', 49.99, 'delivered', 'Miami', 'FL', '2024-10-05 08:45:00'),
(37, '2024-10-08', 79.98, 'shipped', 'Richmond', 'VA', '2024-10-08 14:00:00'),
(38, '2024-10-10', 399.99, 'shipped', 'Cleveland', 'OH', '2024-10-10 10:30:00'),
(8, '2024-10-15', 289.98, 'shipped', 'San Diego', 'CA', '2024-10-15 12:00:00'),
(39, '2024-10-18', 34.99, 'shipped', 'Tampa', 'FL', '2024-10-18 09:15:00'),
(40, '2024-10-20', 49.98, 'shipped', 'Pittsburgh', 'PA', '2024-10-20 11:00:00'),
(41, '2024-10-22', 129.99, 'pending', 'Lexington', 'KY', '2024-10-22 14:30:00'),
(42, '2024-10-25', 24.99, 'pending', 'Stockton', 'CA', '2024-10-25 08:00:00'),
(9, '2024-11-01', 199.99, 'delivered', 'Dallas', 'TX', '2024-11-01 10:00:00'),
(43, '2024-11-03', 59.99, 'delivered', 'Corpus Christi', 'TX', '2024-11-03 11:30:00'),
(44, '2024-11-05', 149.99, 'delivered', 'Buffalo', 'NY', '2024-11-05 09:00:00'),
(45, '2024-11-08', 79.98, 'delivered', 'Madison', 'WI', '2024-11-08 14:00:00'),
(46, '2024-11-10', 34.99, 'delivered', 'New Orleans', 'LA', '2024-11-10 10:45:00'),
(10, '2024-11-15', 459.98, 'shipped', 'San Jose', 'CA', '2024-11-15 12:00:00'),
(47, '2024-11-18', 29.99, 'shipped', 'Cincinnati', 'OH', '2024-11-18 08:30:00'),
(48, '2024-11-20', 199.99, 'shipped', 'Anchorage', 'AK', '2024-11-20 11:00:00'),
(49, '2024-11-22', 89.99, 'shipped', 'Boise', 'ID', '2024-11-22 14:15:00'),
(50, '2024-11-25', 39.99, 'shipped', 'Honolulu', 'HI', '2024-11-25 09:30:00'),
(11, '2024-12-01', 79.99, 'pending', 'Austin', 'TX', '2024-12-01 10:00:00'),
(12, '2024-12-03', 149.99, 'pending', 'Jacksonville', 'FL', '2024-12-03 11:00:00'),
(13, '2024-12-05', 29.99, 'pending', 'Fort Worth', 'TX', '2024-12-05 08:30:00'),
(14, '2024-12-08', 599.99, 'pending', 'Columbus', 'OH', '2024-12-08 14:00:00'),
(15, '2024-12-10', 34.99, 'pending', 'Charlotte', 'NC', '2024-12-10 10:15:00'),
(16, '2024-12-12', 99.99, 'pending', 'Indianapolis', 'IN', '2024-12-12 12:30:00'),
(17, '2024-12-15', 249.98, 'pending', 'San Francisco', 'CA', '2024-12-15 09:00:00'),
(18, '2024-12-18', 59.99, 'pending', 'Seattle', 'WA', '2024-12-18 11:45:00'),
(19, '2024-12-20', 19.99, 'pending', 'Denver', 'CO', '2024-12-20 14:00:00'),
(20, '2024-12-22', 129.99, 'pending', 'Nashville', 'TN', '2024-12-22 08:00:00'),
(21, '2024-12-25', 49.98, 'pending', 'Memphis', 'TN', '2024-12-25 10:30:00'),
(22, '2024-12-28', 399.99, 'pending', 'Louisville', 'KY', '2024-12-28 12:00:00'),
(23, '2025-01-02', 79.99, 'pending', 'Portland', 'OR', '2025-01-02 09:00:00'),
(24, '2025-01-05', 149.99, 'pending', 'Oklahoma City', 'OK', '2025-01-05 11:30:00'),
(25, '2025-01-08', 34.99, 'pending', 'Las Vegas', 'NV', '2025-01-08 14:00:00'),
(26, '2025-01-10', 89.99, 'pending', 'Baltimore', 'MD', '2025-01-10 08:45:00'),
(27, '2025-01-12', 59.99, 'pending', 'Milwaukee', 'WI', '2025-01-12 10:00:00'),
(28, '2025-01-15', 199.99, 'pending', 'Albuquerque', 'NM', '2025-01-15 12:30:00'),
(29, '2025-01-18', 29.99, 'pending', 'Tucson', 'AZ', '2025-01-18 09:00:00'),
(30, '2025-01-20', 499.99, 'pending', 'Fresno', 'CA', '2025-01-20 11:00:00'),
(31, '2025-01-22', 39.99, 'pending', 'Sacramento', 'CA', '2025-01-22 14:15:00'),
(32, '2025-01-25', 79.98, 'pending', 'Kansas City', 'MO', '2025-01-25 08:30:00'),
(33, '2025-02-01', 199.99, 'pending', 'Atlanta', 'GA', '2025-02-01 10:00:00'),
(34, '2025-02-03', 149.99, 'pending', 'Omaha', 'NE', '2025-02-03 11:00:00'),
(35, '2025-02-05', 34.99, 'pending', 'Raleigh', 'NC', '2025-02-05 09:30:00'),
(36, '2025-02-08', 89.99, 'pending', 'Miami', 'FL', '2025-02-08 14:00:00'),
(37, '2025-02-10', 29.99, 'pending', 'Richmond', 'VA', '2025-02-10 10:45:00'),
(38, '2025-02-12', 559.98, 'pending', 'Cleveland', 'OH', '2025-02-12 12:00:00'),
(39, '2025-02-15', 24.99, 'pending', 'Tampa', 'FL', '2025-02-15 08:00:00'),
(40, '2025-02-18', 129.99, 'pending', 'Pittsburgh', 'PA', '2025-02-18 11:30:00'),
(41, '2025-02-20', 49.99, 'pending', 'Lexington', 'KY', '2025-02-20 14:45:00'),
(42, '2025-02-22', 399.99, 'pending', 'Stockton', 'CA', '2025-02-22 09:00:00'),
(43, '2025-03-01', 567.96, 'pending', 'New York', 'NY', '2025-03-01 10:00:00'),
(44, '2025-03-05', 399.99, 'pending', 'Los Angeles', 'CA', '2025-03-05 11:30:00'),
(45, '2025-03-10', 149.99, 'pending', 'Chicago', 'IL', '2025-03-10 09:00:00'),
(46, '2025-03-15', 89.99, 'pending', 'Houston', 'TX', '2025-03-15 14:00:00'),
(47, '2025-03-20', 29.99, 'pending', 'Phoenix', 'AZ', '2025-03-20 08:30:00');

-- Order items (matching line items for each order)
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 29.99), (1, 11, 1, 14.99),
(2, 2, 1, 49.99),
(3, 4, 1, 199.99),
(4, 3, 1, 34.99),
(5, 8, 1, 599.99),
(6, 1, 1, 29.99),
(7, 1, 2, 29.99), (7, 10, 1, 19.99),
(8, 18, 1, 149.99),
(9, 7, 1, 399.99),
(10, 1, 1, 29.99), (10, 10, 1, 19.99),
(11, 17, 1, 129.99),
(12, 1, 1, 29.99),
(13, 1, 2, 29.99), (13, 11, 2, 14.99), (13, 12, 2, 24.99),
(14, 6, 1, 39.99),
(15, 14, 1, 89.99),
(16, 18, 1, 149.99),
(17, 1, 2, 29.99), (17, 10, 1, 19.99),
(18, 19, 1, 59.99),
(19, 8, 1, 599.99), (19, 16, 1, 34.99), -- adjusted to fit
(20, 3, 1, 34.99),
(21, 7, 1, 399.99), (21, 4, 1, 199.99), -- adjusted
(22, 11, 1, 14.99),
(23, 17, 1, 129.99),
(24, 12, 1, 24.99),
(25, 15, 1, 69.99),
(26, 1, 2, 29.99), (26, 2, 2, 49.99),
(27, 10, 1, 19.99), (27, 11, 1, 14.99), (27, 2, 1, 49.99), -- adjusted
(28, 4, 1, 199.99),
(29, 14, 1, 89.99),
(30, 3, 1, 34.99),
(31, 7, 1, 399.99), (31, 8, 1, 599.99), -- adjusted to fit
(32, 1, 1, 29.99),
(33, 18, 1, 149.99),
(34, 6, 1, 39.99),
(35, 1, 2, 29.99), (35, 10, 2, 19.99),
(36, 4, 1, 199.99), (36, 10, 1, 19.99), (36, 1, 1, 29.99), -- adjusted
(37, 19, 1, 59.99),
(38, 7, 1, 399.99),
(39, 9, 1, 49.99), (39, 10, 1, 19.99), (39, 11, 1, 14.99), -- adjusted
(40, 1, 1, 29.99),
(41, 1, 2, 29.99), (41, 10, 2, 19.99), (41, 11, 2, 14.99), -- adjusted
(42, 4, 1, 199.99),
(43, 19, 1, 59.99),
(44, 18, 1, 149.99),
(45, 1, 2, 29.99), (45, 10, 1, 19.99),
(46, 3, 1, 34.99),
(47, 18, 1, 149.99), (47, 19, 1, 59.99), (47, 1, 2, 29.99), (47, 10, 2, 19.99), -- adjusted
(48, 1, 1, 29.99),
(49, 4, 1, 199.99),
(50, 14, 1, 89.99),
(51, 6, 1, 39.99),
(52, 1, 1, 29.99),
(53, 2, 1, 49.99), (53, 3, 1, 34.99), (53, 10, 1, 19.99), (53, 11, 1, 14.99), -- adjusted
(54, 1, 1, 29.99),
(55, 17, 1, 129.99),
(56, 19, 1, 59.99),
(57, 8, 1, 599.99),
(58, 3, 1, 34.99),
(59, 9, 1, 49.99), (59, 10, 1, 19.99), (59, 11, 1, 14.99), -- adjusted
(60, 4, 1, 199.99),
(61, 1, 2, 29.99), (61, 10, 1, 19.99),
(62, 18, 1, 149.99),
(63, 1, 1, 29.99),
(64, 8, 1, 599.99),
(65, 3, 1, 34.99),
(66, 6, 1, 39.99), (66, 10, 1, 19.99), (66, 11, 1, 14.99), (66, 2, 1, 49.99), -- adjusted
(67, 4, 1, 199.99), (67, 10, 1, 19.99), (67, 11, 1, 14.99), (67, 12, 1, 24.99), -- adjusted
(68, 19, 1, 59.99),
(69, 10, 1, 19.99),
(70, 17, 1, 129.99),
(71, 10, 2, 19.99), (71, 11, 2, 14.99), (71, 12, 2, 24.99), -- adjusted
(72, 7, 1, 399.99),
(73, 1, 2, 29.99), (73, 10, 1, 19.99),
(74, 18, 1, 149.99),
(75, 3, 1, 34.99),
(76, 14, 1, 89.99),
(77, 19, 1, 59.99),
(78, 4, 1, 199.99),
(79, 1, 1, 29.99),
(80, 8, 1, 599.99), -- adjusted to fit
(81, 6, 1, 39.99),
(82, 1, 2, 29.99), (82, 10, 1, 19.99), (82, 11, 1, 14.99), -- adjusted
(83, 4, 1, 199.99),
(84, 18, 1, 149.99),
(85, 3, 1, 34.99),
(86, 14, 1, 89.99),
(87, 1, 1, 29.99),
(88, 7, 1, 399.99), (88, 19, 1, 59.99), (88, 1, 1, 29.99), (88, 10, 1, 19.99), (88, 11, 1, 14.99), (88, 12, 1, 24.99), -- adjusted
(89, 12, 1, 24.99),
(90, 17, 1, 129.99),
(91, 2, 1, 49.99),
(92, 7, 1, 399.99),
(93, 1, 2, 29.99), (93, 2, 2, 49.99), (93, 3, 2, 34.99), (93, 4, 2, 199.99), -- adjusted
(94, 7, 1, 399.99),
(95, 18, 1, 149.99),
(96, 14, 1, 89.99),
(97, 13, 1, 29.99);

-- Update order totals based on actual item sums
UPDATE orders o SET total_amount = (
    SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
    FROM order_items oi
    WHERE oi.order_id = o.id
);