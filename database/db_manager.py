import os
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool
import bcrypt
import time
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )
        self._create_tables()

    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool with retry logic"""
        retries = 0
        while retries < self.max_retries:
            try:
                conn = self.pool.getconn()
                if conn.closed:
                    self.pool.putconn(conn)
                    raise psycopg2.OperationalError("Connection is closed")
                yield conn
                self.pool.putconn(conn)
                break
            except psycopg2.OperationalError:
                retries += 1
                if retries == self.max_retries:
                    raise
                time.sleep(self.retry_delay)
                # Recreate pool if needed
                try:
                    self.pool = psycopg2.pool.SimpleConnectionPool(
                        minconn=1,
                        maxconn=10,
                        host=os.environ['PGHOST'],
                        database=os.environ['PGDATABASE'],
                        user=os.environ['PGUSER'],
                        password=os.environ['PGPASSWORD'],
                        port=os.environ['PGPORT']
                    )
                except:
                    continue

    def _create_tables(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash BYTEA NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Update products table to include user_id
                cur.execute("""
                    DO $$
                    BEGIN
                        BEGIN
                            ALTER TABLE products ADD COLUMN user_id INTEGER REFERENCES users(id);
                        EXCEPTION
                            WHEN duplicate_column THEN
                                NULL;
                        END;
                    END $$;
                """)
                conn.commit()

    def create_user(self, username, email, password):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (username, email, password_hash))
                    conn.commit()
                    return cur.fetchone()[0]
                except psycopg2.errors.UniqueViolation:
                    conn.rollback()
                    return None

    def verify_user(self, username, password):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                if result and bcrypt.checkpw(password.encode('utf-8'), bytes(result[1])):
                    return result[0]
                return None

    def add_product(self, product_name, gf_price, regular_price, user_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                difference = float(gf_price) - float(regular_price)
                cur.execute("""
                    INSERT INTO products (product_name, gf_price, regular_price, difference, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (product_name, gf_price, regular_price, difference, user_id))
                conn.commit()
                return cur.fetchone()[0]

    def get_user_products(self, user_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM products WHERE user_id = %s ORDER BY date_added DESC", (user_id,))
                return cur.fetchall()

    def delete_product(self, product_id, user_id):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM products WHERE id = %s AND user_id = %s", (product_id, user_id))
                conn.commit()

    def __del__(self):
        """Cleanup connection pool on deletion"""
        if hasattr(self, 'pool'):
            self.pool.closeall()
