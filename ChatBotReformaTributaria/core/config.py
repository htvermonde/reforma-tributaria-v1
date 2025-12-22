import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    # --- INICIO VARIÁVEIS DA RAG_TOOL
    RAG_API_URL: str = os.getenv("RAG_API_URL")
    RAG_REQUEST_TIMEOUT: float = float(os.getenv("RAG_REQUEST_TIMEOUT", 60.0))
    RAG_QUANTITY: int = int(os.getenv("RAG_QUANTITY", 5))
    RAG_THRESHOLD_SIMILARITY: float = float(os.getenv("RAG_THRESHOLD_SIMILARITY", 0.3))
    RAG_USE_CHUNK_CHAIN: bool = os.getenv("RAG_USE_CHUNK_CHAIN", "False")
    
    # --- INDEXES DOS PROJETOS
    RAG_INDEX_ID_QUERY_ENGINE: str = os.getenv("RAG_INDEX_ID_QUERY_ENGINE")
    

settings = Settings()