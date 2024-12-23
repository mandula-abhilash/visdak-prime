"""
pdf_query.py

Script to:
1. Accept or define a list of questions.
2. Generate embeddings for each question.
3. Find the most similar PDF chunks from 'pdf_documents' table.
"""

import os
import openai
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

# ----------------------
# Configuration
# ----------------------

# Replace with your own OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key")

# Replace with your own Postgres connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# Number of embedding dimensions
N_DIM = 1536

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ----------------------
# Database Model
# ----------------------

class PdfDocument(Base):
    """
    Mirrors the table created in pdf_ingestion.py for storing PDF chunks.
    """
    __tablename__ = 'pdf_documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(String)
    embedding = Vector(N_DIM)

# ----------------------
# Helper Functions
# ----------------------

def generate_query_embedding(question: str) -> list:
    """
    Generate a single embedding for a given question.
    """
    response = openai.Embedding.create(
        input=question,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

def find_similar_documents(query_embedding, limit=5, similarity_threshold=0.7):
    """
    Find similar PDF chunks from the pdf_documents table that have distance
    less than `similarity_threshold`. The vector column in PdfDocument is 
    configured for cosine distance in this example.
    """
    session = SessionLocal()
    try:
        # Build query for similarity
        # `.cosine_distance(query_embedding)` is provided by pgvector.sqlalchemy
        query = (
            session.query(
                PdfDocument,
                PdfDocument.embedding.cosine_distance(query_embedding).label("distance")
            )
            .filter(
                PdfDocument.embedding.cosine_distance(query_embedding) < similarity_threshold
            )
            .order_by("distance")
            .limit(limit)
            .all()
        )

        return query
    except Exception as e:
        print(f"Error in find_similar_documents: {e}")
        return []
    finally:
        session.close()

# ----------------------
# Main Query Flow
# ----------------------

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
        query_embedding = generate_query_embedding(question)

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
        for (pdf_doc, distance) in results:
            print(f" - Chunk ID: {pdf_doc.id}, Distance: {distance:.4f}")
            print(f"   Content: {pdf_doc.content[:200]}...")  # print partial content
        print()
