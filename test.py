import os
from dotenv import load_dotenv

from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from sqlalchemy import create_engine, text

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

# Connect to the PostgreSQL database
db = SQLDatabase.from_uri(POSTGRES_URI)

# Define the LLM (use OpenAI's GPT model)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Define a custom prompt with the required input variables
template = '''Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer.
Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"
SQLResult: "Result of the SQLQuery"
Answer: "Final answer here"

Only use the following tables:

{table_info}.

Limit the results to {top_k} rows.

Question: {input}'''

prompt = PromptTemplate.from_template(template)

# Chain to generate SQL query
write_query = create_sql_query_chain(llm, db, prompt=prompt)

# Example question
question = "How many documentation tasks are there in total?"

# Create an SQLAlchemy engine
engine = create_engine(POSTGRES_URI)

# Generate the SQL query using the chain
response = write_query.invoke({"question": question, "top_k": 5, "table_info": "tasks"})

# Ensure the response contains a valid SQL query
if isinstance(response, str):
    # Clean the generated query to remove unnecessary formatting
    generated_query = response.strip()
    generated_query = generated_query.replace("```sql", "").replace("```", "").strip()
    
    print(f"Generated SQL Query:\n{generated_query}\n")
    
    try:
        # Execute the query and fetch the results
        with engine.connect() as connection:
            result = connection.execute(text(generated_query))
            rows = result.fetchall()  # Fetch all rows

        # Print the query results
        print("Query Results:")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error executing the query: {e}")
else:
    print("Failed to generate a valid SQL query.")