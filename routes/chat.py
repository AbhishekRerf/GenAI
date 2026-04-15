from fastapi import APIRouter, HTTPException
from models.schemas import ChatQuery, ChatResponse, Document
from utils.db import get_mongodb, get_chroma_collection
from utils.rag import rag_query, add_to_vector_store
from bson.objectid import ObjectId
import uuid

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatQuery):
    """
    Main chat endpoint - receives query and returns AI-generated answer with sources
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Perform RAG query
        result = await rag_query(request.message)
        
        response = ChatResponse(
            answer=result['answer'],  # Structured table/chart JSON
            session_id=session_id
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/add-document")
async def add_document(doc: Document):
    """
    Add a new document to MongoDB and Vector DB
    """
    try:
        db = await get_mongodb()
        
        # Insert into MongoDB
        result = await db.documents.insert_one(doc.dict())
        document_id = str(result.inserted_id)
        
        # Add to vector store (ChromaDB)
        add_to_vector_store(
            document_id=document_id,
            title=doc.title,
            content=doc.content,
            metadata={
                "category": doc.category,
                "tags": ",".join(doc.tags)
            }
        )
        
        return {"id": document_id, "message": "Document added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding document: {str(e)}")

@router.get("/documents")
async def get_documents(skip: int = 0, limit: int = 10):
    """
    Retrieve all documents from MongoDB
    """
    try:
        db = await get_mongodb()
        documents = await db.documents.find().skip(skip).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc['_id'] = str(doc['_id'])
        
        return {"documents": documents, "skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """
    Retrieve a specific document
    """
    try:
        db = await get_mongodb()
        document = await db.documents.find_one({"_id": ObjectId(doc_id)})
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document['_id'] = str(document['_id'])
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document: {str(e)}")

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document from MongoDB and Vector DB
    """
    try:
        db = await get_mongodb()
        result = await db.documents.delete_one({"_id": ObjectId(doc_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Also remove from vector store
        from utils.rag import remove_from_vector_store
        remove_from_vector_store(doc_id)
        
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/search")
async def search_documents(query: str, skip: int = 0, limit: int = 10):
    """
    Search documents in MongoDB by title, content, or tags
    """
    try:
        db = await get_mongodb()
        search_regex = {"$regex": query, "$options": "i"}
        
        documents = await db.documents.find(
            {
                "$or": [
                    {"title": search_regex},
                    {"content": search_regex},
                    {"tags": search_regex}
                ]
            }
        ).skip(skip).limit(limit).to_list(length=limit)
        
        for doc in documents:
            doc['_id'] = str(doc['_id'])
        
        return {"documents": documents, "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")
