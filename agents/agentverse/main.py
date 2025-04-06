import logging
import requests
import os
from typing import Optional
from fastapi import FastAPI
import uvicorn

class AgentverseConnector:
    def __init__(self):
        self.logger = logging.getLogger("agentverse")
        self.api_base = os.getenv("AGENTVERSE_API", "https://agentverse.fetch.ai")
        self.agent_id = None
        self.app = FastAPI()
        self._setup_endpoints()

    def _setup_endpoints(self):
        """Setup FastAPI endpoints for agent communication"""
        @self.app.get("/status")
        async def status():
            return {"status": "active"}

        @self.app.post("/nurture-lead")
        async def nurture_lead(lead_data: dict):
            # Placeholder for actual lead processing
            return {"status": "received"}

    def register(self) -> bool:
        """Register this agent with Agentverse"""
        try:
            response = requests.post(
                f"{self.api_base}/register",
                json={
                    "name": "SalesNurturer",
                    "endpoint": os.getenv("AGENT_ENDPOINT", "http://localhost:8000"),
                    "capabilities": ["lead_nurturing", "follow_up_scheduling"]
                }
            )
            response.raise_for_status()
            self.agent_id = response.json().get("agent_id")
            self.logger.info(f"Registered with Agentverse. ID: {self.agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Registration failed: {str(e)}")
            return False

    def discover_agents(self, capability: str) -> Optional[list]:
        """Discover other agents by capability"""
        try:
            response = requests.get(
                f"{self.api_base}/discover",
                params={"capability": capability}
            )
            response.raise_for_status()
            return response.json().get("agents", [])
        except Exception as e:
            self.logger.error(f"Discovery failed: {str(e)}")
            return None

    def run_server(self):
        """Run the agent's HTTP server"""
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=int(os.getenv("AGENT_PORT", 8000))
        )

def register_with_agentverse():
    """Convenience function for registration"""
    connector = AgentverseConnector()
    if not connector.register():
        raise RuntimeError("Agentverse registration failed")
    return connector

if __name__ == "__main__":
    # For testing agent server
    logging.basicConfig(level=logging.INFO)
    connector = AgentverseConnector()
    connector.register()
    connector.run_server()