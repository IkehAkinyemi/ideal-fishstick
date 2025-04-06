import os
import json
import logging
import atexit
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOpenAI

from ...utils.storage import VectorDB
from ...agents.notifier.main import Notifier

class SalesNurturer:
    def __init__(self):
        # Initialize core components
        self.logger = self._setup_logging()
        self.notifier = Notifier()
        self.vector_db = VectorDB()
        self.llm = self._init_llm()
        self.scheduler = self._init_scheduler()
        
        # Configuration
        self.engagement_config = {
            'min_open_rate': 0.3,
            'min_reply_rate': 0.1,
            'negative_keywords': ['unsubscribe', 'not interested', 'stop'],
            'conversion_cooldown': 30  # days
        }
        
        # Templates and prompts
        self._load_prompts()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for nurturer"""
        logger = logging.getLogger("sales_nurturer")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("data/nurturer.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def _init_llm(self):
        """Initialize language model with safety checks"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=api_key
        )

    def _init_scheduler(self):
        """Initialize scheduler with persistent storage"""
        scheduler = BackgroundScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(
                    url='sqlite:///data/scheduler.db'
                )
            },
            timezone="UTC"
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
        return scheduler

    def _load_prompts(self):
        """Load LLM prompt templates"""
        self.plan_prompt = ChatPromptTemplate.from_template("""
            As a sales nurturing assistant, create a follow-up plan for:
            
            Lead: {lead_details}
            Business Type: {business_type}
            Last Contact: {last_contact}
            
            Recent Interactions:
            {interaction_history}
            
            Available Templates:
            {available_templates}
            
            Generate JSON with:
            - strategy: "aggressive"|"moderate"|"conservative"
            - steps: List[{
                "days_after": int,
                "channel": "email"|"slack",
                "template": str,
                "conditions": str
            }]
            """)

    def create_nurture_plan(self, lead: Dict) -> Dict:
        """
        Create and schedule a nurture plan for a lead
        Args:
            lead: Dictionary containing lead data
        Returns:
            Dict containing the generated plan
        """
        try:
            if self._should_skip(lead):
                self.logger.info(f"Skipping lead {lead.get('id')} - not qualified")
                return {"status": "skipped"}
            
            plan = self._generate_plan(lead)
            self._schedule_plan(lead, plan)
            
            self.logger.info(f"Created plan for lead {lead.get('id')}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Plan creation failed: {str(e)}")
            raise

    def _should_skip(self, lead: Dict) -> bool:
        """Determine if lead should be skipped"""
        if lead.get('status') == 'unsubscribed':
            return True
            
        if lead.get('last_conversion'):
            last_conv = datetime.fromisoformat(lead['last_conversion'])
            if (datetime.now() - last_conv).days < self.engagement_config['conversion_cooldown']:
                return True
                
        return False

    def _generate_plan(self, lead: Dict) -> Dict:
        """Generate follow-up plan using LLM"""
        try:
            context = {
                "lead_details": json.dumps(lead),
                "business_type": os.getenv("BUSINESS_TYPE", "B2B"),
                "last_contact": lead.get('last_contact', 'unknown'),
                "interaction_history": self._get_interaction_summary(lead['id']),
                "available_templates": self._get_template_list()
            }
            
            chain = self.plan_prompt | self.llm | JsonOutputParser()
            plan = chain.invoke(context)
            
            # Validate plan structure
            if not all(k in plan for k in ['strategy', 'steps']):
                raise ValueError("Invalid plan format from LLM")
                
            return plan
            
        except Exception as e:
            self.logger.error(f"Plan generation failed: {str(e)}")
            return self._get_fallback_plan()

    def _get_interaction_summary(self, lead_id: str) -> str:
        """Get formatted interaction history"""
        interactions = self.vector_db.query(
            collection="interactions",
            filter={"lead_id": lead_id},
            limit=3
        )
        return "\n".join(
            f"{i['metadata']['action']} ({i['metadata']['timestamp']})"
            for i in interactions
        )

    def _get_template_list(self) -> str:
        """Get available templates as string"""
        templates = self.vector_db.query(
            collection="templates",
            query_text="",
            limit=100
        )
        return "\n".join(t['metadata']['name'] for t in templates)

    def _get_fallback_plan(self) -> Dict:
        """Default plan when generation fails"""
        return {
            "strategy": "conservative",
            "steps": [{
                "days_after": 7,
                "channel": "email",
                "template": "general_followup",
                "conditions": "if no negative response"
            }]
        }

    def _schedule_plan(self, lead: Dict, plan: Dict) -> None:
        """Schedule all follow-up steps"""
        last_date = datetime.fromisoformat(lead.get('last_contact', datetime.now().isoformat()))
        
        for step in plan['steps']:
            trigger_date = last_date + timedelta(days=step['days_after'])
            self._schedule_step(lead, step, trigger_date)
            last_date = trigger_date

    def _schedule_step(self, lead: Dict, step: Dict, trigger_date: datetime) -> str:
        """Schedule single follow-up step"""
        job_id = f"{lead['id']}_{step['template']}_{trigger_date.timestamp()}"
        
        self.scheduler.add_job(
            func=self._execute_followup,
            args=(lead, step),
            trigger='date',
            run_date=trigger_date,
            id=job_id,
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        return job_id

    def _execute_followup(self, lead: Dict, step: Dict) -> None:
        """Execute scheduled follow-up"""
        try:
            if self._should_skip(lead):
                self.logger.info(f"Skipping execution for lead {lead['id']}")
                return
                
            message = self._generate_message(lead, step)
            result = self.notifier.deliver(
                message=message,
                recipient=lead['contact'],
                method=step['channel'],
                subject=f"Follow up: {lead.get('name', '')}",
                lead_id=lead['id']
            )
            
            self._log_interaction(
                lead_id=lead['id'],
                action=f"{step['channel']}_sent",
                content=message,
                **result
            )
            
        except Exception as e:
            self.logger.error(f"Follow-up failed: {str(e)}")

    def _generate_message(self, lead: Dict, step: Dict) -> str:
        """Generate message from template"""
        template = self._get_template(step['template'])
        return template['content'].format(
            name=lead.get('name', ''),
            our_name=os.getenv("BUSINESS_NAME", "Our Team"),
            tracking_pixel='{tracking_pixel}'
        )

    def _get_template(self, name: str) -> Dict:
        """Retrieve template from storage"""
        result = self.vector_db.query(
            collection="templates",
            filter={"name": name},
            limit=1
        )
        if not result:
            return {
                "content": f"Hi {name},\n\nFollowing up.\n\nRegards,\n{os.getenv('BUSINESS_NAME', 'Our Team')}",
                "is_html": False
            }
        return result[0]['metadata']

    def _log_interaction(self, lead_id: str, action: str, **data):
        """Log interaction to database"""
        self.vector_db.upsert(
            documents=[data.get('content', '')],
            metadatas=[{
                "lead_id": lead_id,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                **data
            }],
            collection="interactions"
        )

# Example usage
if __name__ == "__main__":
    # Test configuration
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    os.environ["BUSINESS_NAME"] = "Test Corp"
    
    # Sample lead
    test_lead = {
        "id": "lead_123",
        "name": "John Doe",
        "contact": "john@example.com",
        "last_contact": datetime.now().isoformat(),
        "industry": "Technology"
    }
    
    nurturer = SalesNurturer()
    plan = nurturer.create_nurture_plan(test_lead)
    print(f"Created plan: {json.dumps(plan, indent=2)}")