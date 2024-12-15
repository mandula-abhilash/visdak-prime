import psycopg2
from psycopg2.extensions import connection
import os

class Database:
    _connection: connection = None

    @staticmethod
    def get_connection() -> connection:
        """
        Get a singleton connection to PostgreSQL.
        """
        if Database._connection is None:
            Database._connection = psycopg2.connect(
                user=os.getenv("PG_USER"),
                password=os.getenv("PG_PASSWORD"),
                host=os.getenv("PG_HOST"),
                port=os.getenv("PG_PORT"),
                database=os.getenv("PG_DATABASE"),
            )
        return Database._connection
