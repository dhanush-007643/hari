-- =============================================================
-- DataVista+ Seed Data
-- Sample enterprise datasets: Sales, HR, Financial
-- =============================================================

-- Roles
INSERT OR IGNORE INTO roles (id, name, description) VALUES
(1, 'admin', 'Full system access'),
(2, 'analyst', 'Analytics and query access'),
(3, 'viewer', 'Read-only dashboard access'),
(4, 'data_scientist', 'ML model creation and prediction access');

-- Permissions
INSERT OR IGNORE INTO permissions (name, module, action, description) VALUES
('query.create', 'nlq', 'create', 'Create NL queries'),
('query.read', 'nlq', 'read', 'Read query history'),
('dataset.upload', 'datasets', 'create', 'Upload datasets'),
('dataset.read', 'datasets', 'read', 'View datasets'),
('ml.train', 'ml', 'create', 'Train ML models'),
('ml.predict', 'ml', 'read', 'Run predictions'),
('reports.create', 'reports', 'create', 'Generate reports'),
('reports.read', 'reports', 'read', 'View reports'),
('admin.users', 'admin', 'manage', 'Manage users'),
('admin.system', 'admin', 'manage', 'Manage system settings');

-- Default admin user (password: Admin@123)
INSERT OR IGNORE INTO users (id, username, email, hashed_password, full_name, is_active, is_superuser, role_id) VALUES
(1, 'admin', 'admin@datavista.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXe.PmkuB2YvqQC.3gp9VNjVPyZvtB.pA2', 'System Admin', TRUE, TRUE, 1);

-- Sample datasets metadata
INSERT OR IGNORE INTO datasets (id, name, description, source_type, row_count, column_count, data_quality_score, owner_id) VALUES
(1, 'Sales Analytics 2024', 'Retail sales transactions for the year 2024', 'upload', 10000, 12, 0.94, 1),
(2, 'HR Employee Data', 'Human resources employee records and performance', 'upload', 2500, 18, 0.87, 1),
(3, 'Financial Transactions', 'Monthly financial transactions and P&L data', 'upload', 5000, 15, 0.91, 1);

-- Dataset tables
INSERT OR IGNORE INTO dataset_tables (id, dataset_id, table_name, row_count, description) VALUES
(1, 1, 'sales_orders', 10000, 'Individual sale transactions'),
(2, 1, 'products', 250, 'Product catalog'),
(3, 1, 'customers', 3000, 'Customer records'),
(4, 2, 'employees', 2500, 'Employee master data'),
(5, 2, 'departments', 15, 'Department list'),
(6, 3, 'transactions', 5000, 'Financial transactions'),
(7, 3, 'budget', 120, 'Monthly budget allocations');

-- Dataset columns for sales
INSERT OR IGNORE INTO dataset_columns (table_id, column_name, data_type, sample_values, description, business_term) VALUES
(1, 'order_id', 'INTEGER', '1001,1002,1003', 'Unique order identifier', 'Order ID'),
(1, 'customer_id', 'INTEGER', '501,502,503', 'Customer foreign key', 'Customer'),
(1, 'product_id', 'INTEGER', '101,102,103', 'Product foreign key', 'Product'),
(1, 'order_date', 'DATE', '2024-01-15,2024-02-20', 'Date of order', 'Order Date'),
(1, 'quantity', 'INTEGER', '1,2,5,10', 'Units ordered', 'Quantity'),
(1, 'unit_price', 'FLOAT', '29.99,49.99,99.99', 'Price per unit', 'Unit Price'),
(1, 'total_amount', 'FLOAT', '59.98,249.95', 'Total order value', 'Revenue'),
(1, 'region', 'VARCHAR', 'North,South,East,West', 'Sales region', 'Region'),
(1, 'status', 'VARCHAR', 'Completed,Pending,Cancelled', 'Order status', 'Status');

-- Business KPIs
INSERT OR IGNORE INTO business_kpis (dataset_id, name, value, unit, comparison_value, change_percent, trend) VALUES
(1, 'Total Revenue', 4250000.00, 'USD', 3800000.00, 11.84, 'up'),
(1, 'Total Orders', 10000, 'orders', 8750, 14.29, 'up'),
(1, 'Average Order Value', 425.00, 'USD', 434.29, -2.14, 'down'),
(1, 'Customer Count', 3000, 'customers', 2600, 15.38, 'up'),
(2, 'Total Employees', 2500, 'employees', 2350, 6.38, 'up'),
(2, 'Avg Salary', 75000, 'USD', 72000, 4.17, 'up'),
(2, 'Attrition Rate', 8.5, 'percent', 10.2, -16.67, 'down'),
(3, 'Net Revenue', 12500000, 'USD', 11200000, 11.61, 'up'),
(3, 'Operating Expenses', 8750000, 'USD', 8100000, 8.02, 'up'),
(3, 'Profit Margin', 30.0, 'percent', 27.7, 8.30, 'up');

-- Sample insights
INSERT OR IGNORE INTO insights (dataset_id, insight_type, title, description, confidence_score, impact_level) VALUES
(1, 'trend', 'Revenue Growth Trend', 'Revenue has grown consistently by 11.8% compared to the same period last year, driven primarily by the North region (+24%) and Electronics category (+19%).', 0.92, 'high'),
(1, 'anomaly', 'Unusual Order Spike Detected', 'Orders on March 15th were 340% above the daily average. This coincides with a promotional campaign that may require additional inventory planning.', 0.87, 'medium'),
(1, 'correlation', 'Price-Volume Correlation', 'Products priced between $50-$100 show the highest order volumes. Products above $200 account for 45% of total revenue despite only 12% of order count.', 0.89, 'medium'),
(2, 'trend', 'Attrition Rate Improving', 'Employee attrition has dropped from 10.2% to 8.5%, suggesting recent HR initiatives are effective. Engineering department shows the lowest attrition at 4.2%.', 0.85, 'high'),
(3, 'trend', 'Profit Margin Expansion', 'Profit margin expanded from 27.7% to 30.0%, primarily due to operational efficiency improvements in Q3. Cost optimization in logistics contributed $850K in savings.', 0.91, 'high');

-- Sample recommendations
INSERT OR IGNORE INTO recommendations (insight_id, title, description, action_items, priority, expected_impact) VALUES
(1, 'Scale North Region Investment', 'The North region is outperforming other regions significantly.', '["Increase marketing budget for North by 20%", "Expand warehouse capacity in North", "Hire 5 additional sales reps"]', 1, 'Expected 15-20% additional revenue growth'),
(2, 'Optimize Inventory for Promotions', 'Future promotions should be backed by increased inventory buffers.', '["Set up promotion calendar 30 days in advance", "Increase safety stock by 25% before promotions", "Automate reorder triggers"]', 2, 'Prevent stockouts and capture additional $200K revenue'),
(4, 'Continue HR Retention Programs', 'Current retention initiatives are showing measurable impact.', '["Expand mentorship program to all departments", "Increase L&D budget by 15%", "Implement quarterly pulse surveys"]', 1, 'Further reduce attrition to below 6%');

-- System settings
INSERT OR IGNORE INTO system_settings (key, value, description) VALUES
('app_name', 'DataVista+', 'Application name'),
('max_query_results', '10000', 'Maximum rows returned per query'),
('nlq_confidence_threshold', '0.70', 'Minimum confidence for NLQ results'),
('session_timeout_minutes', '60', 'Session timeout in minutes'),
('max_file_upload_mb', '100', 'Maximum file upload size in MB'),
('enable_ai_insights', 'true', 'Enable automatic AI insights generation'),
('enable_email_notifications', 'false', 'Enable email notifications');
