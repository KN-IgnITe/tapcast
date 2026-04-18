import os

import psycopg
from typing import LiteralString
from dotenv import load_dotenv

load_dotenv()


def get_conn_info() -> str:
    """Build psycopg connection string from environment variables.

    Reads from environment variables with fallbacks:
    - host: DB_HOST (default: localhost)
    - port: DB_PORT (default: 5432)
    - dbname: POSTGRES_DB or DB_NAME (default: postgres)
    - user: POSTGRES_USER or DB_USER (default: postgres)
    - password: POSTGRES_PASSWORD or DB_PASSWORD (default: password)

    Returns:
        Connection string for psycopg.connect()
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "postgres"))
    user = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
    password = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "password"))

    return f"host={host} port={port} dbname={db_name} user={user} password={password}"


def fetch_training_data(query: LiteralString) -> list | None:
    """Execute query and return all rows as a list.

    Args:
        query: SQL query to execute.

    Returns:
        List of rows, or None if an error occurs.
    """
    try:
        with psycopg.connect(get_conn_info()) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()

    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None
