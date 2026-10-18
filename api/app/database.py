import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import settings

@contextmanager
def get_db():
    conn = psycopg2.connect(settings.DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def get_cursor():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()