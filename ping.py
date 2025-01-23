"""
Script for checking that a database server is available.
"""
import time

from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.engine.url import make_url

#from app.config import Config
from app.config import DB_URI, POSTGRES_DB

url = make_url(DB_URI)

# Ignore sqlite databases
if url.drivername.startswith("sqlite"):
    exit(0)

# Null out the database so raw_connection doesnt error if it doesnt exist
# This will create the database if it doesnt exist
url = url._replace(database=None)

# Wait for the database server to be available
engine = create_engine(url)

def wait_for_database(engine, timeout=60):
    """Wait for the database server to be ready."""
    start_time = time.time()
    while True:
        try:
            # Try to connect to the database server
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("Database server is ready!")
                return True
        except Exception as e:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print("Timeout waiting for the database server. Exiting.")
                raise e
            print(f"Waiting for the database server... ({elapsed_time:.1f}s elapsed)")
            time.sleep(1)

# Wait for the database server to be ready
wait_for_database(engine)

# Check if the target database exists; create it if not
with engine.connect() as conn:
    result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = :dbname"), {'dbname': POSTGRES_DB})
    if not result.fetchone():
        conn.execute(text(f"CREATE DATABASE {POSTGRES_DB}"))
        print(f"Database {POSTGRES_DB} created!")
