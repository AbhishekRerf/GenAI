"""
Text Chunking Strategies for Vector Embeddings
Split documents into optimized chunks for better search and embedding
"""
from typing import List, Dict, Any
import re
from typing import Optional


class TextChunker:
    """Different strategies to chunk text for embeddings"""
    
    @staticmethod
    def chunk_by_size(
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[str]:
        """
        Simple size-based chunking
        
        Args:
            text: Text to chunk
            chunk_size: Characters per chunk
            overlap: Overlapping characters between chunks
            
        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            
            # Move start position, accounting for overlap
            start = end - overlap
        
        return [c for c in chunks if c]  # Remove empty chunks
    
    
    @staticmethod
    def chunk_by_sentences(
        text: str,
        sentences_per_chunk: int = 5,
        overlap_sentences: int = 1
    ) -> List[str]:
        """
        Split by sentences for more semantic chunks
        
        Args:
            text: Text to chunk
            sentences_per_chunk: Number of sentences per chunk
            overlap_sentences: Overlapping sentences between chunks
            
        Returns:
            List of chunks
        """
        # Split into sentences (improved regex)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk - overlap_sentences):
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            chunk = ' '.join(chunk_sentences)
            chunks.append(chunk)
        
        return chunks
    
    
    @staticmethod
    def chunk_by_paragraphs(
        text: str,
        max_chars: int = 1000
    ) -> List[str]:
        """
        Chunk by paragraphs, merging small ones
        
        Args:
            text: Text to chunk
            max_chars: Maximum chunk size
            
        Returns:
            List of chunks
        """
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    
    @staticmethod
    def chunk_by_semantic_sections(
        text: str,
        max_chunk_size: int = 800
    ) -> List[str]:
        """
        Split by headers/sections and semantic boundaries
        Useful for structured documents
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum chunk size
            
        Returns:
            List of chunks
        """
        # Split by headers (markdown or text format)
        sections = re.split(r'\n#+\s+|^Title:|^Section:', text, flags=re.MULTILINE)
        sections = [s.strip() for s in sections if s.strip()]
        
        chunks = []
        for section in sections:
            if len(section) <= max_chunk_size:
                chunks.append(section)
            else:
                # If section is too large, chunk it further
                sub_chunks = TextChunker.chunk_by_sentences(section, sentences_per_chunk=5)
                chunks.extend(sub_chunks)
        
        return chunks
    
    
    @staticmethod
    def chunk_by_tokens_approximate(
        text: str,
        tokens_per_chunk: int = 256,  # Roughly 1024 chars
        overlap_tokens: int = 32
    ) -> List[str]:
        """
        Approximate token-based chunking (1 token ~ 4 chars)
        Better for embedding models with token limits
        
        Args:
            text: Text to chunk
            tokens_per_chunk: Tokens per chunk (~4 chars per token)
            overlap_tokens: Overlapping tokens
            
        Returns:
            List of chunks
        """
        # Approximate conversion: 1 token ≈ 4 characters
        char_size = tokens_per_chunk * 4
        char_overlap = overlap_tokens * 4
        
        return TextChunker.chunk_by_size(text, char_size, char_overlap)
    
    
    @staticmethod
    def smart_chunk(
        text: str,
        strategy: str = "hybrid",
        **kwargs
    ) -> List[str]:
        """
        Smart chunking that combines strategies
        
        Args:
            text: Text to chunk
            strategy: 'size', 'sentence', 'paragraph', 'semantic', 'token', 'hybrid'
            **kwargs: Additional arguments for chunking
            
        Returns:
            List of chunks
        """
        if strategy == "size":
            return TextChunker.chunk_by_size(text, **kwargs)
        elif strategy == "sentence":
            return TextChunker.chunk_by_sentences(text, **kwargs)
        elif strategy == "paragraph":
            return TextChunker.chunk_by_paragraphs(text, **kwargs)
        elif strategy == "semantic":
            return TextChunker.chunk_by_semantic_sections(text, **kwargs)
        elif strategy == "token":
            return TextChunker.chunk_by_tokens_approximate(text, **kwargs)
        elif strategy == "hybrid":
            # Try semantic first, fall back to sentences
            chunks = TextChunker.chunk_by_semantic_sections(text, max_chunk_size=800)
            if not chunks or all(len(c) > 1500 for c in chunks):
                chunks = TextChunker.chunk_by_sentences(text, sentences_per_chunk=5)
            return chunks
        else:
            return TextChunker.chunk_by_size(text)


class DocumentChunker:
    """Handle chunking of structured documents (resources, projects, etc.)"""
    
    @staticmethod
    def chunk_resource(resource: Dict[str, Any], max_chunk_size: int = 500) -> List[Dict]:
        """
        Chunk resource document into chunks while preserving metadata
        
        Args:
            resource: Resource document from MongoDB
            max_chunk_size: Max chars per chunk
            
        Returns:
            List of chunks with metadata
        """
        # Create resource description text
        text = f"""
Name: {resource['name']}
Email: {resource['email']}
Type: {resource['resource_type']}
Level: {resource['skill_level']}
Department: {resource['department']}
Hourly Rate: ${resource.get('hourly_rate', 0):.2f}
Status: {'Active' if resource.get('is_active') else 'Inactive'}

Skills:
{', '.join(resource.get('skills', []))}

Summary: A {resource['skill_level']} level {resource['resource_type']} from {resource['department']} 
with expertise in {', '.join(resource.get('skills', [])[:3])}.
"""
        
        # Chunk the text
        chunked_text = TextChunker.chunk_by_sentences(text, sentences_per_chunk=3)
        
        # Return chunks with preserved metadata
        chunks = []
        for i, chunk in enumerate(chunked_text):
            chunks.append({
                "chunk_id": f"res_{resource['_id']}_chunk_{i}",
                "resource_id": resource['_id'],
                "chunk_text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunked_text),
                "metadata": {
                    "type": "resource",
                    "name": resource['name'],
                    "resource_type": resource['resource_type'],
                    "skill_level": resource['skill_level'],
                    "department": resource['department'],
                    "skills": ','.join(resource.get('skills', []))
                }
            })
        
        return chunks
    
    
    @staticmethod
    def chunk_project(project: Dict[str, Any], max_chunk_size: int = 600) -> List[Dict]:
        """
        Chunk project document into chunks with metadata
        
        Args:
            project: Project document from MongoDB
            max_chunk_size: Max chars per chunk
            
        Returns:
            List of chunks with metadata
        """
        # Create project description text
        text = f"""
Project: {project['name']}

Client: {project['client_name']}
Status: {project['status']}
Budget: ${project.get('budget', 0):,.2f}

Description:
{project['description']}

Timeline:
Start: {project['start_date'].strftime('%Y-%m-%d')}
End: {project['end_date'].strftime('%Y-%m-%d')}

Type: Enterprise Project
Industry: Technology
Category: Development
"""
        
        # Chunk the text - projects are usually longer
        chunked_text = TextChunker.chunk_by_semantic_sections(text, max_chunk_size=800)
        
        chunks = []
        for i, chunk in enumerate(chunked_text):
            chunks.append({
                "chunk_id": f"proj_{project['_id']}_chunk_{i}",
                "project_id": project['_id'],
                "chunk_text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunked_text),
                "metadata": {
                    "type": "project",
                    "name": project['name'],
                    "status": project['status'],
                    "client": project['client_name'],
                    "budget": str(project.get('budget', 0))
                }
            })
        
        return chunks
    
    
    @staticmethod
    def chunk_assignment(
        assignment: Dict[str, Any],
        resource_name: str = None,
        project_name: str = None
    ) -> List[Dict]:
        """
        Chunk assignment document
        
        Args:
            assignment: Assignment document from MongoDB
            resource_name: Name of assigned resource
            project_name: Name of assigned project
            
        Returns:
            List of chunks with metadata
        """
        text = f"""
Assignment: {resource_name} to {project_name}

Role: {assignment['role']}
Allocation: {assignment['allocation_percentage']}%
Status: {'Active' if assignment.get('is_active') else 'Inactive'}

Timeline:
Start: {assignment['start_date'].strftime('%Y-%m-%d')}
End: {assignment['end_date'].strftime('%Y-%m-%d')}

Assignment Details:
The resource is assigned to this project in the role of {assignment['role']}.
They are allocated {assignment['allocation_percentage']}% of their time.
"""
        
        # Assignments are usually short, so no need for many chunks
        chunked_text = TextChunker.chunk_by_sentences(text, sentences_per_chunk=4)
        
        chunks = []
        for i, chunk in enumerate(chunked_text):
            chunks.append({
                "chunk_id": f"assign_{assignment['_id']}_chunk_{i}",
                "assignment_id": assignment['_id'],
                "chunk_text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunked_text),
                "metadata": {
                    "type": "assignment",
                    "resource_id": assignment['resource_id'],
                    "project_id": assignment['project_id'],
                    "role": assignment['role'],
                    "allocation": str(assignment['allocation_percentage'])
                }
            })
        
        return chunks


# Example usage
if __name__ == "__main__":
    # Test chunking strategies
    sample_text = """
    This is a sample document. It contains multiple sentences that need to be chunked.
    Chunking is important for creating embeddings. Different strategies work better for different use cases.
    Size-based chunking is simple but may break in the middle of sentences.
    Sentence-based chunking is better for semantic similarity. Paragraph-based chunking preserves structure.
    Token-based chunking respects embedding model limits. Semantic chunking understands document structure.
    The best strategy depends on your use case. Some documents benefit from multiple strategies.
    """
    
    print("=" * 60)
    print("CHUNKING STRATEGY COMPARISON")
    print("=" * 60)
    
    # Test different strategies
    strategies = [
        ("size", {"chunk_size": 100, "overlap": 20}),
        ("sentence", {"sentences_per_chunk": 2, "overlap_sentences": 0}),
        ("paragraph", {"max_chars": 200}),
        ("token", {"tokens_per_chunk": 128}),
    ]
    
    for strategy, kwargs in strategies:
        print(f"\n🔹 Strategy: {strategy.upper()}")
        chunks = TextChunker.smart_chunk(sample_text, strategy=strategy, **kwargs)
        print(f"   Chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            preview = chunk[:50].replace('\n', ' ') + "..."
            print(f"   {i}. {preview}")
