import os
import psycopg2
from psycopg2.extras import RealDictCursor

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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    product_name VARCHAR(255) NOT NULL,
                    gf_price DECIMAL(10,2) NOT NULL,
                    regular_price DECIMAL(10,2) NOT NULL,
                    difference DECIMAL(10,2) NOT NULL,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def add_product(self, product_name, gf_price, regular_price):
        with self.conn.cursor() as cur:
            difference = float(gf_price) - float(regular_price)
            cur.execute("""
                INSERT INTO products (product_name, gf_price, regular_price, difference)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (product_name, gf_price, regular_price, difference))
            self.conn.commit()
            return cur.fetchone()[0]

    def get_all_products(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM products ORDER BY date_added DESC")
            return cur.fetchall()

    def delete_product(self, product_id):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            self.conn.commit()
