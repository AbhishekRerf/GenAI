import os
from dotenv import load_dotenv
from utils.llm_providers import AzureOpenAIProvider

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI provider
_provider = None

def get_llm_provider():
    global _provider
    if _provider is None:
        try:
            provider = AzureOpenAIProvider()
            _provider = provider   # ✅ proper indentation
        except Exception as e:
            print(f"Azure OpenAI initialization failed: {str(e)}")
            _provider = None
    return _provider

def generate_answer(query: str, context: str) -> str:
    """
    Generate answer using Azure OpenAI
    
    Args:
        query: User's question
        context: Retrieved context from vector DB
    
    Returns:
        Generated answer from LLM
    """
    provider = get_llm_provider()
    if not provider:
        return "Error: Azure OpenAI is not available. Please verify your Azure OpenAI configuration."
    
    system_message = """You are a helpful AI assistant. Use the provided context to answer the user's question accurately. 
If the context doesn't contain relevant information, say so clearly."""
    
    prompt = f"""Context:
{context}

User's Question: {query}

Please provide a clear and concise answer based on the context."""

    try:
        response = provider.generate(
            prompt=prompt,
            system_message=system_message,
            temperature=0.7,
            max_tokens=2048
        )
        return response
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return f"Sorry, I couldn't generate a response. Error: {str(e)}"

def generate_system_prompt(documents_summary: str) -> str:
    """Generate a system prompt based on available documents"""
    return f"""You are an AI assistant with knowledge from these documents: {documents_summary}
    Help users by providing accurate information from your knowledge base."""
