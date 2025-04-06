import chromadb
from chromadb.config import Settings
import json
import os
from typing import List, Dict, Optional
import logging

class VectorDB:
    def __init__(self, persist_dir: str = "data/vector_db"):
        self.logger = self._setup_logging()
        self.client = chromadb.Client(self._get_settings(persist_dir))
        self.collections = self._init_collections()
        self._preload_templates()  # New template loading

    def _get_settings(self, persist_dir: str) -> Settings:
        """Configure ChromaDB settings"""
        os.makedirs(persist_dir, exist_ok=True)
        return Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir
        )

    def _setup_logging(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger("vector_db")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("data/vector_db.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def _init_collections(self) -> Dict[str, chromadb.Collection]:
        """Initialize required collections"""
        return {
            "leads": self.client.get_or_create_collection(
                name="leads",
                metadata={"hnsw:space": "cosine"}
            ),
            "templates": self.client.get_or_create_collection(
                name="templates",
                metadata={"hnsw:space": "cosine"}
            ),
            "interactions": self.client.get_or_create_collection(
                name="interactions",
                metadata={"hnsw:space": "cosine"}
            )
        }

    def _preload_templates(self):
        """Load template data from files during initialization"""
        template_dir = "data/templates"
        if not os.path.exists(template_dir):
            self.logger.warning(f"Template directory {template_dir} not found")
            return

        loaded_count = 0
        for filename in os.listdir(template_dir):
            if not filename.endswith('.json'):
                continue

            try:
                with open(os.path.join(template_dir, filename)) as f:
                    template = json.load(f)
                
                # Generate consistent ID from template name
                template_id = f"template_{template['name']}"
                
                self.collections["templates"].upsert(
                    documents=[template["content"]],
                    metadatas=[{
                        "name": template["name"],
                        "industry": template.get("industry", "general"),
                        "is_html": template.get("is_html", False),
                        "trigger": template.get("trigger", "standard")
                    }],
                    ids=[template_id]
                )
                loaded_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to load template {filename}: {str(e)}")

        self.logger.info(f"Preloaded {loaded_count} templates")
    
    def upsert(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str],
        collection: str = "leads"
    ) -> bool:
        """
        Store documents with metadata and embeddings
        Returns True if successful
        """
        try:
            # Validate inputs
            if not all([documents, metadatas, ids]):
                raise ValueError("Missing required fields")
            if len({len(documents), len(metadatas), len(ids)}) != 1:
                raise ValueError("All input lists must be same length")
            
            # Add timestamp if not present
            for meta in metadatas:
                if "timestamp" not in meta:
                    meta["timestamp"] = datetime.now().isoformat()
            
            # Insert into ChromaDB
            self.collections[collection].upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Upserted {len(ids)} items to {collection}")
            return True
            
        except Exception as e:
            self.logger.error(f"Upsert failed: {str(e)}")
            raise
    
    def get_lead(self, lead_id: str) -> Dict:
        """Retrieve a single lead with all metadata"""
        try:
            result = self.collections["leads"].get(
                ids=[lead_id],
                include=["metadatas", "documents"]
            )
            
            if not result["ids"]:
                raise ValueError(f"Lead {lead_id} not found")
                
            return {
                **result["metadatas"][0],
                "content": result["documents"][0]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            raise
    
    def get_template(self, template_name: str) -> str:
        """Retrieve template content by name"""
        try:
            result = self.collections["templates"].get(
                where={"name": template_name},
                include=["documents"]
            )
            
            if not result["ids"]:
                raise ValueError(f"Template {template_name} not found")
                
            return result["documents"][0]
            
        except Exception as e:
            self.logger.error(f"Failed to get template {template_name}: {str(e)}")
            raise
    
    def query(
        self,
        query_text: str,
        collection: str = "leads",
        filter: Optional[Dict] = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Semantic search with optional metadata filtering
        Returns list of {content, metadata, score} dicts
        """
        try:
            results = self.collections[collection].query(
                query_texts=[query_text],
                n_results=limit,
                where=filter,
                include=["metadatas", "documents", "distances"]
            )
            
            return [{
                "content": doc,
                "metadata": meta,
                "score": 1 - dist  # Convert distance to similarity score
            } for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )]
            
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise
    
    def delete(self, ids: List[str], collection: str) -> bool:
        """Delete items by ID"""
        try:
            self.collections[collection].delete(ids=ids)
            self.logger.info(f"Deleted {len(ids)} items from {collection}")
            return True
        except Exception as e:
            self.logger.error(f"Delete failed: {str(e)}")
            raise
    
    def backup(self, file_path: str = "data/vector_db_backup.json") -> bool:
        """Export all data to JSON file"""
        try:
            backup_data = {}
            for col_name, collection in self.collections.items():
                data = collection.get(include=["documents", "metadatas", "ids"])
                backup_data[col_name] = data
            
            with open(file_path, "w") as f:
                json.dump(backup_data, f, indent=2)
                
            self.logger.info(f"Backup saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize with test data
    db = VectorDB()
    
    # Test upsert
    db.upsert(
        documents=["Test lead document content"],
        metadatas=[{
            "name": "Test Lead",
            "industry": "Restaurant",
            "contact": "test@example.com"
        }],
        ids=["test_lead_1"]
    )
    
    # Test query
    results = db.query(
        query_text="restaurant",
        collection="leads"
    )
    print(f"Query results: {json.dumps(results, indent=2)}")
    
    # Test get
    lead = db.get_lead("test_lead_1")
    print(f"Retrieved lead: {lead['name']}")