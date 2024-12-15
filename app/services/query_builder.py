from typing import Dict, Tuple
from langchain.chains import create_sql_query_chain
from langchain.sql_database import SQLDatabase
from .database.connection import get_db_engine
from .llm.openai_client import get_llm

class QueryBuilder:
    @staticmethod
    def build_query(question: str) -> Tuple[str, str, Dict]:
        """
        Build an SQL query using LangChain's SQL query chain.
        Returns:
            Tuple[str, str, Dict]: SQL query, response template, and template variables
        """
        try:
            # Get database engine
            engine = get_db_engine()
            
            # Create SQL database wrapper
            db = SQLDatabase(engine)
            
            # Get LLM
            llm = get_llm()
            
            # Create SQL query chain
            chain = create_sql_query_chain(llm, db)
            
            # Generate SQL query
            sql_query = chain.invoke({"question": question})
            
            # Default template and variables
            template = "Found {count} matching tasks."
            variables = {"count": "len(results)"}
            
            return sql_query, template, variables
            
        except Exception as e:
            print(f"Error generating SQL query: {e}")
            # Fallback to a basic query if chain fails
            return (
                "SELECT * FROM tasks",
                "Found {count} tasks.",
                {"count": "len(results)"}
            )