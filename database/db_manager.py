import os
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool
import bcrypt
import time
from contextlib import contextmanager
from datetime import datetime
import logging
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self._create_connection_pool()
        self._create_tables()

    def _create_connection_pool(self):
        """Create a new connection pool with enhanced SSL configuration"""
        # SSL Context configuration
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True

        conn_params = {
            'host': os.environ['PGHOST'],
            'database': os.environ['PGDATABASE'],
            'user': os.environ['PGUSER'],
            'password': os.environ['PGPASSWORD'],
            'port': os.environ['PGPORT'],
            'sslmode': 'verify-full',
            'sslcert': None,  # Using system default certificates
            'sslkey': None,   # Using system default key
            'connect_timeout': 3,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
            'options': f'-c statement_timeout=30000'  # 30 second statement timeout
        }
        
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    **conn_params
                )
                logger.info("Successfully created database connection pool with SSL")
                return
            except psycopg2.OperationalError as e:
                retry_count += 1
                last_error = e
                error_msg = str(e)
                
                if "SSL" in error_msg:
                    logger.error(f"SSL connection error: {error_msg}")
                    if "certificate verify failed" in error_msg:
                        logger.error("SSL certificate verification failed")
                    elif "SSL SYSCALL error" in error_msg:
                        logger.error("SSL system call error - potential network issue")
                else:
                    logger.error(f"Database connection error: {error_msg}")
                
                if retry_count == self.max_retries:
                    logger.error(f"Failed to create connection pool after {self.max_retries} attempts")
                    raise last_error
                
                logger.warning(f"Connection attempt {retry_count} failed, retrying in {self.retry_delay} seconds")
                time.sleep(self.retry_delay * retry_count)  # Exponential backoff

    def _get_db_connection(self):
        """Get a database connection with enhanced SSL retry logic"""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                conn = self.pool.getconn()
                if conn.closed:
                    logger.warning("Received closed connection from pool, attempting to reconnect")
                    self.pool.putconn(conn)
                    raise psycopg2.OperationalError("Connection is closed")
                
                # Verify SSL connection
                with conn.cursor() as cur:
                    cur.execute("SHOW ssl")
                    ssl_status = cur.fetchone()[0]
                    if ssl_status != 'on':
                        raise psycopg2.OperationalError("SSL is not enabled for this connection")
                
                return conn
            except psycopg2.OperationalError as e:
                last_error = e
                retries += 1
                error_msg = str(e)
                
                if "SSL" in error_msg:
                    logger.error(f"SSL connection error on attempt {retries}: {error_msg}")
                    if "connection has been closed unexpectedly" in error_msg:
                        logger.warning("SSL connection closed unexpectedly, attempting to reconnect")
                    elif "SSL SYSCALL error" in error_msg:
                        logger.warning("SSL system call error, waiting before retry")
                else:
                    logger.error(f"Database error on attempt {retries}: {error_msg}")
                
                if retries < self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retries - 1))  # Exponential backoff
                    time.sleep(sleep_time)
                    try:
                        logger.info("Attempting to recreate connection pool")
                        self._create_connection_pool()
                    except Exception as pool_error:
                        logger.error(f"Failed to recreate connection pool: {str(pool_error)}")
                else:
                    logger.error(f"Failed to get database connection after {self.max_retries} attempts")
                    raise last_error

    @contextmanager
    def get_connection(self):
        """Enhanced connection context manager with SSL error handling"""
        conn = None
        try:
            conn = self._get_db_connection()
            yield conn
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            logger.error(f"Database operational error: {error_msg}")
            
            if any(ssl_error in error_msg for ssl_error in [
                "SSL connection has been closed unexpectedly",
                "SSL SYSCALL error",
                "SSL connection error",
                "certificate verify failed"
            ]):
                logger.info("Detected SSL connection failure, attempting to reconnect")
                if conn:
                    try:
                        conn.close()
                    except Exception as close_error:
                        logger.error(f"Error closing connection: {str(close_error)}")
                    self.pool.putconn(conn)
                self._create_connection_pool()
            raise
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}")
            if conn:
                try:
                    conn.close()
                except Exception as close_error:
                    logger.error(f"Error closing connection: {str(close_error)}")
                self.pool.putconn(conn)
            raise
        else:
            if conn:
                self.pool.putconn(conn)

    # ... [Rest of the DatabaseManager class remains unchanged] ...

    def __del__(self):
        """Enhanced cleanup of connection pool on deletion"""
        if hasattr(self, 'pool'):
            try:
                self.pool.closeall()
                logger.info("Successfully closed all database connections")
            except Exception as e:
                logger.error(f"Error closing connection pool: {str(e)}")
