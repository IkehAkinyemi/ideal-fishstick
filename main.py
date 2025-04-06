import os
import logging
from agents.lead_parser import LeadParser
from agents.sales_nurturer import SalesNurturer
from agents.agentverse import register_with_agentverse
from utils.storage import VectorDB

def setup_logging():
    """Configure root logger"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("data/pipeline.log"),
            logging.StreamHandler()
        ]
    )

def process_leads(file_path: str):
    """Full processing pipeline for leads"""
    logger = logging.getLogger("pipeline")
    
    try:
        # Initialize components
        lead_parser = LeadParser()
        nurturer = SalesNurturer()
        db = VectorDB()
        
        logger.info(f"Processing leads from {file_path}")
        
        # 1. Parse leads
        leads = lead_parser.process_input(file_path)
        logger.info(f"Parsed {len(leads)} leads")
        
        # 2. Store in VectorDB
        for lead in leads:
            db.upsert(
                documents=[str(lead)],
                metadatas=[lead],
                ids=[lead['id']]
            )
        logger.info("Leads stored in VectorDB")
        
        # 3. Create nurture plans
        for lead in leads:
            plan = nurturer.create_nurture_plan(lead)
            logger.info(f"Created plan for lead {lead['id']}: {plan['strategy']}")
        
        # 4. Register with Agentverse
        if os.getenv("ENABLE_AGENTVERSE", "false").lower() == "true":
            register_with_agentverse()
            logger.info("Registered with Agentverse")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    setup_logging()
    process_leads("data/leads/sample.csv")