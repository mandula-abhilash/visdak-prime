class QueryPrompts:
    SQL_GENERATION_TEMPLATE = """
    You are an SQL expert. Given this table schema:
    {table_info}

    For this question: '{question}'
    Generate three things:
    1. A PostgreSQL query to get the data
    2. A natural language template to format the response
    3. A mapping of variables

    Format your response exactly like this:
    QUERY: <the SQL query>
    TEMPLATE: Found {count} tasks.
    VARIABLES: {{"count": "len(results)"}}

    Make sure:
    - The template uses only simple variables
    - Variables JSON is properly formatted
    - Always include 'count' in variables
    """