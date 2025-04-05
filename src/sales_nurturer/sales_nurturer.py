"""
Sales Nurturer Module

This module provides functionality for nurturing leads through personalized follow-ups.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..models.base_models import (
    Lead, FollowUp, MessageTemplate, NurturePlan, 
    EngagementEvent, EngagementType, NotificationChannel, LeadStatus
)
from ..utils.utils import generate_id, logger


class MessagePersonalizer:
    """
    Class for personalizing message templates.
    """
    
    def personalize_message(
        self, 
        template: MessageTemplate, 
        lead: Lead
    ) -> Tuple[str, str]:
        """
        Personalize a message template for a specific lead.
        
        Args:
            template: The message template to personalize
            lead: The lead to personalize the message for
            
        Returns:
            A tuple of (personalized_subject, personalized_body)
        """
        logger.info(f"Personalizing template '{template.name}' for lead {lead.id}")
        
        # Create a dictionary of variables to replace
        variables = {
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "full_name": lead.full_name,
            "email": lead.email,
            "company_name": lead.company_name,
            "job_title": lead.job_title or "",
            "industry": lead.industry or "",
            "company_size": lead.company_size or "",
            "phone": lead.phone or "",
            "website": lead.website or "",
        }
        
        # Add custom fields
        for key, value in lead.custom_fields.items():
            variables[key] = value
        
        # Personalize subject
        personalized_subject = template.subject
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in personalized_subject:
                personalized_subject = personalized_subject.replace(placeholder, str(var_value))
        
        # Personalize body
        personalized_body = template.body
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in personalized_body:
                personalized_body = personalized_body.replace(placeholder, str(var_value))
        
        return personalized_subject, personalized_body


class FollowUpScheduler:
    """
    Class for scheduling follow-ups.
    """
    
    def schedule_follow_up(
        self,
        lead: Lead,
        template: MessageTemplate,
        scheduled_time: datetime,
        trigger: Optional[str] = None
    ) -> FollowUp:
        """
        Schedule a follow-up for a lead.
        
        Args:
            lead: The lead to schedule the follow-up for
            template: The message template to use
            scheduled_time: When to send the follow-up
            trigger: What triggered this follow-up (optional)
            
        Returns:
            The scheduled follow-up
        """
        logger.info(f"Scheduling follow-up for lead {lead.id} at {scheduled_time}")
        
        # Personalize the message
        personalizer = MessagePersonalizer()
        personalized_subject, personalized_body = personalizer.personalize_message(template, lead)
        
        # Create the follow-up
        follow_up = FollowUp(
            id=generate_id("followup"),
            lead_id=lead.id,
            template_id=template.id,
            scheduled_time=scheduled_time,
            channel=template.channel,
            status="scheduled",
            personalized_subject=personalized_subject,
            personalized_body=personalized_body,
            trigger=trigger
        )
        
        # In a real system, this would add the follow-up to a database
        # and schedule it with a task scheduler like APScheduler
        logger.info(f"Created follow-up {follow_up.id} for lead {lead.id}")
        
        return follow_up


class EngagementTracker:
    """
    Class for tracking lead engagement.
    """
    
    def __init__(self):
        """Initialize the engagement tracker."""
        self.engagement_events = []  # In a real system, this would be a database
    
    def track_engagement(
        self,
        lead: Lead,
        event_type: EngagementType,
        details: Optional[Dict[str, Any]] = None
    ) -> EngagementEvent:
        """
        Track an engagement event for a lead.
        
        Args:
            lead: The lead who engaged
            event_type: The type of engagement
            details: Additional details about the engagement (optional)
            
        Returns:
            The created engagement event
        """
        logger.info(f"Tracking {event_type.value} engagement for lead {lead.id}")
        
        # Create the engagement event
        event = EngagementEvent(
            id=generate_id("event"),
            lead_id=lead.id,
            event_type=event_type,
            details=details or {}
        )
        
        # In a real system, this would add the event to a database
        self.engagement_events.append(event)
        
        logger.info(f"Created engagement event {event.id} for lead {lead.id}")
        
        return event
    
    def get_engagement_count(
        self,
        lead: Lead,
        event_type: Optional[EngagementType] = None,
        since: Optional[datetime] = None
    ) -> int:
        """
        Get the number of engagement events for a lead.
        
        Args:
            lead: The lead to check
            event_type: Filter by event type (optional)
            since: Only count events since this time (optional)
            
        Returns:
            The number of engagement events
        """
        count = 0
        
        for event in self.engagement_events:
            if event.lead_id != lead.id:
                continue
            
            if event_type and event.event_type != event_type:
                continue
            
            if since and event.timestamp < since:
                continue
            
            count += 1
        
        return count
    
    def check_escalation_criteria(self, lead: Lead) -> bool:
        """
        Check if a lead meets the criteria for escalation to human intervention.
        
        Args:
            lead: The lead to check
            
        Returns:
            True if the lead should be escalated, False otherwise
        """
        # Example escalation criteria:
        # - 3+ email replies
        # - 2+ meeting requests
        # - Any form submission
        
        # Check email replies
        reply_count = self.get_engagement_count(
            lead, 
            event_type=EngagementType.EMAIL_REPLY,
            since=datetime.now() - timedelta(days=30)  # Last 30 days
        )
        if reply_count >= 3:
            logger.info(f"Lead {lead.id} meets escalation criteria: 3+ email replies")
            return True
        
        # Check meeting requests
        meeting_count = self.get_engagement_count(
            lead,
            event_type=EngagementType.MEETING_SCHEDULED,
            since=datetime.now() - timedelta(days=30)  # Last 30 days
        )
        if meeting_count >= 2:
            logger.info(f"Lead {lead.id} meets escalation criteria: 2+ meeting requests")
            return True
        
        # Check form submissions
        form_count = self.get_engagement_count(
            lead,
            event_type=EngagementType.FORM_SUBMISSION
        )
        if form_count >= 1:
            logger.info(f"Lead {lead.id} meets escalation criteria: form submission")
            return True
        
        return False


class SalesNurturer:
    """
    Main class for nurturing leads.
    """
    
    def __init__(self):
        """Initialize the sales nurturer."""
        self.scheduler = FollowUpScheduler()
        self.engagement_tracker = EngagementTracker()
        self.nurture_plans = {}  # In a real system, this would be a database
    
    def create_nurture_plan(
        self,
        lead: Lead,
        templates: List[MessageTemplate],
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> NurturePlan:
        """
        Create a nurture plan for a lead.
        
        Args:
            lead: The lead to nurture
            templates: The message templates to use
            name: Name for the nurture plan (optional)
            description: Description of the nurture plan (optional)
            
        Returns:
            The created nurture plan
        """
        logger.info(f"Creating nurture plan for lead {lead.id}")
        
        # Generate a name if not provided
        if not name:
            name = f"Nurture Plan for {lead.full_name}"
        
        # Generate a description if not provided
        if not description:
            description = f"Automated nurture plan for {lead.full_name} from {lead.company_name}"
        
        # Create the nurture plan
        plan = NurturePlan(
            id=generate_id("plan"),
            lead_id=lead.id,
            name=name,
            description=description,
            follow_ups=[],
            status="active"
        )
        
        # Schedule follow-ups
        now = datetime.now()
        
        # In a real system, the timing would be more sophisticated
        # and based on the lead's engagement and the template's purpose
        for i, template in enumerate(templates):
            # Schedule each template with increasing delay
            delay_days = (i + 1) * 3  # 3, 6, 9, ... days
            scheduled_time = now + timedelta(days=delay_days)
            
            follow_up = self.scheduler.schedule_follow_up(
                lead=lead,
                template=template,
                scheduled_time=scheduled_time,
                trigger="nurture_plan_creation"
            )
            
            plan.follow_ups.append(follow_up.id)
        
        # In a real system, this would add the plan to a database
        self.nurture_plans[plan.id] = plan
        
        logger.info(f"Created nurture plan {plan.id} for lead {lead.id} with {len(plan.follow_ups)} follow-ups")
        
        return plan
    
    def handle_engagement_event(
        self,
        lead: Lead,
        event_type: EngagementType,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle an engagement event from a lead.
        
        Args:
            lead: The lead who engaged
            event_type: The type of engagement
            details: Additional details about the engagement (optional)
        """
        logger.info(f"Handling {event_type.value} engagement for lead {lead.id}")
        
        # Track the engagement
        self.engagement_tracker.track_engagement(lead, event_type, details)
        
        # Update lead status based on engagement
        if event_type == EngagementType.EMAIL_REPLY:
            lead.status = LeadStatus.ENGAGED
        elif event_type == EngagementType.MEETING_SCHEDULED:
            lead.status = LeadStatus.QUALIFIED
        
        # Check if the lead meets escalation criteria
        if self.engagement_tracker.check_escalation_criteria(lead):
            # In a real system, this would trigger a notification to a human
            logger.info(f"Lead {lead.id} meets escalation criteria, escalating to human")
            
            # Example: Update lead status
            lead.status = LeadStatus.QUALIFIED
            
            # Example: Add a note to the lead
            if not lead.notes:
                lead.notes = ""
            lead.notes += f"\n[{datetime.now().isoformat()}] Escalated to human due to high engagement."
    
    def pause_nurture_plan(self, plan_id: str) -> bool:
        """
        Pause a nurture plan.
        
        Args:
            plan_id: The ID of the nurture plan to pause
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Pausing nurture plan {plan_id}")
        
        # In a real system, this would retrieve the plan from a database
        plan = self.nurture_plans.get(plan_id)
        if not plan:
            logger.warning(f"Nurture plan {plan_id} not found")
            return False
        
        # Update the plan status
        plan.status = "paused"
        plan.updated_at = datetime.now()
        
        # In a real system, this would update the plan in a database
        self.nurture_plans[plan_id] = plan
        
        logger.info(f"Paused nurture plan {plan_id}")
        
        return True
    
    def resume_nurture_plan(self, plan_id: str) -> bool:
        """
        Resume a paused nurture plan.
        
        Args:
            plan_id: The ID of the nurture plan to resume
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Resuming nurture plan {plan_id}")
        
        # In a real system, this would retrieve the plan from a database
        plan = self.nurture_plans.get(plan_id)
        if not plan:
            logger.warning(f"Nurture plan {plan_id} not found")
            return False
        
        # Update the plan status
        plan.status = "active"
        plan.updated_at = datetime.now()
        
        # In a real system, this would update the plan in a database
        self.nurture_plans[plan_id] = plan
        
        logger.info(f"Resumed nurture plan {plan_id}")
        
        return True
