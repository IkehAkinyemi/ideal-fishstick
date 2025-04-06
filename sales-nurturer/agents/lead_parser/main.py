import pandas as pd
import pdfplumber
from typing import List, Dict
import hashlib
import chromadb  # Lightweight vector DB for hackathon

class LeadParser:
    def __init__(self):
        # Initialize ChromaDB in-memory for demo
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("leads")
        
    def process_input(self, file_path: str) -> List[Dict]:
        """Main entry point - handles CSV/PDF automatically"""
        if file_path.endswith('.csv'):
            return self._process_csv(file_path)
        elif file_path.endswith('.pdf'):
            return self._process_pdf(file_path)
        else:
            raise ValueError("Unsupported file format")

    def _process_csv(self, file_path: str) -> List[Dict]:
        """Process CSV files with mandatory fields validation"""
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_columns = {'name', 'industry', 'contact'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        # Clean data
        df = df.where(pd.notnull(df), None)
        leads = df.to_dict('records')
        
        # Store in vector DB
        self._store_leads(leads)
        return leads

    def _process_pdf(self, file_path: str) -> List[Dict]:
        """Extract text from PDF and structure as lead data"""
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])
        
        # Simple PDF parsing (customize per your PDF structure)
        lead = {
            'name': self._extract_field(text, 'Name:'),
            'industry': self._extract_field(text, 'Industry:'),
            'contact': self._extract_field(text, 'Email:'),
            'raw_text': text  # Store full text as fallback
        }
        
        self._store_leads([lead])
        return [lead]

    def _extract_field(self, text: str, prefix: str) -> str:
        """Helper to extract fields from text lines"""
        for line in text.split('\n'):
            if line.startswith(prefix):
                return line.replace(prefix, '').strip()
        return ""

    def _store_leads(self, leads: List[Dict]) -> None:
        """Store leads in vector DB with hashed IDs"""
        documents = []
        metadatas = []
        ids = []
        
        for lead in leads:
            # Generate consistent ID from lead data
            lead_id = hashlib.sha256(str(lead).encode()).hexdigest()[:20]
            documents.append(str(lead))  # Store full lead as document
            metadatas.append(lead)      # Metadata for filtering
            ids.append(lead_id)
        
        # Batch upsert to ChromaDB
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

# Example usage (for testing)
if __name__ == "__main__":
    parser = LeadParser()
    
    # Test CSV processing
    csv_leads = parser.process_input("data/leads/sample.csv")
    print(f"Processed {len(csv_leads)} CSV leads")
    
    # Test PDF processing
    pdf_lead = parser.process_input("data/leads/sample.pdf")
    print(f"Processed PDF lead: {pdf_lead[0]['name']}")