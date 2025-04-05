"""
Test module for the Lead Nurturing System.

This module provides test cases for the Lead Nurturing System components.
"""

import os
import unittest
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.lead_parser.lead_parser import CSVLeadParser, create_lead_parser
from src.sales_nurturer.sales_nurturer import SalesNurturer, MessagePersonalizer, FollowUpScheduler, EngagementTracker
from src.notifier.notifier import EmailNotifier, SlackNotifier, LogNotifier, create_notifier
from src.agentverse_connector.agentverse_connector import AgentverseConnector, AgentRegistrar, AgentDiscoverer
from src.models.base_models import (
    Lead, FollowUp, MessageTemplate, NurturePlan, 
    EngagementEvent, EngagementType, NotificationChannel, LeadSource, LeadStatus
)
from src.utils.utils import generate_id


class TestLeadParser(unittest.TestCase):
    """Test cases for the Lead Parser component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test data directory if it doesn't exist
        os.makedirs("data/test", exist_ok=True)
        
        # Create a test CSV file
        self.test_csv_path = "data/test/test_leads.csv"
        with open(self.test_csv_path, "w") as f:
            f.write("first_name,last_name,email,company_name,job_title,industry\n")
            f.write("John,Doe,john.doe@example.com,Acme Inc,CEO,Technology\n")
            f.write("Jane,Smith,jane.smith@example.com,XYZ Corp,CTO,Healthcare\n")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove test CSV file
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
    
    def test_csv_lead_parser(self):
        """Test the CSV lead parser."""
        # Create a CSV lead parser
        parser = CSVLeadParser()
        
        # Parse the test CSV file
        leads = parser.parse_source(self.test_csv_path)
        
        # Check that we got the expected number of leads
        self.assertEqual(len(leads), 2)
        
        # Check the first lead
        lead1 = leads[0]
        self.assertEqual(lead1.first_name, "John")
        self.assertEqual(lead1.last_name, "Doe")
        self.assertEqual(lead1.email, "john.doe@example.com")
        self.assertEqual(lead1.company_name, "Acme Inc")
        self.assertEqual(lead1.job_title, "CEO")
        self.assertEqual(lead1.industry, "Technology")
        self.assertEqual(lead1.source, LeadSource.CSV)
        
        # Check the second lead
        lead2 = leads[1]
        self.assertEqual(lead2.first_name, "Jane")
        self.assertEqual(lead2.last_name, "Smith")
        self.assertEqual(lead2.email, "jane.smith@example.com")
        self.assertEqual(lead2.company_name, "XYZ Corp")
        self.assertEqual(lead2.job_title, "CTO")
        self.assertEqual(lead2.industry, "Healthcare")
        self.assertEqual(lead2.source, LeadSource.CSV)
    
    def test_create_lead_parser(self):
        """Test the lead parser factory function."""
        # Create parsers for different source types
        csv_parser = create_lead_parser("csv")
        pdf_parser = create_lead_parser("pdf")
        api_parser = create_lead_parser("api")
        
        # Check that we got the expected parser types
        self.assertIsInstance(csv_parser, CSVLeadParser)
        
        # Check that invalid source type raises ValueError
        with self.assertRaises(ValueError):
            create_lead_parser("invalid")


class TestSalesNurturer(unittest.TestCase):
    """Test cases for the Sales Nurturer component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test lead
        self.lead = Lead(
            id="lead_test_1",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            company_name="Acme Inc",
            job_title="CEO",
            industry="Technology"
        )
        
        # Create a test message template
        self.template = MessageTemplate(
            id="template_test_1",
            name="Test Template",
            subject="Hello, {first_name}!",
            body="Dear {first_name} {last_name},\n\nThank you for your interest in our products.\n\nBest regards,\nThe Team",
            channel=NotificationChannel.EMAIL
        )
    
    def test_message_personalizer(self):
        """Test the message personalizer."""
        # Create a message personalizer
        personalizer = MessagePersonalizer()
        
        # Personalize a message
        subject, body = personalizer.personalize_message(self.template, self.lead)
        
        # Check the personalized subject
        self.assertEqual(subject, "Hello, John!")
        
        # Check the personalized body
        expected_body = "Dear John Doe,\n\nThank you for your interest in our products.\n\nBest regards,\nThe Team"
        self.assertEqual(body, expected_body)
    
    def test_follow_up_scheduler(self):
        """Test the follow-up scheduler."""
        # Create a follow-up scheduler
        scheduler = FollowUpScheduler()
        
        # Schedule a follow-up
        scheduled_time = datetime.now() + timedelta(days=3)
        follow_up = scheduler.schedule_follow_up(
            lead=self.lead,
            template=self.template,
            scheduled_time=scheduled_time,
            trigger="test"
        )
        
        # Check the follow-up
        self.assertEqual(follow_up.lead_id, self.lead.id)
        self.assertEqual(follow_up.template_id, self.template.id)
        self.assertEqual(follow_up.scheduled_time, scheduled_time)
        self.assertEqual(follow_up.channel, NotificationChannel.EMAIL)
        self.assertEqual(follow_up.status, "scheduled")
        self.assertEqual(follow_up.trigger, "test")
        
        # Check the personalized subject and body
        self.assertEqual(follow_up.personalized_subject, "Hello, John!")
        expected_body = "Dear John Doe,\n\nThank you for your interest in our products.\n\nBest regards,\nThe Team"
        self.assertEqual(follow_up.personalized_body, expected_body)
    
    def test_engagement_tracker(self):
        """Test the engagement tracker."""
        # Create an engagement tracker
        tracker = EngagementTracker()
        
        # Track an engagement event
        event = tracker.track_engagement(
            lead=self.lead,
            event_type=EngagementType.EMAIL_REPLY,
            details={"message_id": "msg_123"}
        )
        
        # Check the event
        self.assertEqual(event.lead_id, self.lead.id)
        self.assertEqual(event.event_type, EngagementType.EMAIL_REPLY)
        self.assertEqual(event.details, {"message_id": "msg_123"})
        
        # Check engagement count
        count = tracker.get_engagement_count(self.lead, EngagementType.EMAIL_REPLY)
        self.assertEqual(count, 1)
        
        # Track more events
        tracker.track_engagement(
            lead=self.lead,
            event_type=EngagementType.EMAIL_REPLY,
            details={"message_id": "msg_456"}
        )
        tracker.track_engagement(
            lead=self.lead,
            event_type=EngagementType.EMAIL_REPLY,
            details={"message_id": "msg_789"}
        )
        
        # Check escalation criteria
        self.assertTrue(tracker.check_escalation_criteria(self.lead))
    
    def test_sales_nurturer(self):
        """Test the sales nurturer."""
        # Create a sales nurturer
        nurturer = SalesNurturer()
        
        # Create a nurture plan
        plan = nurturer.create_nurture_plan(
            lead=self.lead,
            templates=[self.template]
        )
        
        # Check the plan
        self.assertEqual(plan.lead_id, self.lead.id)
        self.assertEqual(len(plan.follow_ups), 1)
        self.assertEqual(plan.status, "active")
        
        # Handle an engagement event
        nurturer.handle_engagement_event(
            lead=self.lead,
            event_type=EngagementType.EMAIL_REPLY,
            details={"message_id": "msg_123"}
        )
        
        # Check that the lead status was updated
        self.assertEqual(self.lead.status, LeadStatus.ENGAGED)
        
        # Pause the nurture plan
        result = nurturer.pause_nurture_plan(plan.id)
        self.assertTrue(result)
        
        # Check that the plan status was updated
        self.assertEqual(nurturer.nurture_plans[plan.id].status, "paused")
        
        # Resume the nurture plan
        result = nurturer.resume_nurture_plan(plan.id)
        self.assertTrue(result)
        
        # Check that the plan status was updated
        self.assertEqual(nurturer.nurture_plans[plan.id].status, "active")


