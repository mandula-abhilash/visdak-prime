import os
from dotenv import load_dotenv

from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

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

# Tool to execute the SQL query
execute_query = QuerySQLDataBaseTool(db=db)

# Define an answer generation prompt
answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question}
SQL Query: {query}
SQL Result: {result}
Answer: """
)

# Parse the final answer
answer = answer_prompt | llm | StrOutputParser()

# Combine chains: Generate query, execute, and parse the answer
chain = (
    RunnablePassthrough.assign(query=write_query).assign(
        result=itemgetter("query") | execute_query
    )
    | answer
)

# Example question
question = "What are todays tasks?"

# Invoke the chain
response = chain.invoke({"question": question, "top_k": 5, "table_info": "regions, ward, parish, county"})

# Print the final response
print(response)
