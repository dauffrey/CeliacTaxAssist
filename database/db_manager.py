import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )
        self._create_tables()

    def _create_tables(self):
        with self.conn.cursor() as cur:
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
            self.conn.commit()

    def create_user(self, username, email, password):
        with self.conn.cursor() as cur:
            try:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cur.execute("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (username, email, password_hash))
                self.conn.commit()
                return cur.fetchone()[0]
            except psycopg2.errors.UniqueViolation:
                self.conn.rollback()
                return None

    def verify_user(self, username, password):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result and bcrypt.checkpw(password.encode('utf-8'), bytes(result[1])):
                return result[0]
            return None

    def add_product(self, product_name, gf_price, regular_price, user_id):
        with self.conn.cursor() as cur:
            difference = float(gf_price) - float(regular_price)
            cur.execute("""
                INSERT INTO products (product_name, gf_price, regular_price, difference, user_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (product_name, gf_price, regular_price, difference, user_id))
            self.conn.commit()
            return cur.fetchone()[0]

    def get_user_products(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM products WHERE user_id = %s ORDER BY date_added DESC", (user_id,))
            return cur.fetchall()

    def delete_product(self, product_id, user_id):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM products WHERE id = %s AND user_id = %s", (product_id, user_id))
            self.conn.commit()
