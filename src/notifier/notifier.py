"""
Notifier Module

This module provides functionality for sending notifications via different channels.
"""

import logging
import os
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from ..models.base_models import NotificationChannel
from ..utils.utils import logger


class Notifier(ABC):
    """
    Abstract base class for notifiers.
    
    This class defines the interface for all notifiers.
    """
    
    @abstractmethod
    def send_message(
        self,
        recipient: str,
        subject: str,
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to a recipient.
        
        Args:
            recipient: The recipient of the message
            subject: The subject of the message
            body: The body of the message
            **kwargs: Additional arguments specific to the notifier
            
        Returns:
            A dictionary with information about the sent message
        """
        pass
    
    @abstractmethod
    def check_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check the delivery status of a message.
        
        Args:
            message_id: The ID of the message to check
            
        Returns:
            A dictionary with information about the message status
        """
        pass


class EmailNotifier(Notifier):
    """
    Notifier for sending emails.
    """
    
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize the email notifier.
        
        Args:
            smtp_server: The SMTP server to use
            smtp_port: The SMTP port to use
            username: The username for SMTP authentication
            password: The password for SMTP authentication
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.sent_messages = {}  # In a real system, this would be a database
    
    def send_message(
        self,
        recipient: str,
        subject: str,
        body: str,
        sender: Optional[str] = None,
        html_body: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            recipient: The email recipient
            subject: The email subject
            body: The email body (plain text)
            sender: The email sender (optional)
            html_body: The email body in HTML format (optional)
            **kwargs: Additional arguments
            
        Returns:
            A dictionary with information about the sent email
        """
        logger.info(f"Sending email to {recipient}")
        
        # Use default sender if not provided
        sender = sender or self.username or "noreply@example.com"
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        
        # Attach plain text body
        msg.attach(MIMEText(body, "plain"))
        
        # Attach HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        
        try:
            # In a real system, this would actually send the email
            # For this implementation, we'll just log it
            logger.info(f"Would send email: From={sender}, To={recipient}, Subject={subject}")
            logger.debug(f"Email body: {body}")
            
            # Simulate sending email
            message_id = f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(recipient) % 10000}"
            
            # Store message info
            self.sent_messages[message_id] = {
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "sender": sender,
                "status": "sent",
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"Email sent successfully, message_id={message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "status": "sent"
            }
        
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check the delivery status of an email.
        
        Args:
            message_id: The ID of the email to check
            
        Returns:
            A dictionary with information about the email status
        """
        logger.info(f"Checking delivery status for message {message_id}")
        
        # In a real system, this would query the email service
        # For this implementation, we'll just return the stored status
        message_info = self.sent_messages.get(message_id)
        
        if not message_info:
            return {
                "success": False,
                "error": f"Message {message_id} not found"
            }
        
        return {
            "success": True,
            "message_id": message_id,
            "status": message_info.get("status", "unknown"),
            "recipient": message_info.get("recipient"),
            "sent_at": message_info.get("sent_at")
        }


class SlackNotifier(Notifier):
    """
    Notifier for sending Slack messages.
    
    Note: This is a placeholder implementation. In a real system, this would
    use the Slack API to send messages.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Slack notifier.
        
        Args:
            token: The Slack API token
        """
        self.token = token or os.getenv("SLACK_API_TOKEN")
        self.sent_messages = {}  # In a real system, this would be a database
    
    def send_message(
        self,
        recipient: str,
        subject: str,
        body: str,
        channel: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a Slack message.
        
        Args:
            recipient: The Slack user ID or channel
            subject: The message subject (used in message formatting)
            body: The message body
            channel: The Slack channel (optional, overrides recipient)
            **kwargs: Additional arguments
            
        Returns:
            A dictionary with information about the sent message
        """
        logger.info(f"Sending Slack message to {channel or recipient}")
        
        # Use channel if provided, otherwise use recipient
        destination = channel or recipient
        
        try:
            # In a real system, this would actually send the Slack message
            # For this implementation, we'll just log it
            logger.info(f"Would send Slack message to {destination}: {subject}")
            logger.debug(f"Message body: {body}")
            
            # Simulate sending message
            message_id = f"slack_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(destination) % 10000}"
            
            # Store message info
            self.sent_messages[message_id] = {
                "recipient": destination,
                "subject": subject,
                "body": body,
                "status": "sent",
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"Slack message sent successfully, message_id={message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "status": "sent"
            }
        
        except Exception as e:
            logger.error(f"Error sending Slack message to {destination}: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check the delivery status of a Slack message.
        
        Args:
            message_id: The ID of the message to check
            
        Returns:
            A dictionary with information about the message status
        """
        logger.info(f"Checking delivery status for message {message_id}")
        
        # In a real system, this would query the Slack API
        # For this implementation, we'll just return the stored status
        message_info = self.sent_messages.get(message_id)
        
        if not message_info:
            return {
                "success": False,
                "error": f"Message {message_id} not found"
            }
        
        return {
            "success": True,
            "message_id": message_id,
            "status": message_info.get("status", "unknown"),
            "recipient": message_info.get("recipient"),
            "sent_at": message_info.get("sent_at")
        }


class LogNotifier(Notifier):
    """
    Notifier that logs messages instead of sending them.
    
    This is useful as a fallback when other notifiers fail.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the log notifier.
        
        Args:
            log_file: Path to the log file (optional)
        """
        self.log_file = log_file
        self.sent_messages = {}  # In a real system, this would be a database
        
        # Configure file handler if log_file is provided
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            logger.addHandler(file_handler)
    
    def send_message(
        self,
        recipient: str,
        subject: str,
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log a message.
        
        Args:
            recipient: The intended recipient of the message
            subject: The message subject
            body: The message body
            **kwargs: Additional arguments
            
        Returns:
            A dictionary with information about the logged message
        """
        logger.info(f"Logging message for {recipient}: {subject}")
        logger.info(f"Message body: {body}")
        
        # Generate message ID
        message_id = f"log_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(recipient) % 10000}"
        
        # Store message info
        self.sent_messages[message_id] = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "logged",
            "sent_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message_id": message_id,
            "status": "logged"
        }
    
    def check_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check the status of a logged message.
        
        Args:
            message_id: The ID of the message to check
            
        Returns:
            A dictionary with information about the message status
        """
        logger.info(f"Checking status for logged message {message_id}")
        
        message_info = self.sent_messages.get(message_id)
        
        if not message_info:
            return {
                "success": False,
                "error": f"Message {message_id} not found"
            }
        
        return {
            "success": True,
            "message_id": message_id,
            "status": "logged",
            "recipient": message_info.get("recipient"),
            "sent_at": message_info.get("sent_at")
        }


def create_notifier(channel: NotificationChannel) -> Notifier:
    """
    Factory function to create a notifier based on channel.
    
    Args:
        channel: The notification channel
        
    Returns:
        A Notifier instance
        
    Raises:
        ValueError: If the channel is not supported
    """
    if channel == NotificationChannel.EMAIL:
        return EmailNotifier()
    elif channel == NotificationChannel.SLACK:
        return SlackNotifier()
    elif channel == NotificationChannel.LOG:
        return LogNotifier()
    else:
        raise ValueError(f"Unsupported notification channel: {channel}")
