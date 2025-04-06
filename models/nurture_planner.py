from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOpenAI
from typing import Dict, List
import json
import logging
import os

class NurturePlanner:
    def __init__(self):
        self.logger = self._setup_logging()
        self.llm = self._init_llm()
        self.parser = JsonOutputParser()
        self.prompts = self._init_prompts()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for planner"""
        logger = logging.getLogger("nurture_planner")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("data/planner.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def _init_llm(self) -> ChatOpenAI:
        """Initialize language model with validation"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,  # Lower for more deterministic business responses
            api_key=api_key
        )

    def _init_prompts(self) -> Dict[str, ChatPromptTemplate]:
        """Initialize all prompt templates"""
        return {
            "plan": ChatPromptTemplate.from_template("""
                You are a sales nurturing expert creating follow-up sequences.
                
                Business Context:
                - Company: {business_name}
                - Industry: {business_industry}
                - Product: {product_type}
                
                Lead Details:
                {lead_details}
                
                Recent Interactions:
                {interaction_history}
                
                Available Templates:
                {available_templates}
                
                Create a JSON nurture plan with:
                - "strategy": "aggressive"|"moderate"|"conservative"
                - "steps": [
                    {{
                        "days_after": int (days since last contact),
                        "channel": "email"|"slack",
                        "template": str (template name),
                        "customization": {{
                            "key_points": list[str],
                            "urgency_level": "high"|"medium"|"low"
                        }},
                        "conditions": str (conditions to check before sending)
                    }}
                ]
                
                Rules:
                1. Never suggest more than 5 steps
                2. Space steps appropriately based on strategy
                3. Always use available templates
                4. Include lead's pain points in customization
                """),
                
            "message": ChatPromptTemplate.from_template("""
                Customize this template for the lead:
                
                Template: {template_content}
                
                Lead Details:
                {lead_details}
                
                Customization Instructions:
                {customization}
                
                Output the fully customized message exactly as it should be sent.
                """)
        }

    def generate_plan(self, context: Dict) -> Dict:
        """
        Generate a personalized nurture plan
        Args:
            context: {
                "business_name": str,
                "business_industry": str,
                "product_type": str,
                "lead_details": Dict,
                "interaction_history": str,
                "available_templates": str
            }
        Returns:
            Dict containing the generated plan
        """
        try:
            # Validate input context
            required_keys = {
                'business_name', 'business_industry', 
                'product_type', 'lead_details',
                'interaction_history', 'available_templates'
            }
            if not required_keys.issubset(context.keys()):
                missing = required_keys - set(context.keys())
                raise ValueError(f"Missing context keys: {missing}")

            # Generate plan via LLM
            chain = self.prompts["plan"] | self.llm | self.parser
            plan = chain.invoke(context)
            
            # Validate plan structure
            self._validate_plan(plan)
            
            self.logger.info(f"Generated plan for {context['lead_details'].get('name')}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Plan generation failed: {str(e)}")
            return self._get_fallback_plan(context)

    def customize_message(self, template: str, lead: Dict, customization: Dict) -> str:
        """
        Customize a template message for a specific lead
        Args:
            template: Raw template content
            lead: Lead details dictionary
            customization: Customization instructions from plan
        Returns:
            Fully customized message string
        """
        try:
            chain = self.prompts["message"] | self.llm
            return chain.invoke({
                "template_content": template,
                "lead_details": json.dumps(lead),
                "customization": json.dumps(customization)
            }).content
            
        except Exception as e:
            self.logger.error(f"Message customization failed: {str(e)}")
            return template  # Fallback to original

    def _validate_plan(self, plan: Dict) -> None:
        """Validate plan structure and rules"""
        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")
            
        if "steps" not in plan:
            raise ValueError("Plan missing 'steps' key")
            
        if len(plan["steps"]) > 5:
            raise ValueError("Plan exceeds maximum 5 steps")
            
        for step in plan["steps"]:
            if not all(k in step for k in ["days_after", "channel", "template"]):
                raise ValueError("Invalid step structure")

    def _get_fallback_plan(self, context: Dict) -> Dict:
        """Default plan when generation fails"""
        return {
            "strategy": "conservative",
            "steps": [{
                "days_after": 7,
                "channel": "email",
                "template": "general_followup",
                "customization": {
                    "key_points": ["following up"],
                    "urgency_level": "low"
                },
                "conditions": "if no negative response"
            }]
        }

# Example usage
if __name__ == "__main__":
    # Test configuration
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    
    # Test context
    test_context = {
        "business_name": "Acme Corp",
        "business_industry": "Technology",
        "product_type": "CRM Software",
        "lead_details": {
            "name": "John Doe",
            "company": "Tech Solutions",
            "pain_points": ["data organization", "team collaboration"]
        },
        "interaction_history": "Initial call on 2023-01-01",
        "available_templates": ["general", "technical", "urgent"]
    }
    
    planner = NurturePlanner()
    plan = planner.generate_plan(test_context)
    print("Generated Plan:")
    print(json.dumps(plan, indent=2))
    
    # Test message customization
    template = "Hi {name}, we can help with {pain_points}!"
    message = planner.customize_message(
        template=template,
        lead=test_context["lead_details"],
        customization={"key_points": ["data management"], "urgency_level": "medium"}
    )
    print("\nCustomized Message:")
    print(message)