class TestNotifier(unittest.TestCase):
    """Test cases for the Notifier component."""
    
    def test_email_notifier(self):
        """Test the email notifier."""
        # Create an email notifier
        notifier = EmailNotifier()
        
        # Send a message
        result = notifier.send_message(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertTrue("message_id" in result)
        self.assertEqual(result["status"], "sent")
        
        # Check delivery status
        status = notifier.check_delivery_status(result["message_id"])
        self.assertTrue(status["success"])
        self.assertEqual(status["status"], "sent")
        self.assertEqual(status["recipient"], "test@example.com")
    
    def test_slack_notifier(self):
        """Test the Slack notifier."""
        # Create a Slack notifier
        notifier = SlackNotifier()
        
        # Send a message
        result = notifier.send_message(
            recipient="U123456",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertTrue("message_id" in result)
        self.assertEqual(result["status"], "sent")
        
        # Check delivery status
        status = notifier.check_delivery_status(result["message_id"])
        self.assertTrue(status["success"])
        self.assertEqual(status["status"], "sent")
        self.assertEqual(status["recipient"], "U123456")
    
    def test_log_notifier(self):
        """Test the log notifier."""
        # Create a log notifier
        notifier = LogNotifier()
        
        # Send a message
        result = notifier.send_message(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertTrue("message_id" in result)
        self.assertEqual(result["status"], "logged")
        
        # Check delivery status
        status = notifier.check_delivery_status(result["message_id"])
        self.assertTrue(status["success"])
        self.assertEqual(status["status"], "logged")
        self.assertEqual(status["recipient"], "test@example.com")
    
    def test_create_notifier(self):
        """Test the notifier factory function."""
        # Create notifiers for different channels
        email_notifier = create_notifier(NotificationChannel.EMAIL)
        slack_notifier = create_notifier(NotificationChannel.SLACK)
        log_notifier = create_notifier(NotificationChannel.LOG)
        
        # Check that we got the expected notifier types
        self.assertIsInstance(email_notifier, EmailNotifier)
        self.assertIsInstance(slack_notifier, SlackNotifier)
        self.assertIsInstance(log_notifier, LogNotifier)


class TestAgentverseConnector(unittest.TestCase):
    """Test cases for the Agentverse Connector component."""
    
    def test_agentverse_connector(self):
        """Test the Agentverse connector."""
        # Create an Agentverse connector
        connector = AgentverseConnector()
        
        # Register an agent
        agent_address = connector.register_agent(
            name="Test Agent",
            description="A test agent",
            capabilities=["test"]
        )
        
        # Check the agent address
        self.assertTrue(agent_address.startswith("fetch://"))
        
        # Get agent info
        agent_info = connector.get_agent_info(agent_address)
        self.assertEqual(agent_info["name"], "Test Agent")
        self.assertEqual(agent_info["description"], "A test agent")
        self.assertEqual(agent_info["capabilities"], ["test"])
        
        # Discover agents
        agents = connector.discover_agents(capabilities=["crm"])
        self.assertTrue(len(agents) > 0)
        
        # Send a message
        message_id = connector.send_message_to_agent(
            sender_address=agent_address,
            recipient_address="fetch://agent_crm_1",
            content={"text": "Hello, world!"},
            message_type="text"
        )
        self.assertIsNotNone(message_id)
    
    def test_agent_registrar(self):
        """Test the agent registrar."""
        # Create an agent registrar
        registrar = AgentRegistrar()
        
        # Register a sales nurturer
        agent_address = registrar.register_sales_nurturer(
            name="Test Sales Nurturer",
            description="A test sales nurturer"
        )
        
        # Check the agent address
        self.assertTrue(agent_address.startswith("fetch://"))
    
    def test_agent_discoverer(self):
        """Test the agent discoverer."""
        # Create an agent discoverer
        discoverer = AgentDiscoverer()
        
        # Discover agents
        crm_agents = discoverer.discover_crm_agents()
        calendar_agents = discoverer.discover_calendar_agents()
        email_agents = discoverer.discover_email_agents()
        
        # Check that we got some agents
        self.assertTrue(len(crm_agents) > 0)
        self.assertTrue(len(calendar_agents) > 0)
        self.assertTrue(len(email_agents) > 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the Lead Nurturing System."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test data directory if it doesn't exist
        os.makedirs("data/test", exist_ok=True)
        
        # Create a test CSV file
        self.test_csv_path = "data/test/test_leads.csv"
        with open(self.test_csv_path, "w") as f:
            f.write("first_name,last_name,email,company_name,job_title,industry\n")
            f.write("John,Doe,john.doe@example.com,Acme Inc,CEO,Technology\n")
            f.write("Jane,Smith,jane.smith@example.com,XYZ Corp,CTO,Healthcare\n")
        
        # Create a test template
        self.template = MessageTemplate(
            id="template_test_1",
            name="Test Template",
            subject="Hello, {first_name}!",
            body="Dear {first_name} {last_name},\n\nThank you for your interest in our products.\n\nBest regards,\nThe Team",
            channel=NotificationChannel.EMAIL
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove test CSV file
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
