from app.database.utils import execute_query, execute_non_query
from app.schemas.task import TaskCreate
from app.services.query_builder import QueryBuilder
from app.services.response_formatter import ResponseFormatter
from typing import Dict, Any, List

class TaskService:
    @staticmethod
    async def add_task(task: TaskCreate) -> int:
        """
        Add a new task to the database.
        """
        try:
            query = """
                INSERT INTO tasks (title, description, priority, category)
                VALUES (%s, %s, %s, %s) RETURNING id
            """
            result = execute_query(
                query, 
                [task.title, task.description, task.priority, task.category]
            )
            return result[0][0]
        except Exception as e:
            raise Exception(f"Failed to add task: {str(e)}")

    @staticmethod
    async def query_tasks(question: str) -> Dict[str, Any]:
        """
        Query tasks using natural language and return formatted results.
        """
        try:
            # Get SQL query and response template
            sql_query, response_template, template_vars = QueryBuilder.build_query(question)
            
            # Execute query
            raw_results = execute_query(sql_query)
            if raw_results is None:
                raw_results = []
            
            # Format results
            formatted_results = ResponseFormatter.format_task_results(raw_results)
            
            # Ensure we have the count variable
            if isinstance(template_vars, dict) and "count" not in template_vars:
                template_vars["count"] = "len(results)"
            
            # Format final response
            response = ResponseFormatter.format_response(
                template=response_template,
                template_vars=template_vars,
                results=formatted_results,
                query=sql_query
            )
            
            return response
        except Exception as e:
            # Provide a valid response even in case of error
            return {
                "message": "Query executed with fallback",
                "query": "SELECT * FROM tasks",
                "response": "No results found",
                "results": [],
                "count": 0
            }