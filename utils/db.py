import os
import chromadb
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize global variables
mongodb_client: AsyncIOMotorClient = None
mongodb: AsyncIOMotorDatabase = None
chroma_client = None
embedding_model = None

async def init_mongodb():
    """Initialize MongoDB Connection"""
    global mongodb_client, mongodb
    
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "genai_bot")
    
    try:
        mongodb_client = AsyncIOMotorClient(mongodb_uri)
        mongodb = mongodb_client[database_name]
        
        # Test connection
        await mongodb.command("ping")
        
        # Create indexes for better performance
        await mongodb.documents.create_index("title")
        await mongodb.documents.create_index("category")
        await mongodb.documents.create_index("tags")
        
        print(f"✓ Connected to MongoDB: {database_name}")
    except Exception as e:
        print(f"⚠ MongoDB connection failed: {str(e)}")
        print(f"⚠ MongoDB features will be disabled. You can:")
        print(f"  1. Start MongoDB with: mongod")
        print(f"  2. Use MongoDB Atlas: https://www.mongodb.com/cloud/atlas")
        print(f"  3. Set MONGODB_URI environment variable")
        mongodb_client = None
        mongodb = None

async def get_mongodb():
    """Get MongoDB instance"""
    if mongodb is None:
        raise Exception("MongoDB is not connected. Start MongoDB or set MONGODB_URI environment variable.")
    return mongodb

async def close_mongodb():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("MongoDB connection closed")

def init_chroma():
    """Initialize Chroma Vector DB"""
    global chroma_client, embedding_model
    
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    # Initialize embedding model ONCE (cache it)
    if embedding_model is None:
        print("📦 Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Embedding model cached")
    
    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    
    # Get or create collection
    collection = chroma_client.get_or_create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )
    
    print("✓ Chroma Vector DB initialized successfully!")
    return chroma_client

def get_chroma_collection():
    """Get Chroma collection"""
    if not chroma_client:
        init_chroma()
    return chroma_client.get_collection(name="documents")

def get_embedding_model():
    """Get embedding model"""
    if not embedding_model:
        init_chroma()
    return embedding_model
