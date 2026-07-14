import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH=PROJECT_ROOT / 'database' / 'journal.db'
SCHEMA_PATH=PROJECT_ROOT / 'database' / 'schema.sql'

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as function:
            schema=function.read()
        connection.execute("pragma foreign_keys=ON;")
        connection.executescript(schema)
        connection.commit()
if __name__ == "__main__":
    init_db()
