"""
Main application module for the Lead Nurturing System.

This module provides the main entry point for the application.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.lead_parser.lead_parser import create_lead_parser
from src.sales_nurturer.sales_nurturer import SalesNurturer
from src.notifier.notifier import create_notifier
from src.agentverse_connector.agentverse_connector import AgentRegistrar, AgentDiscoverer, AgentverseConnector
from src.models.base_models import Lead, MessageTemplate, NotificationChannel
from src.utils.utils import load_json_file, save_json_file, logger


def parse_leads(source_path: str, source_type: str) -> List[Lead]:
    """
    Parse leads from a source.
    
    Args:
        source_path: Path to the source
        source_type: Type of source (csv, pdf, api)
        
    Returns:
        A list of parsed leads
    """
    logger.info(f"Parsing leads from {source_path} ({source_type})")
    
    try:
        # Create a parser for the source type
        parser = create_lead_parser(source_type)
        
        # Parse the source
        leads = parser.parse_source(source_path)
        
        logger.info(f"Parsed {len(leads)} leads from {source_path}")
        
        return leads
    
    except Exception as e:
        logger.error(f"Error parsing leads: {e}")
        return []


def load_templates(templates_dir: str) -> List[MessageTemplate]:
    """
    Load message templates from a directory.
    
    Args:
        templates_dir: Path to the templates directory
        
    Returns:
        A list of message templates
    """
    logger.info(f"Loading templates from {templates_dir}")
    
    templates = []
    
    try:
        # Get all JSON files in the directory
        template_files = [f for f in os.listdir(templates_dir) if f.endswith(".json")]
        
        for file_name in template_files:
            file_path = os.path.join(templates_dir, file_name)
            
            try:
                # Load the template data
                template_data = load_json_file(file_path)
                
                # Create a MessageTemplate object
                template = MessageTemplate.from_dict(template_data)
                
                templates.append(template)
                
                logger.info(f"Loaded template '{template.name}' from {file_name}")
            
            except Exception as e:
                logger.error(f"Error loading template from {file_name}: {e}")
        
        logger.info(f"Loaded {len(templates)} templates")
        
        return templates
    
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        return []


def create_nurture_plans(leads: List[Lead], templates: List[MessageTemplate]) -> Dict[str, Any]:
    """
    Create nurture plans for leads.
    
    Args:
        leads: The leads to nurture
        templates: The message templates to use
        
    Returns:
        A dictionary with information about the created nurture plans
    """
    logger.info(f"Creating nurture plans for {len(leads)} leads")
    
    # Create a sales nurturer
    nurturer = SalesNurturer()
    
    # Create nurture plans for each lead
    plans = []
    
    for lead in leads:
        try:
            # Create a nurture plan for the lead
            plan = nurturer.create_nurture_plan(lead, templates)
            
            plans.append(plan)
            
            logger.info(f"Created nurture plan {plan.id} for lead {lead.id}")
        
        except Exception as e:
            logger.error(f"Error creating nurture plan for lead {lead.id}: {e}")
    
    logger.info(f"Created {len(plans)} nurture plans")
    
    return {
        "success": True,
        "plans_created": len(plans),
        "plan_ids": [plan.id for plan in plans]
    }


def register_with_agentverse(name: str, description: str) -> Dict[str, Any]:
    """
    Register the Sales Nurturer with Agentverse.
    
    Args:
        name: The name for the agent
        description: A description of the agent
        
    Returns:
        A dictionary with information about the registration
    """
    logger.info(f"Registering with Agentverse as '{name}'")
    
    try:
        # Create an agent registrar
        registrar = AgentRegistrar()
        
        # Register the Sales Nurturer
        agent_address = registrar.register_sales_nurturer(name, description)
        
        logger.info(f"Registered with Agentverse, address={agent_address}")
        
        return {
            "success": True,
            "agent_address": agent_address
        }
    
    except Exception as e:
        logger.error(f"Error registering with Agentverse: {e}")
        
        return {
            "success": False,
            "error": str(e)
        }


def discover_agents() -> Dict[str, Any]:
    """
    Discover agents in Agentverse.
    
    Returns:
        A dictionary with information about discovered agents
    """
    logger.info("Discovering agents in Agentverse")
    
    try:
        # Create an agent discoverer
        discoverer = AgentDiscoverer()
        
        # Discover agents
        crm_agents = discoverer.discover_crm_agents()
        calendar_agents = discoverer.discover_calendar_agents()
        email_agents = discoverer.discover_email_agents()
        
        logger.info(f"Discovered {len(crm_agents)} CRM agents, {len(calendar_agents)} calendar agents, and {len(email_agents)} email agents")
        
        return {
            "success": True,
            "crm_agents": [agent.to_dict() for agent in crm_agents],
            "calendar_agents": [agent.to_dict() for agent in calendar_agents],
            "email_agents": [agent.to_dict() for agent in email_agents]
        }
    
    except Exception as e:
        logger.error(f"Error discovering agents: {e}")
        
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Lead Nurturing System")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Parser for the 'parse' command
    parse_parser = subparsers.add_parser("parse", help="Parse leads from a source")
    parse_parser.add_argument("--source", required=True, help="Path to the source")
    parse_parser.add_argument("--type", required=True, choices=["csv", "pdf", "api"], help="Type of source")
    parse_parser.add_argument("--output", help="Path to save parsed leads (JSON)")
    
    # Parser for the 'nurture' command
    nurture_parser = subparsers.add_parser("nurture", help="Create nurture plans for leads")
    nurture_parser.add_argument("--leads", required=True, help="Path to leads file (JSON)")
    nurture_parser.add_argument("--templates", required=True, help="Path to templates directory")
    nurture_parser.add_argument("--output", help="Path to save nurture plans (JSON)")
    
    # Parser for the 'register' command
    register_parser = subparsers.add_parser("register", help="Register with Agentverse")
    register_parser.add_argument("--name", default="Sales Nurturer", help="Name for the agent")
    register_parser.add_argument("--description", default="An agent for nurturing sales leads", help="Description of the agent")
    
    # Parser for the 'discover' command
    discover_parser = subparsers.add_parser("discover", help="Discover agents in Agentverse")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == "parse":
        # Parse leads
        leads = parse_leads(args.source, args.type)
        
        # Save leads if output path is provided
        if args.output:
            try:
                # Convert leads to dictionaries
                lead_dicts = [lead.to_dict() for lead in leads]
                
                # Save to file
                save_json_file(lead_dicts, args.output)
                
                logger.info(f"Saved {len(leads)} leads to {args.output}")
            
            except Exception as e:
                logger.error(f"Error saving leads: {e}")
        
        # Print summary
        print(f"Parsed {len(leads)} leads from {args.source}")
    
    elif args.command == "nurture":
        try:
            # Load leads
            lead_dicts = load_json_file(args.leads)
            leads = [Lead.from_dict(lead_dict) for lead_dict in lead_dicts]
            
            # Load templates
            templates = load_templates(args.templates)
            
            # Create nurture plans
            result = create_nurture_plans(leads, templates)
            
            # Print result
            print(json.dumps(result, indent=2))
        
        except Exception as e:
            logger.error(f"Error in nurture command: {e}")
            print(f"Error: {e}")
    
    elif args.command == "register":
        # Register with Agentverse
        result = register_with_agentverse(args.name, args.description)
        
        # Print result
        print(json.dumps(result, indent=2))
    
    elif args.command == "discover":
        # Discover agents
        result = discover_agents()
        
        # Print result
        print(json.dumps(result, indent=2))
    
    else:
        # No command specified, print help
        parser.print_help()


if __name__ == "__main__":
    main()
