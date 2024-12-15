from app.database.connection import Database
from app.schemas.task import TaskCreate

class TaskService:
    @staticmethod
    async def add_task(task: TaskCreate):
        """
        Add a new task to the database.
        """
        db = None
        try:
            db = Database.connect()
            cursor = db.cursor()
            query = """
                INSERT INTO tasks (title, description, priority, category)
                VALUES (%s, %s, %s, %s) RETURNING id
            """
            cursor.execute(query, (task.title, task.description, task.priority, task.category))
            task_id = cursor.fetchone()[0]
            db.commit()
            return task_id
        except Exception as e:
            if db:
                db.rollback()
            raise Exception(f"Failed to add task: {str(e)}")
        finally:
            if db:
                cursor.close()

    @staticmethod
    async def query_tasks(question: str):
        """
        Query tasks using natural language.
        """
        db = None
        try:
            db = Database.connect()
            # QueryBuilder logic here
            # Assuming QueryBuilder builds a SQL query from the question
            query = f"SELECT * FROM tasks WHERE priority = 'high'"  # Example query
            cursor = db.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            raise Exception(f"Failed to query tasks: {str(e)}")
        finally:
            if db:
                cursor.close()
