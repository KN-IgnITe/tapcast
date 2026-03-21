CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    bar_id VARCHAR(255) NOT NULL,
    demand FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pos_sales (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) NOT NULL,
    sale_timestamp TIMESTAMP NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    cashier_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS weather_logs (
    id SERIAL PRIMARY KEY,
    log_date DATE NOT NULL,
    temperature_celsius NUMERIC(5, 2) NOT NULL,
    precipitation_mm NUMERIC(5, 2) DEFAULT 0,
    weather_condition VARCHAR(50)
);