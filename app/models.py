import psycopg2
from app.config import Config

db_conn = psycopg2.connect(Config.DATABASE_URL)
db_cursor = db_conn.cursor()

# Create table if not exists
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS public.requests
(
    id uuid NOT NULL,
    input_type character varying(50) COLLATE pg_catalog."default" NOT NULL,
    input_data text COLLATE pg_catalog."default" NOT NULL,
    status character varying(20) COLLATE pg_catalog."default" NOT NULL,
    response text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT requests_pkey PRIMARY KEY (id),
    CONSTRAINT requests_status_check CHECK (status::text = ANY (ARRAY['queued'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying]::text[]))
)
""")
db_conn.commit()
