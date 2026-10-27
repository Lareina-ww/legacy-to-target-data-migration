PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL CHECK (length(country) = 2),
    created_at TEXT NOT NULL,
    is_active INTEGER NOT NULL CHECK (is_active IN (0, 1))
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    transaction_status TEXT NOT NULL CHECK (transaction_status = 'SETTLED'),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

