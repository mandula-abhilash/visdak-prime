from sqlalchemy import create_engine
import os

def get_db_engine():
    """Create and return a SQLAlchemy database engine."""
    connection_string = f"postgresql://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DATABASE')}"
    return create_engine(connection_string)