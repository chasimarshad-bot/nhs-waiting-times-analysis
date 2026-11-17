-- 01: First look at the data
-- Replace <table_name> with a table created by scripts/load_data.py

-- List all tables
SELECT name FROM sqlite_master WHERE type = 'table';

-- See the first 10 rows
SELECT * FROM <table_name> LIMIT 10;

-- Count rows
SELECT COUNT(*) AS total_rows FROM <table_name>;
