import psycopg2
import os

class Database:
    _connection = None

    @staticmethod
    def connect():
        """
        Establish a connection to the PostgreSQL database using environment variables.
        """
        if Database._connection is None:
            try:
                Database._connection = psycopg2.connect(
                    user=os.getenv("PG_USER"),
                    password=os.getenv("PG_PASSWORD"),
                    host=os.getenv("PG_HOST"),
                    port=os.getenv("PG_PORT"),
                    database=os.getenv("PG_DATABASE")
                )
                Database._connection.autocommit = False  # Disable autocommit for transaction control
                print("✅ Connected to PostgreSQL")
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                raise
        return Database._connection

    @staticmethod
    def rollback():
        """
        Rollback the current transaction.
        """
        if Database._connection:
            try:
                Database._connection.rollback()
                print("🔄 Transaction rolled back")
            except Exception as e:
                print(f"❌ Failed to rollback transaction: {e}")

    @staticmethod
    def close():
        """
        Close the database connection.
        """
        if Database._connection:
            try:
                Database._connection.close()
                Database._connection = None
                print("🔒 PostgreSQL connection closed.")
            except Exception as e:
                print(f"❌ Failed to close connection: {e}")
