import os
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_openai import ChatOpenAI
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Read database credentials from environment variables
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")

# Build the connection string
POSTGRES_URI = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

# Create an SQLAlchemy engine
engine = create_engine(POSTGRES_URI)

# Function to create embeddings using the embeddings endpoint
def create_embedding(text):
    try:
        client = OpenAI()
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text]
        )
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)
    except Exception as e:
        print(f"Error generating embedding for text '{text}': {e}")
        return None

# Function to check if task_embeddings table exists and has the correct schema
def verify_table_schema():
    try:
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'task_embeddings'
                );
            """))
            exists = result.scalar()
            
            if not exists:
                print("Error: task_embeddings table does not exist!")
                return False
            
            # Check table schema
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'task_embeddings';
            """))
            columns = result.fetchall()
            print("Table schema:")
            for col in columns:
                print(f"Column: {col[0]}, Type: {col[1]}")
            
            return True
    except Exception as e:
        print(f"Error verifying table schema: {e}")
        return False

# Function to populate the task_embeddings table
def populate_task_embeddings():
    try:
        # First verify the table schema
        if not verify_table_schema():
            return

        # Fetch task data from the tasks table
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, title, description, priority, category, created_at FROM tasks")
            )
            tasks = result.fetchall()
            print(f"Found {len(tasks)} tasks to process")

        # Insert task data and embeddings into the task_embeddings table
        for task_id, title, description, priority, category, created_at in tasks:
            print(f"\nProcessing task_id {task_id}...")
            print(f"Description: {description}")

            # Generate embedding
            embedding = create_embedding(description)
            if embedding is None:
                print(f"Skipping task_id {task_id} due to embedding generation error.")
                continue

            print(f"Generated embedding of length: {len(embedding)}")

            try:
                # Use a single connection for both insert and verify
                with engine.connect() as connection:
                    # Begin transaction
                    with connection.begin():
                        # Insert the embedding
                        connection.execute(
                            text("""
                                INSERT INTO task_embeddings 
                                (task_id, title, description, priority, category, created_at, embedding)
                                VALUES 
                                (:task_id, :title, :description, :priority, :category, :created_at, :embedding)
                                ON CONFLICT (task_id) DO UPDATE SET
                                embedding = :embedding
                            """),
                            {
                                "task_id": task_id,
                                "title": title,
                                "description": description,
                                "priority": priority,
                                "category": category,
                                "created_at": created_at,
                                "embedding": embedding.tolist()
                            }
                        )
                        
                        # Verify the insertion within the same transaction
                        result = connection.execute(
                            text("SELECT embedding FROM task_embeddings WHERE task_id = :task_id"),
                            {"task_id": task_id}
                        )
                        stored_embedding = result.scalar()
                        
                        if stored_embedding is None:
                            print(f"Warning: Failed to verify insertion for task_id {task_id}")
                        else:
                            print(f"Task_id {task_id} inserted and verified successfully")

            except Exception as e:
                print(f"Error processing task_id {task_id}: {e}")
                continue

        # Final verification
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT COUNT(*) FROM task_embeddings")
            )
            count = result.scalar()
            print(f"\nTotal records in task_embeddings table: {count}")

    except Exception as e:
        print(f"Error populating task_embeddings table: {e}")

if __name__ == "__main__":
    populate_task_embeddings()