"""
Agentverse Connector Module

This module provides functionality for integrating with Fetch.ai's Agentverse.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.base_models import Agent
from ..utils.utils import generate_id, logger


class AgentverseConnector:
    """
    Main class for Agentverse integration.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Agentverse connector.
        
        Args:
            api_key: The Fetch.ai API key
            base_url: The Agentverse API base URL
        """
        self.api_key = api_key or os.getenv("FETCH_AI_API_KEY", "demo_key")
        self.base_url = base_url or os.getenv("FETCH_AI_BASE_URL", "https://agentverse.ai/api/v1")
        self.registered_agents = {}  # In a real system, this would be a database
        self.discovered_agents = {}  # Cache of discovered agents
    
    def register_agent(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register an agent with Agentverse.
        
        Args:
            name: The name of the agent
            description: A description of the agent
            capabilities: A list of agent capabilities
            metadata: Additional metadata for the agent (optional)
            
        Returns:
            The agent address in Agentverse
        """
        logger.info(f"Registering agent '{name}' with Agentverse")
        
        try:
            # In a real system, this would make an API call to Agentverse
            # For this implementation, we'll simulate the registration
            
            # Generate an agent ID and address
            agent_id = generate_id("agent")
            agent_address = f"fetch://{agent_id}"
            
            # Create an Agent object
            agent = Agent(
                id=agent_id,
                name=name,
                description=description,
                capabilities=capabilities,
                address=agent_address,
                metadata=metadata or {}
            )
            
            # Store the agent
            self.registered_agents[agent_id] = agent
            
            logger.info(f"Agent '{name}' registered successfully with address {agent_address}")
            
            return agent_address
        
        except Exception as e:
            logger.error(f"Error registering agent '{name}': {e}")
            raise
    
    def discover_agents(
        self,
        capabilities: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Agent]:
        """
        Discover agents in Agentverse.
        
        Args:
            capabilities: Filter by capabilities (optional)
            limit: Maximum number of agents to return
            
        Returns:
            A list of discovered agents
        """
        logger.info(f"Discovering agents with capabilities: {capabilities}")
        
        try:
            # In a real system, this would make an API call to Agentverse
            # For this implementation, we'll simulate the discovery
            
            # Create some mock agents for demonstration
            mock_agents = [
                Agent(
                    id="agent_crm_1",
                    name="Mock CRM Agent",
                    description="A mock CRM agent for demonstration",
                    capabilities=["crm", "contact_management"],
                    address="fetch://agent_crm_1",
                    metadata={"provider": "mock"}
                ),
                Agent(
                    id="agent_calendar_1",
                    name="Mock Calendar Agent",
                    description="A mock calendar agent for demonstration",
                    capabilities=["calendar", "scheduling"],
                    address="fetch://agent_calendar_1",
                    metadata={"provider": "mock"}
                ),
                Agent(
                    id="agent_email_1",
                    name="Mock Email Agent",
                    description="A mock email agent for demonstration",
                    capabilities=["email", "communication"],
                    address="fetch://agent_email_1",
                    metadata={"provider": "mock"}
                )
            ]
            
            # Add our registered agents
            all_agents = list(self.registered_agents.values()) + mock_agents
            
            # Filter by capabilities if provided
            if capabilities:
                filtered_agents = []
                for agent in all_agents:
                    if any(cap in agent.capabilities for cap in capabilities):
                        filtered_agents.append(agent)
                all_agents = filtered_agents
            
            # Limit the number of results
            all_agents = all_agents[:limit]
            
            # Cache the discovered agents
            for agent in all_agents:
                self.discovered_agents[agent.id] = agent
            
            logger.info(f"Discovered {len(all_agents)} agents")
            
            return all_agents
        
        except Exception as e:
            logger.error(f"Error discovering agents: {e}")
            return []
    
    def get_agent_info(self, agent_address: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_address: The agent address
            
        Returns:
            A dictionary with agent information, or None if not found
        """
        logger.info(f"Getting info for agent {agent_address}")
        
        try:
            # Extract agent ID from address
            agent_id = agent_address.replace("fetch://", "")
            
            # Check if we have this agent
            agent = self.registered_agents.get(agent_id) or self.discovered_agents.get(agent_id)
            
            if not agent:
                logger.warning(f"Agent {agent_address} not found")
                return None
            
            return agent.to_dict()
        
        except Exception as e:
            logger.error(f"Error getting agent info: {e}")
            return None
    
    def send_message_to_agent(
        self,
        sender_address: str,
        recipient_address: str,
        content: Dict[str, Any],
        message_type: str = "text"
    ) -> Optional[str]:
        """
        Send a message to another agent.
        
        Args:
            sender_address: The sender's agent address
            recipient_address: The recipient's agent address
            content: The message content
            message_type: The type of message
            
        Returns:
            The message ID if successful, None otherwise
        """
        logger.info(f"Sending message from {sender_address} to {recipient_address}")
        
        try:
            # In a real system, this would make an API call to Agentverse
            # For this implementation, we'll simulate the message sending
            
            # Generate a message ID
            message_id = generate_id("msg")
            
            # Log the message
            logger.info(f"Message sent successfully, message_id={message_id}")
            logger.debug(f"Message content: {content}")
            
            return message_id
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None


class AgentRegistrar:
    """
    Class for registering agents with Agentverse.
    """
    
    def __init__(self, connector: Optional[AgentverseConnector] = None):
        """
        Initialize the agent registrar.
        
        Args:
            connector: The Agentverse connector to use (optional)
        """
        self.connector = connector or AgentverseConnector()
    
    def register_sales_nurturer(
        self,
        name: str = "Sales Nurturer",
        description: str = "An agent for nurturing sales leads",
        additional_capabilities: Optional[List[str]] = None
    ) -> str:
        """
        Register a Sales Nurturer agent with Agentverse.
        
        Args:
            name: The name of the agent
            description: A description of the agent
            additional_capabilities: Additional capabilities beyond the default ones
            
        Returns:
            The agent address in Agentverse
        """
        logger.info(f"Registering Sales Nurturer agent '{name}' with Agentverse")
        
        # Define default capabilities
        capabilities = [
            "lead_nurturing",
            "email_personalization",
            "follow_up_scheduling",
            "engagement_tracking"
        ]
        
        # Add additional capabilities if provided
        if additional_capabilities:
            capabilities.extend(additional_capabilities)
        
        # Register the agent
        return self.connector.register_agent(
            name=name,
            description=description,
            capabilities=capabilities,
            metadata={
                "agent_type": "sales_nurturer",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            }
        )


class AgentDiscoverer:
    """
    Class for discovering agents in Agentverse.
    """
    
    def __init__(self, connector: Optional[AgentverseConnector] = None):
        """
        Initialize the agent discoverer.
        
        Args:
            connector: The Agentverse connector to use (optional)
        """
        self.connector = connector or AgentverseConnector()
    
    def discover_crm_agents(self, limit: int = 5) -> List[Agent]:
        """
        Discover CRM agents in Agentverse.
        
        Args:
            limit: Maximum number of agents to return
            
        Returns:
            A list of discovered CRM agents
        """
        logger.info("Discovering CRM agents")
        
        return self.connector.discover_agents(
            capabilities=["crm", "contact_management"],
            limit=limit
        )
    
    def discover_calendar_agents(self, limit: int = 5) -> List[Agent]:
        """
        Discover calendar agents in Agentverse.
        
        Args:
            limit: Maximum number of agents to return
            
        Returns:
            A list of discovered calendar agents
        """
        logger.info("Discovering calendar agents")
        
        return self.connector.discover_agents(
            capabilities=["calendar", "scheduling"],
            limit=limit
        )
    
    def discover_email_agents(self, limit: int = 5) -> List[Agent]:
        """
        Discover email agents in Agentverse.
        
        Args:
            limit: Maximum number of agents to return
            
        Returns:
            A list of discovered email agents
        """
        logger.info("Discovering email agents")
        
        return self.connector.discover_agents(
            capabilities=["email", "communication"],
            limit=limit
        )
