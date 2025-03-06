import psycopg2
from app.config import Config

db_conn = psycopg2.connect(Config.DATABASE_URL)
db_cursor = db_conn.cursor()

# Create table if not exists
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id UUID PRIMARY KEY,
        input_type TEXT NOT NULL,
        input_data TEXT NOT NULL,
        status TEXT NOT NULL,
        response TEXT
    );
""")
db_conn.commit()
