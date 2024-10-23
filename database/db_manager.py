import os
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool
import bcrypt
import time
from contextlib import contextmanager
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self._create_connection_pool()
        self._create_tables()

    def _create_connection_pool(self):
        """Create a new connection pool"""
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )

    def _get_db_connection(self):
        """Get a database connection with retry logic"""
        retries = 0
        while retries < self.max_retries:
            try:
                return self.pool.getconn()
            except psycopg2.OperationalError as e:
                retries += 1
                if retries == self.max_retries:
                    raise
                time.sleep(self.retry_delay)
                try:
                    self._create_connection_pool()
                except:
                    continue

    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool with proper cleanup"""
        conn = None
        try:
            conn = self._get_db_connection()
            if conn.closed:
                self.pool.putconn(conn)
                raise psycopg2.OperationalError("Connection is closed")
            yield conn
        except psycopg2.OperationalError:
            if conn:
                conn.close()
                self.pool.putconn(conn)
            raise
        except:
            if conn:
                conn.close()
                self.pool.putconn(conn)
            raise
        else:
            self.pool.putconn(conn)

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
                
                # Create products table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        product_name VARCHAR(255) NOT NULL,
                        gf_price DECIMAL(10,2) NOT NULL,
                        regular_price DECIMAL(10,2) NOT NULL,
                        difference DECIMAL(10,2) NOT NULL,
                        user_id INTEGER REFERENCES users(id),
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create stores table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS stores (
                        id SERIAL PRIMARY KEY,
                        store_name VARCHAR(255) NOT NULL,
                        location VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create price_comparisons table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS price_comparisons (
                        id SERIAL PRIMARY KEY,
                        product_name VARCHAR(255) NOT NULL,
                        store_id INTEGER REFERENCES stores(id),
                        gf_price DECIMAL(10,2) NOT NULL,
                        regular_price DECIMAL(10,2) NOT NULL,
                        price_date DATE NOT NULL,
                        added_by INTEGER REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(product_name, store_id, price_date)
                    )
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

    def add_store(self, store_name, location=None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO stores (store_name, location)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (store_name, location))
                    conn.commit()
                    return cur.fetchone()[0]
                except psycopg2.errors.UniqueViolation:
                    conn.rollback()
                    return None

    def get_stores(self):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM stores ORDER BY store_name")
                return cur.fetchall()

    def add_price_comparison(self, product_name, store_id, gf_price, regular_price, added_by, price_date=None):
        if price_date is None:
            price_date = datetime.now().date()
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO price_comparisons 
                        (product_name, store_id, gf_price, regular_price, price_date, added_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (product_name, store_id, gf_price, regular_price, price_date, added_by))
                    conn.commit()
                    return cur.fetchone()[0]
                except psycopg2.errors.UniqueViolation:
                    conn.rollback()
                    return None

    def get_price_comparisons(self, product_name=None):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if product_name:
                    cur.execute("""
                        SELECT pc.*, s.store_name, s.location
                        FROM price_comparisons pc
                        JOIN stores s ON pc.store_id = s.id
                        WHERE pc.product_name = %s
                        ORDER BY pc.price_date DESC, pc.gf_price ASC
                    """, (product_name,))
                else:
                    cur.execute("""
                        SELECT pc.*, s.store_name, s.location
                        FROM price_comparisons pc
                        JOIN stores s ON pc.store_id = s.id
                        ORDER BY pc.price_date DESC, pc.product_name, pc.gf_price ASC
                    """)
                return cur.fetchall()

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
