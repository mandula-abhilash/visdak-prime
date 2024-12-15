from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Dict, Tuple, Optional
import json
from .templates.query_prompts import QueryPrompts

class QueryBuilder:
    TABLE_INFO = """
    Table: tasks
    Columns:
    - id (integer, primary key)
    - title (text)
    - description (text)
    - priority (text: 'low', 'medium', 'high')
    - category (text)
    """

    @staticmethod
    def parse_llm_response(response: str) -> Tuple[str, str, Dict]:
        """Parse the LLM response into query, template, and variables."""
        default_template = "Found {count} matching tasks."
        default_vars = {"count": "len(results)"}
        
        try:
            # Extract query part
            query_parts = response.split("TEMPLATE:")
            if len(query_parts) < 2:
                return response.strip(), default_template, default_vars
                
            query = query_parts[0].replace("QUERY:", "").strip()
            
            # Extract template and variables
            remaining = query_parts[1]
            template_parts = remaining.split("VARIABLES:")
            
            if len(template_parts) < 2:
                return query, default_template, default_vars
                
            template = template_parts[0].strip()
            variables_str = template_parts[1].strip()
            
            try:
                variables = json.loads(variables_str)
                if not isinstance(variables, dict):
                    variables = default_vars
            except:
                variables = default_vars
            
            # Ensure count is present
            if "count" not in variables:
                variables["count"] = "len(results)"
                
            return query, template, variables
            
        except Exception as e:
            # If anything fails, return defaults
            return response.strip(), default_template, default_vars

    @staticmethod
    def build_query(question: str) -> Tuple[str, str, Dict]:
        """
        Build an SQL query and response template based on the user's question.
        Returns:
            Tuple[str, str, Dict]: SQL query, response template, and template variables
        """
        try:
            prompt = PromptTemplate(
                input_variables=["question", "table_info"],
                template=QueryPrompts.SQL_GENERATION_TEMPLATE
            )

            llm = OpenAI(temperature=0)
            chain = LLMChain(llm=llm, prompt=prompt)
            
            result = chain.run({
                "question": question,
                "table_info": QueryBuilder.TABLE_INFO
            })

            return QueryBuilder.parse_llm_response(result)
        except Exception as e:
            # Fallback to a basic query if LLM fails
            return (
                "SELECT * FROM tasks",
                "Found {count} tasks.",
                {"count": "len(results)"}
            )