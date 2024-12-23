"""
pdf_ingestion.py

Script to:
1. Read a PDF file.
2. Split the text into smaller chunks.
3. Generate embeddings for each chunk.
4. Insert chunk + embedding into the 'pdf_documents' table.
"""

import os
import openai
import numpy as np
from pypdf import PdfReader
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

# ----------------------
# Load Environment Variables
# ----------------------

load_dotenv()

# ----------------------
# Configuration
# ----------------------


# Read database credentials from environment variables
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Database connection URL
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

# Number of embedding dimensions for 'text-embedding-ada-002'
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
    A table to store each chunk of PDF text and its corresponding embedding.
    """
    __tablename__ = 'pdf_documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Optionally store the PDF filename or page number for reference
    filename = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(String)
    embedding = Vector(N_DIM)  # Uses pgvector extension

# Create the table if it doesn't already exist
Base.metadata.create_all(engine)

# ----------------------
# Helper Functions
# ----------------------

def read_pdf(file_path: str) -> str:
    """
    Read a PDF file and return its entire text as a single string.
    """
    reader = PdfReader(file_path)
    text = ""
    for page_index, page in enumerate(reader.pages):
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text

def split_text(text, chunk_size=500, overlap=50):
    """
    Split text into overlapping chunks of size `chunk_size`.
    Overlap is `overlap` characters.
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap to avoid infinite loop.")

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))  # Ensure `end` doesn't exceed text length
        chunks.append(text[start:end])
        start += chunk_size - overlap  # Advance `start` by chunk_size minus overlap

    return chunks

def generate_embeddings(text_chunks: list) -> list:
    """
    Generate embeddings for each text chunk using OpenAI's Embedding API.
    """
    embeddings = []
    for chunk in text_chunks:
        response = openai.Embedding.create(
            input=chunk,
            model="text-embedding-ada-002"
        )
        embeddings.append(response['data'][0]['embedding'])
    return embeddings

def insert_into_pdf_documents(filename: str, page_number: int, content: str, embedding: list):
    """
    Insert a single chunk (with embedding) into the pdf_documents table.
    """
    session = SessionLocal()
    try:
        doc = PdfDocument(
            filename=filename,
            page_number=page_number,
            content=content,
            embedding=embedding  # pgvector will store this as a vector
        )
        session.add(doc)
        session.commit()
    except Exception as e:
        print(f"Error inserting record: {e}")
        session.rollback()
    finally:
        session.close()

# ----------------------
# Main Ingestion Flow
# ----------------------

def ingest_pdf(file_path: str):
    """
    Orchestrates the ingestion of a PDF file into the pdf_documents table.
    """
    # Read PDF
    pdf_text = read_pdf(file_path)
    # pdf_text = "This is a sample text for testing. It will be split into smaller chunks with overlap."

    # Split into chunks
    text_chunks = split_text(pdf_text, chunk_size=500, overlap=50)

    # Generate embeddings
    embeddings = generate_embeddings(text_chunks)

    # Insert each chunk into db
    for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
        insert_into_pdf_documents(
            filename=file_path,
            page_number=i,   # or store actual page if you want to track real PDF pages
            content=chunk,
            embedding=embedding
        )

if __name__ == "__main__":
    import os

    # Example usage
    pdf_file = "./pdf-semantic-search/shreya_md_thesis_sample.pdf"
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if file exists
    if not os.path.exists(pdf_file):
        print(f"File not found: {pdf_file}")
        exit(1)

    ingest_pdf(pdf_file)
    print("PDF ingestion complete.")
