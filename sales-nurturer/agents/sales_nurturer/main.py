import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from utils.storage import VectorDB
from agents.notifier.main import Notifier
import atexit

class SalesNurturer:
    def __init__(self):
        # Initialize scheduler
        self.scheduler = BackgroundScheduler(
            jobstores={
                'default': SQLAlchemyJobStore(
                    url='sqlite:///data/scheduler.db'
                )
            },
            timezone="UTC"
        )
        self.scheduler.start()
        atexit.register(self._shutdown_scheduler)

        # Initialize components
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.notifier = Notifier()
        self.vector_db = VectorDB()
        self.logger = logging.getLogger("nurturer")

        # Engagement thresholds
        self.engagement_config = {
            'min_open_rate': 0.3,  # 30%
            'min_reply_rate': 0.1,  # 10%
            'negative_keywords': ['unsubscribe', 'not interested', 'stop'],
            'conversion_cooldown': 30  # days
        }

        self._load_prompts()

    def _shutdown_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.logger.info("Scheduler shut down")

    def _load_prompts(self):
        """Initialize LLM prompt templates"""
        self.plan_prompt = ChatPromptTemplate.from_template("""
              You're a sales nurturing assistant. Create a personalized follow-up plan based on:

              Lead Details: {lead_details}
              Business Type: {business_type}
              Engagement Rules: {engagement_rules}

              Recent Interactions:
              {history}

              Available Templates:
              {templates}

              Generate a JSON plan with:
              - strategy: "aggressive"|"moderate"|"conservative" (based on engagement)
              - steps: [{
                  "days_after_previous": int,
                  "channel": "email"|"slack",
                  "template_name": str,
                  "trigger_conditions": str,
                  "require_open": bool (wait for open before next step?),
                  "require_reply": bool (require reply to continue?)
              }]

              Rules:
              1. If open rate < min_open_rate, use "conservative" strategy
              2. If reply rate < min_reply_rate, space steps further apart
              3. Never suggest more than 5 steps
              4. Always include template_name from available templates
              """)
        
        self.message_prompt = ChatPromptTemplate.from_template("""
            [Previous template remains exactly the same]
            """)

    def create_nurture_plan(self, lead: Dict) -> Dict:
        """Generate and schedule follow-up plan"""
        try:
            plan = self._generate_plan(lead)
            self._schedule_plan(lead, plan)
            return plan
        except Exception as e:
            self.logger.error(f"Plan creation failed: {str(e)}")
            raise

    # --- Engagement Tracking Methods ---
    def _should_skip(self, lead: Dict) -> bool:
        """Determine if follow-up should be skipped"""
        lead_id = lead['id']
        
        if self._is_unsubscribed(lead):
            return True
            
        if self._recently_converted(lead):
            return True
            
        if not self._meets_engagement(lead_id):
            return True
            
        if self._detected_negative(lead_id):
            return True
            
        return False

    def _is_unsubscribed(self, lead: Dict) -> bool:
        """Check for explicit opt-out"""
        return lead.get('status') == 'unsubscribed'

    def _recently_converted(self, lead: Dict) -> bool:
        """Check conversion cooldown period"""
        last_conversion = lead.get('last_conversion')
        if not last_conversion:
            return False
        return (datetime.now() - last_conversion).days < self.engagement_config['conversion_cooldown']

    def _meets_engagement(self, lead_id: str) -> bool:
        """Check engagement thresholds"""
        interactions = self._get_lead_interactions(lead_id)
        if not interactions:
            return False
            
        stats = {'sent': 0, 'opened': 0, 'replied': 0}
        for interaction in interactions:
            stats['sent'] += 1
            stats['opened'] += int(interaction.get('opened', False))
            stats['replied'] += int(interaction.get('replied', False))
        
        open_rate = stats['opened'] / stats['sent']
        reply_rate = stats['replied'] / stats['sent']
        
        return (open_rate >= self.engagement_config['min_open_rate'] and 
                reply_rate >= self.engagement_config['min_reply_rate'])

    def _detected_negative(self, lead_id: str) -> bool:
        """Check for negative signals"""
        interactions = self._get_lead_interactions(lead_id, limit=5)
        for interaction in interactions:
            content = interaction.get('content', '').lower()
            if any(kw in content for kw in self.engagement_config['negative_keywords']):
                return True
        return False

    def _get_lead_interactions(self, lead_id: str, limit: int = 100) -> List[Dict]:
        """Retrieve lead's interaction history"""
        return self.vector_db.query(
            query_text="",
            collection="interactions",
            filter={"lead_id": lead_id},
            limit=limit
        )

    # --- Scheduling Core ---
    def _schedule_plan(self, lead: Dict, plan: Dict) -> None:
        """Schedule all follow-up steps"""
        last_contact = self._parse_date(lead.get('last_contact'))
        
        for step in plan['steps']:
            trigger_date = last_contact + timedelta(days=step['days_after_previous'])
            self._schedule_step(lead, step, trigger_date)
            last_contact = trigger_date

    def _schedule_step(self, lead: Dict, step: Dict, trigger_date: datetime) -> str:
        """Schedule single follow-up"""
        job_id = f"{lead['id']}_{step['template_name']}_{trigger_date.timestamp()}"
        
        self.scheduler.add_job(
            func=self._execute_followup,
            args=(lead, step),
            trigger='date',
            run_date=trigger_date,
            id=job_id,
            misfire_grace_time=3600
        )
        return job_id

    def _execute_followup(self, lead: Dict, step: Dict) -> None:
        """Execute scheduled follow-up"""
        if self._should_skip(lead):
            self.logger.info(f"Skipping follow-up for {lead['id']}")
            return
            
        message = self._generate_message(lead, step)
        result = self.notifier.deliver(
            message=message,
            recipient=lead['contact'],
            method=step['channel']
        )
        
        self._log_interaction(
            lead_id=lead['id'],
            action=f"{step['channel']}_sent",
            content=message,
            **result
        )

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string with fallback to now"""
        try:
            return datetime.fromisoformat(date_str) if date_str else datetime.now()
        except ValueError:
            return datetime.now()

    def _log_interaction(self, lead_id: str, action: str, content: str, **metrics):
        """Log interaction with engagement metrics"""
        self.vector_db.upsert(
            documents=[content],
            metadatas=[{
                "lead_id": lead_id,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                **metrics
            }],
            collection="interactions"
        )

    def _generate_message(self, lead: Dict, step: Dict) -> str:
        """Generate message with tracking pixel"""
        template = self._get_template(step['template_name'])
        
        template_vars = {
            **lead,
            'our_name': os.getenv("BUSINESS_NAME", "Our Team"),
            'tracking_pixel': '{tracking_pixel}'  # Placeholder
        }
        
        message = template['content'].format(**template_vars)
        
        return message

    def _get_relevant_templates(self, industry: str, pain_points: str) -> List[Dict]:
        """Retrieve templates matching lead context from JSON files"""
        templates = []
        template_dir = "data/templates"
        
        try:
            # Scan template directory
            for filename in os.listdir(template_dir):
                if filename.endswith(".json"):
                    with open(f"{template_dir}/{filename}") as f:
                        template = json.load(f)
                        
                        # Basic industry matching
                        if template["industry"].lower() == industry.lower():
                            templates.append(template)
            
            # Fallback if no industry matches
            if not templates:
                default_path = f"{template_dir}/general_followup.json"
                with open(default_path) as f:
                    templates.append(json.load(f))
                    
        except Exception as e:
            self.logger.error(f"Template load failed: {str(e)}")
            # Hardcoded fallback
            templates = [{
                "name": "emergency_fallback",
                "content": "Hi {name},\n\nFollowing up on our conversation.\n\nRegards,\n{our_name}",
                "industry": "general",
                "trigger": "fallback"
            }]
        
        return templates

    def _generate_plan(self, lead: Dict) -> Dict:
        """Generate personalized follow-up sequence with engagement awareness"""
        try:
            # Get lead context
            lead_id = lead["id"]
            history = self._get_lead_interactions(lead_id)
            templates = self._get_relevant_templates(
                lead.get("industry", ""),
                lead.get("pain_points", "")
            )

            # Build LLM prompt context
            context = {
                "lead_details": json.dumps({
                    "name": lead.get("name", ""),
                    "industry": lead.get("industry", ""),
                    "pain_points": lead.get("pain_points", []),
                    "last_contact": lead.get("last_contact", "")
                }),
                "business_type": os.getenv("BUSINESS_TYPE", "B2B"),
                "history": "\n".join([
                    f"{i['action']} ({i.get('timestamp')}): "
                    f"{'Opened' if i.get('opened') else ''}"
                    f"{'Replied' if i.get('replied') else ''}"
                    for i in history[-3:]  # Last 3 interactions
                ]),
                "templates": "\n".join(
                    f"{t['name']}:\n{t['content']}" 
                    for t in templates
                ),
                "engagement_rules": json.dumps({
                    "min_open_rate": self.engagement_config['min_open_rate'],
                    "min_reply_rate": self.engagement_config['min_reply_rate']
                })
            }

            # Generate plan via LLM
            plan_chain = (
                self.plan_prompt 
                | self.llm 
                | JsonOutputParser()
            )
            plan = plan_chain.invoke(context)
            
            # Add engagement awareness to steps
            for step in plan["steps"]:
                step["engagement_checks"] = {
                    "require_open": step.get("require_open", True),
                    "require_reply": step.get("require_reply", False),
                    "skip_if_negative": True
                }
            
            return plan

        except Exception as e:
            self.logger.error(f"Plan generation failed: {str(e)}")
            # Return conservative default plan
            return {
                "strategy": "conservative",
                "steps": [{
                    "days_after_previous": 7,
                    "channel": "email",
                    "template_name": "default_followup",
                    "trigger_conditions": "If no negative response"
                }]
            }

    def _generate_message(self, lead: Dict, step: Dict) -> str:
        """Generate message with tracking pixel"""
        template = self._get_template(step['template_name'])
        
        # Prepare template variables
        template_vars = {
            **lead,
            'our_name': os.getenv("BUSINESS_NAME", "Our Team"),
            'tracking_pixel': '{tracking_pixel}'  # Placeholder
        }
        
        # Render template
        message = template['content'].format(**template_vars)
        
        return message