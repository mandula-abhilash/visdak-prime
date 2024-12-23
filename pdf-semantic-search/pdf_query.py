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
engine = create_engine(DATABASE_URL, echo=True)  # Enable echo to debug SQL queries
SessionLocal = sessionmaker(bind=engine)

class PdfDocument(Base):
    __tablename__ = 'pdf_documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(String)
    embedding = Vector(N_DIM)

Base.metadata.create_all(engine)

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

if __name__ == "__main__":
    # Example questions
    questions = [
        "What does the PDF say about software architecture?",
        "Tell me about any testing strategies mentioned.",
        "Are there any references to memory leaks?",
        "Is there a conclusion or summary in the document?",
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

        if not results:
            print("No similar text found for this question.\n")
            continue

        # Print out the results
        for row in results:
            print(f" - Chunk ID: {row.id}, Filename: {row.filename}, Page: {row.page_number}, Similarity: {row.similarity:.4f}")
            print(f"   Content: {row.content[:200]}...")  # print partial content
        print()
