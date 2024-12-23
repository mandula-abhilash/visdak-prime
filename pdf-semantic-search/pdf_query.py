"""
pdf_query.py

Script to:
1. Accept or define a list of questions.
2. Generate embeddings for each question.
3. Find the most similar PDF chunks from 'pdf_documents' table.
"""

import os
import numpy as np
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

# Configuration
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
N_DIM = 1536

Base = declarative_base()
# engine = create_engine(DATABASE_URL, echo=True)  # Enable echo to debug SQL queries
engine = create_engine(DATABASE_URL)  # Enable echo to debug SQL queries
SessionLocal = sessionmaker(bind=engine)

class PdfDocument(Base):
    __tablename__ = 'pdf_documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(String)
    embedding = Vector(N_DIM)

Base.metadata.create_all(engine)

response_template = '''Analyze the following matched PDF chunks and provide a concise response to the original question.

Original Question: {input}
Matched Chunks:
{similar_records}

Strategies for response:
- Summarize the key points from the matched chunks.
- If no chunks match closely, explain the lack of results.
- Provide clear, actionable insights based on the available information.'''

response_prompt = PromptTemplate(
    input_variables=["input", "similar_records"],
    template=response_template
)

def create_embedding(text: str) -> np.ndarray:
    try:
        client = OpenAI()
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text]
        )
        embedding = response.data[0].embedding
        if len(embedding) != N_DIM:
            raise ValueError(f"Unexpected embedding dimension: {len(embedding)}")
        return np.array(embedding, dtype=np.float32)  # Convert to numpy array for compatibility
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def find_similar_documents(query_embedding: np.ndarray, limit=5, similarity_threshold=0.7):
    """
    Find similar PDF chunks from the pdf_documents table that have distance
    less than `similarity_threshold`. The vector column in PdfDocument is 
    configured for cosine distance in this example.
    """
    session = SessionLocal()
    try:
        # Convert embedding to string for querying
        embedding_str = f"[{','.join(f'{float(val):.6f}' for val in query_embedding)}]"

        # Build query for similarity
        query_str = f"""
        SELECT id, filename, page_number, content, 1 - (embedding <=> :embedding) AS similarity
        FROM pdf_documents
        WHERE 1 - (embedding <=> :embedding) >= :similarity_threshold
        ORDER BY embedding <=> :embedding
        LIMIT :limit;
        """

        result = session.execute(
            text(query_str),
            {"embedding": embedding_str, "similarity_threshold": similarity_threshold, "limit": limit}
        )

        results = result.fetchall()
        return results
    except Exception as e:
        print(f"Error in find_similar_documents: {e}")
        return []
    finally:
        session.close()

def get_semantic_response(question: str, results):
    if not results:
        similar_records_str = "No matching chunks found."
    else:
        similar_records_str = "\n".join(
            [f"Chunk ID: {row.id}, Page: {row.page_number}, Content: {row.content[:200]}..." for row in results]
        )

    response_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    response = response_llm.invoke(
        response_prompt.format(
            input=question,
            similar_records=similar_records_str
        )
    ).content

    return response

if __name__ == "__main__":
    # Example questions
    questions = [
        "What is the prevalence of HPV in oral cavity cancer?",
        "What are the objectives of the study?",
        "What does the PDF say about the anatomical structure of the oral cavity?",
        "What conclusions were drawn regarding HPV-positive patients?",
    ]

    for question in questions:
        print(f"\nQuestion: {question}")

        # Generate embedding for the question
        query_embedding = create_embedding(question)
        if query_embedding is None:
            print("Failed to generate embedding for the question.")
            continue

        # Retrieve similar documents
        results = find_similar_documents(
            query_embedding=query_embedding,
            limit=5,                 # how many results to return
            similarity_threshold=0.7 # how strict the similarity is
        )

        # Generate response from matched chunks
        response = get_semantic_response(question, results)
        print("Response:", response)
        print()
