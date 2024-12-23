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

# LLM for embedding generation
embedding_llm = ChatOpenAI(model="text-embedding-ada-002", temperature=0)

# Function to create embeddings using the embeddings endpoint
def create_embedding(text):
    """
    Create embeddings using OpenAI's text-embedding-ada-002 model.
    
    Args:
        text (str): The text to create embeddings for
        
    Returns:
        numpy.ndarray: The embedding vector, or None if there's an error
    """
    try:
        # Initialize the client
        client = OpenAI()  # Make sure you have OPENAI_API_KEY set in your environment
        
        # Generate embeddings using the new client syntax
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text]  # Input should be a list
        )
        
        # Extract the embedding from the response
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)
        
    except Exception as e:
        print(f"Error generating embedding for text '{text}': {e}")
        return None

# Function to populate the task_embeddings table
def populate_task_embeddings():
    try:
        # Fetch task data from the tasks table
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, title, description, priority, category, created_at FROM tasks")
            )
            tasks = result.fetchall()

        # Insert task data and embeddings into the task_embeddings table
        for task_id, title, description, priority, category, created_at in tasks:
            print(f"Processing task_id {task_id}...")

            # Generate embedding
            embedding = create_embedding(description)
            if embedding is None:
                print(f"Skipping task_id {task_id} due to embedding generation error.")
                continue

            # Insert into task_embeddings table
            with engine.connect() as connection:
                connection.execute(
                    text("""
                        INSERT INTO task_embeddings (task_id, title, description, priority, category, created_at, embedding)
                        VALUES (:task_id, :title, :description, :priority, :category, :created_at, :embedding)
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
            print(f"Task_id {task_id} inserted successfully.")

        print("Task embeddings table populated successfully.")

    except Exception as e:
        print(f"Error populating task_embeddings table: {e}")

# Run the script
if __name__ == "__main__":
    populate_task_embeddings()
