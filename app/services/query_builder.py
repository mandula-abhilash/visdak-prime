# query_builder.py
from langchain_community.llms import OpenAI  # Updated import
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

class QueryBuilder:
    @staticmethod
    def build_query(question: str, table_info: str) -> str:
        """
        Build an SQL query based on the user's question and table schema information.
        """
        prompt = PromptTemplate(
            input_variables=["question", "table_info"],
            template=(
                "You are an expert at writing SQL queries. Given the following table schema:\n"
                "{table_info}\n\n"
                "Write an SQL query to answer this question:\n"
                "{question}\n"
            ),
        )
        llm = OpenAI(temperature=0, model_name="gpt-4")  # Ensure correct model is used
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run({"question": question, "table_info": table_info})
