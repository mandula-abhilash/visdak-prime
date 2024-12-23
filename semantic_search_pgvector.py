import os
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from openai import OpenAI

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

# Read database credentials from environment variables
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Build the connection string
POSTGRES_URI = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

# Create an SQLAlchemy engine
engine = create_engine(POSTGRES_URI)

# Define a prompt for formatting the response
response_template = '''Analyze the query result and provide a concise response to the original question.

Original Question: {input}
Most Similar Tasks: {similar_records}

Strategies for response:
- Summarize the matched tasks.
- If no tasks match closely, explain the lack of results.
- Provide clear, actionable information.

Your response should directly address the question and provide meaningful insights.'''

response_prompt = PromptTemplate(
    input_variables=["input", "similar_records"],
    template=response_template
)

# Table and vector column setup
VECTOR_TABLE = "task_embeddings"  # Updated table name
VECTOR_COLUMN = "embedding"       # Column for the vector
TEXT_COLUMN = "description"       # Column for task descriptions

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

# Function to find similar records
def find_similar_records(question, top_k=5):
    try:
        # Generate embedding for the input question
        question_embedding = create_embedding(question)
        if question_embedding is None:
            return f"Error: Could not generate embedding for question: '{question}'"

        # Ensure the dimension is 1536 if your column is VECTOR(1536)
        if len(question_embedding) != 1536:
            return f"Error: Embedding dimension {len(question_embedding)} does not match VECTOR(1536)."

        # Convert numpy array into a pgvector-compatible string, e.g. '{0.12,0.98,...}'
        # Use .6f (or other precision) to ensure consistent formatting
        embedding_str_values = [f"{float(val):.6f}" for val in question_embedding]
        embedding_str = "{" + ",".join(embedding_str_values) + "}"

        # Remove the ::vector cast; pass the string directly
        query_str = f"""
        SELECT 
            task_id, 
            {TEXT_COLUMN} AS description,
            1 - ({VECTOR_COLUMN} <=> :embedding) AS similarity
        FROM {VECTOR_TABLE}
        WHERE {VECTOR_COLUMN} IS NOT NULL
        ORDER BY {VECTOR_COLUMN} <=> :embedding
        LIMIT :top_k;
        """

        with engine.connect() as connection:
            result = connection.execute(
                text(query_str),
                {"embedding": embedding_str, "top_k": top_k}
            )
            records = result.fetchall()

        # Format the results
        similar_records = [
            {"id": row["task_id"], "text": row["description"], "similarity": float(row["similarity"])} 
            for row in records
        ]
        return similar_records

    except Exception as e:
        print(f"Error : {str(e)}")
        return f"Error performing semantic search: {str(e)}"

# Function to generate a response
def get_semantic_search_response(question, top_k=5):
    try:
        # Perform the semantic search
        similar_records = find_similar_records(question, top_k)

        # Check if there are any results or errors
        if isinstance(similar_records, str):  # Error case
            return similar_records

        if not similar_records:
            similar_records_str = "No matching tasks found."
        else:
            # Format the similar records as a string for LLM response generation
            similar_records_str = "\n".join(
                [f"Task ID: {rec['id']}, Description: {rec['text']} (Similarity: {rec['similarity']:.2f})"
                 for rec in similar_records]
            )

        # Generate a human-readable response using LLM
        response_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        response = response_llm.invoke(
            response_prompt.format(
                input=question,
                similar_records=similar_records_str
            )
        ).content

        return response

    except Exception as e:
        return f"Error processing the question: {e}"

# Example usage
questions = [
    "What tasks are related to development?",
    "Are there any tasks about documentation?",
    "Which tasks involve testing?",
    "Tell me about the tasks scheduled for June 21.",

    "How many documentation tasks are there in total?",
    "Are there any memory leak issue related tasks?",
    "List memory leak related tasks",
    "List some high priority tasks which are very critical and I must do now"
]

for question in questions:
    print(f"\nQuestion: {question}")
    response = get_semantic_search_response(question)
    print("Response:", response)
