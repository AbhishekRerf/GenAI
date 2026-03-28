"""
RAG Pipeline: Query → Embed → Retrieve → Generate
Main orchestration for Retrieval Augmented Generation
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils.chunked_search import ChunkedVectorSearch
from utils.llm_providers import AzureOpenAIProvider


class RAGPipeline:
    """Complete RAG pipeline: retrieve chunks + generate with LLM"""
    
    def __init__(
        self,
        llm_provider_name: str = "azure",
        search_top_k: int = 5,
        chunk_context_count: int = 2,
        **llm_kwargs
    ):
        """
        Initialize RAG pipeline
        
        Args:
            llm_provider_name: Azure provider name, defaults to "azure"
            search_top_k: Number of chunks to retrieve
            chunk_context_count: Top chunks per document to include in context
            **llm_kwargs: Provider-specific arguments
        """
        self.search_top_k = search_top_k
        self.chunk_context_count = chunk_context_count
        
        if llm_provider_name not in ["auto", "azure"]:
            raise ValueError(f"Unsupported provider: {llm_provider_name}. Only Azure OpenAI is enabled.")

        try:
            provider = AzureOpenAIProvider(**llm_kwargs)
            self.llm_provider = provider if provider.is_available() else None
        except Exception as e:
            raise ValueError(f"Failed to initialize Azure OpenAI provider: {e}")
        
        if not self.llm_provider:
            raise ValueError("Azure OpenAI is not available. Check your Azure OpenAI configuration.")
        
        self.conversation_history = []
    
    
    def _format_chunks_for_context(
        self,
        chunks: List[Dict[str, Any]],
        max_context_length: int = 6000,  # Increased for more context
        max_tokens: int = 10000  # Token limit
    ) -> str:
        """
        Format retrieved chunks into readable context
        
        Args:
            chunks: List of chunk results from Chr omaDB
            max_context_length: Maximum context length in characters
            
        Returns:
            Formatted context string
        """
        context_lines = []
        current_length = 0
        
        for i, chunk in enumerate(chunks, 1):
            chunk_text = chunk.get("chunk_text", "")
            score = chunk.get("similarity_score", 0)
            metadata = chunk.get("metadata", {})
            chunk_type = metadata.get("type", "unknown")
            
            # Format chunk with metadata
            formatted_chunk = f"""[Source {i} - {chunk_type.upper()} - Match: {score:.1%}]
{chunk_text}
"""
            
            chunk_length = len(formatted_chunk)
            
            if current_length + chunk_length > max_context_length:
                break
            
            context_lines.append(formatted_chunk)
            current_length += chunk_length
        
        if not context_lines:
            return "No relevant information found."
        
        return "\n".join(context_lines)
    
    
    def _build_system_prompt(self, query: str, context: str) -> str:
        """
        Build comprehensive system prompt with RAG context
        
        Args:
            query: User query
            context: Retrieved context from ChromaDB
            
        Returns:
            Full system prompt
        """
        system_prompt = f"""You are a helpful assistant for resource management queries.

You have access to the following relevant information from our database:

{context}

---

INSTRUCTIONS:
1. Answer based on the provided information above
2. If information is not in the context, say so clearly
3. Be specific and cite which source where applicable
4. For resource/project questions, reference the specific names/IDs
5. Keep answers concise but complete
6. If context seems incomplete or contradictory, mention that

