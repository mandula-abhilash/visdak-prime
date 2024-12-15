import os
import re
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

# Define the LLMs (one for query generation, one for response formatting)
query_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
response_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Define a custom prompt for SQL query generation
query_template = '''Given an input question, create a syntactically correct PostgreSQL query to run.
Return ONLY the SQL query without any additional text.
Be smart about the type of query needed based on the question.

Possible strategies:
- Use COUNT(*) to count matching rows
- Use SELECT * to fetch full details
- Use appropriate WHERE clauses to filter

Only use the following tables:
{table_info}

Limit the results to {top_k} rows.

Question: {input}'''

query_prompt = PromptTemplate(
    template=query_template,
    input_variables=["input", "table_info", "top_k"]
)

# Define a prompt for formatting the response
response_template = '''Analyze the SQL query result and provide a clear, concise response to the original question.

Original Question: {input}
SQL Query Result: {sql_result}

Strategies for response:
- If result is a count, summarize the number
- If result is full rows, describe the details
- Use natural language and be informative

Your response should directly address the question and provide meaningful insights.'''

response_prompt = PromptTemplate(
    input_variables=["input", "sql_result"],
    template=response_template
)

# Function to extract just the SQL query
def extract_sql_query(llm_output):
    # Remove any code block markers
    clean_output = llm_output.replace('```sql', '').replace('```', '').strip()
    
    # Try to extract query using regex
    match = re.search(r'SELECT.*?;', clean_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0)
    
    # If no match, return the entire cleaned output
    return clean_output

# Create an SQLAlchemy engine
engine = create_engine(POSTGRES_URI)

def get_sql_query_result(question, table_info='tasks', top_k=5):
    try:
        # Modify the query generation to use a different approach
        # Use the database's sample tables to inform the query
        table_sample = db.get_table_info(table_names=[table_info])
        
        # Generate the SQL query
        generated_query = query_llm.invoke(
            query_prompt.format(
                input=question, 
                table_info=table_sample, 
                top_k=top_k
            )
        ).content
        
        # Extract clean SQL query
        clean_query = extract_sql_query(generated_query)
        
        print(f"Generated SQL Query:\n{clean_query}\n")
        
        # Execute the query
        with engine.connect() as connection:
            result = connection.execute(text(clean_query))
            rows = result.fetchall()  # Fetch all rows

        # Determine how to format the result based on the query
        if 'COUNT(' in clean_query or 'count(' in clean_query:
            # Count query
            result_str = str(rows[0][0]) if rows else "0"
        elif '*' in clean_query:
            # Full details query
            result_str = "\n".join([str(row) for row in rows])
        else:
            # Generic fallback
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
questions = [
    "How many documentation tasks are there in total?",
    "Are there any memory leak issue related tasks?",
    "List memory leak related tasks",
    "List some high priority tasks which are very critical and I must do now"
]

for question in questions:
    print(f"\nQuestion: {question}")
    response = get_sql_query_result(question)
    print("Response:", response)