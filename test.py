import os
import re
from dotenv import load_dotenv

from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableSequence
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

# Define the LLMs (one for query generation, one for response formatting)
query_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
response_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Define a custom prompt for SQL query generation
query_template = '''Given an input question, create a syntactically correct PostgreSQL query to run.
Return ONLY the SQL query without any additional text.

Only use the following tables:

{table_info}

Limit the results to {top_k} rows.

Question: {input}'''

query_prompt = PromptTemplate.from_template(query_template)

# Define a prompt for formatting the response
response_template = '''Based on the SQL query result, craft a human-readable response to the original question.

Original Question: {input}
SQL Query Result: {sql_result}

Provide a clear, concise answer that directly addresses the question. Use natural language and make the response easy to understand.'''

response_prompt = PromptTemplate(
    input_variables=["input", "sql_result"],
    template=response_template
)

# Function to extract just the SQL query
def extract_sql_query(llm_output):
    # Remove any code block markers
    clean_output = llm_output.replace('```sql', '').replace('```', '').strip()
    
    # Try to extract query using regex
    match = re.search(r'SELECT.*?;', clean_output, re.DOTALL)
    if match:
        return match.group(0)
    
    # If no match, return the entire cleaned output
    return clean_output

# Chain to generate SQL query
write_query = create_sql_query_chain(query_llm, db, prompt=query_prompt)

# Create an SQLAlchemy engine
engine = create_engine(POSTGRES_URI)

def get_sql_query_result(question, table_info='tasks', top_k=5):
    try:
        # Generate the SQL query using the chain
        generated_query = write_query.invoke({
            "question": question, 
            "top_k": top_k, 
            "table_info": table_info
        })
        
        # Extract clean SQL query
        clean_query = extract_sql_query(generated_query)
        
        print(f"Generated SQL Query:\n{clean_query}\n")
        
        # Execute the query
        with engine.connect() as connection:
            result = connection.execute(text(clean_query))
            rows = result.fetchall()  # Fetch all rows

        # Format the results as a string
        result_str = ", ".join(str(row[0]) for row in rows)
        
        # Generate a human-readable response using LLM
        response = response_llm.invoke(
            response_prompt.format(
                input=question,
                sql_result=result_str
            )
        ).content

        return response
    
    except Exception as e:
        return f"Error processing the query: {e}"

# Example usage
question = "How many documentation tasks are there in total?"
response = get_sql_query_result(question)
print("\nFormatted Response:")
print(response)