USER QUERY: {query}
"""
        return system_prompt
    
    
    def _build_rag_prompt(
        self,
        query: str,
        search_results: Dict[str, List[Dict]]
    ) -> Tuple[str, str]:
        """
        Build system message with RAG context and user prompt
        
        Args:
            query: User query
            search_results: Results from ChunkedVectorSearch.search_all_chunks()
            
        Returns:
            Tuple of (system_message, user_prompt)
        """
        # Aggregate all chunks by source
        all_chunks = (
            search_results.get("resources", []) +
            search_results.get("projects", []) +
            search_results.get("assignments", [])
        )
        
        # Sort by similarity
        all_chunks = sorted(
            all_chunks,
            key=lambda x: x.get("similarity_score", 0),
            reverse=True
        )[:self.search_top_k]
        
        # Format context
        context = self._format_chunks_for_context(all_chunks)
        print(f"RAG context length: {len(context)} chars")
        
        # Build system prompt
        system_message = self._build_system_prompt(query, context)
        
        return system_message, query
    
    
    def generate(
        self,
        query: str,
        collection_type: str = "all",
        temperature: float = 0.7,
        return_context: bool = False
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: search → retrieve → generate
        
        Args:
            query: User query/prompt
            collection_type: "resources", "projects", "assignments", or "all"
            temperature: LLM temperature (0-1)
            return_context: Include retrieved context in response
            
        Returns:
            Dict with response and metadata
        """
        start_time = datetime.now()
        
        # Step 1: Retrieve relevant chunks
        if collection_type == "resources":
            search_results = {
                "resources": ChunkedVectorSearch.search_resource_chunks(query, self.search_top_k),
                "projects": [],
                "assignments": []
            }
        elif collection_type == "projects":
            search_results = {
                "resources": [],
                "projects": ChunkedVectorSearch.search_project_chunks(query, self.search_top_k),
                "assignments": []
            }
        elif collection_type == "assignments":
            search_results = {
                "resources": [],
                "projects": [],
                "assignments": ChunkedVectorSearch.search_assignment_chunks(query, self.search_top_k)
            }
        else:  # "all"
            search_results = ChunkedVectorSearch.search_all_chunks(query, self.search_top_k)
        
        # Step 2: Build RAG prompts
        system_message, user_prompt = self._build_rag_prompt(query, search_results)
        
        # Step 3: Generate structured response with LLM
        response = self.llm_provider.generate(
            prompt=user_prompt,
            system_message=system_message,
            temperature=temperature
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Add to conversation history
        self.conversation_history.append({
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build result
        result = {
            "query": query,
            "structured_response": response,  # Now JSON dict with IS_TABLEVIEW/IS_CHARTVIEW
            "llm_provider": self.llm_provider.name,
            "retrieval_stats": {
                "resources_found": len(search_results.get("resources", [])),
                "projects_found": len(search_results.get("projects", [])),
                "assignments_found": len(search_results.get("assignments", []))
            },
            "performance": {
                "elapsed_seconds": elapsed,
                "chunks_retrieved": sum(
                    len(v) for v in search_results.values() if isinstance(v, list)
                )
            }
        }
        
        if return_context:
            # Combine all chunks for context return
            all_chunks = (
                search_results.get("resources", []) +
                search_results.get("projects", []) +
                search_results.get("assignments", [])
            )
            all_chunks = sorted(
                all_chunks,
                key=lambda x: x.get("similarity_score", 0),
                reverse=True
            )[:self.search_top_k]
            
            result["context"] = {
                "sources": [{
                    "id": chunk.get("chunk_id"),
                    "similarity": chunk.get("similarity_score"),
                    "type": chunk.get("metadata", {}).get("type"),
                    "preview": chunk.get("chunk_text", "")[:100]
                } for chunk in all_chunks]
            }
        
        return result
    
    
    def chat(
        self,
        query: str,
        collection_type: str = "all",
        return_context: bool = False
    ) -> str:
        """
        Simple chat interface (returns just the response)
        
        Args:
            query: User query
            collection_type: Collection to search in
            return_context: Include context info
            
        Returns:
            Response text
        """
        result = self.generate(query, collection_type, return_context=return_context)
        return result.get("structured_response", "No response generated")
    
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


class RAGStats:
    """Statistics and analysis for RAG queries"""
    
    @staticmethod
    def analyze_response(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze RAG response quality
        
        Args:
            result: Result dict from RAGPipeline.generate()
            
        Returns:
            Analysis metrics
        """
        analysis = {
            "query_length": len(result.get("query", "")),
            "response_length": len(result.get("response", "")),
            "chunks_used": result.get("performance", {}).get("chunks_retrieved", 0),
            "latency_ms": result.get("performance", {}).get("elapsed_seconds", 0) * 1000,
            "has_sources": "context" in result,
            "source_types": list(set([
                c.get("type") for c in result.get("context", {}).get("sources", [])
            ])) if "context" in result else []
        }
        
        return analysis


# Example usage
if __name__ == "__main__":
    print("RAG Pipeline Example")
    print("=" * 60)
    
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline(
            llm_provider_name="azure",
            search_top_k=5,
            chunk_context_count=2
        )
        
        # Example queries
        queries = [
            "Which senior Python developers are available?",
            "What projects are currently in progress?",
            "Tell me about the e-commerce team",
        ]
        
        for query in queries:
            print(f"\n🔍 Query: {query}")
            print("-" * 60)
            
            result = rag.generate(
                query=query,
                collection_type="all",
                return_context=True
            )
            
            print(f"\n📝 Response:\n{result['response']}")
            print(f"\n📊 Stats:")
            print(f"   Provider: {result['llm_provider']}")
            print(f"   Resources: {result['retrieval_stats']['resources_found']}")
            print(f"   Projects: {result['retrieval_stats']['projects_found']}")
            print(f"   Time: {result['performance']['elapsed_seconds']:.2f}s")
            
            if "context" in result and result["context"]["sources"]:
                print(f"\n📚 Sources ({len(result['context']['sources'])}):")
                for i, source in enumerate(result["context"]["sources"][:3], 1):
                    print(f"   {i}. {source['type']} ({source['similarity']:.1%})")
    
    except Exception as e:
        print(f"Error: {e}")
        print("\nSetup required:")
        print("Configure Azure OpenAI credentials:")
        print("  - AZURE_OPENAI_API_KEY")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_MODEL")
