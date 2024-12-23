# PRIME

**Processing and Retrieval of Indexed Metadata & Embeddings**

_A universal module for creating, managing, and querying relational and embedding-based data for diverse applications._

---

## Overview

PRIME is a robust, modular system designed to handle both structured SQL queries and embedding-based semantic search for various use cases. Built with flexibility, scalability, and high performance in mind, PRIME seamlessly integrates into your existing tech stack, making it suitable for tasks like productivity tools, chatbots, business intelligence, and more.

With PRIME, you can:

- Dynamically generate SQL queries from natural language inputs.
- Perform semantic similarity searches using vector embeddings.
- Support hybrid use cases combining structured and unstructured data queries.

---

## Features

### **Dynamic SQL Query Generation**

- Generate syntactically correct SQL queries based on natural language input.
- Supports relational data queries such as counts, filters, aggregations, and more.
- Tailored for structured data like tasks, projects, reviews, and business information.
- Powered by OpenAI LLMs for natural language understanding and SQL generation.

### **Vector-Based Semantic Search**

- Perform embedding-based searches using the PostgreSQL pgvector extension.
- Store and retrieve high-dimensional vectors for semantic similarity.
- Ideal for FAQs, recommendations, and unstructured knowledge bases.
- Uses OpenAI’s embedding models for vector generation.

### **Hybrid Query Handling**

- Combine SQL query generation with vector-based search for advanced use cases.
- Enable seamless transitions between structured data querying and semantic search.
- Serve diverse applications like chatbots, virtual assistants, and productivity tools.

---

## Use Cases

### **1. Dynamic SQL Query Generation**

**Purpose:** To enable natural language querying of structured data in relational databases.

**Example Applications:**

- Productivity tools with task management and progress tracking.
- Business intelligence dashboards for reporting and insights.
- User-friendly interfaces for querying structured datasets without SQL knowledge.

**Key Features:**

- Natural language to SQL conversion.
- Support for SELECT, COUNT, WHERE, and other common SQL operations.
- Real-time query execution and result formatting.

**Script Name:** `dynamic_sql_query.py`

---

### **2. Vector-Based Semantic Search**

**Purpose:** To enable similarity-based retrieval of data using embeddings.

**Example Applications:**

- Chatbots capable of intent matching and FAQ retrieval.
- Recommendation systems for products, services, or content.
- Knowledge bases with semantic understanding of user queries.

**Key Features:**

- Embedding generation using OpenAI models.
- Semantic similarity search using pgvector.
- Fast and efficient contextual matching.

**Script Name:** `semantic_search_pgvector.py`

---

## Architecture

### **Core Components:**

1. **SQL Query Generator:**

   - Converts natural language into SQL queries for structured data querying.
   - Optimized for relational database operations.

2. **Semantic Search Engine:**

   - Leverages pgvector to store and retrieve embeddings for similarity search.
   - Uses cosine similarity for ranking results.

3. **LLM Integration:**
   - OpenAI models for natural language understanding, SQL generation, and embedding creation.
   - Supports human-readable response formatting.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/prime.git
   cd prime
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:

   - Create a `.env` file with the following keys:
     ```env
     PG_HOST=your_postgres_host
     PG_PORT=your_postgres_port
     PG_USER=your_postgres_user
     PG_PASSWORD=your_postgres_password
     PG_DATABASE=your_database_name
     ```

4. Enable pgvector in your PostgreSQL instance:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## Getting Started

### **Dynamic SQL Query Generation**

Run the SQL query generation script:

```bash
python dynamic_sql_query.py
```

- Input: Natural language question (e.g., "How many tasks are overdue?")
- Output: SQL query execution and human-readable response.

### **Vector-Based Semantic Search**

Run the semantic search script:

```bash
python semantic_search_pgvector.py
```

- Input: Natural language question (e.g., "What are your business hours?")
- Output: Most relevant records based on semantic similarity.

---

## Roadmap

- **Custom Embedding Models:** Support for user-provided embedding generation.
- **Hybrid Query Optimization:** Seamless integration of SQL and semantic search workflows.
- **Multi-Tenant Support:** Isolation of data for multiple clients or businesses.
