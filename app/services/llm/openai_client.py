from langchain_openai import ChatOpenAI

def get_llm():
    """Initialize and return the OpenAI LLM client."""
    return ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0
    )