import sqlite3 
from pathlib import Path

from langgraph import func

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH=PROJECT_ROOT / 'database' / 'journal.db'
SCHEMA_PATH=PROJECT_ROOT / 'database' / 'schema.sql'

def init_db():
    connection=sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as function:
        schema=function.read()
    connection.executescript(schema)
    connection.execute("pragma foreign_keys=ON;")
    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()