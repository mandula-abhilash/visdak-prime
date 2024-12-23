import os
import numpy as np
from pypdf import PdfReader
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class PdfDocument(Base):
    __tablename__ = 'pdf_documents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(String)
    embedding = Vector(N_DIM)

Base.metadata.create_all(engine)

def read_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text

def split_text(text, chunk_size=500, overlap=50):
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def create_embedding(text: str) -> np.ndarray:
    try:
        client = OpenAI()
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text]
        )
        embedding = response.data[0].embedding
        if len(embedding) != 1536:
            raise ValueError(f"Unexpected embedding dimension: {len(embedding)}")
        
        # Convert to numpy array for compatibility with pgvector
        return np.array(embedding, dtype=np.float32)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def ingest_pdf(file_path: str):
    print(f"Processing PDF: {file_path}")
    
    # Read PDF
    pdf_text = read_pdf(file_path)
    print(f"Extracted {len(pdf_text)} characters")
    
    # Split into chunks
    text_chunks = split_text(pdf_text, chunk_size=500, overlap=50)
    print(f"Created {len(text_chunks)} chunks")
    
    session = SessionLocal()
    try:
        for i, chunk in enumerate(text_chunks):
            try:
                # Generate embedding
                embedding = create_embedding(chunk)
                if embedding is None:
                    print(f"Skipping chunk {i}: embedding generation failed")
                    continue
                
                print(f"Embedding type: {type(embedding)}, length: {len(embedding)}")
                # Create document
                doc = PdfDocument(
                    filename=file_path,
                    page_number=i,
                    content=chunk,
                    embedding=embedding
                )
                session.add(doc)
                session.commit()
                print(f"Successfully inserted chunk {i}")
                
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                session.rollback()
                continue
    
    finally:
        session.close()
        print("Ingestion complete")

if __name__ == "__main__":
    pdf_file = "./pdf-semantic-search/shreya_md_thesis_sample.pdf"
    print(f"Current working directory: {os.getcwd()}")
    
    if not os.path.exists(pdf_file):
        print(f"File not found: {pdf_file}")
        exit(1)
        
    ingest_pdf(pdf_file)