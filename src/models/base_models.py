"""
Base models for the Lead Nurturing System.

This module defines the core data models used throughout the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class LeadSource(Enum):
    """Enum representing the source of a lead."""
    CSV = "csv"
    PDF = "pdf"
    API = "api"
    MANUAL = "manual"


class EngagementType(Enum):
    """Enum representing types of lead engagement."""
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    EMAIL_REPLY = "email_reply"
    WEBSITE_VISIT = "website_visit"
    FORM_SUBMISSION = "form_submission"
    MEETING_SCHEDULED = "meeting_scheduled"
    CUSTOM = "custom"


class NotificationChannel(Enum):
    """Enum representing notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    LOG = "log"


class LeadStatus(Enum):
    """Enum representing the status of a lead."""
    NEW = "new"
    NURTURING = "nurturing"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    CLOSED_LOST = "closed_lost"
    ON_HOLD = "on_hold"


@dataclass
class Lead:
    """Represents a lead in the system."""
    id: str
    first_name: str
    last_name: str
    email: str
    company_name: str
    job_title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    source: LeadSource = LeadSource.MANUAL
    status: LeadStatus = LeadStatus.NEW
    pain_points: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def full_name(self) -> str:
        """Get the full name of the lead."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the lead to a dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "industry": self.industry,
            "company_size": self.company_size,
            "phone": self.phone,
            "website": self.website,
            "source": self.source.value,
            "status": self.status.value,
            "pain_points": self.pain_points,
            "interests": self.interests,
            "notes": self.notes,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Create a lead from a dictionary."""
        # Handle enum conversions
        if "source" in data and isinstance(data["source"], str):
            data["source"] = LeadSource(data["source"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = LeadStatus(data["status"])
        
        # Handle datetime conversions
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)


@dataclass
class EngagementEvent:
    """Represents an engagement event from a lead."""
    id: str
    lead_id: str
    event_type: EngagementType
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the engagement event to a dictionary."""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EngagementEvent':
        """Create an engagement event from a dictionary."""
        # Handle enum conversions
        if "event_type" in data and isinstance(data["event_type"], str):
            data["event_type"] = EngagementType(data["event_type"])
        
        # Handle datetime conversions
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        return cls(**data)


@dataclass
class MessageTemplate:
    """Represents a message template for lead nurturing."""
    id: str
    name: str
    subject: str
    body: str
    channel: NotificationChannel
    variables: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message template to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel.value,
            "variables": self.variables,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageTemplate':
        """Create a message template from a dictionary."""
        # Handle enum conversions
        if "channel" in data and isinstance(data["channel"], str):
            data["channel"] = NotificationChannel(data["channel"])
        
        # Handle datetime conversions
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)


@dataclass
class FollowUp:
    """Represents a scheduled follow-up for a lead."""
    id: str
    lead_id: str
    template_id: str
    scheduled_time: datetime
    channel: NotificationChannel
    status: str = "scheduled"  # scheduled, sent, failed, cancelled
    personalized_subject: Optional[str] = None
    personalized_body: Optional[str] = None
    trigger: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the follow-up to a dictionary."""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "template_id": self.template_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "channel": self.channel.value,
            "status": self.status,
            "personalized_subject": self.personalized_subject,
            "personalized_body": self.personalized_body,
            "trigger": self.trigger,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FollowUp':
        """Create a follow-up from a dictionary."""
        # Handle enum conversions
        if "channel" in data and isinstance(data["channel"], str):
            data["channel"] = NotificationChannel(data["channel"])
        
        # Handle datetime conversions
        if "scheduled_time" in data and isinstance(data["scheduled_time"], str):
            data["scheduled_time"] = datetime.fromisoformat(data["scheduled_time"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "sent_at" in data and isinstance(data["sent_at"], str) and data["sent_at"]:
            data["sent_at"] = datetime.fromisoformat(data["sent_at"])
        
        return cls(**data)


@dataclass
class NurturePlan:
    """Represents a nurture plan for a lead."""
    id: str
    lead_id: str
    name: str
    description: str
    follow_ups: List[str] = field(default_factory=list)  # List of follow-up IDs
    status: str = "active"  # active, completed, paused
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the nurture plan to a dictionary."""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "name": self.name,
            "description": self.description,
            "follow_ups": self.follow_ups,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NurturePlan':
        """Create a nurture plan from a dictionary."""
        # Handle datetime conversions
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)


@dataclass
class Agent:
    """Represents an agent in the Agentverse."""
    id: str
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "address": self.address,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create an agent from a dictionary."""
        # Handle datetime conversions
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        return cls(**data)
