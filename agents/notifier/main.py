import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Literal, Optional, Dict
import uuid
from datetime import datetime

class Notifier:
    def __init__(self):
        self.logger = self._setup_logging()
        self.tracking_pixels = {}  # {pixel_id: metadata}
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for notifier"""
        logger = logging.getLogger("notifier")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("data/notifier.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def deliver(
        self,
        message: str,
        recipient: str,
        method: Literal["email", "slack"],
        **kwargs
    ) -> Dict:
        """
        Deliver message with tracking
        Args:
            message: Content to send
            recipient: Email address or Slack channel ID
            method: Channel to use
            **kwargs:
                - subject (email only)
                - is_html (email only)
                - lead_id (for tracking)
        Returns:
            Dict with delivery status and metadata
        """
        try:
            if method == "email":
                return self._send_email(
                    message=message,
                    to_email=recipient,
                    subject=kwargs.get("subject", "Follow Up"),
                    is_html=kwargs.get("is_html", False),
                    lead_id=kwargs.get("lead_id")
                )
            elif method == "slack":
                return self._send_slack(
                    message=message,
                    channel_id=recipient
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
                
        except Exception as e:
            self.logger.error(f"Delivery failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _send_email(
        self,
        message: str,
        to_email: str,
        subject: str,
        is_html: bool = False,
        lead_id: Optional[str] = None
    ) -> Dict:
        """Send email with tracking pixel"""
        try:
            # Generate tracking data
            email_id = str(uuid.uuid4())
            tracking_data = {
                "email_id": email_id,
                "lead_id": lead_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Configure message
            msg = MIMEMultipart("alternative")
            msg["From"] = os.getenv("SMTP_USER")
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Add tracking pixel
            if is_html:
                pixel_url = self._generate_pixel_url(email_id, lead_id)
                message = message.replace(
                    "{tracking_pixel}",
                    f'<img src="{pixel_url}" width="1" height="1">'
                )
                msg.attach(MIMEText(message, "html"))
            else:
                msg.attach(MIMEText(message, "plain"))
            
            # Send via SMTP
            with smtplib.SMTP(
                host=os.getenv("SMTP_HOST"),
                port=int(os.getenv("SMTP_PORT", 587))
            ) as server:
                server.starttls()
                server.login(
                    user=os.getenv("SMTP_USER"),
                    password=os.getenv("SMTP_PASS")
                )
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {to_email}")
            return {
                "status": "sent",
                "email_id": email_id,
                "method": "email",
                **tracking_data
            }
            
        except Exception as e:
            self.logger.error(f"Email failed to {to_email}: {str(e)}")
            raise

    def _send_slack(self, message: str, channel_id: str) -> Dict:
        """Send message to Slack channel"""
        try:
            client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
            response = client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            
            self.logger.info(f"Slack message sent to {channel_id}")
            return {
                "status": "sent",
                "method": "slack",
                "channel": channel_id,
                "timestamp": datetime.now().isoformat(),
                "slack_response": response.data
            }
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e.response['error']}")
            raise
        except Exception as e:
            self.logger.error(f"Slack failed: {str(e)}")
            raise

    def _generate_pixel_url(self, email_id: str, lead_id: str) -> str:
        """Generate tracking pixel URL and store metadata"""
        pixel_id = str(uuid.uuid4())
        self.tracking_pixels[pixel_id] = {
            "email_id": email_id,
            "lead_id": lead_id,
            "timestamp": datetime.now().isoformat()
        }
        return f"{os.getenv('TRACKING_DOMAIN', 'http://localhost:8000')}/track/{pixel_id}"

# Example usage
if __name__ == "__main__":
    # Test configuration
    os.environ["SMTP_HOST"] = "smtp.example.com"
    os.environ["SMTP_USER"] = "test@example.com"
    os.environ["SMTP_PASS"] = "password"
    
    notifier = Notifier()
    
    # Test email delivery
    result = notifier.deliver(
        message="<html>Test email {tracking_pixel}</html>",
        recipient="test@example.com",
        method="email",
        subject="Test",
        is_html=True,
        lead_id="lead_123"
    )
    print(f"Email result: {result}")