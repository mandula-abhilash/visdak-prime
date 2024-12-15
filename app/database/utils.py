from typing import List, Any
import psycopg2
from app.database.connection import Database


def execute_query(query: str, params: List[Any] = None) -> List[tuple]:
    """
    Execute a SQL query with optional parameters and fetch results.
    Args:
        query (str): The SQL query to execute.
        params (list): Optional list of parameters for the query.
    Returns:
        list: Query results as a list of tuples.
    """
    try:
        conn = Database.connect()
        cursor = conn.cursor()

        # Execute query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Fetch results
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        raise Exception(f"Failed to execute query: {str(e)}")


def execute_non_query(query: str, params: List[Any] = None):
    """
    Execute a SQL query that does not return results (e.g., INSERT, UPDATE).
    Args:
        query (str): The SQL query to execute.
        params (list): Optional list of parameters for the query.
    """
    try:
        conn = Database.connect()
        cursor = conn.cursor()

        # Execute query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Commit transaction
        conn.commit()
        cursor.close()
    except Exception as e:
        raise Exception(f"Failed to execute non-query: {str(e)}")
