"""
Vector Store - ChromaDB integration for semantic search
FIXED: Compatible with ChromaDB 0.5.x API
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """ChromaDB-based vector store for document embeddings."""
    
    def __init__(
        self,
        persist_dir: str = "./data/chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "documents"
    ):
        self.persist_dir = persist_dir
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        self._init_embeddings()
        self._init_chroma()
    
    def _init_embeddings(self):
        """Initialize sentence transformer embeddings."""
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"Loading embedding model: {self.embedding_model_name}...")
        self.embedder = SentenceTransformer(self.embedding_model_name)
        logger.info(f"✅ Loaded embedding model: {self.embedding_model_name}")
    
    def _init_chroma(self):
        """Initialize ChromaDB client and collection - compatible with 0.5.x"""
        import chromadb
        from chromadb.config import Settings
        
        # Use Settings API for ChromaDB 0.5.x
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"✅ Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(self.collection_name)
            logger.info(f"✅ Created new collection: {self.collection_name}")
    
    def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        if doc_id is None:
            doc_id = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        logger.info(f"Creating embedding for document...")
        embedding = self.embedder.encode(text).tolist()
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}]
        )
        
        logger.info(f"✅ Added document: {doc_id}")
        return doc_id
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        logger.info(f"Creating embeddings for {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(chunk['text'].encode()).hexdigest()[:16]
            ids.append(chunk_id)
            
            embedding = self.embedder.encode(chunk['text']).tolist()
            embeddings.append(embedding)
            
            documents.append(chunk['text'])
            
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': i,
                'page': chunk.get('page', 1)
            })
            metadatas.append(chunk_metadata)
        
        logger.info(f"Adding {len(ids)} chunks to vector store...")
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"✅ Added {len(ids)} chunks")
        return ids
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Searching for: {query[:50]}...")
        
        query_embedding = self.embedder.encode(query).tolist()
        
        # Build where clause for ChromaDB 0.5.x
        where_clause = None
        if filter_dict:
            where_clause = filter_dict
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results - handle ChromaDB 0.5.x response format
        matches = []
        if results and results.get('ids') and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                match = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i] if results.get('documents') else '',
                    'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                }
                
                # Add distance/score if available
                if results.get('distances'):
                    distance = results['distances'][0][i]
                    match['distance'] = distance
                    match['score'] = 1.0 - distance  # Convert to similarity score
                
                matches.append(match)
        
        logger.info(f"✅ Found {len(matches)} results")
        return matches
    
    def delete_document(self, doc_id: str) -> None:
        self.collection.delete(ids=[doc_id])
        logger.info(f"Deleted document: {doc_id}")
    
    def reset(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        
        self.collection = self.client.create_collection(self.collection_name)
        logger.info(f"Reset collection: {self.collection_name}")
    
    def count(self) -> int:
        """Return number of documents in collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.warning(f"Failed to get collection count: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'embedding_model': self.embedding_model_name,
                'persist_directory': self.persist_dir,
                'status': 'OK'
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'collection_name': self.collection_name,
                'document_count': 0,
                'embedding_model': self.embedding_model_name,
                'persist_directory': self.persist_dir,
                'status': f'Error: {str(e)}',
                'error': str(e)
            }
